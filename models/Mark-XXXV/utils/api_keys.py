"""
Shared API key loader - reads from .env first, falls back to config JSON.
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv


def _find_env_file(start_dir: Path) -> Path | None:
    """Walk up from start_dir looking for .env file."""
    current = start_dir
    while current != current.parent:
        env_path = current / ".env"
        if env_path.exists():
            return env_path
        current = current.parent
    return None


def _load_env_keys() -> dict:
    """Load API keys from .env file."""
    env_file = _find_env_file(Path(__file__).resolve().parent)
    if env_file:
        load_dotenv(env_file, override=True)
    return {}


def get_gemini_api_key() -> str:
    """Get Gemini API key from .env, then config JSON, then environment."""
    # 1. Check environment variable (may be set by .env loading)
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key and not key.startswith("ENV:"):
        return key
    
    # 2. Load .env explicitly
    _load_env_keys()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key and not key.startswith("ENV:"):
        return key
    
    # 3. Fallback to config JSON (for backward compat)
    config_paths = [
        Path(__file__).resolve().parent.parent / "config" / "api_keys.json",  # Mark-XXXV
        Path(__file__).resolve().parent.parent.parent / "Mark-XXXV" / "config" / "api_keys.json",
    ]
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path) as f:
                    data = json.load(f)
                    val = data.get("gemini_api_key", "")
                    if val and not val.startswith("ENV:"):
                        return val
            except (json.JSONDecodeError, KeyError):
                continue
    
    return ""


def get_serper_api_key() -> str:
    """Get Serper API key from .env, then config JSON, then environment."""
    key = os.environ.get("SERPER_API_KEY", "").strip()
    if key and not key.startswith("ENV:"):
        return key
    
    _load_env_keys()
    key = os.environ.get("SERPER_API_KEY", "").strip()
    if key and not key.startswith("ENV:"):
        return key
    
    # Fallback to Omnis config.json
    config_paths = [
        Path(__file__).resolve().parent.parent.parent / "Omnis" / "config.json",
        Path(__file__).resolve().parent.parent / "config.json",
    ]
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path) as f:
                    data = json.load(f)
                    val = data.get("serper_api_key", "")
                    if val and not val.startswith("ENV:"):
                        return val
            except (json.JSONDecodeError, KeyError):
                continue
    
    return ""


def has_api_key(name: str = "gemini") -> bool:
    """Check if an API key is configured."""
    if name == "gemini":
        return bool(get_gemini_api_key())
    elif name == "serper":
        return bool(get_serper_api_key())
    return False
