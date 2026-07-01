"""
Module 1 — Settings & Configuration
Loads environment variables and provides a single config object
used across every agent, tool, and task.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from crewai import LLM 

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BRAND_GUIDELINES_DIR = DATA_DIR / "brand_guidelines"
MOCK_METRICS_DIR = DATA_DIR / "mock_metrics"
OUTPUTS_DIR = BASE_DIR / "outputs"

# ── Env ────────────────────────────────────────────────────────────────────────
load_dotenv(BASE_DIR / ".env")

# 🔑 Core API Keys
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# 🔥 Force Gemini API-key usage (avoid Vertex AI)
if GOOGLE_API_KEY:
    os.environ["GEMINI_API_KEY"] = GOOGLE_API_KEY
    # Optional but helps avoid Vertex routing confusion
    os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)

# 🧠 LLM Config
LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini/gemini-3.1-flash-lite-preview")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
#LLM_OPENAI_MODEL: str = os.getenv("LLM_OPENAI_MODEL", "")
#LLM_OPENAI_TEMPERATURE: float = float(os.getenv("LLM_OPENAI_TEMPERATURE", "0.7"))
#LLM_OPENAI_BASE_URL: str = os.getenv("LLM_OPENAI_BASE_URL", "")

# ✅ Central LLM config (USE THIS in agents)
def get_llm():
    return LLM(
        model=LLM_MODEL,
        api_key=GOOGLE_API_KEY,
        #temperature=LLM_OPENAI_TEMPERATURE,
        #base_url=LLM_OPENAI_BASE_URL,
        max_tokens=4096,
        #provider="google"
    )
# ── Platforms ──────────────────────────────────────────────────────────────────
SUPPORTED_PLATFORMS: list[str] = ["Instagram", "LinkedIn", "X (Twitter)", "Facebook"]

PLATFORM_LIMITS: dict[str, dict] = {
    "Instagram": {
        "max_caption_chars": 2200,
        "max_hashtags": 30,
        "best_hashtags": 11,
    },
    "LinkedIn": {
        "max_caption_chars": 3000,
        "max_hashtags": 5,
        "best_hashtags": 3,
    },
    "X (Twitter)": {
        "max_caption_chars": 280,
        "max_hashtags": 3,
        "best_hashtags": 2,
    },
    "Facebook": {
        "max_caption_chars": 63206,
        "max_hashtags": 10,
        "best_hashtags": 5,
    },
}

# ── Crew config ────────────────────────────────────────────────────────────────
MAX_ITERATIONS: int = 3
VERBOSE_LOGGING: bool = True
MEMORY_ENABLED: bool = True