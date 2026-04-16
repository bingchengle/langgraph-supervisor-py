#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试雨课堂二创项目推荐
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from recommendation.entrypoints import analyze_user_need

# 测试用例
test_case = "推荐几个针对雨课堂进行二创的项目"

# 运行测试
print(f"\n=== 测试: {test_case} ===")
try:
    result = analyze_user_need(test_case)
    print(f"用户需求: {result['user_need']}")
    print(f"需求分析: {result['llm_result'].get('task_type', '未知')}")
    print(f"意图识别: {result['llm_result'].get('intent', {})}")
    print(f"找到项目数: {len(result['projects'])}")
    
    if 'message' in result:
        print(f"消息: {result['message']}")
    
    for i, project in enumerate(result['projects'], 1):
        print(f"\n{i}. {project['name']}")
        print(f"   描述: {project['description']}")
        print(f"   链接: {project.get('html_url', '无')}")
        print(f"   总分: {project['total_score']:.3f}")
except Exception as e:
    print(f"测试失败: {e}")
print("=" * 50)
