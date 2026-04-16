from langgraph.prebuilt import create_react_agent
from tools import APITools

def create_scenario_agent(model):
    """创建场景匹配Agent"""
    
    def analyze_user_requirement(requirement: str) -> dict:
        """分析用户需求"""
        # 这里可以使用LLM进行更复杂的需求分析
        # 简化处理，直接返回需求内容
        return {
            "requirement": requirement,
            "keywords": requirement.split(),
            "analysis": "用户需要一个适合特定场景的开源项目"
        }
    
    def search_relevant_projects(keywords: list, platform: str = "github", limit: int = 5) -> list:
        """搜索相关项目"""
        try:
            query = " ".join(keywords)
            if platform == "github":
                return APITools.search_github_repositories(query, per_page=limit)
            elif platform == "pypi":
                return APITools.search_pypi_packages(query)
            elif platform == "npm":
                return APITools.search_npm_packages(query)
            else:
                return []
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def evaluate_scenario_match(project: dict, requirement: str) -> dict:
        """评估项目与场景的匹配度"""
        try:
            # 简化的匹配度评估
            # 实际应用中可以使用更复杂的算法
            project_name = project.get("name", "")
            description = project.get("description", "") or project.get("info", {}).get("summary", "")
            
            # 计算匹配度得分
            match_score = 0
            requirement_lower = requirement.lower()
            
            # 检查项目名称是否包含需求关键词
            for keyword in requirement_lower.split():
                if keyword in project_name.lower():
                    match_score += 20
                if keyword in description.lower():
                    match_score += 10
            
            # 检查项目描述是否与需求相关
            if any(keyword in description.lower() for keyword in requirement_lower.split()):
                match_score += 30
            
            # 确保得分在合理范围内
            match_score = min(match_score, 100)
            
            return {
                "project_name": project_name,
                "description": description,
                "match_score": round(match_score, 2),
                "match_level": "高" if match_score > 70 else "中" if match_score > 40 else "低"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def generate_migration_cost_estimate(project: dict) -> dict:
        """生成迁移成本评估"""
        try:
            # 简化的迁移成本评估
            project_name = project.get("name", "")
            
            # 基于项目复杂度和生态系统评估迁移成本
            complexity = 0
            if project.get("size", 0) > 10000:
                complexity += 20
            if project.get("dependencies", {}) and len(project.get("dependencies", {})) > 10:
                complexity += 20
            if project.get("requires_dist", []) and len(project.get("requires_dist", [])) > 10:
                complexity += 20
            
            # 计算迁移成本
            migration_cost = {
                "project_name": project_name,
                "complexity": complexity,
                "time_estimate": "1-2周" if complexity < 30 else "2-4周" if complexity < 60 else "4周以上",
                "resource_estimate": "低" if complexity < 30 else "中" if complexity < 60 else "高",
                "risk_level": "低" if complexity < 30 else "中" if complexity < 60 else "高"
            }
            
            return migration_cost
        except Exception as e:
            return {"error": str(e)}
    
    tools = [
        analyze_user_requirement,
        search_relevant_projects,
        evaluate_scenario_match,
        generate_migration_cost_estimate
    ]
    
    return create_react_agent(
        model=model,
        tools=tools,
        name="scenario_agent",
        prompt="You are a scenario matching agent. Your task is to analyze user requirements, search for relevant open-source projects, evaluate their match with the requirements, and generate migration cost estimates. Provide detailed analysis and recommendations."
    )