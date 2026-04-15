from langgraph.prebuilt import create_react_agent
from tools import APITools
from datetime import datetime

def create_trend_agent(model):
    """创建趋势预测Agent"""
    
    def analyze_github_trend(repo_owner: str, repo_name: str) -> dict:
        """分析GitHub仓库趋势"""
        try:
            repo_info = APITools.get_github_repo_info(repo_owner, repo_name)
            if not repo_info:
                return {"error": "Failed to get repo info"}
            
            # 分析趋势指标
            created_at = repo_info.get("created_at")
            updated_at = repo_info.get("updated_at")
            stars = repo_info.get("stargazers_count", 0)
            forks = repo_info.get("forks_count", 0)
            open_issues = repo_info.get("open_issues_count", 0)
            
            if created_at and updated_at:
                created_date = datetime.fromisoformat(created_at[:-1])
                updated_date = datetime.fromisoformat(updated_at[:-1])
                days_since_creation = (updated_date - created_date).days
                days_since_update = (datetime.now() - updated_date).days
            else:
                days_since_creation = 0
                days_since_update = 999
            
            # 计算趋势指标
            # 假设每天增长的Star数
            daily_star_growth = stars / days_since_creation if days_since_creation > 0 else 0
            # 假设每天增长的Fork数
            daily_fork_growth = forks / days_since_creation if days_since_creation > 0 else 0
            
            trend_metrics = {
                "created_at": created_at,
                "updated_at": updated_at,
                "days_since_creation": days_since_creation,
                "days_since_update": days_since_update,
                "stars": stars,
                "forks": forks,
                "open_issues": open_issues,
                "daily_star_growth": round(daily_star_growth, 2),
                "daily_fork_growth": round(daily_fork_growth, 2)
            }
            
            # 预测趋势
            if daily_star_growth > 10:
                trend = "上升期"
                trend_score = 90
            elif daily_star_growth > 1:
                trend = "稳定期"
                trend_score = 70
            elif days_since_update < 30:
                trend = "稳定期"
                trend_score = 60
            else:
                trend = "衰退期"
                trend_score = 40
            
            trend_metrics["trend"] = trend
            trend_metrics["trend_score"] = trend_score
            
            return trend_metrics
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_pypi_trend(package_name: str) -> dict:
        """分析PyPI包趋势"""
        try:
            package_info = APITools.get_pypi_package_info(package_name)
            download_stats = APITools.get_pypi_download_stats(package_name)
            
            if not package_info:
                return {"error": "Failed to get package info"}
            
            info = package_info.get("info", {})
            version = info.get("version", "0.0.0")
            
            # 分析趋势指标
            downloads_last_month = download_stats.get("data", {}).get("last_month", 0) if download_stats else 0
            
            trend_metrics = {
                "version": version,
                "downloads_last_month": downloads_last_month,
                "description": info.get("summary"),
                "license": info.get("license")
            }
            
            # 预测趋势
            if downloads_last_month > 1000000:
                trend = "上升期"
                trend_score = 90
            elif downloads_last_month > 100000:
                trend = "稳定期"
                trend_score = 70
            elif downloads_last_month > 10000:
                trend = "稳定期"
                trend_score = 60
            else:
                trend = "衰退期"
                trend_score = 40
            
            trend_metrics["trend"] = trend
            trend_metrics["trend_score"] = trend_score
            
            return trend_metrics
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_npm_trend(package_name: str) -> dict:
        """分析NPM包趋势"""
        try:
            package_info = APITools.get_npm_package_info(package_name)
            if not package_info:
                return {"error": "Failed to get package info"}
            
            version = package_info.get("version", "0.0.0")
            
            # 分析趋势指标
            dependencies = package_info.get("dependencies", {})
            devDependencies = package_info.get("devDependencies", {})
            
            trend_metrics = {
                "version": version,
                "dependencies_count": len(dependencies),
                "devDependencies_count": len(devDependencies),
                "description": package_info.get("description"),
                "license": package_info.get("license")
            }
            
            # 预测趋势
            if len(dependencies) > 20 or len(devDependencies) > 30:
                trend = "稳定期"
                trend_score = 70
            elif version and not version.startswith("0."):
                trend = "稳定期"
                trend_score = 60
            else:
                trend = "上升期" if version.startswith("0.") else "衰退期"
                trend_score = 50 if version.startswith("0.") else 40
            
            trend_metrics["trend"] = trend
            trend_metrics["trend_score"] = trend_score
            
            return trend_metrics
        except Exception as e:
            return {"error": str(e)}
    
    tools = [
        analyze_github_trend,
        analyze_pypi_trend,
        analyze_npm_trend
    ]
    
    return create_react_agent(
        model=model,
        tools=tools,
        name="trend_agent",
        prompt="You are a trend prediction agent. Your task is to analyze historical data of open-source projects and predict their future activity. Identify projects in上升期, 稳定期, or 衰退期. Provide detailed analysis and predictions."
    )