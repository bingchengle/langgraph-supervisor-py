"""推荐流水线共享状态类型与全局配置（多 Agent / Supervisor 与各阶段共用）。"""

from __future__ import annotations

import os
from typing import Any, TypedDict

CANONICAL_CACHE_TTL_SECONDS = 900
MIN_RECOMMENDED_PROJECTS = 3
_CANONICAL_PROJECT_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
ENABLE_REPORT_LLM = os.getenv("ENABLE_REPORT_LLM", "1").strip().lower() not in {"0", "false", "no", "off"}


class RecommendationState(TypedDict, total=False):
    user_need: str
    original_need: str
    blocked: bool
    llm_result: dict[str, Any]
    normalized_need: str
    retrieval_queries: list[str]
    broaden_query: str
    canonical_query: str
    normalization_confidence: float
    core_keywords: list[str]
    search_query: str
    semantic_queries: list[str]
    projects: list[dict[str, Any]]
    filtered_projects: list[dict[str, Any]]
    results: list[dict[str, Any]]
    final_response: dict[str, Any]
