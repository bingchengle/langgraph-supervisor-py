"""
langgraph_supervisor.create_supervisor + 多专家 React Agent。

各专家绑定一个 Tool，内部调用 phases.apply_phase_* 与 context 中的共享状态。
"""

from __future__ import annotations

from functools import lru_cache
from uuid import uuid4

try:
    from langchain_core.messages import HumanMessage
    from langchain_core.tools import tool
    from langgraph.prebuilt import create_react_agent
except ImportError as exc:
    raise ImportError("需要 langchain-core / langgraph") from exc

try:
    from langgraph_supervisor import create_supervisor
except ImportError as exc:
    raise ImportError("需要 langgraph_supervisor") from exc

try:
    from recommendation.chat_model import get_chat_model
    from recommendation.context import begin_session, end_session, get_state
    from recommendation.phases import (
        apply_phase_evaluate,
        apply_phase_filter,
        apply_phase_finalize,
        apply_phase_intent,
        apply_phase_prepare,
        apply_phase_search,
    )
except ImportError:
    from recommendation.chat_model import get_chat_model
    from recommendation.context import begin_session, end_session, get_state
    from recommendation.phases import (
        apply_phase_evaluate,
        apply_phase_filter,
        apply_phase_finalize,
        apply_phase_intent,
        apply_phase_prepare,
        apply_phase_search,
    )


SUPERVISOR_SYSTEM_PROMPT = (
    "你是开源项目推荐系统的总调度员。用户会用自然语言描述想找的开源项目或技术需求。\n"
    "你必须严格按顺序把任务交给下列专家各一次（每位专家调用其工具一次即可）：\n"
    "1) prepare_expert — 整理输入并做安全校验\n"
    "2) intent_expert — 语义归一化与需求分析\n"
    "3) search_expert — 检索候选项目\n"
    "4) filter_expert — 语义过滤与候选压缩\n"
    "5) evaluate_expert — 多维度打分与排序\n"
    "6) report_expert — 生成最终推荐结果（含描述摘要与报告字段）\n"
    "若第 1 步表明内容被安全策略拦截，则跳过 2–5，直接交给 report_expert 收尾。\n"
    "不要跳过顺序，不要对同一专家重复 handoff。"
)


@tool
def prepare_and_screen_input() -> str:
    """第一步：规范化用户输入并执行安全校验。返回 ok 或 blocked。"""
    st = get_state()
    apply_phase_prepare(st)
    return "blocked" if st.get("blocked") else "ok"


@tool
def run_intent_analysis_phase() -> str:
    """第二步：查询归一化与需求分析（关键词、检索查询、权重等）。"""
    st = get_state()
    apply_phase_intent(st)
    return "intent_done"


@tool
def run_search_phase() -> str:
    """第三步：在 GitHub / 条件触发时在 PyPI 等渠道检索项目。"""
    st = get_state()
    apply_phase_search(st)
    return "search_done"


@tool
def run_filter_phase() -> str:
    """第四步：按与用户需求的相关性过滤并保留候选。"""
    st = get_state()
    apply_phase_filter(st)
    return "filter_done"


@tool
def run_evaluate_phase() -> str:
    """第五步：对候选项目进行多维度评分并取 Top。"""
    st = get_state()
    apply_phase_evaluate(st)
    return "evaluate_done"


@tool
def run_finalize_report_phase() -> str:
    """第六步：组装 final_response（成功 / 空结果 / 拦截）。"""
    st = get_state()
    apply_phase_finalize(st)
    return "report_done"


@lru_cache(maxsize=1)
def get_supervisor_recommendation_graph():
    model = get_chat_model()

    prepare_expert = create_react_agent(
        model=model,
        tools=[prepare_and_screen_input],
        name="prepare_expert",
        prompt=(
            "你是输入预处理专家。收到任务后只调用一次工具 prepare_and_screen_input，"
            "然后回复简短确认。"
        ),
    )
    intent_expert = create_react_agent(
        model=model,
        tools=[run_intent_analysis_phase],
        name="intent_expert",
        prompt="你是需求分析专家。请调用一次 run_intent_analysis_phase，然后回复完成。",
    )
    search_expert = create_react_agent(
        model=model,
        tools=[run_search_phase],
        name="search_expert",
        prompt="你是检索专家。请调用一次 run_search_phase，然后回复完成。",
    )
    filter_expert = create_react_agent(
        model=model,
        tools=[run_filter_phase],
        name="filter_expert",
        prompt="你是过滤专家。请调用一次 run_filter_phase，然后回复完成。",
    )
    evaluate_expert = create_react_agent(
        model=model,
        tools=[run_evaluate_phase],
        name="evaluate_expert",
        prompt="你是评估专家。请调用一次 run_evaluate_phase，然后回复完成。",
    )
    report_expert = create_react_agent(
        model=model,
        tools=[run_finalize_report_phase],
        name="report_expert",
        prompt="你是报告专家。请调用一次 run_finalize_report_phase，然后回复完成。",
    )

    builder = create_supervisor(
        [
            prepare_expert,
            intent_expert,
            search_expert,
            filter_expert,
            evaluate_expert,
            report_expert,
        ],
        model=model,
        prompt=SUPERVISOR_SYSTEM_PROMPT,
        add_handoff_messages=True,
        supervisor_name="recommendation_supervisor",
    )
    return builder.compile()


def invoke_recommendation(user_need: str) -> dict:
    """执行 Supervisor 多智能体推荐，返回 final_response 形状的字典。"""
    token = begin_session(user_need)
    try:
        graph = get_supervisor_recommendation_graph()
        thread_id = str(uuid4())
        graph.invoke(
            {"messages": [HumanMessage(content=user_need)]},
            config={
                "recursion_limit": 50,
                "configurable": {"thread_id": thread_id},
            },
        )
        st = get_state()
        out = st.get("final_response")
        if not isinstance(out, dict):
            out = {
                "user_need": st.get("user_need", user_need),
                "llm_result": st.get("llm_result", {}),
                "projects": [],
                "message": "Supervisor 未生成 final_response",
            }
        if st.get("blocked"):
            out = {**out, "blocked": True}
        return out
    finally:
        end_session(token)


# 兼容旧名称
invoke_recommendation_supervisor = invoke_recommendation
