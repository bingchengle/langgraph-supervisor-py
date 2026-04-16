"""单次请求内共享的推荐状态（Supervisor 各 Tool 读写，避免用 messages 传大块 JSON）。"""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Any

_ctx: ContextVar[dict[str, Any] | None] = ContextVar("recommendation_pipeline_state", default=None)


def begin_session(user_need: str) -> Token:
    try:
        from core.security import normalize_text
    except ImportError:
        from security import normalize_text

    text = normalize_text(user_need).strip()
    return _ctx.set(
        {
            "user_need": text,
            "original_need": text,
        }
    )


def end_session(token: Token) -> None:
    _ctx.reset(token)


def get_state() -> dict[str, Any]:
    data = _ctx.get()
    if data is None:
        raise RuntimeError("recommendation session not initialized; call begin_session first")
    return data
