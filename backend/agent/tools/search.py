import json
import sys

from tavily import TavilyClient

from backend.config import TAVILY_API_KEY


def tavily_search(query: str, mode: str = "general") -> str:
    """Search the web. Use mode='news' for current events, 'general' for factual queries."""
    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(query, topic=mode, max_results=5)
        return json.dumps(response)
    except Exception as exc:
        print(f"[search] tavily error: {exc}", file=sys.stderr)
        return json.dumps({"error": str(exc)})
