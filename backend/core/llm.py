import json
import re
import time

import requests

try:
    from core.config import get_model_api_key, get_model_api_url, get_model_candidates
    from core.security import check_safety, normalize_text
except ImportError:
    from config import get_model_api_key, get_model_api_url, get_model_candidates
    from security import check_safety, normalize_text

requests.packages.urllib3.disable_warnings()
requests.adapters.DEFAULT_RETRIES = 5
PROJECT_ANALYSIS_CACHE_TTL_SECONDS = 900
_PROJECT_ANALYSIS_CACHE: dict[str, tuple[float, dict]] = {}


def _build_canonical_query(text: str) -> str:
    normalized = normalize_text(text).strip().lower()
    tokens = re.findall(r"[a-z0-9_\-]+|[\u4e00-\u9fff]{2,}", normalized)
    if not tokens:
        return normalized
    return " ".join(tokens[:8])


def _extract_keywords_fallback(prompt: str) -> dict:
    tokens = re.findall(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fff]{2,}", prompt)
    core_keywords = tokens[:8]
    return {
        "core_keywords": core_keywords,
        "search_query": prompt,
        "semantic_queries": [prompt],
        "intent_summary": prompt,
    }


def _normalize_query_fallback(prompt: str) -> dict:
    normalized = normalize_text(prompt).strip()
    tokens = re.findall(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fff]{2,}", normalized)
    retrieval_queries = [normalized]
    if tokens:
        retrieval_queries.append(" ".join(tokens[:8]))
    # 去重并保持顺序
    deduped = []
    for query in retrieval_queries:
        candidate = normalize_text(query).strip()
        if candidate and candidate not in deduped:
            deduped.append(candidate)
    return {
        "normalized_need": normalized,
        "retrieval_queries": deduped[:4] if deduped else [normalized],
        "broaden_query": normalized,
        "canonical_query": _build_canonical_query(normalized),
        "normalization_confidence": 0.5,
    }


def _call_chat_completion(prompt: str, system_prompt: str) -> dict | None:
    api_key = get_model_api_key()
    api_url = get_model_api_url()
    if not api_key or not api_url:
        return None

    url = f"{api_url}/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    for model_name in get_model_candidates():
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code != 200:
                print(f"API错误: {response.status_code}")
                print(f"错误信息: {response.text}")
                continue

            data = response.json()
            if "choices" not in data or not data["choices"]:
                continue
            content = normalize_text(data["choices"][0]["message"]["content"])
            return json.loads(content)
        except Exception as exc:
            print(f"调用API时发生错误: {exc}")
            continue
    return None


def get_llm_query_normalization(prompt: str) -> dict:
    """对用户输入做通用语义归一化，增强口语/错别字/长文本鲁棒性。"""
    normalized_prompt = normalize_text(prompt)
    if not normalized_prompt:
        return _normalize_query_fallback(prompt)

    system_prompt = (
        "你是搜索意图归一化助手。"
        "目标：将用户输入统一转换为更稳定的检索表达，能够覆盖错别字、口语化、情绪化、长文本。"
        "要求：不要做领域假设，不要引入用户未表达的约束。"
        "如果存在同音错别字、近形错别字或口语化缩略，请优先给出最可能的规范表达。"
        "当你不确定纠错是否准确时，请降低 normalization_confidence。"
        "输出JSON字段："
        "1. normalized_need: 对原需求的一句话标准化表达"
        "2. retrieval_queries: 2-5条用于检索的改写查询（第一条必须是你认为最稳妥的规范检索写法）"
        "3. broaden_query: 当检索过窄时可用的一条更宽泛查询"
        "4. canonical_query: 用于稳定召回的标准化检索短语（不超过10个词）"
        "5. normalization_confidence: 0到1之间，表示你对归一化是否保持原意的置信度"
    )
    result = _call_chat_completion(normalized_prompt, system_prompt)
    if not result:
        return _normalize_query_fallback(normalized_prompt)

    required_fields = ("normalized_need", "retrieval_queries", "broaden_query")
    if any(field not in result for field in required_fields):
        return _normalize_query_fallback(normalized_prompt)

    retrieval_queries = result.get("retrieval_queries", [])
    if not isinstance(retrieval_queries, list):
        retrieval_queries = [normalize_text(retrieval_queries)]
    confidence = result.get("normalization_confidence", 0.7)
    try:
        confidence = float(confidence)
    except Exception:
        confidence = 0.7
    confidence = max(0.0, min(1.0, confidence))

    # 原始输入始终保留在第一通道，防止错别字/口语被过度改写
    deduped_queries = []
    for query in [
        normalized_prompt,
        *retrieval_queries,
        result.get("normalized_need", ""),
        result.get("broaden_query", ""),
    ]:
        candidate = normalize_text(query).strip()
        if candidate and candidate not in deduped_queries:
            deduped_queries.append(candidate)

    # 当模型对归一化置信较低时，强化原始表达召回权重（通过重复保留原句）
    if confidence < 0.55 and normalized_prompt not in deduped_queries[:2]:
        deduped_queries.insert(0, normalized_prompt)

    canonical_base = retrieval_queries[0] if retrieval_queries else result.get("canonical_query") or result.get(
        "normalized_need", normalized_prompt
    )
    return {
        "normalized_need": normalize_text(result.get("normalized_need", normalized_prompt)),
        "retrieval_queries": deduped_queries[:5] if deduped_queries else [normalized_prompt],
        "broaden_query": normalize_text(result.get("broaden_query", normalized_prompt)),
        "canonical_query": _build_canonical_query(canonical_base),
        "normalization_confidence": confidence,
    }


