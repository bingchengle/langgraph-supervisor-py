#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试纯中文输入的处理功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_app import analyze_user_need

if __name__ == "__main__":
    # 测试纯中文输入：推荐轻量级的数据库工具
    user_need = "推荐轻量级的数据库工具"
    print(f"测试用户输入: {user_need}")
    
    # 分析用户需求并推荐项目
    result = analyze_user_need(user_need)
    print("\n测试结果:")
    print(result)