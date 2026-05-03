#!/usr/bin/env python3
"""
Trading-RIL MCP Server.

Two transports supported:
  stdio (local, default)         : trading-ril-server
  streamable-http (Cloud Run)    : MCP_TRANSPORT=streamable-http trading-ril-server
"""
import os, json, logging
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trading_ril.mcp_server")

mcp = FastMCP(
    "trading-ril",
    instructions=(
        "Trading Research Intelligence Layer. Peer-reviews trading signals using "
        "multi-agent AI frameworks before execution. Call ril_review() before placing "
        "any futures or equity trade. Call morning_signals() after 8am to get crowd "
        "sentiment for all instruments."
    ),
)


@mcp.tool(
    description=(
        "Peer-review a trading signal using 3 AI research frameworks: "
        "Bull/Bear debate, OASIS crowd simulation, and MiroFish swarm intelligence. "
        "Returns gate0_pass (bool), confidence_modifier (-0.05 to +0.05), "
        "and research_brief (human-readable). Use BEFORE placing any trade order."
    )
)
def ril_review(
    instrument: str,
    strategy: str,
    signal_confidence: float,
    news_context: str = "",
    firestore_project: str = "",
) -> str:
    """Review a trading signal before execution."""
    from trading_ril import RILGate0
    gate = RILGate0(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        firestore_project=firestore_project or None,
    )
    result = gate.evaluate(
        instrument=instrument,
        strategy=strategy,
        signal_confidence=signal_confidence,
        news_context=news_context,
    )
    return json.dumps({
        "gate0_pass":          result["gate0_pass"],
        "confidence_modifier": result["confidence_modifier"],
        "research_brief":      result["research_brief"],
        "layer0_rating":       result.get("layer0", {}).get("rating", "N/A"),
        "layer1_dissent":      result.get("layer1", {}).get("dissent_rate", 0.35),
        "layer2_direction":    result.get("layer2", {}).get("direction", "PENDING"),
        "elapsed_secs":        result.get("elapsed_secs", 0),
        "recommendation": (
            "PROCEED - research supports this trade"
            if result["gate0_pass"] else
            "BLOCK - all three research layers disagree with this trade"
        ),
    }, indent=2)


@mcp.tool(
    description=(
        "Get morning crowd sentiment for one or more instruments. "
        "Runs 50 AI trader agents through 5 interaction rounds. "
        "Returns direction (BULL/BEAR/MIXED), dissent_rate, and threshold_adj. "
        "Call once before market open. Takes 2-4 minutes for 6 instruments."
    )
)
def morning_signals(
    instruments: str = "MGC,MCL,MES,MNQ,MHG,MNG",
    firestore_project: str = "",
) -> str:
    """Run morning batch crowd simulation for all instruments."""
    from trading_ril.runners.morning_batch import MorningBatch
    inst_list = [i.strip() for i in instruments.split(",")]
    batch = MorningBatch(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        firestore_project=firestore_project or None,
    )
    results = batch.run(inst_list)
    output = {}
    for inst, r in results.items():
        dr = r.get("dissent_rate", 0.35)
        output[inst] = {
            "direction":     r.get("direction", "MIXED"),
            "dissent_rate":  dr,
            "consensus_pct": r.get("consensus_pct", 0.50),
            "threshold_adj": -0.005 if dr < 0.25 else (+0.030 if dr > 0.40 else 0.0),
            "signal": (
                "CLEAR - strong consensus, trade with confidence"
                if dr < 0.25 else
                "CAUTION - market split, raise your threshold"
                if dr > 0.40 else
                "NORMAL - typical market conditions"
            ),
        }
    return json.dumps(output, indent=2)


@mcp.tool(description="Explain what a dissent_rate value means for trading.")
def explain_dissent(dissent_rate: float) -> str:
    """Get the dissent rate interpretation for a given value."""
    if dissent_rate < 0.20:
        msg = "VERY STRONG consensus. Rare. High-confidence directional move likely."
        adj = -0.010
    elif dissent_rate < 0.25:
        msg = "Strong consensus. Good conditions for directional trading."
        adj = -0.005
    elif dissent_rate < 0.35:
        msg = "Normal market conditions. Proceed with standard thresholds."
        adj = 0.000
    elif dissent_rate < 0.40:
        msg = "Slightly elevated disagreement. Be aware of potential chop."
        adj = +0.010
    elif dissent_rate < 0.50:
        msg = "High disagreement. Market genuinely split. Raise your threshold."
        adj = +0.030
    else:
        msg = "Extreme disagreement. Do not trade unless exceptional setup."
        adj = +0.050
    return json.dumps({
        "dissent_rate": dissent_rate,
        "interpretation": msg,
        "recommended_threshold_adjustment": adj,
    }, indent=2)


def main():
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    port      = int(os.environ.get("PORT", "8080"))
    if transport == "streamable-http":
        # Cloud Run / hosted MCP: the runtime hostname is not known at build time
        # (e.g. trading-ril-1073730545783.us-central1.run.app), so disable
        # DNS rebinding protection. The endpoint is still public and HTTPS.
        from mcp.server.transport_security import TransportSecuritySettings
        mcp.settings.transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
        )
        mcp.settings.host = "0.0.0.0"
        mcp.settings.port = port
        logger.info(f"Starting trading-ril MCP server on streamable-http :{port}")
        mcp.run(transport="streamable-http")
    else:
        logger.info("Starting trading-ril MCP server on stdio")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
