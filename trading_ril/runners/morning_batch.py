"""Morning batch runner - populates OASIS + MiroFish signals before market open."""
import argparse, asyncio, logging, os, random
from datetime import date
from typing import Optional
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trading_ril.morning")

PERSONAS = [
    ("gold_bug", "Buys on dips. Long-term inflation hedge believer."),
    ("momentum", "Follows price trends. Buys breakouts."),
    ("macro", "Analyzes central bank policy before trading."),
    ("contrarian", "Fades the crowd. Sells when sentiment is extreme."),
    ("technical", "Chart-based. Follows support and resistance."),
    ("fundamental", "Supply/demand analysis and fair value."),
    ("fear_trader", "Buys defensive assets on uncertainty."),
    ("carry", "Follows interest rate differentials."),
    ("news_reactor", "Trades immediately on headlines."),
    ("patient", "Waits for only highest-conviction setups."),
]


class MorningBatch:
    def __init__(self, anthropic_api_key: Optional[str] = None,
                 firestore_project: Optional[str] = None):
        self.client = Anthropic(api_key=anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self._db = None
        if firestore_project:
            try:
                from google.cloud import firestore
                self._db = firestore.Client(project=firestore_project)
            except ImportError:
                pass

    def run(self, instruments: list, news_context: dict = None) -> dict:
        results = {}
        for inst in instruments:
            news = (news_context or {}).get(inst, f"{inst} commodity futures markets")
            results[inst] = asyncio.run(self._simulate(inst, news))
            if self._db:
                self._write(inst, results[inst])
        return results

    async def _simulate(self, instrument: str, news: str, n: int = 50, rounds: int = 5) -> dict:
        agents = [{"id": i, "type": PERSONAS[i % 10][0], "view": "NEUTRAL", "conviction": 0.5}
                  for i in range(n)]
        for rnd in range(rounds):
            active = random.sample(agents, min(10, n))
            b = sum(1 for a in agents if a["view"] == "BULL")
            e = sum(1 for a in agents if a["view"] == "BEAR")
            ctx = f"Community: {b} bull, {e} bear, {n - b - e} neutral of {n}. Round {rnd + 1}/{rounds}."
            batch_descs = "\n".join(f"Agent {a['id']} ({a['type']}): view={a['view']}"
                                     for a in active[:5])
            prompt = (f"Simulate commodity traders on {instrument}.\nNews: {news[:300]}\n{ctx}\n"
                      f"Agents:\n{batch_descs}\n\n"
                      f"For each output: Agent [ID]: [BULL/BEAR/NEUTRAL] conviction=[0.0-1.0]")
            try:
                resp = self.client.messages.create(
                    model="claude-haiku-4-5-20251001", max_tokens=150,
                    messages=[{"role": "user", "content": prompt}]
                ).content[0].text
                for line in resp.strip().split("\n"):
                    if not line.startswith("Agent"): continue
                    try:
                        aid = int(line.split(":")[0].replace("Agent", "").strip())
                        rest = line.split(":", 1)[1].strip()
                        ag = next((a for a in active if a["id"] == aid), None)
                        if ag:
                            ag["view"] = ("BULL" if "BULL" in rest else
                                           ("BEAR" if "BEAR" in rest else "NEUTRAL"))
                    except Exception: continue
            except Exception as e:
                logger.warning(f"Simulation batch failed: {e}")

        fb = sum(1 for a in agents if a["view"] == "BULL")
        fe = sum(1 for a in agents if a["view"] == "BEAR")
        bp, ep = fb / n, fe / n
        dr = min(bp, ep) / max(bp + ep, 0.01)
        direction = "BULL" if bp > 0.58 else ("BEAR" if ep > 0.58 else "MIXED")
        return {"direction": direction, "dissent_rate": round(dr, 3),
                "consensus_pct": round(max(bp, ep), 3),
                "bull_count": fb, "bear_count": fe}

    def _write(self, instrument, result):
        try:
            from google.cloud import firestore
            today = date.today().isoformat()
            result.update({"date": today, "instrument": instrument,
                           "status": "complete", "updated_at": firestore.SERVER_TIMESTAMP})
            self._db.collection("tah2_oasis_signals").document(
                f"{today}_{instrument}").set(result, merge=True)
        except Exception as e:
            logger.warning(f"Write failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Trading-RIL Morning Batch")
    parser.add_argument("--instruments", nargs="+",
                        default=["MGC", "MCL", "MES", "MNQ", "MHG", "MNG"])
    parser.add_argument("--firestore-project", default=None)
    args = parser.parse_args()
    batch = MorningBatch(firestore_project=args.firestore_project)
    results = batch.run(args.instruments)
    for inst, r in results.items():
        print(f"{inst}: {r.get('direction', '?')} dissent={r.get('dissent_rate', 0):.2f}")


if __name__ == "__main__":
    main()
