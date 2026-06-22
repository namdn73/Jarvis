import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
MODEL_AGENT    = os.getenv("MODEL_AGENT", "google_genai:gemini-2.0-flash")

# --- Server ---
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

# --- Audio ---
WHISPER_MODEL       = os.getenv("WHISPER_MODEL", "base")
TTS_VOICE           = os.getenv("TTS_VOICE", "en-GB-RyanNeural")
WAKE_WORD_THRESHOLD = float(os.getenv("WAKE_WORD_THRESHOLD", "0.5"))
SPEECH_THRESHOLD    = float(os.getenv("SPEECH_THRESHOLD", "0.02"))
SILENCE_THRESHOLD   = float(os.getenv("SILENCE_THRESHOLD", "0.01"))
SILENCE_FRAMES      = int(os.getenv("SILENCE_FRAMES", "24"))  # 1.5s @ ~16fps
LISTEN_TIMEOUT_S    = int(os.getenv("LISTEN_TIMEOUT_S", "10"))
ACTIVE_WINDOW_S     = int(os.getenv("ACTIVE_WINDOW_S", "30"))

# --- Paths ---
PROMPTS_DIR          = Path(os.getenv("PROMPTS_DIR", "backend/prompts"))
AGENT_DATA_DIR       = Path(os.getenv("AGENT_DATA_DIR", "backend/agent_data"))
SESSION_RECALL_WINDOW = int(os.getenv("SESSION_RECALL_WINDOW", "7200"))


def load_prompt(filename: str) -> str:
    """Read and return the contents of a prompt file from PROMPTS_DIR."""
    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")
