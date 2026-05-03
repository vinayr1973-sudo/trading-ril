"""Basic tests for RILGate0."""
from unittest.mock import patch, MagicMock


def test_neutral_on_error():
    """Gate 0 fails safe - always returns neutral on error."""
    from trading_ril import RILGate0
    gate = RILGate0(anthropic_api_key="bad-key")
    result = gate._neutral("test error")
    assert result["gate0_pass"] is True
    assert result["confidence_modifier"] == 0.0
    assert "test error" in result["research_brief"]


def test_gate0_returns_required_keys():
    """Gate 0 always returns the contract keys."""
    with patch("trading_ril.gate0.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value.content = [
            MagicMock(text="FINAL_RATING: Hold\nDEBATE_INTENSITY: low\nONE_LINE: neutral market")
        ]
        from trading_ril import RILGate0
        gate = RILGate0(anthropic_api_key="test-key")
        result = gate.evaluate("MGC", "MACRO_GOLD", 0.93)
        assert "gate0_pass" in result
        assert "confidence_modifier" in result
        assert "research_brief" in result
        assert isinstance(result["gate0_pass"], bool)
        assert -0.05 <= result["confidence_modifier"] <= 0.05
