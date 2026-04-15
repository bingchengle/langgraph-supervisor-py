import pytest
from tools import APITools

class TestAPITools:
    def test_search_github_repositories(self):
        """测试搜索GitHub仓库"""
        results = APITools.search_github_repositories("langchain", per_page=2)
        assert isinstance(results, list)
        if results:
            assert "name" in results[0]
    
    def test_get_github_repo_info(self):
        """测试获取GitHub仓库信息"""
        info = APITools.get_github_repo_info("langchain-ai", "langchain")
        if info:
            assert info.get("name") == "langchain"
    
    def test_get_pypi_package_info(self):
        """测试获取PyPI包信息"""
        info = APITools.get_pypi_package_info("langchain")
        if info:
            assert info.get("info", {}).get("name") == "langchain"
    
    def test_search_npm_packages(self):
        """测试搜索NPM包"""
        results = APITools.search_npm_packages("react", limit=2)
        assert isinstance(results, list)
    
    def test_check_osv_vulnerabilities(self):
        """测试检查OSV漏洞"""
        vulns = APITools.check_osv_vulnerabilities("langchain", "0.1.0", "PyPI")
        assert isinstance(vulns, list)