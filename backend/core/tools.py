import requests
import json
from typing import Dict, List, Optional, Any

class APITools:
    @staticmethod
    def search_github_repositories(query: str, sort: str = "stars", order: str = "desc", per_page: int = 5) -> List[Dict]:
        """搜索GitHub仓库"""
        try:
            url = f"https://api.github.com/search/repositories?q={query}&sort={sort}&order={order}&per_page={per_page}"
            headers = {"Accept": "application/vnd.github.v3+json"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json().get("items", [])
        except Exception as e:
            print(f"GitHub API error: {e}")
            return []
    
    @staticmethod
    def get_github_repo_info(owner: str, repo: str) -> Optional[Dict]:
        """获取GitHub仓库详细信息"""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}"
            headers = {"Accept": "application/vnd.github.v3+json"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"GitHub repo info error: {e}")
            return None
    
    @staticmethod
    def get_github_repo_stats(owner: str, repo: str) -> Optional[Dict]:
        """获取GitHub仓库统计信息"""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/stats/contributors"
            headers = {"Accept": "application/vnd.github.v3+json"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"GitHub stats error: {e}")
            return None
    
    @staticmethod
    def search_pypi_packages(query: str) -> List[Dict]:
        """搜索PyPI包"""
        try:
            url = f"https://pypi.org/search/?q={query}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            # 这里需要解析HTML，简化处理
            return []
        except Exception as e:
            print(f"PyPI search error: {e}")
            return []
    
    @staticmethod
    def get_pypi_package_info(package_name: str) -> Optional[Dict]:
        """获取PyPI包详细信息"""
        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"PyPI package info error: {e}")
            return None
    
    @staticmethod
    def get_pypi_download_stats(package_name: str) -> Optional[Dict]:
        """获取PyPI包下载统计"""
        try:
            url = f"https://pypistats.org/api/packages/{package_name}/recent"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"PyPI stats error: {e}")
            return None
    
    @staticmethod
    def search_npm_packages(query: str, limit: int = 5) -> List[Dict]:
        """搜索NPM包"""
        try:
            url = f"https://registry.npmjs.org/-/v1/search?text={query}&size={limit}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json().get("objects", [])
        except Exception as e:
            print(f"NPM search error: {e}")
            return []
    
    @staticmethod
    def get_npm_package_info(package_name: str) -> Optional[Dict]:
        """获取NPM包详细信息"""
        try:
            url = f"https://registry.npmjs.org/{package_name}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"NPM package info error: {e}")
            return None
    
    @staticmethod
    def search_docker_images(query: str, limit: int = 5) -> List[Dict]:
        """搜索Docker镜像"""
        try:
            url = f"https://hub.docker.com/v2/search/repositories/?query={query}&page_size={limit}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json().get("results", [])
        except Exception as e:
            print(f"Docker Hub search error: {e}")
            return []
    
    @staticmethod
    def get_docker_image_info(name: str) -> Optional[Dict]:
        """获取Docker镜像详细信息"""
        try:
            url = f"https://hub.docker.com/v2/repositories/{name}/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Docker Hub info error: {e}")
            return None
    
    @staticmethod
    def check_osv_vulnerabilities(package: str, version: str, ecosystem: str = "PyPI") -> List[Dict]:
        """检查OSV漏洞"""
        try:
            url = "https://api.osv.dev/v1/query"
            data = {
                "package": {
                    "name": package,
                    "ecosystem": ecosystem
                },
                "version": version
            }
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            return response.json().get("vulns", [])
        except Exception as e:
            print(f"OSV API error: {e}")
            return []