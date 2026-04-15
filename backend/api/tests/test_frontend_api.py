#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端API调用
"""

import requests

# 测试用例
test_case = "推荐几个针对雨课堂进行二创的项目"

# 调用API
print(f"\n=== 测试API调用: {test_case} ===")
try:
    response = requests.post('http://localhost:8003/api/recommend', json={'need': test_case})
    response.raise_for_status()
    result = response.json()
    
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
