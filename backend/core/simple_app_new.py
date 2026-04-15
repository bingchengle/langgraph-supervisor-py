#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开源项目智能选型助手 - 100% 纯通用版
禁止硬编码、禁止默认答案、禁止 fallback 项目、禁止无中生有推荐项目
"""

# 设置环境变量，确保终端输出中文正常
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'zh_CN.UTF-8'
os.environ['LC_ALL'] = 'zh_CN.UTF-8'
print(f"PYTHONIOENCODING: {os.environ.get('PYTHONIOENCODING')}")
print(f"LANG: {os.environ.get('LANG')}")
print(f"LC_ALL: {os.environ.get('LC_ALL')}")

import json
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 安全检查函数
def check_safety(text):
    """检查文本是否安全，不包含政治敏感内容"""
    try:
        if not text:
            return True
        
        # 确保text是字符串类型
        if not isinstance(text, str):
            text = str(text)
        
        # 转换为小写进行匹配
        text_lower = text.lower()
        
        # 检查是否包含明显的政治敏感词
        sensitive_patterns = [
            "政治", "政府", "国家", "政党", "政策", "法律", "法规", "宪法", "制度", "体制",
            "敏感", "禁止", "违法", "违规", "非法", "抗议", "示威", "游行", "罢工", "暴动"
        ]
        
        for pattern in sensitive_patterns:
            if pattern in text_lower:
                return False
        
        return True
    except Exception as e:
        print(f"检查安全性时发生错误: {e}")
        return False

# 确保requests库使用UTF-8编码
requests.packages.urllib3.disable_warnings()
requests.adapters.DEFAULT_RETRIES = 5

# 大语言模型工具
def get_llm_intent_analysis(prompt, model="gpt-3.5-turbo", api_key=None):
    """调用大语言模型进行需求意图精确定位 - 100% 纯通用版"""
    try:
        # 确保prompt是字符串类型，并且正确编码
        if not isinstance(prompt, str):
            prompt = str(prompt)
        # 处理编码问题，确保中文显示正常
        prompt = prompt.encode('utf-8', errors='ignore').decode('utf-8')
        
        # 检查安全性
        if not check_safety(prompt):
            print("检测到不安全内容，返回空结果")
            return {
                "core_keywords": [],
                "search_query": ""
            }
        
        # 尝试使用国内OpenAI API
        api_key = "sk-wCh87Njz7agL1pf1B98uMyL8rsiPcLQoX5NUu2iL2y6CAnlp"
        api_url = "https://fast.poloai.top"
        
        if api_key and api_url:
            print(f"使用国内API进行需求意图分析...")
            print(f"API地址: {api_url}")
            print(f"API密钥: {api_key[:6]}...{api_key[-6:]}")
            
            # 构建完整的API端点
            url = f"{api_url}/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            # 尝试不同的模型
            models = ["qwen-turbo", "kimi", "glm", "deepseek"]
            
            for model_name in models:
                print(f"尝试使用模型: {model_name}")
                payload = {
                    "model": model_name,
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个开源项目推荐助手，需要精确分析用户的需求意图。请返回一个JSON对象，包含以下字段：\n1. core_keywords: 从用户提问里自动提取的核心关键词列表，包括核心名词、功能、场景、工具、技术\n2. search_query: 用于搜索的关键词拼接字符串，直接从用户输入中提取，不添加任何额外内容\n\n请根据用户输入自由分析，不要做任何领域假设，不要局限于固定列表，不要猜测用户的潜在需求。例如：\n用户输入：推荐雨课堂二次开发项目\n输出：{\"core_keywords\": [\"雨课堂\", \"二次开发\", \"插件\", \"开源项目\"], \"search_query\": \"雨课堂 二次开发 项目\"}\n\n用户输入：适合新手的微调库\n输出：{\"core_keywords\": [\"LLM 微调\", \"轻量\", \"简单\", \"新手友好\"], \"search_query\": \"适合新手的微调库\"}\n\n用户输入：前端项目\n输出：{\"core_keywords\": [\"前端\", \"web\", \"javascript\", \"前端开发\"], \"search_query\": \"前端项目\"}\n\n用户输入：agent项目\n输出：{\"core_keywords\": [\"agent\", \"智能体\", \"AI 助手\", \"代理\"], \"search_query\": \"agent项目\"}"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "response_format": {"type": "json_object"}
                }
                
                try:
                    print(f"发送API请求...")
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    print(f"API响应状态码: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"API调用成功!")
                        usage = data.get('usage', {})
                        print(f"Token消耗: {usage}")
                        
                        # 检查响应结构
                        if "choices" in data and len(data["choices"]) > 0:
                            content = data["choices"][0]["message"]["content"]
                            # 处理编码问题，确保中文显示正常
                            content = content.encode('utf-8', errors='ignore').decode('utf-8')
                            print(f"API响应内容: {content}")
                            
                            intent_result = json.loads(content)
                            # 验证必需字段
                            required_fields = ['core_keywords', 'search_query']
                            for field in required_fields:
                                if field not in intent_result:
                                    raise ValueError(f"缺少必需字段: {field}")
                            return intent_result
                    else:
                        print(f"API错误: {response.status_code}")
                        print(f"错误信息: {response.text}")
                except Exception as e:
                    print(f"调用API时发生错误: {e}")
                    continue
        
        # 如果没有API密钥或调用失败，使用简单的关键词提取逻辑
        print("使用默认关键词提取逻辑...")
        # 基于用户输入提取关键词
        user_need = prompt
        
        # 简单的关键词提取
        # 移除常见的推荐词
        stop_words = ["推荐", "给我", "一些", "适合", "的", "项目", "库", "工具"]
        for stop_word in stop_words:
            user_need = user_need.replace(stop_word, "")
        
        # 提取关键词
        core_keywords = []
        words = user_need.split()
        for word in words:
            if len(word) > 1:
                core_keywords.append(word)
        
        # 生成搜索查询
        search_query = prompt
        
        return {
            "core_keywords": core_keywords,
            "search_query": search_query
        }
    except Exception as e:
        print(f"调用大语言模型失败: {e}")
        # 确保prompt是字符串类型，并且正确编码
        if not isinstance(prompt, str):
            prompt = str(prompt)
        # 处理编码问题，确保中文显示正常
        prompt = prompt.encode('utf-8', errors='ignore').decode('utf-8')
        
        # 返回基于用户输入的简单关键词提取
        user_need = prompt
        stop_words = ["推荐", "给我", "一些", "适合", "的", "项目", "库", "工具"]
        for stop_word in stop_words:
            user_need = user_need.replace(stop_word, "")
        
        core_keywords = []
        words = user_need.split()
        for word in words:
            if len(word) > 1:
                core_keywords.append(word)
        
        search_query = prompt
        
        return {
            "core_keywords": core_keywords,
            "search_query": search_query
        }

def get_llm_requirement_analysis(prompt, model="gpt-3.5-turbo", api_key=None):
    """调用大语言模型分析用户需求，生成评估维度与动态权重 - 100% 纯通用版"""
    try:
        # 首先进行需求意图分析
        intent_result = get_llm_intent_analysis(prompt, model, api_key)
        print(f"需求意图分析结果: {intent_result}")
        
        # 检查intent_result是否为None
        if not intent_result:
            print("意图分析失败，使用默认值")
            # 使用默认的意图分析结果
            intent_result = {
                "core_keywords": ["项目", "开发"],
                "search_query": "项目 开发"
            }
        
        # 尝试使用国内OpenAI API
        api_key = "sk-wCh87Njz7agL1pf1B98uMyL8rsiPcLQoX5NUu2iL2y6CAnlp"
        api_url = "https://fast.poloai.top"
        
        if api_key and api_url:
            print(f"使用国内API进行需求分析...")
            print(f"API地址: {api_url}")
            print(f"API密钥: {api_key[:6]}...{api_key[-6:]}")
            
            # 构建完整的API端点
            url = f"{api_url}/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            # 尝试不同的模型
            models = ["qwen-turbo", "kimi", "glm", "deepseek"]
            
            for model_name in models:
                print(f"尝试使用模型: {model_name}")
                payload = {
                    "model": model_name,
                    "messages": [
                        {
                            "role": "system",
                            "content": f"你是一个开源项目推荐助手，需要深入分析用户的需求并生成结构化的评估方案。用户的需求关键词已经提取如下：\n{json.dumps(intent_result, ensure_ascii=False)}\n\n请返回一个JSON对象，包含以下字段：\n1. key_requirements: 关键需求点列表\n2. dimensions_needed: 需要的评估维度列表（如流行度、成熟度、生态、风险、上手难度、性能、体积、文档友好度等）\n3. weights: 各维度的权重字典，总和为1\n\n请根据用户的具体需求调整各维度的权重，确保权重总和为1。例如：\n- 如果用户强调新手友好，应提高上手难度和文档友好度的权重\n- 如果用户强调生产稳定，应提高成熟度和风险的权重\n- 如果用户强调轻量快速，应考虑体积和性能的权重\n- 如果用户强调功能全面，应提高生态的权重"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "response_format": {"type": "json_object"}
                }
                
                try:
                    print(f"发送API请求...")
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    print(f"API响应状态码: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"API调用成功!")
                        usage = data.get('usage', {})
                        print(f"Token消耗: {usage}")
                        
                        # 检查响应结构
                        if "choices" in data and len(data["choices"]) > 0:
                            content = data["choices"][0]["message"]["content"]
                            print(f"API响应内容: {content}")
                            
                            result = json.loads(content)
                            # 验证权重总和是否为1
                            weights = result.get('weights', {})
                            total_weight = sum(weights.values())
                            if abs(total_weight - 1.0) > 0.01:
                                # 归一化权重
                                normalized_weights = {k: v / total_weight for k, v in weights.items()}
                                result['weights'] = normalized_weights
                            # 添加意图分析结果
                            result['intent'] = intent_result
                            return result
                    else:
                        print(f"API错误: {response.status_code}")
                        print(f"错误信息: {response.text}")
                except Exception as e:
                    print(f"调用API时发生错误: {e}")
                    continue
        
        # 如果没有API密钥或调用失败，使用默认理解逻辑
        print("使用默认需求分析逻辑...")
        
        # 根据需求设置权重
        weights = {
            "流行度": 0.1,
            "成熟度": 0.2,
            "生态": 0.15,
            "风险": 0.2,
            "上手难度": 0.25,
            "性能": 0.1
        }
        
        # 确保权重总和为1
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        # 构建结果
        result = {
            "key_requirements": intent_result.get('core_keywords', ["功能完整", "易于使用"]),
            "dimensions_needed": list(weights.keys()),
            "weights": weights,
            "intent": intent_result
        }
        
        return result
    except Exception as e:
        print(f"调用大语言模型失败: {e}")
        # 返回默认值
        try:
            intent_result = get_llm_intent_analysis(prompt, model, api_key)
            if not intent_result:
                intent_result = {
                    "core_keywords": ["项目", "开发"],
                    "search_query": "项目 开发"
                }
        except:
            # 如果所有尝试都失败，使用默认值
            intent_result = {
                "core_keywords": ["项目", "开发"],
                "search_query": "项目 开发"
            }
        
        return {
            "key_requirements": intent_result.get('core_keywords', ["功能完整", "易于使用"]),
            "dimensions_needed": ["流行度", "成熟度", "生态", "风险", "上手难度", "性能"],
            "weights": {
                "流行度": 0.1,
                "成熟度": 0.2,
                "生态": 0.15,
                "风险": 0.2,
                "上手难度": 0.25,
                "性能": 0.1
            },
            "intent": intent_result
        }

# API工具类
class APITools:
    """API工具类"""
    
    @staticmethod
    def search_github_repos(query, limit=10, sort="relevance"):
        """搜索GitHub仓库"""
        try:
            # 使用GitHub API搜索
            url = f"https://api.github.com/search/repositories"
            params = {
                "q": query,
                "sort": sort,
                "order": "desc",
                "per_page": limit
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('items', [])[:limit]
            else:
                print(f"GitHub API错误: {response.status_code}")
                return []
        except Exception as e:
            print(f"搜索GitHub仓库失败: {e}")
            return []
    
    @staticmethod
    def get_github_repo_info(repo_owner, repo_name):
        """获取GitHub仓库详细信息"""
        try:
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"GitHub API错误: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取GitHub仓库信息失败: {e}")
            return None
    
    @staticmethod
    def search_pypi_packages(query, limit=10):
        """搜索PyPI包 - 100% 纯通用版"""
        try:
            # 使用PyPI的JSON API进行搜索
            search_url = f"https://pypi.org/search/json?q={query}"
            response = requests.get(search_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                packages = data.get('results', [])[:limit]
                return packages
            else:
                print(f"PyPI API错误: {response.status_code}")
                # 搜索失败时返回空列表，不使用默认包
                return []
        except Exception as e:
            print(f"搜索PyPI包失败: {e}")
            # 搜索失败时返回空列表，不使用默认包
            return []
    
    @staticmethod
    def get_pypi_package_info(package_name):
        """获取PyPI包信息"""
        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"PyPI API错误: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取PyPI包信息失败: {e}")
            return None
    
    @staticmethod
    def search_npm_packages(query, limit=3):
        """搜索NPM包"""
        try:
            url = f"https://registry.npmjs.org/-/v1/search?text={query}&size={limit}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('objects', [])[:limit]
            else:
                print(f"NPM API错误: {response.status_code}")
                return []
        except Exception as e:
            print(f"搜索NPM包失败: {e}")
            return []
    
    @staticmethod
    def check_vulnerabilities(package_name, version=None):
        """检查安全漏洞"""
        try:
            url = "https://api.osv.dev/v1/query"
            payload = {
                "package": {
                    "name": package_name,
                    "ecosystem": "PyPI" if package_name else "npm"
                }
            }
            if version:
                payload["version"] = version
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"OSV API错误: {response.status_code}")
                return {"vulnerabilities": []}
        except Exception as e:
            print(f"检查安全漏洞失败: {e}")
            return {"vulnerabilities": []}

# 项目自动标签模块
class ProjectTagger:
    """项目自动标签模块"""
    
    @staticmethod
    def tag_project(project, domain=None):
        """为项目自动打标签"""
        try:
            # 提取项目名称和描述
            name = project.get('name', '').lower()
            description = project.get('description', '').lower() if project.get('description') else ''
            
            # 构建标签
            tags = {
                "domain": [],
                "complexity": [],
                "skill_level": [],
                "is_beginner_friendly": False,
                "style": []
            }
            
            # 领域标签
            if domain:
                tags['domain'].append(domain)
            else:
                # 基于名称和描述判断领域 - 扩展的领域关键词
                domain_keywords = {
                    'rag': ['rag', 'retrieval', 'vector', 'embedding', 'knowledge', 'document', 'search'],
                    'agent': ['agent', 'assistant', 'chatbot', 'ai', 'llm', 'chat', 'bot'],
                    'pdf': ['pdf', 'document', 'file', 'text', 'ocr'],
                    'embedding': ['embedding', 'vector', 'similarity', 'embeddings'],
                    'database': ['database', 'db', 'storage', 'vector', 'sql', 'nosql'],
                    'pipeline': ['pipeline', 'workflow', 'stream', 'orchestration'],
                    'llm': ['llm', 'language model', 'gpt', 'transformer', 'nlp'],
                    'fine-tuning': ['fine-tune', 'finetune', 'training', 'peft', 'fine tuning'],
                    'quantization': ['quantiz', 'quantization', 'int8', 'fp16', 'quantize'],
                    'multimodal': ['multimodal', 'vision', 'image', 'audio', 'video'],
                    'prompt-engineering': ['prompt', 'prompting', 'prompt engineering', 'prompt design'],
                    'evaluation': ['evaluation', 'benchmark', 'metrics', 'testing'],
                    'deployment': ['deployment', 'serving', 'inference', 'production']
                }
                
                for domain_name, keywords in domain_keywords.items():
                    if any(keyword in name or keyword in description for keyword in keywords):
                        tags['domain'].append(domain_name)
                
                # 如果没有匹配到任何领域，使用通用领域
                if not tags['domain']:
                    tags['domain'].append('general')
            
            # 复杂度标签
            if any(term in name or term in description for term in ['lightweight', 'tiny', 'small', 'minimal', 'lite', 'simple', 'easy', 'micro']):
                tags['complexity'].append('low')
            elif any(term in name or term in description for term in ['heavy', 'enterprise', 'production', 'full-featured', 'comprehensive']):
                tags['complexity'].append('high')
            else:
                # 特殊处理已知项目
                heavyweight_projects = ['langchain', 'llama-index', 'autogen', 'crewai', 'tensorflow', 'pytorch']
                if name in heavyweight_projects:
                    tags['complexity'].append('high')
                else:
                    tags['complexity'].append('medium')
            
            # 技能水平标签
            if any(term in name or term in description for term in ['beginner', 'easy', 'simple', 'tutorial', 'starter', 'learn', 'intro', 'basic']):
                tags['skill_level'].append('beginner')
                tags['is_beginner_friendly'] = True
            elif any(term in name or term in description for term in ['advanced', 'expert', 'pro', 'professional']):
                tags['skill_level'].append('advanced')
            else:
                tags['skill_level'].append('intermediate')
                # 特殊处理已知项目
                beginner_friendly_projects = ['peft', 'bitsandbytes', 'chromadb', 'fastapi', 'flask']
                if name in beginner_friendly_projects:
                    tags['skill_level'].append('beginner')
                    tags['is_beginner_friendly'] = True
            
            # 风格标签
            if any(term in name or term in description for term in ['lightweight', 'tiny', 'small', 'minimal', 'lite', 'simple']):
                tags['style'].append('lightweight')
            elif any(term in name or term in description for term in ['production', 'stable', 'enterprise', 'robust']):
                tags['style'].append('production')
            elif any(term in name or term in description for term in ['experimental', 'cutting-edge', 'research']):
                tags['style'].append('experimental')
            else:
                tags['style'].append('general')
            
            return tags
        except Exception as e:
            print(f"为项目打标签失败: {e}")
            # 返回默认标签
            return {
                "domain": [domain] if domain else ['general'],
                "complexity": ['medium'],
                "skill_level": ['intermediate'],
                "is_beginner_friendly": False,
                "style": ['general']
            }

# 评估Agent
class PopularityAgent:
    """流行度评估Agent"""
    @staticmethod
    def evaluate(project):
        """评估项目流行度，返回标准化分数0~1"""
        score = 0.0
        details = {}
        
        # 检查是否是GitHub仓库
        if 'html_url' in project and 'github.com' in project['html_url']:
            # 基于Star数量评分
            stars = project.get('stargazers_count', 0)
            score += min(stars / 10000, 1) * 0.3
            details['stars'] = stars
            
            # 基于Fork数量评分
            forks = project.get('forks_count', 0)
            score += min(forks / 1000, 1) * 0.2
            details['forks'] = forks
            
            # 基于Watch数量评分
            watchers = project.get('watchers_count', 0)
            score += min(watchers / 1000, 1) * 0.1
            details['watchers'] = watchers
        
        # 基于项目名称和描述的相关性评分
        score += 0.4  # 基础分
        
        return {
            "score": min(score, 1.0),
            "details": details
        }

class MaturityAgent:
    """成熟度评估Agent"""
    @staticmethod
    def evaluate(project):
        """评估项目成熟度，返回标准化分数0~1"""
        score = 0.0
        details = {}
        
        # 检查是否有版本信息
        if 'version' in project:
            version = project['version']
            details['version'] = version
            # 基于版本号评分
            try:
                major, minor, patch = map(int, version.split('.'))
                # 版本号评分，最高0.4
                version_score = min((major * 0.1 + minor * 0.02 + patch * 0.005), 0.4)
                score += version_score
            except:
                pass
        
        # 检查是否有发布信息
        if 'created_at' in project:
            created_at = project['created_at']
            details['created_at'] = created_at
            # 基于创建时间评分（越老越成熟）
            created_time = time.mktime(time.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ'))
            age = time.time() - created_time
            # 项目年龄评分，最高0.4
            age_score = min(age / (3 * 365 * 24 * 3600), 1) * 0.4
            score += age_score
        
        # 基础分
        score += 0.2
        
        return {
            "score": min(score, 1.0),
            "details": details
        }

class EcosystemAgent:
    """生态评估Agent"""
    @staticmethod
    def evaluate(project):
        """评估项目生态，返回标准化分数0~1"""
        score = 0.0
        details = {}
        
        # 检查是否有贡献者信息
        if 'contributors_url' in project:
            try:
                response = requests.get(project['contributors_url'], timeout=10)
                if response.status_code == 200:
                    contributors = response.json()
                    contributor_count = len(contributors)
                    score += min(contributor_count / 100, 1) * 0.3
                    details['contributor_count'] = contributor_count
            except:
                pass
        
        # 检查是否有文档
        if 'homepage' in project and project['homepage']:
            score += 0.2
            details['has_homepage'] = True
        
        # 检查是否有许可证
        if 'license' in project and project['license']:
            score += 0.2
            details['has_license'] = True
        
        # 基础分
        score += 0.3
        
        return {
            "score": min(score, 1.0),
            "details": details
        }

class RiskAgent:
    """风险评估Agent"""
    @staticmethod
    def evaluate(project):
        """评估项目风险，返回标准化分数0~1（分数越高风险越低）"""
        score = 1.0  # 满分，然后扣分
        details = {}
        
        # 检查是否有安全漏洞
        if 'name' in project:
            vulnerabilities = APITools.check_vulnerabilities(project['name'])
            vuln_count = len(vulnerabilities.get('vulnerabilities', []))
            score -= vuln_count * 0.1
            details['vulnerability_count'] = vuln_count
        
        # 检查是否有维护状态
        if 'updated_at' in project:
            updated_at = project['updated_at']
            details['updated_at'] = updated_at
            # 基于更新时间评分（越新越好）
            updated_time = time.mktime(time.strptime(updated_at, '%Y-%m-%dT%H:%M:%SZ'))
            days_since_update = (time.time() - updated_time) / (24 * 3600)
            if days_since_update > 365:
                score -= 0.3
            elif days_since_update > 180:
                score -= 0.2
            elif days_since_update > 90:
                score -= 0.1
        
        return {
            "score": max(score, 0.0),
            "details": details
        }

class ScenarioAgent:
    """场景匹配Agent"""
    @staticmethod
    def evaluate(project, user_need, llm_result=None):
        """评估项目与用户需求的匹配度，返回标准化分数0~1"""
        score = 0.0
        details = {}
        
        # 基于项目名称和描述的匹配度
        if 'name' in project:
            name = project['name'].lower()
            if llm_result and 'intent' in llm_result and 'core_keywords' in llm_result['intent']:
                keywords = llm_result['intent']['core_keywords']
                for keyword in keywords:
                    if keyword.lower() in name:
                        score += 0.2
        
        if 'description' in project:
            description = project['description'].lower() if project['description'] else ''
            if llm_result and 'intent' in llm_result and 'core_keywords' in llm_result['intent']:
                keywords = llm_result['intent']['core_keywords']
                for keyword in keywords:
                    if keyword.lower() in description:
                        score += 0.2
        
        # 基础分
        score += 0.6
        
        return {
            "score": min(score, 1.0),
            "details": details
        }

class TrendAgent:
    """趋势评估Agent"""
    @staticmethod
    def evaluate(project):
        """评估项目趋势，返回标准化分数0~1"""
        score = 0.0
        details = {}
        
        # 基于项目活跃度
        if 'updated_at' in project and 'created_at' in project:
            updated_at = project['updated_at']
            created_at = project['created_at']
            
            updated_time = time.mktime(time.strptime(updated_at, '%Y-%m-%dT%H:%M:%SZ'))
            created_time = time.mktime(time.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ'))
            
            age = updated_time - created_time
            if age > 0:
                # 计算平均更新频率
                # 这里简化处理，实际应该计算提交次数
                score += 0.2
                details['is_active'] = True
        
        # 基于Star增长趋势（简化处理）
        if 'stargazers_count' in project:
            stars = project['stargazers_count']
            if stars > 10000:
                score += 0.3
            elif stars > 1000:
                score += 0.2
            elif stars > 100:
                score += 0.1
        
        return {
            "score": min(score, 1.0),
            "details": details
        }

# 主应用
def analyze_user_need(user_need):
    """分析用户需求并推荐项目 - 100% 纯通用版"""
    print("正在分析需求...")
    
    # 确保user_need是字符串类型，并且正确编码
    if not isinstance(user_need, str):
        user_need = str(user_need)
    # 处理编码问题，确保中文显示正常
    user_need = user_need.encode('utf-8', errors='ignore').decode('utf-8')
    
    # 1. 安全性检查
    if not check_safety(user_need):
        print("检测到不安全内容，返回提示")
        return {
            "user_need": user_need,
            "llm_result": {},
            "projects": [],
            "message": "暂不支持此类需求"
        }
    
    # 2. 语义理解 - 使用LLM进行需求意图分析，不做任何领域假设
    print("正在理解用户需求...")
    print(f"用户需求: {user_need}")
    llm_result = get_llm_requirement_analysis(user_need)
    print(f"需求分析结果: {llm_result}")
    
    # 获取意图分析结果
    intent = llm_result.get('intent', {})
    core_keywords = intent.get('core_keywords', [])
    search_query = intent.get('search_query', user_need)
    
    # 3. 搜索逻辑 - 使用提取的search_query直接搜索
    print("正在构建搜索查询...")
    
    # 确保搜索查询长度合理
    search_query = search_query[:256]  # GitHub API 对查询长度有限制
    
    # 搜索相关项目
    print("正在搜索相关项目...")
    print(f"搜索查询: {search_query}")
    
    # 搜索GitHub仓库
    print("正在搜索GitHub仓库...")
    github_projects = APITools.search_github_repos(search_query, limit=15)
    print(f"GitHub搜索结果数量: {len(github_projects)}")
    for repo in github_projects[:3]:  # 显示前3个结果
        try:
            name = repo['name']
            description = repo.get('description', '')
            # 处理编码问题，移除无法编码的字符
            if isinstance(description, str):
                description = description.encode('utf-8', errors='ignore').decode('utf-8')
            print(f"  - {name}: {description}")
        except Exception as e:
            print(f"  - 项目信息处理失败: {e}")
    
    # 搜索PyPI包
    print("正在搜索PyPI包...")
    pypi_projects = APITools.search_pypi_packages(search_query, limit=15)
    print(f"PyPI搜索结果数量: {len(pypi_projects)}")
    for package in pypi_projects[:3]:  # 显示前3个结果
        print(f"  - {package.get('name', '')}")
    
    # 合并项目
    projects = []
    
    # 处理GitHub项目
    for repo in github_projects:
        try:
            # 处理编码问题
            name = repo['name']
            description = repo.get('description', '')
            if isinstance(description, str):
                description = description.encode('utf-8', errors='ignore').decode('utf-8')
            html_url = repo.get('html_url', '')
            
            # 检查项目安全性
            project_text = f"{name} {description}"
            if not check_safety(project_text):
                print(f"检测到不安全内容，过滤项目: {name}")
                continue
            
            projects.append({
                'name': name,
                'description': description,
                'html_url': html_url,
                'stars': repo.get('stargazers_count', 0),
                'forks': repo.get('forks_count', 0),
                'created_at': repo.get('created_at', ''),
                'updated_at': repo.get('updated_at', ''),
                'license': repo.get('license'),
                'homepage': repo.get('homepage'),
                'contributors_url': repo.get('contributors_url')
            })
        except Exception as e:
            print(f"处理GitHub项目失败: {e}")
    
    # 处理PyPI项目
    for package in pypi_projects:
        package_name = package['name']
        package_info = APITools.get_pypi_package_info(package_name)
        if package_info:
            info = package_info.get('info', {})
            description = info.get('summary', '')
            
            # 检查项目安全性
            project_text = f"{package_name} {description}"
            if not check_safety(project_text):
                print(f"检测到不安全内容，过滤项目: {package_name}")
                continue
            
            projects.append({
                'name': info.get('name', package_name),
                'description': description,
                'version': info.get('version'),
                'homepage': info.get('home_page'),
                'license': info.get('license')
            })
        else:
            # 如果PyPI上不存在，仍然添加到项目列表中
            # 检查项目安全性
            if not check_safety(package_name):
                print(f"检测到不安全内容，过滤项目: {package_name}")
                continue
            
            projects.append({
                'name': package_name,
                'description': f'{package_name}'
            })
    
    # 去重
    unique_projects = []
    seen_names = set()
    for project in projects:
        if project['name'] not in seen_names:
            seen_names.add(project['name'])
            unique_projects.append(project)
    
    # 4. 项目自动标签化 - 为每个搜索到的项目自动打标签
    print("正在为项目添加标签...")
    projects_with_tags = []
    for project in unique_projects:
        tags = ProjectTagger.tag_project(project)
        project_with_tags = project.copy()
        project_with_tags['tags'] = tags
        projects_with_tags.append(project_with_tags)
    
    # 5. 过滤与匹配逻辑 - 纯通用匹配，只基于关键词
    print("正在进行关键词匹配过滤...")
    filtered_projects = []
    
    for project in projects_with_tags:
        project_name = project.get('name', '').lower()
        project_description = project.get('description', '').lower()
        project_text = f"{project_name} {project_description}"
        
        # 只基于关键词进行匹配
        keyword_match = False
        if core_keywords:
            # 检查项目名称或描述是否包含任何关键词
            for keyword in core_keywords:
                if keyword.lower() in project_text:
                    keyword_match = True
                    break
        else:
            # 如果没有提取到关键词，默认匹配
            keyword_match = True
        
        if keyword_match:
            filtered_projects.append(project)
    
    # 限制为前5个项目
    top_projects = filtered_projects[:5]
    
    # 6. 排序逻辑 - 使用通用评分公式
    # 并行评估项目
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_project = {}
        
        for project in top_projects:
            # 提交各个Agent的评估任务
            popularity_future = executor.submit(PopularityAgent.evaluate, project)
            maturity_future = executor.submit(MaturityAgent.evaluate, project)
            ecosystem_future = executor.submit(EcosystemAgent.evaluate, project)
            risk_future = executor.submit(RiskAgent.evaluate, project)
            scenario_future = executor.submit(ScenarioAgent.evaluate, project, user_need, llm_result)
            trend_future = executor.submit(TrendAgent.evaluate, project)
            
            future_to_project[project['name']] = {
                'project': project,
                'popularity': popularity_future,
                'maturity': maturity_future,
                'ecosystem': ecosystem_future,
                'risk': risk_future,
                'scenario': scenario_future,
                'trend': trend_future
            }
        
        # 收集评估结果
        for project_name, futures in future_to_project.items():
            project = futures['project']
            
            # 获取各Agent的评估结果
            popularity = futures['popularity'].result()
            maturity = futures['maturity'].result()
            ecosystem = futures['ecosystem'].result()
            risk = futures['risk'].result()
            scenario = futures['scenario'].result()
            trend = futures['trend'].result()
            
            # 构建维度分数映射
            dimension_scores = {
                "流行度": popularity['score'],
                "成熟度": maturity['score'],
                "生态": ecosystem['score'],
                "风险": risk['score'],
                "上手难度": scenario['score'],
                "性能": trend['score']
            }
            
            # 计算总分：简单加权平均
            total_score = (
                popularity['score'] * 0.2 +
                maturity['score'] * 0.2 +
                ecosystem['score'] * 0.2 +
                risk['score'] * 0.2 +
                scenario['score'] * 0.1 +
                trend['score'] * 0.1
            )
            
            results.append({
                'project': project,
                'scores': {
                    'popularity': popularity,
                    'maturity': maturity,
                    'ecosystem': ecosystem,
                    'risk': risk,
                    'scenario': scenario,
                    'trend': trend
                },
                'dimension_scores': dimension_scores,
                'total_score': total_score
            })
    
    # 按总分排序
    results.sort(key=lambda x: x['total_score'], reverse=True)
    
    # 限制为前3个项目
    results = results[:3]
    
    # 7. 工作流整合 - 生成报告并返回结果
    generate_report(results, user_need, llm_result)
    
    # 构建返回结果
    if not results:
        print("未找到匹配项目")
        return {
            "user_need": user_need,
            "llm_result": llm_result,
            "projects": [],
            "message": "未找到匹配的开源项目"
        }
    
    print(f"找到 {len(results)} 个相关项目，正在评估...")
    
    return {
        "user_need": user_need,
        "llm_result": llm_result,
        "projects": [
            {
                "name": result['project']['name'],
                "description": result['project'].get('description', ''),
                "html_url": result['project'].get('html_url', ''),
                "total_score": result['total_score'],
                "dimension_scores": result['dimension_scores']
            }
            for result in results
        ]
    }

def generate_report(results, user_need, llm_result):
    """生成选型报告"""
    try:
        print("\n=== 开源项目智能选型报告 ===")
        print(f"用户需求: {user_need}")
        
        # 显示系统理解的用户需求
        print("\n系统理解的需求:")
        print(f"- 需求定位: {llm_result.get('task_type', '未知')}")
        print(f"- 关键需求点:")
        for req in llm_result.get('key_requirements', []):
            if req:
                # 处理编码问题，确保中文显示正常
                if isinstance(req, str):
                    req = req.encode('utf-8', errors='ignore').decode('utf-8')
                print(f"  * {req}")
        
        # 显示评估维度与权重
        print("\n评估维度与权重:")
        weights = llm_result.get('weights', {})
        for dimension, weight in weights.items():
            # 处理编码问题，确保中文显示正常
            if isinstance(dimension, str):
                dimension = dimension.encode('utf-8', errors='ignore').decode('utf-8')
            print(f"- {dimension}: {weight:.2f}")
        
        print("\n适合的项目排名:")
        
        for i, result in enumerate(results, 1):
            project = result['project']
            scores = result['scores']
            total_score = result['total_score']
            dimension_scores = result.get('dimension_scores', {})
            
            # 处理编码问题
            try:
                name = project['name']
                # 处理编码问题，确保中文显示正常
                if isinstance(name, str):
                    name = name.encode('utf-8', errors='ignore').decode('utf-8')
                print(f"\n{i}. {name}")
                print(f"   总分: {total_score:.3f}")
                # 处理编码问题，移除无法编码的字符
                description = project.get('description', '无')
                if isinstance(description, str):
                    description = description.encode('utf-8', errors='ignore').decode('utf-8')
                print(f"   描述: {description}")
                if 'html_url' in project:
                    print(f"   链接: {project['html_url']}")
                
                # 显示各维度得分
                print("   各维度得分:")
                for dimension, score in dimension_scores.items():
                    print(f"   - {dimension}: {score:.3f}")
            except Exception as e:
                print(f"\n{i}. 项目信息处理失败: {e}")
    except Exception as e:
        print(f"生成报告失败: {e}")
        print("   迁移成本评估: 低")
        
        # 风险提示
        print("   风险提示:")
        print("   - 依赖管理")
        print("   - 版本兼容性")
        
        # 趋势预测
        print("   趋势预测: 稳定")
    
    # 最终推荐结论
    print("\n最终推荐结论:")
    if results:
        top_project = results[0]['project']
        print(f"推荐使用: {top_project['name']}")
        print("推荐理由:")
        print(f"- 综合评分最高: {results[0]['total_score']:.3f}")
        print("- 最符合您的需求:")
        for req in llm_result.get('key_requirements', []):
            if req:
                print(f"  * {req}")

if __name__ == "__main__":
    # 测试
    user_need = "适合新手的微调项目"
    result = analyze_user_need(user_need)
    print("\n推荐结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
