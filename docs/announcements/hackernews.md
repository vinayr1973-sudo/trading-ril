**Title:** Show HN: Trading-RIL — peer-reviewed signal validation for AI trading bots

**URL:** https://github.com/vinayr1973-sudo/trading-ril

**Text (optional, if Show HN policy requires it):**

I built this as the research layer for my own commodity futures trading bot (IBKR micro futures, paper trading). Wanted to share it because the core idea — running peer review on a trade signal before execution — felt like something the algo trading community would find useful.

Three frameworks run in parallel before any signal becomes an order:
1. Bull/Bear debate (inspired by TradingAgents from Tauric Research)
2. OASIS-style crowd simulation: 50 trader agents argue for 5 rounds (Oxford/KAUST/Imperial research)
3. MiroFish swarm intelligence verdict

The output that turned out to matter most isn't direction — it's `dissent_rate`. Tells you whether the market actually has conviction or is just flipping a coin. High dissent → choppy session → sit tight.

MIT licensed. pip installable. Also exposed as a Claude MCP server so any agent harness can call it. ~$0.03 per signal review using Claude Haiku.

Built solo. Happy to answer questions about the architecture, the failure modes I hit, or how the dissent_rate signal performed in backtests.
