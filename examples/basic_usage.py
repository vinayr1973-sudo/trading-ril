"""Basic usage example - Trading-RIL."""
from trading_ril import RILGate0

gate = RILGate0()  # uses ANTHROPIC_API_KEY env var

result = gate.evaluate(
    instrument="MGC",
    strategy="MACRO_GOLD",
    signal_confidence=0.93,
    news_context="Federal Reserve holds rates steady. Gold edges higher.",
)

print(f"Gate 0 Pass:      {result['gate0_pass']}")
print(f"Modifier:         {result['confidence_modifier']:+.4f}")
print(f"Brief:            {result['research_brief']}")
print(f"Research rating:  {result['layer0'].get('rating')}")
print(f"Crowd dissent:    {result['layer1'].get('dissent_rate', 0):.1%}")
print(f"Swarm direction:  {result['layer2'].get('direction')}")
print(f"Time taken:       {result.get('elapsed_secs')}s")
