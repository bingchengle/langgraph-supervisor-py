from langgraph.prebuilt import create_react_agent
from tools import APITools

def create_popularity_agent(model):
    """创建流行度评估Agent"""
    
    def evaluate_github_popularity(repo_owner: str, repo_name: str) -> dict:
        """评估GitHub仓库流行度"""
        try:
            repo_info = APITools.get_github_repo_info(repo_owner, repo_name)
            if not repo_info:
                return {"error": "Failed to get repo info"}
            
            popularity_metrics = {
                "stars": repo_info.get("stargazers_count", 0),
                "forks": repo_info.get("forks_count", 0),
                "watchers": repo_info.get("watchers_count", 0),
                "open_issues": repo_info.get("open_issues_count", 0),
                "subscribers": repo_info.get("subscribers_count", 0),
                "created_at": repo_info.get("created_at"),
                "updated_at": repo_info.get("updated_at")
            }
            
            # 计算流行度得分 (0-100)
            max_stars = 100000  # 假设最大Star数为10万
            star_score = min(popularity_metrics["stars"] / max_stars * 40, 40)
            fork_score = min(popularity_metrics["forks"] / 10000 * 20, 20)
            issue_score = min(popularity_metrics["open_issues"] / 1000 * 10, 10)
            subscriber_score = min(popularity_metrics["subscribers"] / 1000 * 30, 30)
            
            total_score = star_score + fork_score + issue_score + subscriber_score
            
            popularity_metrics["score"] = round(total_score, 2)
            return popularity_metrics
        except Exception as e:
            return {"error": str(e)}
    
    def evaluate_pypi_popularity(package_name: str) -> dict:
        """评估PyPI包流行度"""
        try:
            package_info = APITools.get_pypi_package_info(package_name)
            download_stats = APITools.get_pypi_download_stats(package_name)
            
            popularity_metrics = {
                "version": package_info.get("info", {}).get("version"),
                "description": package_info.get("info", {}).get("summary"),
                "downloads": download_stats.get("data", {}).get("last_month", 0) if download_stats else 0,
                "project_urls": package_info.get("info", {}).get("project_urls", {})
            }
            
            # 计算流行度得分 (0-100)
            max_downloads = 1000000  # 假设最大月下载量为100万
            download_score = min(popularity_metrics["downloads"] / max_downloads * 100, 100)
            popularity_metrics["score"] = round(download_score, 2)
            
            return popularity_metrics
        except Exception as e:
            return {"error": str(e)}
    
    def evaluate_npm_popularity(package_name: str) -> dict:
        """评估NPM包流行度"""
        try:
            package_info = APITools.get_npm_package_info(package_name)
            if not package_info:
                return {"error": "Failed to get package info"}
            
            popularity_metrics = {
                "version": package_info.get("version"),
                "description": package_info.get("description"),
                "license": package_info.get("license"),
                "repository": package_info.get("repository", {}).get("url")
            }
            
            # NPM API不直接提供下载统计，这里简化处理
            popularity_metrics["score"] = 50  # 默认得分
            
            return popularity_metrics
        except Exception as e:
            return {"error": str(e)}
    
    tools = [
        evaluate_github_popularity,
        evaluate_pypi_popularity,
        evaluate_npm_popularity
    ]
    
    return create_react_agent(
        model=model,
        tools=tools,
        name="popularity_agent",
        prompt="You are a popularity evaluation agent. Your task is to evaluate the popularity of open-source projects based on various metrics like stars, downloads, community engagement, and growth trends. Provide detailed analysis and scores for each project."
    )