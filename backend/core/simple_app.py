#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开源项目智能选型助手 - 模块化实现
"""

import json
import os

try:
    from core.security import normalize_text
    from core.workflow import get_recommendation_graph
except ImportError:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[1]))

    from security import normalize_text
    from workflow import get_recommendation_graph

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LANG"] = "zh_CN.UTF-8"
os.environ["LC_ALL"] = "zh_CN.UTF-8"


def analyze_user_need(user_need):
    """分析用户需求并推荐项目。"""
    state = get_recommendation_graph().invoke({"user_need": user_need})
    final_response = state.get("final_response", {})
    llm_result = final_response.get("llm_result", {})
    normalized_user_need = final_response.get("user_need", normalize_text(user_need))
    final_projects = final_response.get("projects", [])

    if not state.get("blocked"):
        generate_report(final_projects, normalized_user_need, llm_result)

    return final_response


def generate_report(projects, user_need, llm_result):
    """生成选型报告。"""
    try:
        print("\n=== 开源项目智能选型报告 ===")
        print(f"用户需求: {user_need}")
        print("\n系统理解的需求:")
        print(f"- 需求定位: {llm_result.get('task_type', '未知')}")
        print("- 关键需求点:")
        for req in llm_result.get("key_requirements", []):
            if req:
                print(f"  * {normalize_text(req)}")

        print("\n评估维度与权重:")
        weights = llm_result.get("weights", {})
        for dimension, weight in weights.items():
            print(f"- {normalize_text(dimension)}: {weight:.2f}")

        print("\n适合的项目排名:")
        for index, project in enumerate(projects, 1):
            print(f"\n{index}. {normalize_text(project['name'])}")
            print(f"   总分: {project['total_score']:.3f}")
            print(f"   描述: {normalize_text(project.get('description', '无'))}")
            if "html_url" in project:
                print(f"   链接: {project['html_url']}")
            print("   各维度得分:")
            for dimension, score in project.get("dimension_scores", {}).items():
                print(f"   - {dimension}: {score:.3f}")
            if project.get("project_analysis"):
                print("   项目分析:")
                print(f"   {normalize_text(project.get('project_analysis', ''))}")
            if project.get("innovation_suggestions"):
                print("   二创方向建议:")
                for idx, suggestion in enumerate(project.get("innovation_suggestions", []), 1):
                    print(f"   {idx}. {normalize_text(suggestion)}")
    except Exception as exc:
        print(f"生成报告失败: {exc}")

    print("\n最终推荐结论:")
    if projects:
        top_project = projects[0]
        print(f"推荐使用: {top_project['name']}")
        print("推荐理由:")
        print(f"- 综合评分最高: {projects[0]['total_score']:.3f}")
        print("- 最符合您的需求:")
        for req in llm_result.get("key_requirements", []):
            if req:
                print(f"  * {normalize_text(req)}")


if __name__ == "__main__":
    user_need = "适合新手的微调项目"
    result = analyze_user_need(user_need)
    print("\n推荐结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
