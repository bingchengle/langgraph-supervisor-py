import requests
import json
import sys

# 设置标准输出编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# 测试推荐雨课堂二次开发项目
print("测试推荐雨课堂二次开发项目:")
response = requests.post('http://localhost:8004/api/recommend', json={'user_need': '推荐雨课堂二次开发项目'})
print('Status Code:', response.status_code)
print('Response:', response.json())
print()

# 测试推荐前端项目
print("测试推荐前端项目:")
response = requests.post('http://localhost:8004/api/recommend', json={'user_need': '推荐前端项目'})
print('Status Code:', response.status_code)
print('Response:', response.json())
print()

# 测试推荐agent项目
print("测试推荐agent项目:")
response = requests.post('http://localhost:8004/api/recommend', json={'user_need': '推荐agent项目'})
print('Status Code:', response.status_code)
print('Response:', response.json())
