**I built an open source peer-review engine for trading bot signals — uses 3 AI research frameworks in 45 seconds**

Before my IBKR futures bot executes any order, it runs a peer review — like academic papers before publication, but for trading signals.

Three frameworks run in parallel:
1. **Bull/Bear debate** (inspired by TradingAgents, Tauric Research) — optimist and pessimist agents argue the trade
2. **OASIS crowd simulation** (Oxford/KAUST/Imperial College research) — 50 trader agents with different personalities react to the news for 5 rounds
3. **MiroFish swarm intelligence** — swarm verdict: BULL, BEAR, or MIXED

The key signal that nobody else is using: **dissent_rate**

```
dissent_rate = 0.18  → strong consensus → proceed with confidence
dissent_rate = 0.43  → market genuinely split → raise threshold, sit tight
```

Traditional sentiment scoring tells you *which way* the market leans. Dissent rate tells you *how convinced* the market is. That's the signal that prevents you from trading into a choppy session.

**Open source, MIT license, pip install:**
```
pip install trading-ril
```

**Works as a Claude skill / MCP server:**
```
claude mcp add trading-ril -- uvx trading-ril-server
```

GitHub: https://github.com/vinayr1973-sudo/trading-ril

Built for IBKR micro futures (MGC, MCL, MES, MNQ, MHG, MNG) but works for any instrument. ~$0.03 per signal review.

Happy to answer questions about the architecture or how the dissent_rate signal works in practice.
