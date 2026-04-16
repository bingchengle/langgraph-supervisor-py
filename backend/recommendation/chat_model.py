"""LangChain Chat 模型（Supervisor / React Agent），与 HTTP llm 共用环境变量。"""

from __future__ import annotations

try:
    from langchain_openai import ChatOpenAI
except ImportError as exc:
    raise ImportError("需要安装 langchain-openai") from exc

try:
    from core.config import get_model_api_key, get_model_api_url, get_model_candidates
except ImportError:
    from config import get_model_api_key, get_model_api_url, get_model_candidates


def get_chat_model():
    """OpenAI 兼容 Chat 接口（base_url = MODEL_API_URL/v1）。"""
    api_key = get_model_api_key()
    if not api_key:
        raise RuntimeError("需要配置 MODEL_API_KEY 或 OPENAI_API_KEY")

    base = get_model_api_url().rstrip("/")
    candidates = get_model_candidates()
    model_name = candidates[0] if candidates else "gpt-3.5-turbo"

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=f"{base}/v1",
        timeout=120.0,
        max_retries=2,
    )
