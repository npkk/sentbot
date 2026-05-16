import pytest
from unittest.mock import MagicMock, patch
from src.sentbot.sentiment_analyzer import SentimentAnalyzer

@pytest.fixture
def analyzer():
    return SentimentAnalyzer(api_key="mock-api-key")

@patch("src.sentbot.sentiment_analyzer.Groq")
def test_analyze_context_yes(mock_groq_class, analyzer):
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client
    
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "YES"
    mock_client.chat.completions.create.return_value = mock_completion
    
    result = analyzer.analyze_context("User1", "攻撃的なメッセージ", [])
    
    assert result is True
    mock_client.chat.completions.create.assert_called_once()

@patch("src.sentbot.sentiment_analyzer.Groq")
def test_analyze_context_no(mock_groq_class, analyzer):
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client
    
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "NO"
    mock_client.chat.completions.create.return_value = mock_completion
    
    result = analyzer.analyze_context("User1", "建設的なメッセージ", [])
    
    assert result is False
