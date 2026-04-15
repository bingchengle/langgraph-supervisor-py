from langgraph.prebuilt import create_react_agent
from tools import APITools
from datetime import datetime

def create_risk_agent(model):
    """创建风险评估Agent"""
    
    def evaluate_github_risk(repo_owner: str, repo_name: str) -> dict:
        """评估GitHub仓库风险"""
        try:
            repo_info = APITools.get_github_repo_info(repo_owner, repo_name)
            if not repo_info:
                return {"error": "Failed to get repo info"}
            
            # 分析风险指标
            updated_at = repo_info.get("updated_at")
            days_since_update = 0
            if updated_at:
                updated_date = datetime.fromisoformat(updated_at[:-1])
                days_since_update = (datetime.now() - updated_date).days
            
            risk_metrics = {
                "days_since_update": days_since_update,
                "license": repo_info.get("license", {}).get("name"),
                "open_issues": repo_info.get("open_issues_count", 0),
                "watchers": repo_info.get("watchers_count", 0),
                "stargazers": repo_info.get("stargazers_count", 0)
            }
            
            # 计算风险得分 (0-100，得分越高风险越低)
            # 更新频率得分
            update_score = max(0, 30 - (days_since_update / 30 * 30))
            # License得分
            license_score = 20 if risk_metrics["license"] else 0
            # 社区活跃度得分
            community_score = min((risk_metrics["watchers"] + risk_metrics["stargazers"]) / 1000 * 30, 30)
            # 问题处理得分
            issue_score = 20 if risk_metrics["open_issues"] < 100 else max(0, 20 - (risk_metrics["open_issues"] - 100) / 100 * 20)
            
            total_score = update_score + license_score + community_score + issue_score
            risk_metrics["score"] = round(total_score, 2)
            risk_metrics["risk_level"] = "低" if total_score > 70 else "中" if total_score > 40 else "高"
            
            return risk_metrics
        except Exception as e:
            return {"error": str(e)}
    
    def evaluate_pypi_risk(package_name: str) -> dict:
        """评估PyPI包风险"""
        try:
            package_info = APITools.get_pypi_package_info(package_name)
            if not package_info:
                return {"error": "Failed to get package info"}
            
            info = package_info.get("info", {})
            version = info.get("version", "0.0.0")
            
            # 检查安全漏洞
            vulnerabilities = APITools.check_osv_vulnerabilities(package_name, version, "PyPI")
            
            # 分析风险指标
            risk_metrics = {
                "version": version,
                "license": info.get("license"),
                "vulnerabilities_count": len(vulnerabilities),
                "vulnerabilities": vulnerabilities,
                "requires_python": info.get("requires_python"),
                "description": info.get("summary")
            }
            
            # 计算风险得分
            # 漏洞得分
            vuln_score = max(0, 40 - (len(vulnerabilities) * 10))
            # License得分
            license_score = 20 if info.get("license") else 0
            # 版本得分
            version_score = 20 if version and not version.startswith("0.") else 10
            # 文档得分
            doc_score = 20 if info.get("summary") else 0
            
            total_score = vuln_score + license_score + version_score + doc_score
            risk_metrics["score"] = round(total_score, 2)
            risk_metrics["risk_level"] = "低" if total_score > 70 else "中" if total_score > 40 else "高"
            
            return risk_metrics
        except Exception as e:
            return {"error": str(e)}
    
    def evaluate_npm_risk(package_name: str) -> dict:
        """评估NPM包风险"""
        try:
            package_info = APITools.get_npm_package_info(package_name)
            if not package_info:
                return {"error": "Failed to get package info"}
            
            version = package_info.get("version", "0.0.0")
            
            # 分析风险指标
            risk_metrics = {
                "version": version,
                "license": package_info.get("license"),
                "dependencies": package_info.get("dependencies", {}),
                "repository": package_info.get("repository", {}).get("url"),
                "homepage": package_info.get("homepage")
            }
            
            # 计算风险得分
            # 版本得分
            version_score = 25 if version and not version.startswith("0.") else 10
            # License得分
            license_score = 25 if package_info.get("license") else 0
            # 依赖得分
            dep_score = 25 if len(package_info.get("dependencies", {})) < 20 else max(0, 25 - (len(package_info.get("dependencies", {})) - 20) / 10 * 25)
            # 文档得分
            doc_score = 25 if package_info.get("homepage") and package_info.get("repository") else 0
            
            total_score = version_score + license_score + dep_score + doc_score
            risk_metrics["score"] = round(total_score, 2)
            risk_metrics["risk_level"] = "低" if total_score > 70 else "中" if total_score > 40 else "高"
            
            return risk_metrics
        except Exception as e:
            return {"error": str(e)}
    
    tools = [
        evaluate_github_risk,
        evaluate_pypi_risk,
        evaluate_npm_risk
    ]
    
    return create_react_agent(
        model=model,
        tools=tools,
        name="risk_agent",
        prompt="You are a risk evaluation agent. Your task is to evaluate the risk of open-source projects based on maintenance status, license compatibility, security vulnerabilities, and abandonment risk. Provide detailed analysis and scores for each project."
    )