def get_llm_intent_analysis(prompt, model="gpt-3.5-turbo", api_key=None):
    """调用大语言模型进行需求意图精确定位。"""
    del model, api_key
    try:
        prompt = normalize_text(prompt)
        if not check_safety(prompt):
            return {"core_keywords": [], "search_query": ""}

        system_prompt = (
            "你是一个开源项目推荐助手，需要精确分析用户需求语义并生成可检索表达。"
            "请返回JSON对象，包含字段："
            "1. core_keywords: 语义关键短语列表（可包含同义表达）"
            "2. search_query: 一条主搜索查询语句"
            "3. semantic_queries: 2-4条语义等价或近义改写查询，用于召回更多相关项目"
            "4. intent_summary: 一句话概括用户真实意图"
        )
        response = _call_chat_completion(prompt, system_prompt)
        if not response:
            return _extract_keywords_fallback(prompt)

        required_fields = ("core_keywords", "search_query", "semantic_queries", "intent_summary")
        if any(field not in response for field in required_fields):
            return _extract_keywords_fallback(prompt)
        if not isinstance(response.get("semantic_queries"), list):
            response["semantic_queries"] = [response["search_query"]]
        return response
    except Exception as exc:
        print(f"调用大语言模型失败: {exc}")
        return _extract_keywords_fallback(normalize_text(prompt))


def get_llm_requirement_analysis(prompt, model="gpt-3.5-turbo", api_key=None):
    """调用大语言模型分析用户需求，生成评估维度与动态权重。"""
    del model, api_key
    try:
        prompt = normalize_text(prompt)
        system_prompt = (
            "你是一个开源项目推荐助手，需要一次性完成意图理解和评估方案生成。"
            "请返回一个JSON对象，包含以下字段："
            "0. intent: 对象，包含 core_keywords、search_query、semantic_queries、intent_summary"
            "1. key_requirements: 关键需求点列表 "
            "2. dimensions_needed: 需要的评估维度列表 "
            "3. weights: 各维度的权重字典，总和为1"
        )
        result = _call_chat_completion(prompt, system_prompt)
        if result and isinstance(result.get("weights"), dict) and isinstance(result.get("intent"), dict):
            total_weight = sum(result["weights"].values())
            if total_weight:
                if abs(total_weight - 1.0) > 0.01:
                    result["weights"] = {
                        key: value / total_weight for key, value in result["weights"].items()
                    }
                intent = result.get("intent", {})
                if not isinstance(intent.get("semantic_queries"), list):
                    intent["semantic_queries"] = [intent.get("search_query", prompt)]
                result["intent"] = intent
                return result

        intent_result = get_llm_intent_analysis(prompt)
        if not intent_result:
            intent_result = _extract_keywords_fallback(prompt)
        weights = {
            "流行度": 0.1,
            "成熟度": 0.2,
            "生态": 0.15,
            "风险": 0.2,
            "上手难度": 0.25,
            "性能": 0.1,
        }
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            weights = {k: v / total_weight for k, v in weights.items()}
        return {
            "key_requirements": intent_result.get("core_keywords", ["功能完整", "易于使用"]),
            "dimensions_needed": list(weights.keys()),
            "weights": weights,
            "intent": intent_result,
        }
    except Exception as exc:
        print(f"调用大语言模型失败: {exc}")
        intent_result = get_llm_intent_analysis(prompt) if prompt else {}
        if not intent_result:
            intent_result = _extract_keywords_fallback(normalize_text(prompt))
        return {
            "key_requirements": intent_result.get("core_keywords", ["功能完整", "易于使用"]),
            "dimensions_needed": ["流行度", "成熟度", "生态", "风险", "上手难度", "性能"],
            "weights": {
                "流行度": 0.1,
                "成熟度": 0.2,
                "生态": 0.15,
                "风险": 0.2,
                "上手难度": 0.25,
                "性能": 0.1,
            },
            "intent": intent_result,
        }


