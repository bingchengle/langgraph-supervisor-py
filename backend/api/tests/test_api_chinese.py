#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# 测试健康检查端点
def test_health_check():
    print("测试健康检查端点...")
    response = requests.get("http://localhost:8004/api/health")
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    print()

# 测试推荐API端点
def test_recommend_api():
    print("测试推荐API端点...")
    url = "http://localhost:8004/api/recommend"
    headers = {"Content-Type": "application/json"}
    
    # 测试中文输入
    test_cases = [
        "适合新手的前端项目",
        "agent项目",
        "雨课堂二次开发项目",
        "适合新手的微调库"
    ]
    
    for test_case in test_cases:
        print(f"测试用例: {test_case}")
        data = {"user_need": test_case}
        response = requests.post(url, headers=headers, json=data)
        print(f"状态码: {response.status_code}")
        # 处理响应内容，确保能够正确显示中文和特殊字符
        try:
            # 获取原始响应内容
            content = response.content.decode('utf-8', errors='ignore')
            # 打印响应内容的前500个字符，避免PowerShell编码问题
            print(f"响应内容: {content[:500]}...")
        except Exception as e:
            print(f"处理响应内容时发生错误: {e}")
        print()

if __name__ == "__main__":
    test_health_check()
    test_recommend_api()
