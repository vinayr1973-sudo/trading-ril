**Trading-RIL — Peer-reviewed AI signal validation for trading bots**

**Tagline:** Before your bot trades, 3 AI researchers debate the signal.

**Description:**
Trading-RIL is the open source peer-review engine for trading signals. Inspired by academic peer review — before any order executes, three independent AI research frameworks analyze the trade:

- 🐂 Bull researcher makes the case
- 🐻 Bear researcher challenges it
- 🧑‍🔬 50 crowd simulation agents argue for 5 rounds
- 🌊 Swarm intelligence renders a verdict

The output: `gate0_pass` (True/False) + `confidence_modifier` + `research_brief`

The key insight: `dissent_rate` tells you whether the market has conviction, not just direction. High dissent = choppy session = tighten your threshold.

Built on 5 peer-reviewed research papers:
- TradingAgents (Tauric Research, AAAI 2025)
- OASIS (Oxford, KAUST, Imperial College London)
- FinMem (Stanford/IEEE)
- FinAgent (multimodal trading AI)
- ContestTrade (competitive agent ranking)

Works as a Claude MCP skill: `claude mcp add trading-ril -- uvx trading-ril-server`

MIT. pip install. ~$0.03/signal. 45 seconds per review.

GitHub: https://github.com/vinayr1973-sudo/trading-ril
