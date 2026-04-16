#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试纯中文输入的处理功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from recommendation.entrypoints import analyze_user_need

if __name__ == "__main__":
    # 测试纯中文输入：推荐轻量级的数据库工具
    user_need = "推荐轻量级的数据库工具"
    print(f"测试用户输入: {user_need}")
    
    # 分析用户需求并推荐项目
    result = analyze_user_need(user_need)
    print("\n测试结果:")
    print(result)