def summarize_project_description(description: str, max_chars: int = 300) -> str:
    """当描述过长时，调用 LLM 摘要。"""
    normalized = normalize_text(description)
    if len(normalized) <= max_chars:
        return normalized

    system_prompt = (
        "你是开源项目信息摘要助手。"
        "请将输入描述总结为不超过180字，保留核心功能、使用场景和技术亮点。"
        "输出JSON：{\"summary\":\"...\"}"
    )
    result = _call_chat_completion(normalized, system_prompt)
    if result and isinstance(result.get("summary"), str):
        summary = normalize_text(result["summary"]).strip()
        if summary:
            return summary[:max_chars]
    return normalized[:max_chars]


def generate_project_analysis_and_suggestions(
    project: dict,
    user_need: str = "",
    llm_result: dict | None = None,
) -> dict:
    """生成项目分析与二创方向建议。"""
    llm_result = llm_result or {}
    project_context = {
        "name": project.get("name", ""),
        "description": normalize_text(project.get("description", "")),
        "html_url": project.get("html_url", ""),
        "total_score": project.get("total_score"),
        "dimension_scores": project.get("dimension_scores", {}),
        "user_need": normalize_text(user_need),
        "key_requirements": llm_result.get("key_requirements", []),
    }
    cache_key = json.dumps(project_context, ensure_ascii=False, sort_keys=True)
    cached = _PROJECT_ANALYSIS_CACHE.get(cache_key)
    if cached and time.time() - cached[0] <= PROJECT_ANALYSIS_CACHE_TTL_SECONDS:
        return cached[1].copy()

    context_text = json.dumps(project_context, ensure_ascii=False)
    system_prompt = (
        "你是专业的开源项目选型顾问，请为当前项目生成【项目分析】和【二创方向建议】，必须同时满足以下要求：\n\n"
        "1.  内容必须基于项目本身的真实信息，禁止使用“表现一般/可能不足”这类通用套话，所有表述需具体、客观。\n"
        "2.  【项目分析】部分：\n"
        "    - 篇幅控制在 80-100 字以内。\n"
        "    - 必须包含3个核心信息：适用场景、核心优势、关键局限。\n"
        "    - 语言简洁干练，不展开冗余描述。\n"
        "3.  【二创方向建议】部分：\n"
        "    - 篇幅控制在 80-100 字以内。\n"
        "    - 给出2条具体、可落地的扩展建议，必须和项目特性强相关，禁止“优化性能/开发插件”这类空话。\n"
        "4.  两个板块合计不超过 200 字，格式清晰，适合直接放入项目报告/PPT。\n\n"
        "返回JSON格式："
        "{\"project_analysis\":\"...\",\"innovation_suggestions\":[\"...\",\"...\"]}"
    )

    def _clean_result(raw: dict | None) -> dict | None:
        if not raw:
            return None
        analysis = normalize_text(raw.get("project_analysis", "")).strip()
        suggestions = raw.get("innovation_suggestions", [])
        if not isinstance(suggestions, list):
            suggestions = [normalize_text(str(suggestions))]
        cleaned_suggestions = [normalize_text(item).strip() for item in suggestions if str(item).strip()]
        if not analysis or len(cleaned_suggestions) < 2:
            return None
        cleaned_suggestions = cleaned_suggestions[:2]
        suggestion_text = "".join(cleaned_suggestions)
        total_len = len(analysis) + len(suggestion_text)
        is_len_ok = 80 <= len(analysis) <= 100 and 80 <= len(suggestion_text) <= 100 and total_len <= 200
        return {
            "project_analysis": analysis,
            "innovation_suggestions": cleaned_suggestions,
            "is_len_ok": is_len_ok,
        }

    parsed = _clean_result(_call_chat_completion(context_text, system_prompt))
    if parsed and parsed["is_len_ok"]:
        payload = {
            "project_analysis": parsed["project_analysis"],
            "innovation_suggestions": parsed["innovation_suggestions"],
        }
        _PROJECT_ANALYSIS_CACHE[cache_key] = (time.time(), payload.copy())
        return payload

    if parsed:
        payload = {
            "project_analysis": parsed["project_analysis"],
            "innovation_suggestions": parsed["innovation_suggestions"],
        }
        _PROJECT_ANALYSIS_CACHE[cache_key] = (time.time(), payload.copy())
        return payload

    desc_hint = normalize_text(project.get("description", "具备开源实现基础"))[:16]
    fallback_analysis = (
        f"适用场景：{project.get('name', '该项目')}在业务功能验证与学习实践中落地；"
        f"核心优势：{desc_hint}，结构清晰且便于快速接入；"
        "关键局限：复杂场景仍需补齐工程化配置与数据治理能力。"
    )
    fallback_suggestions = [
        "围绕仓库现有模块封装行业模板，补充参数化配置、示例数据与初始化脚本，形成可直接复用的业务骨架。",
        "基于项目当前能力设计两条高频用户流程，增加可视化操作页、效果对比面板与演示用例，支撑对外展示和快速验收。",
    ]
    payload = {
        "project_analysis": fallback_analysis,
        "innovation_suggestions": fallback_suggestions,
    }
    _PROJECT_ANALYSIS_CACHE[cache_key] = (time.time(), payload.copy())
    return payload
