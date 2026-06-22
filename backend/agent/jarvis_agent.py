import json
import os
import re
import sys

from deepagents import (
    GeneralPurposeSubagentProfile,
    HarnessProfile,
    create_deep_agent,
    register_harness_profile,
)
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver

from backend.config import AGENT_DATA_DIR, GEMINI_API_KEY, MODEL_AGENT, load_prompt
from backend.agent.tools.search import tavily_search
from backend.agent.tools.datetime_tool import tell_time_date

# langchain-google-genai reads GOOGLE_API_KEY; bridge from our GEMINI_API_KEY
os.environ.setdefault("GOOGLE_API_KEY", GEMINI_API_KEY)

# Strip all built-in harness tools so Gemini only sees our 2 custom tools.
# This removes ~6 extra tool definitions from the context and eliminates the
# general-purpose subagent delegation round-trip — cuts ~0.5s per query.
register_harness_profile(
    MODEL_AGENT,
    HarnessProfile(
        excluded_tools=frozenset({
            "write_todos", "ls", "read_file", "write_file",
            "edit_file", "glob", "grep", "execute",
        }),
        system_prompt_suffix=(
            "Answer queries directly and immediately. "
            "Do not plan. Do not write todos. "
            "Respond in one pass without intermediate steps."
        ),
        general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
    ),
)

_backend = FilesystemBackend(
    root_dir=str(AGENT_DATA_DIR.resolve()),
    virtual_mode=True,
)
_checkpointer = MemorySaver()
_agent = create_deep_agent(
    model=MODEL_AGENT,
    tools=[tavily_search, tell_time_date],
    system_prompt=load_prompt("system.md"),
    memory=["/memories/AGENTS.md"],
    backend=_backend,
    checkpointer=_checkpointer,
)


def _extract_text(content: str | list) -> str:
    """Normalise LangChain message content to a plain string."""
    if isinstance(content, str):
        return content
    parts = [block["text"] for block in content if isinstance(block, dict) and block.get("type") == "text"]
    return "\n".join(parts)


async def run(query: str, thread_id: str) -> dict:
    """Invoke the agent and return a parsed response dict."""
    try:
        result = await _agent.ainvoke(
            {"messages": [{"role": "user", "content": query}]},
            config={"configurable": {"thread_id": thread_id}},
        )
        raw_text = _extract_text(result["messages"][-1].content)
        match = re.search(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # Agent replied in plain text (e.g. "You're welcome, sir.") — use it directly
        if raw_text:
            return {"spoken_summary": raw_text, "items": []}
        return {"spoken_summary": "I'm sorry sir, I encountered an error.", "items": []}
    except Exception as exc:
        print(f"[agent] error: {exc}", file=sys.stderr)
        return {"spoken_summary": "I'm sorry sir, I encountered an error.", "items": []}
