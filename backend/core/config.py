import os


DEFAULT_MODEL_PROVIDER_URL = "https://fast.poloai.top"
DEFAULT_MODEL_CANDIDATES = ("qwen-turbo", "kimi", "glm", "deepseek")


def get_model_api_key() -> str | None:
    """Read model API key from environment variables."""
    return os.getenv("MODEL_API_KEY") or os.getenv("OPENAI_API_KEY")


def get_model_api_url() -> str:
    """Read model API base URL from env with a safe default."""
    return os.getenv("MODEL_API_URL", DEFAULT_MODEL_PROVIDER_URL).rstrip("/")


def get_model_candidates() -> list[str]:
    """Read candidate model list from env or return defaults."""
    raw = os.getenv("MODEL_CANDIDATES", "")
    if not raw:
        return list(DEFAULT_MODEL_CANDIDATES)

    candidates = [item.strip() for item in raw.split(",")]
    return [item for item in candidates if item]
