from langgraph.prebuilt import create_react_agent
from tools import APITools
from datetime import datetime

def create_maturity_agent(model):
    """创建成熟度评估Agent"""
    
    def evaluate_github_maturity(repo_owner: str, repo_name: str) -> dict:
        """评估GitHub仓库成熟度"""
        try:
            repo_info = APITools.get_github_repo_info(repo_owner, repo_name)
            if not repo_info:
                return {"error": "Failed to get repo info"}
            
            # 分析版本号
            default_branch = repo_info.get("default_branch", "main")
            
            # 分析发布频率
            created_at = repo_info.get("created_at")
            updated_at = repo_info.get("updated_at")
            
            if created_at and updated_at:
                created_date = datetime.fromisoformat(created_at[:-1])
                updated_date = datetime.fromisoformat(updated_at[:-1])
                days_since_creation = (updated_date - created_date).days
                days_since_update = (datetime.now() - updated_date).days
            else:
                days_since_creation = 0
                days_since_update = 999
            
            # 评估成熟度
            maturity_metrics = {
                "created_at": created_at,
                "updated_at": updated_at,
                "days_since_creation": days_since_creation,
                "days_since_update": days_since_update,
                "default_branch": default_branch,
                "size": repo_info.get("size"),
                "has_wiki": repo_info.get("has_wiki"),
                "has_pages": repo_info.get("has_pages")
            }
            
            # 计算成熟度得分 (0-100)
            # 项目年龄得分
            age_score = min(days_since_creation / 365 * 20, 20)
            # 更新频率得分
            update_score = max(0, 30 - (days_since_update / 30 * 30))
            # 项目大小得分
            size_score = min(repo_info.get("size", 0) / 10000 * 20, 20)
            # 功能完整性得分
            feature_score = 0
            if repo_info.get("has_wiki"):
                feature_score += 10
            if repo_info.get("has_pages"):
                feature_score += 10
            if repo_info.get("has_issues"):
                feature_score += 10
            
            total_score = age_score + update_score + size_score + feature_score
            maturity_metrics["score"] = round(total_score, 2)
            
            return maturity_metrics
        except Exception as e:
            return {"error": str(e)}
    
    def evaluate_pypi_maturity(package_name: str) -> dict:
        """评估PyPI包成熟度"""
        try:
            package_info = APITools.get_pypi_package_info(package_name)
            if not package_info:
                return {"error": "Failed to get package info"}
            
            info = package_info.get("info", {})
            version = info.get("version", "0.0.0")
            
            # 分析版本号
            version_parts = version.split(".")
            major_version = int(version_parts[0]) if version_parts else 0
            
            # 分析发布历史
            releases = package_info.get("releases", {})
            release_count = len(releases)
            
            # 计算成熟度得分
            maturity_metrics = {
                "version": version,
                "major_version": major_version,
                "release_count": release_count,
                "description": info.get("summary"),
                "license": info.get("license"),
                "classifiers": info.get("classifiers", [])
            }
            
            # 版本号得分
            version_score = min(major_version * 20, 40)
            # 发布次数得分
            release_score = min(release_count / 10 * 30, 30)
            # 功能完整性得分
            feature_score = 0
            if info.get("license"):
                feature_score += 10
            if info.get("classifiers"):
                feature_score += 20
            
            total_score = version_score + release_score + feature_score
            maturity_metrics["score"] = round(total_score, 2)
            
            return maturity_metrics
        except Exception as e:
            return {"error": str(e)}
    
    def evaluate_npm_maturity(package_name: str) -> dict:
        """评估NPM包成熟度"""
        try:
            package_info = APITools.get_npm_package_info(package_name)
            if not package_info:
                return {"error": "Failed to get package info"}
            
            version = package_info.get("version", "0.0.0")
            
            # 分析版本号
            version_parts = version.split(".")
            major_version = int(version_parts[0]) if version_parts else 0
            
            # 计算成熟度得分
            maturity_metrics = {
                "version": version,
                "major_version": major_version,
                "description": package_info.get("description"),
                "license": package_info.get("license"),
                "repository": package_info.get("repository", {}).get("url")
            }
            
            # 版本号得分
            version_score = min(major_version * 20, 40)
            # 功能完整性得分
            feature_score = 0
            if package_info.get("license"):
                feature_score += 20
            if package_info.get("repository"):
                feature_score += 20
            if package_info.get("description"):
                feature_score += 20
            
            total_score = version_score + feature_score
            maturity_metrics["score"] = round(total_score, 2)
            
            return maturity_metrics
        except Exception as e:
            return {"error": str(e)}
    
    tools = [
        evaluate_github_maturity,
        evaluate_pypi_maturity,
        evaluate_npm_maturity
    ]
    
    return create_react_agent(
        model=model,
        tools=tools,
        name="maturity_agent",
        prompt="You are a maturity evaluation agent. Your task is to evaluate the maturity of open-source projects based on version number, release frequency, update status, and breaking change history. Provide detailed analysis and scores for each project."
    )