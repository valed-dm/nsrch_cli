"""
Application Configuration Management.

Uses Pydantic's BaseSettings to load and validate configuration
from environment variables stored in a .env file.
"""

from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


class Settings(BaseSettings):
    """
    Defines the application's configuration settings.
    """

    # --- Application Metadata ---
    APP_NAME: str = "AI Search & Solve CLI"

    # --- Logging Configuration ---
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Path = OUTPUT_DIR / "app.log"
    SCREENSHOT_DIR: Path = PROJECT_ROOT / "screens"
    CAPTCHAS_DIR: Path = PROJECT_ROOT / "captchas"
    SUCCESS_DIR: Path = PROJECT_ROOT / "success"

    # --- Proxy Configuration (Optional) ---
    PROXY_HOST: Optional[str] = None
    PROXY_PORT: Optional[int] = None
    PROXY_USER: Optional[str] = None
    PROXY_PASS: Optional[str] = None

    NO_PROXY: Optional[str] = "localhost,127.0.0.1"

    USE_FREE_PROXIES: bool = True
    PROXYSCRAPE_URL: str = (
        "https://api.proxyscrape.com/v3/free-proxy-list/get?request="
        "displayproxies&proxy_format=ipport&format=json"
    )

    # --- AI Configuration ---
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    AI_TEXT_MODEL_NAME: str = "llama3"  # Or TinyLlama or llama3
    AI_TEXT_MODEL_API: str = "http://localhost:11434/api/generate"

    AI_VISION_MODEL_NAME: str = "llava"  # Or "bakllava"
    AI_VISION_MODEL_API: str = "http://localhost:11434/api/generate"

    # --- Browser & Scraper Settings ---
    REQUEST_TIMEOUT: int = 30
    IMPERSONATE_TARGET: str = "chrome116"  # For curl_cffi

    # --- Search Engine Configuration ---
    SEARCH_ENGINES: dict = {
        "google": {
            "name": "Google",
            "base_url": "https://www.google.com",
            "search_url_template": "https://www.google.com/search?q={query}&hl=ru",
            "consent_button_selectors": [
                'button[aria-label="Accept all"]',
                'button:has-text("Accept all")',
                'div[role="button"]:has-text("Принять все")',
            ],
            "captcha_keywords": ["unusual traffic", "prove you're not a robot"],
        },
        "yandex": {
            "name": "Yandex",
            "base_url": "https://yandex.ru",
            "search_url_template": "https://yandex.ru/search/?text={query}",
            "consent_button_selectors": [
                'button:has-text("Accept")',
                'button:has-text("Принять")',
            ],
            "captcha_keywords": [
                "Подтвердите, что вы не робот",
                "yandex.ru/showcaptcha",
                "CheckboxCaptcha-Inner",    # The main captcha container class
                "I'm not a robot",          # The specific text label
                "SmartCaptcha",             # The name of the system
            ],
        },
    }

    @field_validator(
        "PROXY_HOST", "PROXY_USER", "PROXY_PASS", "PROXY_PORT", mode="before"
    )
    def empty_string_as_none(cls, v):
        if v == "" or v is None:
            return None
        return v

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


def create_required_directories():
    """Ensures that all necessary output directories exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    settings.CAPTCHAS_DIR.mkdir(parents=True, exist_ok=True)
    settings.SUCCESS_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()


create_required_directories()
