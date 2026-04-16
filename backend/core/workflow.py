from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from math import sqrt
import os
import re
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

try:
    from agents.evaluators import (
        EcosystemAgent,
        MaturityAgent,
        PopularityAgent,
        RiskAgent,
        ScenarioAgent,
        TrendAgent,
    )
except ImportError:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from agents.evaluators import (
        EcosystemAgent,
        MaturityAgent,
        PopularityAgent,
        RiskAgent,
        ScenarioAgent,
        TrendAgent,
    )

try:
    from core.llm import (
        generate_project_analysis_and_suggestions,
        get_llm_query_normalization,
        get_llm_requirement_analysis,
        summarize_project_description,
    )
    from core.security import check_safety, normalize_text
except ImportError:
    from llm import (
        generate_project_analysis_and_suggestions,
        get_llm_query_normalization,
        get_llm_requirement_analysis,
        summarize_project_description,
    )
    from security import check_safety, normalize_text
from tools import APITools

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


def _tokenize_text(text: str) -> list[str]:
    if not text:
        return []
    english_tokens = re.findall(r"[a-z0-9_]+", text.lower())
    chinese_chunks = re.findall(r"[\u4e00-\u9fff]+", text)
    chinese_bigrams = []
    for chunk in chinese_chunks:
        if len(chunk) == 1:
            chinese_bigrams.append(chunk)
            continue
        chinese_bigrams.extend([chunk[i:i + 2] for i in range(len(chunk) - 1)])
    return english_tokens + chinese_bigrams


def _text_to_vector(text: str) -> dict[str, float]:
    vector: dict[str, float] = {}
    for token in _tokenize_text(text):
        vector[token] = vector.get(token, 0.0) + 1.0
    return vector


