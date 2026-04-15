#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API工具相关项目推荐功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_app import analyze_user_need

if __name__ == "__main__":
    # 测试用户输入：推荐几个api工具相关的项目
    user_need = "推荐几个api工具相关的项目"
    print(f"测试用户输入: {user_need}")
    
    # 分析用户需求并推荐项目
    result = analyze_user_need(user_need)
    print("\n测试结果:")
    print(result)