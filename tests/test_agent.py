"""Tests for backend.agent.jarvis_agent.run().

The module-level _agent object is patched so no real LLM calls are made.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_result(content: str) -> dict:
    """Build the dict structure that _agent.ainvoke returns."""
    msg = MagicMock()
    msg.content = content
    return {"messages": [msg]}


# ─── JSON code-fence response ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_parses_json_fence():
    """Agent returns ```json ... ``` → dict is parsed and returned."""
    from backend.agent import jarvis_agent

    payload = {"spoken_summary": "It is Monday, June 23.", "items": []}
    fake_text = f"```json\n{json.dumps(payload)}\n```"

    with patch.object(jarvis_agent, "_agent") as mock_agent:
        mock_agent.ainvoke = AsyncMock(return_value=_make_result(fake_text))
        result = await jarvis_agent.run("what time is it?", "thread-1")

    assert result["spoken_summary"] == "It is Monday, June 23."
    assert result["items"] == []


# ─── Raw JSON response (no fences) ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_parses_raw_json():
    """Agent returns a raw JSON string without fences → parsed correctly."""
    from backend.agent import jarvis_agent

    payload = {
        "spoken_summary": "Here are the latest AI news.",
        "items": [{"title": "OpenAI Update", "url": "https://example.com"}],
    }

    with patch.object(jarvis_agent, "_agent") as mock_agent:
        mock_agent.ainvoke = AsyncMock(return_value=_make_result(json.dumps(payload)))
        result = await jarvis_agent.run("latest AI news", "thread-2")

    assert result["spoken_summary"] == "Here are the latest AI news."
    assert len(result["items"]) == 1
    assert result["items"][0]["title"] == "OpenAI Update"


# ─── Plain text response (not JSON) ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_plain_text_wrapped_as_spoken_summary():
    """Agent replies in plain text → returned as spoken_summary with empty items."""
    from backend.agent import jarvis_agent

    with patch.object(jarvis_agent, "_agent") as mock_agent:
        mock_agent.ainvoke = AsyncMock(
            return_value=_make_result("You're welcome, sir.")
        )
        result = await jarvis_agent.run("thank you", "thread-3")

    assert result["spoken_summary"] == "You're welcome, sir."
    assert result["items"] == []


# ─── Empty plain text (edge case) ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_empty_text_returns_error_fallback():
    """Empty agent reply → error fallback dict."""
    from backend.agent import jarvis_agent

    with patch.object(jarvis_agent, "_agent") as mock_agent:
        mock_agent.ainvoke = AsyncMock(return_value=_make_result(""))
        result = await jarvis_agent.run("something", "thread-4")

    assert "I'm sorry" in result["spoken_summary"]
    assert result["items"] == []


# ─── ainvoke raises an exception ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_exception_returns_error_fallback():
    """Any exception from ainvoke → safe error fallback dict, never raises."""
    from backend.agent import jarvis_agent

    with patch.object(jarvis_agent, "_agent") as mock_agent:
        mock_agent.ainvoke = AsyncMock(side_effect=RuntimeError("network down"))
        result = await jarvis_agent.run("query", "thread-5")

    assert "I'm sorry" in result["spoken_summary"]
    assert result["items"] == []


# ─── List content (multi-block message) ──────────────────────────────────────

@pytest.mark.asyncio
async def test_run_list_content_extracted():
    """LangChain can return content as a list of text blocks → joined correctly."""
    from backend.agent import jarvis_agent

    payload = {"spoken_summary": "Done.", "items": []}
    blocks = [{"type": "text", "text": json.dumps(payload)}]

    msg = MagicMock()
    msg.content = blocks
    fake_result = {"messages": [msg]}

    with patch.object(jarvis_agent, "_agent") as mock_agent:
        mock_agent.ainvoke = AsyncMock(return_value=fake_result)
        result = await jarvis_agent.run("query", "thread-6")

    assert result["spoken_summary"] == "Done."


# ─── thread_id is forwarded ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_forwards_thread_id():
    """run() must pass thread_id in the configurable config."""
    from backend.agent import jarvis_agent

    with patch.object(jarvis_agent, "_agent") as mock_agent:
        mock_agent.ainvoke = AsyncMock(
            return_value=_make_result('{"spoken_summary": "ok", "items": []}')
        )
        await jarvis_agent.run("ping", "my-session-id")

    _, kwargs = mock_agent.ainvoke.call_args
    config = kwargs.get("config", {})
    assert config.get("configurable", {}).get("thread_id") == "my-session-id"
