import time

import requests

from tools import APITools


class PopularityAgent:
    @staticmethod
    def evaluate(project):
        score = 0.0
        details = {}

        if "html_url" in project and "github.com" in project["html_url"]:
            stars = project.get("stargazers_count", 0)
            score += min(stars / 10000, 1) * 0.3
            details["stars"] = stars

            forks = project.get("forks_count", 0)
            score += min(forks / 1000, 1) * 0.2
            details["forks"] = forks

            watchers = project.get("watchers_count", 0)
            score += min(watchers / 1000, 1) * 0.1
            details["watchers"] = watchers

        score += 0.4
        return {"score": min(score, 1.0), "details": details}


class MaturityAgent:
    @staticmethod
    def evaluate(project):
        score = 0.0
        details = {}

        if "version" in project:
            version = project["version"]
            details["version"] = version
            try:
                major, minor, patch = map(int, version.split("."))
                score += min((major * 0.1 + minor * 0.02 + patch * 0.005), 0.4)
            except Exception:
                pass

        if "created_at" in project:
            created_at = project["created_at"]
            details["created_at"] = created_at
            created_time = time.mktime(time.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ"))
            age = time.time() - created_time
            score += min(age / (3 * 365 * 24 * 3600), 1) * 0.4

        score += 0.2
        return {"score": min(score, 1.0), "details": details}


class EcosystemAgent:
    @staticmethod
    def evaluate(project):
        score = 0.0
        details = {}

        if "contributors_url" in project:
            try:
                response = requests.get(project["contributors_url"], timeout=10)
                if response.status_code == 200:
                    contributor_count = len(response.json())
                    score += min(contributor_count / 100, 1) * 0.3
                    details["contributor_count"] = contributor_count
            except Exception:
                pass

        if "homepage" in project and project["homepage"]:
            score += 0.2
            details["has_homepage"] = True

        if "license" in project and project["license"]:
            score += 0.2
            details["has_license"] = True

        score += 0.3
        return {"score": min(score, 1.0), "details": details}


class RiskAgent:
    @staticmethod
    def evaluate(project):
        score = 1.0
        details = {}

        if "name" in project:
            vulnerabilities = APITools.check_vulnerabilities(project["name"])
            vuln_count = len(vulnerabilities.get("vulnerabilities", []))
            score -= vuln_count * 0.1
            details["vulnerability_count"] = vuln_count

        if "updated_at" in project:
            updated_at = project["updated_at"]
            details["updated_at"] = updated_at
            updated_time = time.mktime(time.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ"))
            days_since_update = (time.time() - updated_time) / (24 * 3600)
            if days_since_update > 365:
                score -= 0.3
            elif days_since_update > 180:
                score -= 0.2
            elif days_since_update > 90:
                score -= 0.1

        return {"score": max(score, 0.0), "details": details}


class ScenarioAgent:
    @staticmethod
    def evaluate(project, user_need, llm_result=None):
        del user_need
        score = 0.0
        details = {}

        if "name" in project:
            name = project["name"].lower()
            if llm_result and "intent" in llm_result and "core_keywords" in llm_result["intent"]:
                for keyword in llm_result["intent"]["core_keywords"]:
                    if keyword.lower() in name:
                        score += 0.2

        if "description" in project:
            description = project["description"].lower() if project["description"] else ""
            if llm_result and "intent" in llm_result and "core_keywords" in llm_result["intent"]:
                for keyword in llm_result["intent"]["core_keywords"]:
                    if keyword.lower() in description:
                        score += 0.2

        score += 0.6
        return {"score": min(score, 1.0), "details": details}


class TrendAgent:
    @staticmethod
    def evaluate(project):
        score = 0.0
        details = {}

        if "updated_at" in project and "created_at" in project:
            updated_time = time.mktime(time.strptime(project["updated_at"], "%Y-%m-%dT%H:%M:%SZ"))
            created_time = time.mktime(time.strptime(project["created_at"], "%Y-%m-%dT%H:%M:%SZ"))
            if updated_time - created_time > 0:
                score += 0.2
                details["is_active"] = True

        if "stargazers_count" in project:
            stars = project["stargazers_count"]
            if stars > 10000:
                score += 0.3
            elif stars > 1000:
                score += 0.2
            elif stars > 100:
                score += 0.1

        return {"score": min(score, 1.0), "details": details}
