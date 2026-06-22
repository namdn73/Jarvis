import difflib
import re
import sys
import webbrowser

_WORD_TO_INDEX = {"one": 0, "1": 0, "two": 1, "2": 1, "three": 2, "3": 2, "four": 3, "4": 3, "five": 4, "5": 4}
_INDEX_PATTERN = re.compile(r"\b(one|two|three|four|five|[1-5])\b", re.IGNORECASE)


def open_result(utterance: str, results: list[dict]) -> str:
    """Open a result card URL in the default browser by index or name reference."""
    if not results:
        return "There are no results to open, sir."

    idx: int | None = None

    match = _INDEX_PATTERN.search(utterance)
    if match:
        idx = _WORD_TO_INDEX.get(match.group(1).lower())

    if idx is None:
        titles = [r.get("title", "") for r in results]
        close = difflib.get_close_matches(utterance, titles, n=1, cutoff=0.3)
        if close:
            idx = titles.index(close[0])

    if idx is None or idx >= len(results):
        return "I couldn't find that result, sir."

    result = results[idx]
    url = result.get("url", "")
    title = result.get("title", "that result")

    if not url:
        return f"That result has no URL to open, sir."

    try:
        webbrowser.open(url)
        return f"Opening {title}, sir."
    except Exception as exc:
        print(f"[browser] webbrowser error: {exc}", file=sys.stderr)
        return "I was unable to open the browser, sir."
