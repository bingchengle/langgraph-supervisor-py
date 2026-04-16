#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API工具相关项目推荐功能
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from recommendation.entrypoints import analyze_user_need

if __name__ == "__main__":
    # 测试用户输入：推荐几个api工具相关的项目
    user_need = "推荐几个api工具相关的项目"
    print(f"测试用户输入: {user_need}")
    
    # 分析用户需求并推荐项目
    result = analyze_user_need(user_need)
    print("\n测试结果:")
    print(result)