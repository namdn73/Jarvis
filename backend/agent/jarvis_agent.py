import json
import os
import re
import sys

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver

from backend.config import AGENT_DATA_DIR, GEMINI_API_KEY, MODEL_AGENT, load_prompt
from backend.agent.tools.search import tavily_search
from backend.agent.tools.datetime_tool import tell_time_date

# langchain-google-genai reads GOOGLE_API_KEY; bridge from our GEMINI_API_KEY
os.environ.setdefault("GOOGLE_API_KEY", GEMINI_API_KEY)

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
    # List of content blocks — concatenate all text blocks
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
    except Exception as exc:
        print(f"[agent] error: {exc}", file=sys.stderr)
        return {"spoken_summary": "I'm sorry sir, I encountered an error.", "items": []}
