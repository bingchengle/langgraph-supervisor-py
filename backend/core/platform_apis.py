import requests
import os
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

class APITools:
    @staticmethod
    def _github_headers() -> Dict[str, str]:
        headers = {"Accept": "application/vnd.github.v3+json"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @staticmethod
    def has_github_token() -> bool:
        return bool(os.getenv("GITHUB_TOKEN"))

    @staticmethod
    def search_github_repositories(query: str, sort: str = "stars", order: str = "desc", per_page: int = 5) -> List[Dict]:
        """搜索GitHub仓库"""
        try:
            url = "https://api.github.com/search/repositories"
            params = {"q": query, "sort": sort, "order": order, "per_page": per_page}
            response = requests.get(url, headers=APITools._github_headers(), params=params, timeout=10)
            response.raise_for_status()
            return response.json().get("items", [])
        except Exception as e:
            print(f"GitHub API error: {e}")
            return []

    @staticmethod
    def search_github_repos(query: str, limit: int = 10, sort: str = "relevance") -> List[Dict]:
        """便捷封装：按条数限制搜索 GitHub 仓库。"""
        return APITools.search_github_repositories(
            query=query, sort=sort, order="desc", per_page=limit
        )
    
    @staticmethod
    def get_github_repo_info(owner: str, repo: str) -> Optional[Dict]:
        """获取GitHub仓库详细信息"""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}"
            response = requests.get(url, headers=APITools._github_headers(), timeout=10)
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
            response = requests.get(url, headers=APITools._github_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"GitHub stats error: {e}")
            return None
    
    @staticmethod
    def search_pypi_packages(query: str, limit: int = 10) -> List[Dict]:
        """搜索PyPI包 - 通过 GitHub 搜索 PyPI 相关仓库再提取包名。"""
        try:
            keywords = query.strip().split()
            gh_query = " ".join(keywords) + " pypi python package"
            url = "https://api.github.com/search/repositories"
            params = {"q": gh_query, "sort": "stars", "order": "desc", "per_page": limit * 2}
            response = requests.get(url, headers=APITools._github_headers(), params=params, timeout=10)

            if response.status_code != 200:
                print(f"PyPI search (via GitHub) error: {response.status_code}")
                return []

            repos = response.json().get("items", [])
            candidates = []
            seen = set()
            for repo in repos:
                name = repo.get("name", "").lower().replace("-", "").replace("_", "")
                if name in seen:
                    continue
                seen.add(name)
                candidates.append(repo["name"])

            results: List[Dict] = []
            with ThreadPoolExecutor(max_workers=min(len(candidates), 8) or 1) as executor:
                package_infos = list(executor.map(APITools.get_pypi_package_info, candidates))
            for repo_name, pkg_info in zip(candidates, package_infos):
                if pkg_info and pkg_info.get("info"):
                    results.append({"name": pkg_info["info"].get("name", repo_name)})
                if len(results) >= limit:
                    break
            return results
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

    @staticmethod
    def check_vulnerabilities(package_name: str, version: str | None = None) -> Dict:
        """查询 OSV 漏洞并包装为统一结构。"""
        vulns = APITools.check_osv_vulnerabilities(
            package=package_name,
            version=version or "",
            ecosystem="PyPI" if package_name else "npm",
        )
        return {"vulnerabilities": vulns}