import pytest
from unittest.mock import Mock, patch
from agents.experts.popularity_agent import create_popularity_agent
from agents.experts.maturity_agent import create_maturity_agent
from agents.experts.ecosystem_agent import create_ecosystem_agent
from agents.experts.risk_agent import create_risk_agent
from agents.experts.scenario_agent import create_scenario_agent
from agents.experts.trend_agent import create_trend_agent

class TestAgents:
    def setup_method(self):
        """设置测试环境"""
        self.mock_model = Mock()
    
    def test_popularity_agent_creation(self):
        """测试流行度评估Agent创建"""
        agent = create_popularity_agent(self.mock_model)
        assert agent is not None
    
    def test_maturity_agent_creation(self):
        """测试成熟度评估Agent创建"""
        agent = create_maturity_agent(self.mock_model)
        assert agent is not None
    
    def test_ecosystem_agent_creation(self):
        """测试生态评估Agent创建"""
        agent = create_ecosystem_agent(self.mock_model)
        assert agent is not None
    
    def test_risk_agent_creation(self):
        """测试风险评估Agent创建"""
        agent = create_risk_agent(self.mock_model)
        assert agent is not None
    
    def test_scenario_agent_creation(self):
        """测试场景匹配Agent创建"""
        agent = create_scenario_agent(self.mock_model)
        assert agent is not None
    
    def test_trend_agent_creation(self):
        """测试趋势预测Agent创建"""
        agent = create_trend_agent(self.mock_model)
        assert agent is not None