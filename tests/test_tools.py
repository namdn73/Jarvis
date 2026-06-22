import json
import re
from unittest.mock import MagicMock, patch


# ─── tell_time_date ───────────────────────────────────────────────────────────

def test_tell_time_date_returns_string():
    from backend.agent.tools.datetime_tool import tell_time_date
    result = tell_time_date()
    assert isinstance(result, str)


def test_tell_time_date_format():
    """Return value must start with 'It is' and contain a 4-digit year."""
    from backend.agent.tools.datetime_tool import tell_time_date
    result = tell_time_date()
    assert result.startswith("It is ")
    assert re.search(r"\b\d{4}\b", result), "Expected a 4-digit year in the output"


def test_tell_time_date_contains_time():
    """Return value must contain HH:MM."""
    from backend.agent.tools.datetime_tool import tell_time_date
    result = tell_time_date()
    assert re.search(r"\d{2}:\d{2}", result), "Expected HH:MM in the output"


# ─── tavily_search ────────────────────────────────────────────────────────────

_FAKE_RESPONSE = {
    "results": [
        {"title": "AI news", "url": "https://example.com", "content": "snippet"}
    ]
}


def test_tavily_search_success_returns_json():
    from backend.agent.tools.search import tavily_search

    with patch("backend.agent.tools.search.TavilyClient") as MockClient:
        MockClient.return_value.search.return_value = _FAKE_RESPONSE
        result = tavily_search("AI news", mode="news")

    parsed = json.loads(result)
    assert parsed == _FAKE_RESPONSE


def test_tavily_search_uses_mode_param():
    """mode kwarg is forwarded to TavilyClient.search as topic=."""
    from backend.agent.tools.search import tavily_search

    with patch("backend.agent.tools.search.TavilyClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.search.return_value = {}
        tavily_search("something", mode="news")

    mock_instance.search.assert_called_once()
    _, kwargs = mock_instance.search.call_args
    assert kwargs.get("topic") == "news"


def test_tavily_search_default_mode_is_general():
    from backend.agent.tools.search import tavily_search

    with patch("backend.agent.tools.search.TavilyClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.search.return_value = {}
        tavily_search("something")

    _, kwargs = mock_instance.search.call_args
    assert kwargs.get("topic") == "general"


def test_tavily_search_exception_returns_json_error():
    from backend.agent.tools.search import tavily_search

    with patch("backend.agent.tools.search.TavilyClient") as MockClient:
        MockClient.return_value.search.side_effect = RuntimeError("bad key")
        result = tavily_search("something")

    parsed = json.loads(result)
    assert "error" in parsed
    assert "bad key" in parsed["error"]


# ─── open_result ──────────────────────────────────────────────────────────────

_RESULTS = [
    {"title": "BBC News", "url": "https://bbc.com"},
    {"title": "Reuters World", "url": "https://reuters.com"},
    {"title": "CNN Breaking", "url": "https://cnn.com"},
]


def test_open_result_by_word_one():
    from backend.agent.tools.browser import open_result

    with patch("backend.agent.tools.browser.webbrowser.open") as mock_open:
        msg = open_result("open the one", _RESULTS)

    mock_open.assert_called_once_with("https://bbc.com")
    assert "BBC News" in msg


def test_open_result_by_word_two():
    from backend.agent.tools.browser import open_result

    with patch("backend.agent.tools.browser.webbrowser.open") as mock_open:
        msg = open_result("open two please", _RESULTS)

    mock_open.assert_called_once_with("https://reuters.com")
    assert "Reuters" in msg


def test_open_result_by_digit():
    from backend.agent.tools.browser import open_result

    with patch("backend.agent.tools.browser.webbrowser.open") as mock_open:
        msg = open_result("open number 3", _RESULTS)

    mock_open.assert_called_once_with("https://cnn.com")
    assert "CNN" in msg


def test_open_result_by_title_fuzzy_match():
    from backend.agent.tools.browser import open_result

    with patch("backend.agent.tools.browser.webbrowser.open") as mock_open:
        msg = open_result("open the Reuters article", _RESULTS)

    mock_open.assert_called_once_with("https://reuters.com")


def test_open_result_no_match_returns_error_string():
    from backend.agent.tools.browser import open_result

    with patch("backend.agent.tools.browser.webbrowser.open") as mock_open:
        msg = open_result("open the zzzzz article", _RESULTS)

    mock_open.assert_not_called()
    assert "couldn't find" in msg.lower()


def test_open_result_empty_list():
    from backend.agent.tools.browser import open_result

    msg = open_result("open one", [])
    assert "no results" in msg.lower()


def test_open_result_missing_url():
    from backend.agent.tools.browser import open_result

    with patch("backend.agent.tools.browser.webbrowser.open") as mock_open:
        msg = open_result("open one", [{"title": "No-URL article", "url": ""}])

    mock_open.assert_not_called()
    assert "no url" in msg.lower()


def test_open_result_index_out_of_range():
    """Requesting result 5 when only 2 exist → error string."""
    from backend.agent.tools.browser import open_result

    with patch("backend.agent.tools.browser.webbrowser.open") as mock_open:
        msg = open_result("open five", _RESULTS[:2])

    mock_open.assert_not_called()
    assert "couldn't find" in msg.lower()
