# Trading-RIL — Research Intelligence Layer

**Open source peer-reviewed signal validation for AI trading bots.**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![Claude Skill](https://img.shields.io/badge/Claude-Skill-orange.svg)](https://claude.ai)

Before your trading bot places any order, Trading-RIL runs a **peer review** of the signal using three independent research engines. Like an academic paper reviewed before publication — except it runs in 45 seconds and costs ~$0.03.

## What It Does

Every trading signal gets reviewed by three layers before execution:

| Layer | Engine | What It Adds |
|-------|--------|--------------|
| **Layer 0** | Bull/Bear Debate (TradingAgents inspired) | Structured debate between optimist and pessimist agents |
| **Layer 1** | OASIS Crowd Simulation | 50 trader agents argue for 5 rounds → dissent_rate |
| **Layer 2** | MiroFish Swarm Intelligence | Swarm sentiment direction + confidence score |

**Output**: `gate0_pass` (True/False) + `confidence_modifier` (-0.05 to +0.05) + `research_brief` (human-readable)

## The Key Signal Nobody Else Has: `dissent_rate`

```
dissent_rate = 0.18  → Strong consensus → lower threshold (more trades)
dissent_rate = 0.43  → Market confused → raise threshold (sit tight)
```

High dissent means the market is genuinely split. Traditional sentiment scoring misses this entirely.

## Quick Start

```bash
pip install trading-ril
```

```python
from trading_ril import RILGate0

# Layer 0 only (Bull/Bear debate). No external state required.
gate = RILGate0(anthropic_api_key="sk-ant-...")

result = gate.evaluate(
    instrument="MGC",           # Micro Gold Futures
    strategy="MACRO_GOLD",
    signal_confidence=0.93,
    news_context="Fed holds rates. Gold edges higher on dollar weakness.",
)

print(result["gate0_pass"])           # True
print(result["confidence_modifier"])  # -0.010 (research agrees - ease threshold)
print(result["research_brief"])       # "MGC MACRO_GOLD | Research:Overweight | Crowd:n/a | Swarm:n/a | ..."
```

## Enabling all 3 layers (optional)

By default Trading-RIL runs **Layer 0 only** (Bull/Bear debate). Layers 1 (OASIS crowd) and 2 (MiroFish swarm) require pre-computed daily signals stored in your own Firestore project — populated by `trading-ril-morning` once per day before market open.

To enable Layers 1 + 2, pass `firestore_project`:

```python
gate = RILGate0(
    anthropic_api_key="sk-ant-...",
    firestore_project="your-gcp-project-id",  # reads tah2_oasis_signals + tah2_mirofish_signals
)
```

And populate your Firestore once per day (typically 8am market local time):

```bash
trading-ril-morning --instruments MGC MCL MES MNQ MHG MNG \
                    --firestore-project your-gcp-project-id
```

**Cost note:** the morning batch costs ~$0.08 (50 agents × 5 rounds for 6 instruments). Per-signal Layer 0 review is ~$0.03. Total: ~$0.38/day for 10 trades. Without the morning batch, you only pay the per-signal cost (~$0.03/trade).

## As a Claude Skill / MCP Server

Add to Claude Code (stdio, runs locally):

```bash
claude mcp add trading-ril -- uvx trading-ril-server
```

Or connect to the hosted MCP server (HTTP):
```bash
claude mcp add --transport http trading-ril https://trading-ril-1073730545783.us-central1.run.app/mcp
```

The hosted server runs **Layer 0 only** (no Firestore — keeps it stateless and free for everyone).
To get all 3 layers from the hosted server, pass your own `firestore_project` to the tool:

```
Review this trade with my Firestore: MGC, MACRO_GOLD, confidence 0.93,
firestore_project=my-gcp-project-id, news: "Fed holds rates"
```

(Your GCP project's Firestore needs `tah2_oasis_signals` and `tah2_mirofish_signals` collections — populated by `trading-ril-morning`. The hosted server's service account does not have read access to your Firestore — it uses your project's own credentials via the MCP tool argument.)

Then in Claude Code, ask:
```
Review this gold trade: MGC, MACRO_GOLD strategy, confidence 0.93,
news: "Fed holds rates steady"
```

## Supported Instruments

| Symbol | Name | Typical Drivers |
|--------|------|----------------|
| MGC | Micro Gold | Fed, DXY, inflation, ETF flows |
| MCL | Micro Crude Oil | OPEC, EIA, demand |
| MES | Micro S&P 500 | Earnings, Fed, VIX |
| MNQ | Micro Nasdaq | Tech earnings, rates |
| MHG | Micro Copper | China PMI, EV demand |
| MNG | Micro Natural Gas | Weather, storage |
| **Custom** | Any instrument | You define the context |

## Morning Batch Mode

Run once before market open. Populates all six instruments:

```bash
trading-ril-morning --instruments MGC MCL MES MNQ MHG MNG
```

Outputs `dissent_rate` + `direction` + `confidence` per instrument.
Gate 0 reads these instantly — no simulation overhead per trade.

## Research Foundation

Trading-RIL synthesizes five academic frameworks:

| Paper | Institution | Contribution |
|-------|-------------|--------------|
| [TradingAgents](https://arxiv.org/abs/2412.20138) | Tauric Research | Bull/Bear debate framework |
| [FinMem](https://arxiv.org/abs/2311.13743) | Stanford/IEEE | 3-layer memory architecture |
| [FinAgent](https://arxiv.org/abs/2402.18485) | Multimodal AI | Dual-level reflection |
| [OASIS](https://arxiv.org/abs/2411.11581) | Oxford/KAUST/Imperial | Social simulation engine |
| [ContestTrade](https://arxiv.org/abs/2508.00554) | FinStep-AI | Competitive agent ranking |

## Cost

| Component | Daily Cost |
|-----------|-----------|
| Morning batch (6 instruments) | ~$0.08 |
| Per-signal review (10/day) | ~$0.30 |
| **Total** | **~$0.38/day ≈ $11.50/month** |

Built entirely on open source. MIT licensed. No per-seat fees. No cloud lock-in.

## Who Built This

Trading-RIL is the open source release of the research layer built for **TAH-2** — a personal commodity futures trading system on IBKR PRO by Vinay Sharma.

TAH-2 paper trades on GLOBEX micro futures (MGC, MCL, MES, MNQ, MHG, MNG). Every signal goes through this peer review before execution.

## Contributing

PRs welcome. Areas that need help:
- Additional instrument contexts (crypto, equity, FX)
- More agent personas for OASIS simulation
- Integration examples (Alpaca, Interactive Brokers, Binance)
- Backtesting framework

## License

MIT. Do whatever you want with it. If it makes you money, consider contributing back.
