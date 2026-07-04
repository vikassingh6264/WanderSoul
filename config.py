"""
Application configuration loaded from environment variables.

All config values are centralized here — nothing is hardcoded inline
in business logic. Uses python-dotenv to load from .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# --- Groq / LLM Settings ---
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "15"))

# --- Server Settings ---
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))

# --- Data Paths ---
DATA_DIR: str = os.path.join(os.path.dirname(__file__), "data")
DESTINATIONS_FILE: str = os.path.join(DATA_DIR, "destinations.json")

# --- Rate Limiting ---
RATE_LIMIT_REQUESTS: int = 10
RATE_LIMIT_WINDOW_SECONDS: int = 60
