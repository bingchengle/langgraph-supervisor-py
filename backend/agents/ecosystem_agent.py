from langgraph.prebuilt import create_react_agent
from tools import APITools

def create_ecosystem_agent(model):
    """创建生态评估Agent"""
    
    def evaluate_github_ecosystem(repo_owner: str, repo_name: str) -> dict:
        """评估GitHub仓库生态系统"""
        try:
            repo_info = APITools.get_github_repo_info(repo_owner, repo_name)
            contributors = APITools.get_github_repo_stats(repo_owner, repo_name)
            
            if not repo_info:
                return {"error": "Failed to get repo info"}
            
            # 分析生态系统指标
            ecosystem_metrics = {
                "forks": repo_info.get("forks_count", 0),
                "contributors_count": len(contributors) if contributors else 0,
                "open_issues": repo_info.get("open_issues_count", 0),
                "closed_issues": repo_info.get("closed_issues_count", 0),
                "pulls": repo_info.get("open_pr_count", 0),
                "project_urls": repo_info.get("homepage"),
                "topics": repo_info.get("topics", [])
            }
            
            # 计算生态系统得分 (0-100)
            # Fork数量得分
            fork_score = min(ecosystem_metrics["forks"] / 1000 * 30, 30)
            # 贡献者数量得分
            contributor_score = min(ecosystem_metrics["contributors_count"] / 100 * 30, 30)
            # 问题活跃度得分
            issue_score = min((ecosystem_metrics["open_issues"] + ecosystem_metrics["closed_issues"]) / 100 * 20, 20)
            # 社区参与得分
            community_score = 0
            if repo_info.get("homepage"):
                community_score += 10
            if repo_info.get("topics"):
                community_score += 10
            
            total_score = fork_score + contributor_score + issue_score + community_score
            ecosystem_metrics["score"] = round(total_score, 2)
            
            return ecosystem_metrics
        except Exception as e:
            return {"error": str(e)}
    
    def evaluate_pypi_ecosystem(package_name: str) -> dict:
        """评估PyPI包生态系统"""
        try:
            package_info = APITools.get_pypi_package_info(package_name)
            if not package_info:
                return {"error": "Failed to get package info"}
            
            info = package_info.get("info", {})
            
            # 分析生态系统指标
            ecosystem_metrics = {
                "project_urls": info.get("project_urls", {}),
                "classifiers": info.get("classifiers", []),
                "requires_dist": info.get("requires_dist", []),
                "requires_python": info.get("requires_python"),
                "description": info.get("summary")
            }
            
            # 计算生态系统得分
            # 项目URL得分
            url_score = 0
            if info.get("project_urls"):
                url_score = min(len(info["project_urls"]) * 5, 20)
            # 分类器得分
            classifier_score = min(len(info.get("classifiers", [])) / 10 * 20, 20)
            # 依赖得分
            dependency_score = min(len(info.get("requires_dist", [])) / 10 * 20, 20)
            # 文档得分
            doc_score = 0
            if info.get("description"):
                doc_score += 20
            if info.get("requires_python"):
                doc_score += 20
            
            total_score = url_score + classifier_score + dependency_score + doc_score
            ecosystem_metrics["score"] = round(total_score, 2)
            
            return ecosystem_metrics
        except Exception as e:
            return {"error": str(e)}
    
    def evaluate_npm_ecosystem(package_name: str) -> dict:
        """评估NPM包生态系统"""
        try:
            package_info = APITools.get_npm_package_info(package_name)
            if not package_info:
                return {"error": "Failed to get package info"}
            
            # 分析生态系统指标
            ecosystem_metrics = {
                "dependencies": package_info.get("dependencies", {}),
                "devDependencies": package_info.get("devDependencies", {}),
                "peerDependencies": package_info.get("peerDependencies", {}),
                "repository": package_info.get("repository", {}).get("url"),
                "homepage": package_info.get("homepage"),
                "keywords": package_info.get("keywords", [])
            }
            
            # 计算生态系统得分
            # 依赖得分
            dep_score = min((len(ecosystem_metrics["dependencies"]) + len(ecosystem_metrics["devDependencies"])) / 20 * 30, 30)
            # 仓库得分
            repo_score = 0
            if ecosystem_metrics["repository"]:
                repo_score += 20
            if ecosystem_metrics["homepage"]:
                repo_score += 20
            # 关键词得分
            keyword_score = min(len(ecosystem_metrics["keywords"]) / 10 * 30, 30)
            
            total_score = dep_score + repo_score + keyword_score
            ecosystem_metrics["score"] = round(total_score, 2)
            
            return ecosystem_metrics
        except Exception as e:
            return {"error": str(e)}
    
    tools = [
        evaluate_github_ecosystem,
        evaluate_pypi_ecosystem,
        evaluate_npm_ecosystem
    ]
    
    return create_react_agent(
        model=model,
        tools=tools,
        name="ecosystem_agent",
        prompt="You are an ecosystem evaluation agent. Your task is to evaluate the ecosystem of open-source projects based on周边 tools, integration solutions, contributor count, forks, and learning resources. Provide detailed analysis and scores for each project."
    )