def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    common = set(vec_a).intersection(vec_b)
    dot = sum(vec_a[token] * vec_b[token] for token in common)
    norm_a = sqrt(sum(value * value for value in vec_a.values()))
    norm_b = sqrt(sum(value * value for value in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _prepare_input(state: RecommendationState) -> RecommendationState:
    user_need = normalize_text(state.get("user_need", ""))
    print("正在分析需求...")
    return {"user_need": user_need, "original_need": user_need}


def _safety_check(state: RecommendationState) -> RecommendationState:
    user_need = state["user_need"]
    is_safe = check_safety(user_need)
    if not is_safe:
        print("检测到不安全内容，返回提示")
    return {"blocked": not is_safe}


def _route_after_safety(state: RecommendationState) -> str:
    return "blocked_response" if state.get("blocked") else "intent_worker"


def _normalize_input(state: RecommendationState) -> RecommendationState:
    user_need = state["user_need"]
    normalized = get_llm_query_normalization(user_need)
    return {
        "normalized_need": normalize_text(normalized.get("normalized_need", user_need)),
        "retrieval_queries": normalized.get("retrieval_queries", [user_need]),
        "broaden_query": normalize_text(normalized.get("broaden_query", user_need)),
        "canonical_query": normalize_text(normalized.get("canonical_query", user_need)),
        "normalization_confidence": float(normalized.get("normalization_confidence", 0.7)),
    }


def _llm_analyze(state: RecommendationState) -> RecommendationState:
    confidence = float(state.get("normalization_confidence", 0.7))
    user_need = state.get("normalized_need", state["user_need"]) if confidence >= 0.45 else state["user_need"]
    print("正在理解用户需求...")
    print(f"用户需求: {user_need}")
    llm_result = get_llm_requirement_analysis(user_need)
    print(f"需求分析结果: {llm_result}")

    intent = llm_result.get("intent", {})
    return {
        "llm_result": llm_result,
        "core_keywords": intent.get("core_keywords", []),
        "search_query": normalize_text(intent.get("search_query", user_need))[:256],
        "semantic_queries": intent.get("semantic_queries", []),
    }


def _search_projects(state: RecommendationState) -> RecommendationState:
    search_query = state["search_query"]
    semantic_queries = state.get("semantic_queries", [])
    retrieval_queries = state.get("retrieval_queries", [])
    broaden_query = state.get("broaden_query", search_query)
    canonical_query = normalize_text(state.get("canonical_query", search_query)).strip()
    normalized_need = state.get("normalized_need", state.get("user_need", ""))
    original_need = state.get("original_need", state.get("user_need", ""))
    print("正在搜索相关项目...")
    print(f"搜索查询: {search_query}")

    # 如果与已有 canonical 语义接近，则复用已有 canonical 键，保证同义表达结果一致
    if canonical_query and _CANONICAL_PROJECT_CACHE:
        query_vector = _text_to_vector(canonical_query)
        best_key = canonical_query
        best_score = 0.0
        for cache_key, (cache_ts, _) in _CANONICAL_PROJECT_CACHE.items():
            if time.time() - cache_ts > CANONICAL_CACHE_TTL_SECONDS:
                continue
            score = _cosine_similarity(query_vector, _text_to_vector(cache_key))
            if score > best_score:
                best_score = score
                best_key = cache_key
        if best_score >= 0.3:
            canonical_query = best_key

    cached_projects_seed: list[dict[str, Any]] = []

    # 同一语义标准查询在短时间内复用召回结果，提升同义表达一致性
    if canonical_query:
        cached = _CANONICAL_PROJECT_CACHE.get(canonical_query)
        if cached and time.time() - cached[0] <= CANONICAL_CACHE_TTL_SECONDS:
            cached_projects = [project.copy() for project in cached[1]]
            if len(cached_projects) >= MIN_RECOMMENDED_PROJECTS:
                print(f"命中 canonical 缓存: {canonical_query}")
                return {"projects": cached_projects}
            print(f"命中 canonical 缓存但数量不足，继续补充召回: {canonical_query}")
            cached_projects_seed = cached_projects

    query_candidates = [
        (canonical_query, 1.1),
        (original_need, 1.0),
        (normalized_need, 0.95),
        (search_query, 0.9),
        *[(query, 0.85) for query in retrieval_queries],
        *[(query, 0.8) for query in semantic_queries],
    ]
    query_weights: dict[str, float] = {}
    for query, weight in query_candidates:
        normalized = normalize_text(query).strip()
        if not normalized:
            continue
        query_weights[normalized] = max(query_weights.get(normalized, 0.0), weight)
    unique_queries = sorted(query_weights.keys(), key=lambda query: query_weights[query], reverse=True)

    query_budget = 5 if APITools.has_github_token() else 3
    selected_queries = unique_queries[:query_budget]
    github_projects = []
    if selected_queries:
        with ThreadPoolExecutor(max_workers=min(len(selected_queries), 4)) as executor:
            futures = [executor.submit(APITools.search_github_repos, query, 12) for query in selected_queries]
            for future in futures:
                github_projects.extend(future.result())
    print(f"GitHub搜索结果数量: {len(github_projects)}")

    query_text_for_pypi = normalize_text(f"{search_query} {normalized_need} {original_need}").lower()
    pypi_hints = ("python", "pypi", "pip", "包", "库", "sdk", "wheel")
    should_search_pypi = any(hint in query_text_for_pypi for hint in pypi_hints)
    pypi_projects = APITools.search_pypi_packages(search_query, limit=15) if should_search_pypi else []
    if should_search_pypi:
        print(f"PyPI搜索结果数量: {len(pypi_projects)}")
    else:
        print("当前需求非 Python 包检索场景，跳过 PyPI 搜索")

    projects: list[dict[str, Any]] = [project.copy() for project in cached_projects_seed]

    def append_github_projects(repos: list[dict[str, Any]]):
        for repo in repos:
            try:
                name = normalize_text(repo["name"])
                description = normalize_text(repo.get("description", ""))
                if not check_safety(f"{name} {description}"):
                    print(f"检测到不安全内容，过滤项目: {name}")
                    continue
                projects.append(
                    {
                        "name": name,
                        "description": description,
                        "html_url": repo.get("html_url", ""),
                        "stargazers_count": repo.get("stargazers_count", 0),
                        "forks_count": repo.get("forks_count", 0),
                        "watchers_count": repo.get("watchers_count", 0),
                        "created_at": repo.get("created_at", ""),
                        "updated_at": repo.get("updated_at", ""),
                        "license": repo.get("license"),
                        "homepage": repo.get("homepage"),
                        "contributors_url": repo.get("contributors_url"),
                    }
                )
            except Exception as exc:
                print(f"处理GitHub项目失败: {exc}")

    append_github_projects(github_projects)

    for package in pypi_projects:
        package_name = package.get("name", "")
        package_info = APITools.get_pypi_package_info(package_name)
        if package_info:
            info = package_info.get("info", {})
            description = normalize_text(info.get("summary", ""))
            name = normalize_text(info.get("name", package_name))
            if not check_safety(f"{name} {description}"):
                print(f"检测到不安全内容，过滤项目: {name}")
                continue
            projects.append(
                {
                    "name": name,
                    "description": description,
                    "version": info.get("version"),
                    "homepage": info.get("home_page"),
                    "license": info.get("license"),
                }
            )
        elif check_safety(package_name):
            projects.append({"name": package_name, "description": package_name})

    def dedupe_projects(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        unique_items = []
        seen_names = set()
        for item in items:
            name = item.get("name", "")
            if not name or name in seen_names:
                continue
            seen_names.add(name)
            unique_items.append(item)
        return unique_items

    unique_projects = dedupe_projects(projects)

    # 当首轮搜索候选不足时，执行通用回退搜索补齐
    if len(unique_projects) < MIN_RECOMMENDED_PROJECTS:
        fallback_queries = [
            broaden_query,
            f"{normalized_need} stars:>100",
            "open source projects stars:>500",
        ]
        for fallback_query in fallback_queries:
            candidate = normalize_text(fallback_query).strip()
            if not candidate:
                continue
            print(f"候选不足({len(unique_projects)})，执行回退搜索: {candidate}")
            fallback_projects = APITools.search_github_repos(candidate, limit=20, sort="stars")
            append_github_projects(fallback_projects)
            unique_projects = dedupe_projects(projects)
            if len(unique_projects) >= MIN_RECOMMENDED_PROJECTS:
                break

    if canonical_query and unique_projects:
        _CANONICAL_PROJECT_CACHE[canonical_query] = (
            time.time(),
            [project.copy() for project in unique_projects],
        )

    return {"projects": unique_projects}


def _tag_and_filter(state: RecommendationState) -> RecommendationState:
    projects = state.get("projects", [])
    core_keywords = state.get("core_keywords", [])
    user_need = state.get("user_need", "")
    semantic_queries = state.get("semantic_queries", [])

    if not projects:
        return {"filtered_projects": []}

    semantic_query_text = " ".join([user_need, *core_keywords, *semantic_queries]).strip()
    query_vector = _text_to_vector(semantic_query_text)
    scored_projects = []
    for project in projects:
        project_text = normalize_text(
            f"{project.get('name', '')} {project.get('description', '')}"
        )
        similarity = _cosine_similarity(query_vector, _text_to_vector(project_text))
        scored_projects.append((similarity, project))

    scored_projects.sort(key=lambda item: item[0], reverse=True)
    best_score = scored_projects[0][0] if scored_projects else 0.0
    dynamic_threshold = max(0.01, best_score * 0.5)
    filtered_projects = [project for score, project in scored_projects if score >= dynamic_threshold]

    # 对泛需求或低匹配场景做回退，避免返回空结果
    if not filtered_projects:
        filtered_projects = [project for _, project in scored_projects]

    # 结果数量兜底，避免阈值过严导致候选过少
    if len(filtered_projects) < MIN_RECOMMENDED_PROJECTS:
        selected_names = {project.get("name", "") for project in filtered_projects}
        for _, project in scored_projects:
            name = project.get("name", "")
            if name in selected_names:
                continue
            filtered_projects.append(project)
            selected_names.add(name)
            if len(filtered_projects) >= MIN_RECOMMENDED_PROJECTS:
                break

    return {"filtered_projects": filtered_projects[: max(5, MIN_RECOMMENDED_PROJECTS)]}


def _evaluate_projects(state: RecommendationState) -> RecommendationState:
    top_projects = state.get("filtered_projects", [])
    user_need = state.get("user_need", "")
    llm_result = state.get("llm_result", {})
    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_project = {}
        for project in top_projects:
            future_to_project[project["name"]] = {
                "project": project,
                "popularity": executor.submit(PopularityAgent.evaluate, project),
                "maturity": executor.submit(MaturityAgent.evaluate, project),
                "ecosystem": executor.submit(EcosystemAgent.evaluate, project),
                "risk": executor.submit(RiskAgent.evaluate, project),
                "scenario": executor.submit(ScenarioAgent.evaluate, project, user_need, llm_result),
                "trend": executor.submit(TrendAgent.evaluate, project),
            }

        for futures in future_to_project.values():
            project = futures["project"]
            popularity = futures["popularity"].result()
            maturity = futures["maturity"].result()
            ecosystem = futures["ecosystem"].result()
            risk = futures["risk"].result()
            scenario = futures["scenario"].result()
            trend = futures["trend"].result()

            dimension_scores = {
                "流行度": popularity["score"],
                "成熟度": maturity["score"],
                "生态": ecosystem["score"],
                "风险": risk["score"],
                "上手难度": scenario["score"],
                "性能": trend["score"],
            }
            total_score = (
                popularity["score"] * 0.2
                + maturity["score"] * 0.2
                + ecosystem["score"] * 0.2
                + risk["score"] * 0.2
                + scenario["score"] * 0.1
                + trend["score"] * 0.1
            )
            results.append(
                {
                    "project": project,
                    "scores": {
                        "popularity": popularity,
                        "maturity": maturity,
                        "ecosystem": ecosystem,
                        "risk": risk,
                        "scenario": scenario,
                        "trend": trend,
                    },
                    "dimension_scores": dimension_scores,
                    "total_score": total_score,
                }
            )

    results.sort(key=lambda item: item["total_score"], reverse=True)
    return {"results": results[:3]}


def _route_after_evaluate(state: RecommendationState) -> str:
    return "build_success_response" if state.get("results") else "build_empty_response"


def _blocked_response(state: RecommendationState) -> RecommendationState:
    user_need = state.get("user_need", "")
    return {
        "final_response": {
            "user_need": user_need,
            "llm_result": {},
            "projects": [],
            "message": "暂不支持此类需求",
        }
    }


def _build_empty_response(state: RecommendationState) -> RecommendationState:
    user_need = state.get("user_need", "")
    llm_result = state.get("llm_result", {})
    print("未找到匹配项目")
    message = "未找到匹配的开源项目"
    if not APITools.has_github_token():
        message += "（当前可能受 GitHub 匿名限流影响，可配置 GITHUB_TOKEN 提升召回稳定性）"
    return {
        "final_response": {
            "user_need": user_need,
            "llm_result": llm_result,
            "projects": [],
            "message": message,
        }
    }


def _build_success_response(state: RecommendationState) -> RecommendationState:
    user_need = state.get("user_need", "")
    llm_result = state.get("llm_result", {})
    results = state.get("results", [])
    response = {
        "final_response": {
            "user_need": user_need,
            "llm_result": llm_result,
            "projects": [],
        }
    }
    def build_project_payload(result: dict[str, Any]) -> dict[str, Any]:
        project = result["project"]
        description = project.get("description", "")
        if ENABLE_REPORT_LLM:
            final_description = summarize_project_description(description, max_chars=300)
        else:
            final_description = normalize_text(description)[:300]
        project_for_analysis = {
            **project,
            "total_score": result["total_score"],
            "dimension_scores": result["dimension_scores"],
            "description": final_description,
        }
        if ENABLE_REPORT_LLM:
            analysis_bundle = generate_project_analysis_and_suggestions(
                project_for_analysis,
                user_need=user_need,
                llm_result=llm_result,
            )
        else:
            analysis_bundle = {
                "project_analysis": "",
                "innovation_suggestions": [],
            }
        return {
            "name": project["name"],
            "description": final_description,
            "html_url": project.get("html_url", ""),
            "total_score": result["total_score"],
            "dimension_scores": result["dimension_scores"],
            "project_analysis": analysis_bundle.get("project_analysis", ""),
            "innovation_suggestions": analysis_bundle.get("innovation_suggestions", []),
        }

    if results:
        with ThreadPoolExecutor(max_workers=min(len(results), 3)) as executor:
            project_payloads = list(executor.map(build_project_payload, results))
        response["final_response"]["projects"].extend(project_payloads)
    return response


def _compile_intent_worker():
    """意图 Worker：归一化 + 需求分析（原 normalize_input → llm_analyze）。"""
    g = StateGraph(RecommendationState)
    g.add_node("normalize_input", _normalize_input)
    g.add_node("llm_analyze", _llm_analyze)
    g.add_edge(START, "normalize_input")
    g.add_edge("normalize_input", "llm_analyze")
    g.add_edge("llm_analyze", END)
    return g.compile()


def _compile_search_worker():
    """搜索 Worker：多路召回 GitHub / 条件 PyPI（原 search_projects）。"""
    g = StateGraph(RecommendationState)
    g.add_node("search_projects", _search_projects)
    g.add_edge(START, "search_projects")
    g.add_edge("search_projects", END)
    return g.compile()


def _compile_filter_worker():
    """过滤 Worker：语义相似度筛选（原 tag_and_filter）。"""
    g = StateGraph(RecommendationState)
    g.add_node("tag_and_filter", _tag_and_filter)
    g.add_edge(START, "tag_and_filter")
    g.add_edge("tag_and_filter", END)
    return g.compile()


def _compile_evaluate_worker():
    """评估 Worker：多维度打分（原 evaluate_projects）。"""
    g = StateGraph(RecommendationState)
    g.add_node("evaluate_projects", _evaluate_projects)
    g.add_edge(START, "evaluate_projects")
    g.add_edge("evaluate_projects", END)
    return g.compile()


def _compile_report_worker():
    """报告 Worker：摘要 + 项目分析与二创建议（原 build_success_response）。"""
    g = StateGraph(RecommendationState)
    g.add_node("build_success_response", _build_success_response)
    g.add_edge(START, "build_success_response")
    g.add_edge("build_success_response", END)
    return g.compile()


@lru_cache(maxsize=1)
def get_recommendation_graph():
    """
    推荐主图（方案 B：Supervisor 式流水线 + Worker 子图）。

    各阶段拆成独立编译子图（intent / search / filter / evaluate / report），
    主图做确定性路由，行为与原先单图串联一致。

    说明：`langgraph_supervisor.create_supervisor` 依赖 LangChain ChatModel 与
    messages 状态；当前栈为 HTTP LLM + RecommendationState。若需 LLM 动态路由，
    可在此主图前接入 supervisor，或为本状态增加 messages 适配层。
    """
    intent_worker = _compile_intent_worker()
    search_worker = _compile_search_worker()
    filter_worker = _compile_filter_worker()
    evaluate_worker = _compile_evaluate_worker()
    report_worker = _compile_report_worker()

    workflow = StateGraph(RecommendationState)
    workflow.add_node("prepare_input", _prepare_input)
    workflow.add_node("safety_check", _safety_check)
    workflow.add_node("intent_worker", intent_worker)
    workflow.add_node("search_worker", search_worker)
    workflow.add_node("filter_worker", filter_worker)
    workflow.add_node("evaluate_worker", evaluate_worker)
    workflow.add_node("blocked_response", _blocked_response)
    workflow.add_node("build_empty_response", _build_empty_response)
    workflow.add_node("report_worker", report_worker)

    workflow.add_edge(START, "prepare_input")
    workflow.add_edge("prepare_input", "safety_check")
    workflow.add_conditional_edges(
        "safety_check",
        _route_after_safety,
        {
            "blocked_response": "blocked_response",
            "intent_worker": "intent_worker",
        },
    )
    workflow.add_edge("intent_worker", "search_worker")
    workflow.add_edge("search_worker", "filter_worker")
    workflow.add_edge("filter_worker", "evaluate_worker")
    workflow.add_conditional_edges(
        "evaluate_worker",
        _route_after_evaluate,
        {
            "build_success_response": "report_worker",
            "build_empty_response": "build_empty_response",
        },
    )
    workflow.add_edge("blocked_response", END)
    workflow.add_edge("build_empty_response", END)
    workflow.add_edge("report_worker", END)
    return workflow.compile()
