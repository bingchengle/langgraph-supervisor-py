from simple_app import APITools

# 测试GitHub搜索
print("测试GitHub搜索...")
github_result = APITools.search_github_repos('react', limit=5)
print(f"GitHub搜索结果数量: {len(github_result)}")
for repo in github_result[:3]:
    print(f"  - {repo.get('name')}: {repo.get('description', '')[:50]}...")

# 测试PyPI搜索
print("\n测试PyPI搜索...")
pypi_result = APITools.search_pypi_packages('react', limit=5)
print(f"PyPI搜索结果数量: {len(pypi_result)}")
for package in pypi_result[:3]:
    print(f"  - {package.get('name')}")
