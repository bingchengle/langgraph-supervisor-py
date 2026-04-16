"""
开源项目推荐子系统（Supervisor + 多专家 Tool）。

- ``phases``: 检索、过滤、评估、组装响应
- ``supervisor``: 调度图与 ``invoke_recommendation``
- ``state`` / ``context``: 状态类型与请求内上下文
- ``entrypoints``: API/CLI 入口（``analyze_user_need``）
"""

from .state import RecommendationState
from .supervisor import (
    get_supervisor_recommendation_graph,
    invoke_recommendation,
    invoke_recommendation_supervisor,
)
from .entrypoints import analyze_user_need, generate_report

__all__ = [
    "RecommendationState",
    "analyze_user_need",
    "generate_report",
    "get_supervisor_recommendation_graph",
    "invoke_recommendation",
    "invoke_recommendation_supervisor",
]
