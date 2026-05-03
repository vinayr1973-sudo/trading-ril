# Trading-RIL Skill

Peer-reviewed AI signal validation for trading bots.
Before any trade executes, run 3 research frameworks in parallel:
Bull/Bear debate + OASIS crowd simulation + MiroFish swarm intelligence.

## When to activate this skill

Trigger on ANY of these:
- "review this trade signal"
- "should I buy/sell [instrument]"
- "validate this trade before I execute"
- "what does the research say about [instrument]"
- "run RIL on [trade setup]"
- User has a futures or equity trade and wants a second opinion

## Core workflow

1. Call `ril_review()` with instrument, strategy, confidence, news
2. Read `gate0_pass` — if False, explain why the research disagrees
3. Read `confidence_modifier` — apply to the user's threshold
4. Read `research_brief` — share the summary with the user
5. If `layer1_dissent` > 0.40, warn: "Market is split — choppy session possible"

## Interpreting results

```
gate0_pass = True   → Research supports the trade
gate0_pass = False  → All 3 layers disagree — reconsider

confidence_modifier:
  -0.05 to -0.01  → Research agrees strongly — threshold can ease
  0.00            → Neutral — no change
  +0.01 to +0.05  → Research disagrees — raise your threshold

layer1_dissent (dissent_rate):
  < 0.25  → Strong consensus → directional move likely
  0.25-0.40 → Normal market
  > 0.40  → Market confused → choppy → sit tight
```

## Example usage

User: "Review this: MGC long, confidence 0.93, Fed held rates today"

Claude uses ril_review("MGC", "MACRO_GOLD", 0.93, "Fed held rates steady")

Response:
"Research review complete for MGC:
- Bull/Bear debate: Overweight (bulls won the debate)
- Crowd sentiment: 28% dissent (strong consensus — bullish)
- Swarm intelligence: BULL direction, 0.74 confidence
- Threshold adjustment: -1.0% (research supports this trade)
- Gate 0: PASS

The research supports this entry. Proceed with standard risk management."

## Supported instruments (default contexts built-in)

MGC (Micro Gold), MCL (Micro Crude), MES (Micro S&P 500),
MNQ (Micro Nasdaq), MHG (Micro Copper), MNG (Micro Nat Gas)

For any other instrument: provide instrument code + describe drivers in news_context.

## Install

```bash
pip install trading-ril
claude mcp add trading-ril -- uvx trading-ril-server
```

Or hosted:
```bash
claude mcp add --transport http trading-ril <MCP_URL_PLACEHOLDER>/mcp
```

## Research credits

TradingAgents (Tauric Research, Apache 2.0) · CAMEL-AI OASIS (Oxford/KAUST/Imperial, MIT) ·
FinMem (Stanford/IEEE) · FinAgent · ContestTrade (FinStep-AI)
