"""
Gate 0 - Pre-signal peer review engine.
Three layers run in parallel. Fails safe on timeout/error.
"""
import asyncio, logging, os, time
from datetime import date
from typing import Optional
from anthropic import Anthropic

logger = logging.getLogger("trading_ril.gate0")

INSTRUMENT_CONTEXT = {
    "MGC": {"name": "Micro Gold",      "drivers": "Fed policy, DXY, inflation, ETF flows"},
    "MCL": {"name": "Micro Crude Oil", "drivers": "OPEC, EIA inventory, demand, crack spreads"},
    "MES": {"name": "Micro S&P 500",   "drivers": "earnings, Fed, VIX, sector rotation"},
    "MNQ": {"name": "Micro Nasdaq",    "drivers": "tech earnings, rate sensitivity"},
    "MHG": {"name": "Micro Copper",    "drivers": "China PMI, EV demand, LME inventories"},
    "MNG": {"name": "Micro Nat Gas",   "drivers": "weather, storage levels, LNG exports"},
}

RATING_MODIFIERS = {
    "Buy": -0.010, "Overweight": -0.005, "Hold": 0.000,
    "Underweight": +0.020, "Sell": +0.030,
}


class RILGate0:
    """
    Research Intelligence Layer Gate 0.

    Args:
        anthropic_api_key: Anthropic API key (falls back to ANTHROPIC_API_KEY env var)
        firestore_project: Optional GCP project for persistent OASIS/MiroFish signals
        timeout_secs:      Max seconds before neutral fallback (default 90)
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        firestore_project: Optional[str] = None,
        timeout_secs: int = 90,
    ):
        self.client  = Anthropic(api_key=anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.timeout = timeout_secs
        self._db     = None

        if firestore_project:
            try:
                from google.cloud import firestore
                self._db = firestore.Client(project=firestore_project)
            except ImportError:
                logger.warning("google-cloud-firestore not installed - running without persistence")

    def evaluate(
        self,
        instrument: str,
        strategy: str,
        signal_confidence: float,
        news_context: str = "",
    ) -> dict:
        """
        Run peer review on a trading signal.

        Returns dict with: gate0_pass (bool), confidence_modifier (float),
        research_brief (str), layer0/1/2 details, elapsed_secs.
        """
        ctx = INSTRUMENT_CONTEXT.get(instrument, {
            "name": instrument,
            "drivers": "market fundamentals and sentiment",
        })
        start = time.time()
        try:
            result = asyncio.run(asyncio.wait_for(
                self._run_all(instrument, strategy, signal_confidence, news_context, ctx),
                timeout=self.timeout,
            ))
            result["elapsed_secs"] = round(time.time() - start, 1)
            if self._db:
                self._persist(instrument, strategy, result)
            return result
        except asyncio.TimeoutError:
            return self._neutral(f"timeout after {self.timeout}s")
        except Exception as e:
            return self._neutral(str(e))

    async def _run_all(self, instrument, strategy, confidence, news, ctx):
        l0, l1, l2 = await asyncio.gather(
            self._bull_bear_debate(instrument, strategy, confidence, news, ctx),
            self._read_oasis(instrument),
            self._read_mirofish(instrument),
            return_exceptions=True,
        )
        l0 = l0 if isinstance(l0, dict) else {}
        l1 = l1 if isinstance(l1, dict) else {}
        l2 = l2 if isinstance(l2, dict) else {}

        total = max(-0.05, min(0.05,
            l0.get("modifier", 0.0) +
            l1.get("modifier", 0.0) +
            l2.get("modifier", 0.0)
        ))
        hard_no = (
            l0.get("rating") == "Sell" and
            l1.get("dissent_rate", 0) > 0.50 and
            l2.get("direction") in ("BEAR", "PENDING")
        )
        brief = (
            f"{instrument} {strategy} conf={confidence:.3f} | "
            f"Research:{l0.get('rating', 'Hold')} | "
            f"Crowd dissent:{l1.get('dissent_rate', 0.35) * 100:.0f}% | "
            f"Swarm:{l2.get('direction', 'PENDING')} | "
            f"Threshold adj:{total * 100:+.1f}%"
        )
        return {
            "gate0_pass": not hard_no,
            "confidence_modifier": round(total, 4),
            "research_brief": brief,
            "hard_no": hard_no,
            "layer0": l0, "layer1": l1, "layer2": l2,
        }

    async def _bull_bear_debate(self, instrument, strategy, confidence, news, ctx):
        name, drivers = ctx.get("name", instrument), ctx.get("drivers", "markets")
        nc = news[:400] if news else "No specific news."

        async def haiku(prompt):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: (
                self.client.messages.create(
                    model="claude-haiku-4-5-20251001", max_tokens=250,
                    messages=[{"role": "user", "content": prompt}]
                ).content[0].text
            ))

        bull_r, bear_r = await asyncio.gather(
            haiku(f"Bullish commodity researcher on {name}.\n"
                  f"Signal: {strategy} conf={confidence:.3f}\nDrivers: {drivers}\nNews: {nc}\n\n"
                  f"3-point BULL CASE (each <=20 words).\n"
                  f"BULL CASE: [p1] | [p2] | [p3]\nRATING: Buy or Overweight or Hold"),
            haiku(f"Skeptical bear researcher on {name}.\n"
                  f"Signal: {strategy} conf={confidence:.3f}\nDrivers: {drivers}\nNews: {nc}\n\n"
                  f"3-point BEAR CASE (each <=20 words).\n"
                  f"BEAR CASE: [p1] | [p2] | [p3]\nRATING: Hold or Underweight or Sell"),
        )
        synth = await haiku(
            f"Portfolio Manager adjudicating:\nBULL: {bull_r[:200]}\nBEAR: {bear_r[:200]}\n\n"
            f"Output ONLY:\nFINAL_RATING: [Buy/Overweight/Hold/Underweight/Sell]\n"
            f"DEBATE_INTENSITY: [low/medium/high]\nONE_LINE: [verdict <=20 words]"
        )
        rating, intensity = "Hold", "low"
        for line in synth.split("\n"):
            if "FINAL_RATING:" in line:
                r = line.split(":")[-1].strip()
                if r in RATING_MODIFIERS: rating = r
            if "DEBATE_INTENSITY:" in line:
                intensity = line.split(":")[-1].strip().lower()

        mod = RATING_MODIFIERS.get(rating, 0.0) + (0.010 if intensity == "high" else 0.0)
        return {"modifier": round(mod, 4), "rating": rating, "intensity": intensity}

    async def _read_oasis(self, instrument) -> dict:
        if not self._db:
            return {"modifier": 0.0, "dissent_rate": 0.35, "status": "no_firestore"}
        today = date.today().isoformat()
        doc = self._db.collection("tah2_oasis_signals").document(f"{today}_{instrument}").get()
        if not doc.exists or doc.to_dict().get("status") != "complete":
            return {"modifier": 0.0, "dissent_rate": 0.35, "status": "pending"}
        d = doc.to_dict()
        dr = d.get("dissent_rate", 0.35)
        mod = -0.005 if dr < 0.25 else (+0.030 if dr > 0.40 else 0.0)
        return {"modifier": round(mod, 4), "dissent_rate": dr, "direction": d.get("direction", "MIXED")}

    async def _read_mirofish(self, instrument) -> dict:
        if not self._db:
            return {"modifier": 0.0, "direction": "PENDING", "status": "no_firestore"}
        today = date.today().isoformat()
        doc = self._db.collection("tah2_mirofish_signals").document(f"{today}_{instrument}").get()
        if not doc.exists or doc.to_dict().get("status") != "complete":
            return {"modifier": 0.0, "direction": "PENDING", "status": "pending"}
        d = doc.to_dict()
        direction, conf = d.get("direction", "MIXED"), d.get("confidence", 0.50)
        if direction == "BULL" and conf > 0.70:   mod = -0.010
        elif direction == "BEAR" and conf > 0.70: mod = +0.025
        elif direction == "MIXED":                mod = +0.020
        else:                                     mod = 0.0
        return {"modifier": round(mod, 4), "direction": direction, "confidence": conf}

    def _persist(self, instrument, strategy, result):
        try:
            from google.cloud import firestore
            self._db.collection("trading_ril_reviews").add({
                "instrument": instrument, "strategy": strategy,
                "gate0_pass": result["gate0_pass"],
                "confidence_modifier": result["confidence_modifier"],
                "research_brief": result["research_brief"],
                "reviewed_at": firestore.SERVER_TIMESTAMP,
            })
        except Exception as e:
            logger.warning(f"Persistence failed: {e}")

    def _neutral(self, reason: str) -> dict:
        return {
            "gate0_pass": True, "confidence_modifier": 0.0,
            "research_brief": f"RIL {reason} - neutral pass",
            "hard_no": False, "layer0": {}, "layer1": {}, "layer2": {},
        }
