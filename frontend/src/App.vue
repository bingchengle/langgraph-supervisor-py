<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import LogoYuFish from './components/LogoYuFish.vue'
import { 
  ElButton, ElInput, ElLoading, ElMessage, ElCard, ElTag, 
  ElProgress, ElDivider, ElSelect, ElOption, ElTooltip, 
  ElBadge, ElIcon, ElPopconfirm, ElScrollbar
} from 'element-plus'
import { Star, Download, Top, Edit, Check, Link, Document, Clock } from '@element-plus/icons-vue'

// 响应式数据
const userNeed = ref('')
const loading = ref(false)
const recommendationResult = ref(null)
let weightsBarChartInstance = null
let weightsBarResizeHandler = null
const showBackToTop = ref(false)
const favorites = ref([])
const history = ref([])
const userNeedEdit = ref('')
const showNeedEdit = ref(false)
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8004'

// 热门提问
const hotQuestions = [
  '给我推荐适合新手的Agent项目',
  'PDF问答用什么框架好？',
  '我应该选LangChain还是LlamaIndex？'
]

// 各评估维度的固定释义（面向使用者：说明「是什么、看什么」；得分一般为 0–1，越高越好）
const dimensionDefinitions = {
  流行度:
    '社区热度与采用广度：综合 Star、Fork、关注者、下载与检索热度等，越高表示越常被使用与讨论。',
  成熟度:
    '工程化与可依赖程度：综合版本号、发布节奏、维护年限与 issue 处理等，越高表示越适合长期依赖。',
  生态:
    '周边工具与集成丰富度：插件、扩展、上下游集成与第三方示例多少，越高表示扩展与对接越容易。',
  风险:
    '安全与合规风险（分数越高表示风险越低）：综合漏洞信息、许可证、依赖健康与更新及时性等。',
  上手难度:
    '学习与接入成本（分数越高表示越容易上手）：综合文档、示例、API 复杂度与社区答疑等。',
  性能:
    '运行效率与资源占用：在典型场景下的响应速度、吞吐与开销表现，越高表示越省资源或越快。',
  体积:
    '安装与依赖体量：安装包大小、依赖数量与冷启动成本等，越高表示越轻量（在可比场景下）。',
  文档友好度:
    '文档与教程质量：是否易查、示例是否够用、中英文与检索体验等，越高表示越省学习成本。',
  场景匹配:
    '与当前需求场景的贴合度：名称、描述与标签是否命中你的使用场景与关键词。',
  趋势:
    '近期活跃度与增长：提交频率、发版节奏与社区讨论趋势，越高表示越在积极演进。',
}

/** 维度标准含义（悬停工具提示） */
function dimensionDefinitionText(dim) {
  return dimensionDefinitions[dim] || `「${dim}」用于从该侧面比较候选项目；分数一般在 0–1 之间，越高越好（若另有说明以工具提示为准）。`
}

/** 项目卡片内短释义（完整释义见悬停） */
function dimensionDefinitionShort(dim) {
  const full = dimensionDefinitionText(dim)
  if (full.length <= 64) {
    return full
  }
  return `${full.slice(0, 62).replace(/[，、；：]$/, '')}…`
}

// 推荐项目
const recommendProjects = async () => {
  if (!userNeed.value.trim()) {
    ElMessage.warning('请输入您的需求')
    return
  }
  
  loading.value = true
  try {
    const response = await axios.post(`${apiBaseUrl}/api/recommend`, {
      user_need: userNeed.value
    })
    
    // 修正评分逻辑，重型框架上手难度自动下调
    const result = response.data
    result.projects.forEach(project => {
      // 识别重型框架
      const heavyFrameworks = ['langchain', 'llamaindex', 'autogen']
      const projectName = project.name.toLowerCase()
      
      if (heavyFrameworks.some(framework => projectName.includes(framework))) {
        // 重型框架上手难度自动下调
        if (project.dimension_scores['上手难度'] > 0.5) {
          project.dimension_scores['上手难度'] *= 0.7
        }
      }
    })
    
    recommendationResult.value = result
    userNeedEdit.value = userNeed.value
    
    // 保存到历史记录
    history.value.unshift({
      id: Date.now(),
      need: userNeed.value,
      timestamp: new Date().toLocaleString()
    })
    if (history.value.length > 10) {
      history.value = history.value.slice(0, 10)
    }
    
    // 渲染图表
    setTimeout(() => {
      renderCharts()
    }, 100)
  } catch (error) {
    console.error('推荐失败:', error)
    ElMessage.error('推荐失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 渲染图表（当前仅：评估维度与权重 — 单张柱状图）
const renderCharts = () => {
  if (!recommendationResult.value?.llm_result?.weights) {
    return
  }
  renderWeightsBarChart()
}

const renderWeightsBarChart = () => {
  const el = document.getElementById('weights-bar-chart')
  if (!el || !recommendationResult.value?.llm_result?.weights) {
    return
  }
  if (weightsBarChartInstance) {
    weightsBarChartInstance.dispose()
    weightsBarChartInstance = null
  }
  const weights = recommendationResult.value.llm_result.weights
  const dimensions = Object.keys(weights)
  const data = dimensions.map((d) => Number((weights[d] * 100).toFixed(2)))

  weightsBarChartInstance = echarts.init(el)
  weightsBarChartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params[0]
        return `${p.name}<br/>权重：${p.value}%`
      },
    },
    grid: { left: '3%', right: '4%', bottom: dimensions.length > 8 ? '18%' : '10%', top: 24, containLabel: true },
    xAxis: {
      type: 'category',
      data: dimensions,
      axisLabel: {
        rotate: dimensions.length > 6 ? 28 : 0,
        interval: 0,
        color: '#606266',
      },
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: { formatter: '{value}%' },
      splitLine: { lineStyle: { type: 'dashed', opacity: 0.6 } },
    },
    series: [
      {
        name: '权重',
        type: 'bar',
        barMaxWidth: 48,
        data,
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#7c8ef5' },
            { offset: 1, color: '#5b4b9a' },
          ]),
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}%',
          color: '#303133',
          fontSize: 12,
        },
      },
    ],
  })

  if (weightsBarResizeHandler) {
    window.removeEventListener('resize', weightsBarResizeHandler)
  }
  weightsBarResizeHandler = () => weightsBarChartInstance?.resize()
  window.addEventListener('resize', weightsBarResizeHandler)
}

// 解析项目核心数据（展示层不再包含 Star/下载/版本等易缺失字段）
const parseProjectData = (project) => {
  // 解析总分
  const parseTotalScore = (score) => {
    if (score >= 0.8) {
      return { display: score.toFixed(3), explanation: '综合表现优秀，强烈推荐' }
    } else if (score >= 0.6) {
      return { display: score.toFixed(3), explanation: '综合表现良好，推荐使用' }
    } else if (score >= 0.4) {
      return { display: score.toFixed(3), explanation: '综合表现一般，可作为备选' }
    } else {
      return { display: score.toFixed(3), explanation: '综合表现较差，不推荐使用' }
    }
  }
  
  // 解析维度评分
  const parseDimensionScore = (dimension, score) => {
    let explanation = ''
    switch (dimension) {
      case '上手难度':
        if (score >= 0.8) explanation = '上手难度低，适合纯新手'
        else if (score >= 0.5) explanation = '中等难度，适合有基础的开发者'
        else explanation = '上手难度高，适合有经验的开发者'
        break
      case '成熟度':
        if (score >= 0.8) explanation = '成熟度高，稳定性好，适合生产环境'
        else if (score >= 0.5) explanation = '成熟度中等，功能基本完善'
        else explanation = '成熟度低，可能存在稳定性问题'
        break
      case '生态':
        if (score >= 0.8) explanation = '生态完善，有大量第三方集成'
        else if (score >= 0.5) explanation = '生态一般，基本满足需求'
        else explanation = '生态较小，可能需要自行开发功能'
        break
      case '风险':
        if (score >= 0.8) explanation = '风险低，MIT许可证，维护活跃'
        else if (score >= 0.5) explanation = '风险中等，需要关注依赖和漏洞'
        else explanation = '风险较高，可能存在安全问题'
        break
      case '性能':
        if (score >= 0.8) explanation = '性能优秀，处理速度快'
        else if (score >= 0.5) explanation = '性能一般，满足基本需求'
        else explanation = '性能较差，不适合大规模应用'
        break
      case '体积':
        if (score >= 0.8) explanation = '体积小巧，依赖少'
        else if (score >= 0.5) explanation = '体积适中，依赖合理'
        else explanation = '体积较大，依赖较多'
        break
      case '文档友好度':
        if (score >= 0.8) explanation = '文档完善，示例丰富'
        else if (score >= 0.5) explanation = '文档一般，基本够用'
        else explanation = '文档缺乏，学习成本高'
        break
      case '流行度':
        if (score >= 0.8) explanation = '非常流行，社区活跃'
        else if (score >= 0.5) explanation = '有一定流行度，社区支持'
        else explanation = '相对小众，社区活跃度低'
        break
      default:
        explanation = '暂无解析'
    }
    return { display: score.toFixed(3), explanation }
  }
  
  return {
    totalScore: parseTotalScore(project.total_score),
    dimensionScores: Object.fromEntries(
      Object.entries(project.dimension_scores).map(([dim, score]) => [dim, parseDimensionScore(dim, score)])
    )
  }
}

// 按用户需求优先级排序维度
const sortedDimensions = (project) => {
  if (!recommendationResult.value || !recommendationResult.value.llm_result.weights) {
    return project.dimension_scores
  }
  
  const weights = recommendationResult.value.llm_result.weights
  
  // 按权重降序排序
  return Object.fromEntries(
    Object.entries(project.dimension_scores)
      .sort(([dimA], [dimB]) => {
        const weightA = weights[dimA] || 0
        const weightB = weights[dimB] || 0
        return weightB - weightA
      })
  )
}

// 填充热门提问
const fillHotQuestion = (question) => {
  userNeed.value = question
}

// 收藏项目
const toggleFavorite = (project) => {
  const index = favorites.value.findIndex(p => p.name === project.name)
  if (index > -1) {
    favorites.value.splice(index, 1)
    ElMessage.success('已取消收藏')
  } else {
    favorites.value.push(project)
    ElMessage.success('已添加到收藏')
  }
}

// 检查项目是否已收藏
const isFavorite = (project) => {
  return favorites.value.some(p => p.name === project.name)
}

// 导出报告
const exportReport = (format) => {
  if (!recommendationResult.value) {
    ElMessage.warning('请先获取推荐结果')
    return
  }
  
  ElMessage.success(`正在导出${format.toUpperCase()}报告...`)
  // 这里可以实现实际的导出逻辑
}

// 回到顶部
const backToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 监听滚动事件
window.addEventListener('scroll', () => {
  showBackToTop.value = window.scrollY > 300
})

// 修正用户需求
const confirmNeedEdit = () => {
  userNeed.value = userNeedEdit.value
  showNeedEdit.value = false
  ElMessage.success('需求已修正')
}

// 从历史记录加载
const loadFromHistory = (item) => {
  userNeed.value = item.need
  recommendProjects()
}

// 生成项目分析（差异化）
const generateProjectAnalysis = (project, index) => {
  if (project.project_analysis) {
    return [project.project_analysis]
  }
  const analysis = []
  
  // 基于项目名称和得分生成差异化分析
  const projectName = project.name.toLowerCase()
  const projectScore = project.total_score
  
  // 总分分析
  if (projectScore >= 0.9) {
    analysis.push('该项目综合表现卓越，在多个维度都有出色表现，是同类项目中的佼佼者。')
  } else if (projectScore >= 0.8) {
    analysis.push('该项目综合表现优秀，在核心功能上表现突出，值得推荐使用。')
  } else if (projectScore >= 0.7) {
    analysis.push('该项目综合表现良好，满足基本需求，适合特定场景使用。')
  } else {
    analysis.push('该项目综合表现一般，可能在某些方面存在不足，需要根据具体需求评估。')
  }
  
  // 上手难度分析
  if (project.dimension_scores['上手难度'] > 0.8) {
    if (projectName.includes('simple')) {
      analysis.push('该项目设计简洁，API直观，非常适合新手入门学习。')
    } else if (projectName.includes('agent')) {
      analysis.push('该项目提供了丰富的示例和文档，新手可以快速上手。')
    } else if (projectName.includes('langchain')) {
      analysis.push('该项目虽然功能强大，但提供了友好的API和详细的文档，新手也能较快掌握。')
    } else if (projectName.includes('llama')) {
      analysis.push('该项目提供了直观的接口和丰富的示例，降低了学习门槛。')
    } else {
      analysis.push('该项目上手难度低，适合初学者快速掌握。')
    }
  } else if (project.dimension_scores['上手难度'] > 0.5) {
    if (projectName.includes('langchain')) {
      analysis.push('该项目功能强大但学习曲线较陡，建议有一定Python基础后再尝试。')
    } else if (projectName.includes('llama')) {
      analysis.push('该项目文档完善，但需要了解向量数据库等概念，适合有一定经验的开发者。')
    } else if (projectName.includes('agent')) {
      analysis.push('该项目需要了解智能体的基本概念，建议有一定AI基础后再使用。')
    } else {
      analysis.push('该项目有一定的学习曲线，但通过文档和示例可以较快掌握。')
    }
  } else {
    if (projectName.includes('langchain')) {
      analysis.push('该项目学习曲线较陡，需要扎实的Python和AI基础，建议有经验的开发者使用。')
    } else if (projectName.includes('llama')) {
      analysis.push('该项目需要深入了解向量数据库、嵌入模型等概念，适合专业开发者。')
    } else {
      analysis.push('该项目上手难度较高，建议有相关领域经验后再尝试。')
    }
  }
  
  // 成熟度分析
  if (project.dimension_scores['成熟度'] > 0.8) {
    if (projectName.includes('langchain')) {
      analysis.push('该项目是行业标准工具，版本稳定，功能完善，适合生产环境使用。')
    } else if (projectName.includes('llama')) {
      analysis.push('该项目经过多次迭代，稳定性高，适合企业级应用。')
    } else {
      analysis.push('该项目成熟度高，稳定性好，适合生产环境使用。')
    }
  } else if (project.dimension_scores['成熟度'] > 0.5) {
    if (projectName.includes('agent')) {
      analysis.push('该项目处于快速发展阶段，功能不断完善，适合测试和小规模使用。')
    } else {
      analysis.push('该项目处于发展阶段，功能基本完善，适合测试和小规模使用。')
    }
  } else {
    analysis.push('该项目相对较新，可能存在稳定性问题，建议谨慎使用。')
  }
  
  // 生态分析
  if (project.dimension_scores['生态'] > 0.8) {
    if (projectName.includes('langchain')) {
      analysis.push('该项目生态丰富，拥有大量集成和插件，可扩展性强，支持多种模型和工具。')
    } else if (projectName.includes('llama')) {
      analysis.push('该项目生态完善，有活跃的社区支持和丰富的资源，适合构建复杂应用。')
    } else if (projectName.includes('agent')) {
      analysis.push('该项目生态正在快速发展，有众多社区贡献的插件和集成。')
    } else {
      analysis.push('该项目生态完善，有活跃的社区支持和丰富的资源。')
    }
  } else if (project.dimension_scores['生态'] > 0.5) {
    analysis.push('该项目生态正在发展中，基本满足日常使用需求。')
  } else {
    analysis.push('该项目生态相对较小，可能需要自行开发一些功能。')
  }
  
  // 性能分析
  if (project.dimension_scores['性能'] > 0.8) {
    analysis.push('该项目性能优秀，处理速度快，适合大规模应用。')
  } else if (project.dimension_scores['性能'] > 0.5) {
    analysis.push('该项目性能一般，满足基本需求，适合中小规模应用。')
  } else {
    analysis.push('该项目性能较差，不适合大规模应用，建议在小型项目中使用。')
  }
  
  // 文档友好度分析
  if (project.dimension_scores['文档友好度'] > 0.8) {
    analysis.push('该项目文档完善，示例丰富，学习资源充足，大大降低了使用成本。')
  } else if (project.dimension_scores['文档友好度'] > 0.5) {
    analysis.push('该项目文档基本完善，能够满足日常使用需求。')
  } else {
    analysis.push('该项目文档缺乏，学习成本高，建议参考社区资源和示例。')
  }
  
  return analysis
}

// 生成二创建议（差异化）
const generateProjectSuggestions = (project, index) => {
  if (Array.isArray(project.innovation_suggestions) && project.innovation_suggestions.length > 0) {
    return project.innovation_suggestions
  }
  const suggestions = []
  
  // 基于项目名称和得分生成差异化建议
  const projectName = project.name.toLowerCase()
  
  // 根据项目类型生成特定建议
  if (projectName.includes('langchain')) {
    suggestions.push('可以开发针对特定行业的解决方案，如金融、医疗、法律等领域的智能应用。')
    suggestions.push('可以构建基于LangChain的定制化智能体，集成特定领域的知识和工具。')
    suggestions.push('可以开发LangChain与其他框架的集成插件，扩展其功能。')
  } else if (projectName.includes('llama')) {
    suggestions.push('可以开发基于LlamaIndex的知识库系统，为企业提供智能问答服务。')
    suggestions.push('可以构建多模态应用，结合文本、图像等多种数据类型。')
    suggestions.push('可以优化向量检索算法，提高检索效率和准确性。')
  } else if (projectName.includes('agent')) {
    suggestions.push('可以开发特定场景的智能体应用，如客服、教育、医疗等领域。')
    suggestions.push('可以构建多智能体协作系统，解决复杂任务。')
    suggestions.push('可以开发智能体的评估框架，提高智能体的性能和可靠性。')
  } else if (projectName.includes('simple')) {
    suggestions.push('可以开发适合新手的教程和示例，帮助更多人快速上手。')
    suggestions.push('可以构建简单易用的工具和插件，降低使用门槛。')
    suggestions.push('可以开发可视化界面，让非技术用户也能轻松使用。')
  }
  
  // 根据维度得分生成针对性建议
  if (project.dimension_scores['上手难度'] > 0.8) {
    suggestions.push('可以开发适合新手的教程和示例，帮助更多人快速上手。')
  } else if (project.dimension_scores['上手难度'] < 0.5) {
    suggestions.push('可以开发简化版API或封装库，降低学习门槛。')
  }
  
  if (project.dimension_scores['生态'] > 0.5) {
    suggestions.push('可以开发针对特定领域的插件或扩展，丰富项目的功能。')
  } else {
    suggestions.push('可以构建生态系统，吸引更多开发者贡献插件和集成。')
  }
  
  if (project.dimension_scores['性能'] < 0.5) {
    suggestions.push('可以优化项目的性能，提高运行效率，特别是在处理大规模数据时。')
    suggestions.push('可以开发性能测试工具，帮助识别和解决性能瓶颈。')
  }
  
  if (project.dimension_scores['文档友好度'] < 0.5) {
    suggestions.push('可以完善项目文档，添加更多示例和使用指南，提高用户体验。')
    suggestions.push('可以开发交互式教程，帮助用户快速掌握核心功能。')
  }
  
  if (project.dimension_scores['成熟度'] < 0.5) {
    suggestions.push('可以参与项目的维护和发展，推动项目的成熟和稳定。')
  }
  
  // 通用建议
  suggestions.push('可以结合其他开源项目，开发更复杂的应用场景。')
  suggestions.push('可以贡献代码，参与项目的维护和发展，推动项目进步。')
  suggestions.push('可以分享使用经验和最佳实践，帮助社区成长。')
  
  return suggestions
}

// 健康检查
onMounted(async () => {
  try {
    await axios.get(`${apiBaseUrl}/api/health`)
    console.log('API服务正常')
  } catch (error) {
    console.error('API服务异常:', error)
    ElMessage.warning(`API服务可能未启动，请确认后端地址: ${apiBaseUrl}`)
  }
})
</script>

<template>
  <div class="app">
    <header class="header">
      <div class="header-backdrop" aria-hidden="true"></div>
      <div class="header-content">
        <div class="brand-row">
          <LogoYuFish class="brand-logo-mark" />
        </div>
        <h1 class="hero-title">开源项目智能选型助手</h1>
        <p class="hero-subtitle">基于 LLM 的动态加权推荐</p>
      </div>
    </header>
    
    <main class="main">
      <section class="input-section">
        <el-card shadow="hover" class="input-card">
          <template #header>
            <div class="card-header">
              <span class="panel-title">输入您的需求</span>
            </div>
          </template>
          <div class="input-container">
            <el-input
              v-model="userNeed"
              type="textarea"
              :rows="3"
              placeholder="给我推荐适合新手的Agent项目\nPDF问答用什么框架好？\n我应该选LangChain还是LlamaIndex？"
              class="input-textarea"
            ></el-input>
            
            <!-- 热门提问快捷标签 -->
            <div class="hot-questions">
              <el-tag 
                v-for="(question, index) in hotQuestions" 
                :key="index"
                class="hot-tag"
                @click="fillHotQuestion(question)"
              >
                {{ question }}
              </el-tag>
            </div>
            
            <el-button 
              type="primary" 
              @click="recommendProjects" 
              :loading="loading"
              class="recommend-button"
            >
              推荐项目
            </el-button>
          </div>
        </el-card>
      </section>
      
      <section v-if="recommendationResult" class="result-section">
        <el-card shadow="hover" class="result-card">
          <template #header>
            <div class="card-header">
              <span class="panel-title">推荐结果</span>
              <div class="header-actions">
                <el-button size="small" @click="exportReport('pdf')" class="action-button">
                  <Download /> 导出PDF
                </el-button>
                <el-button size="small" @click="exportReport('markdown')" class="action-button">
                  <Download /> 导出Markdown
                </el-button>
              </div>
            </div>
          </template>
          
          <!-- 需求分析 -->
          <div class="need-analysis">
            <h3 class="section-title">需求分析</h3>
            
            <!-- 需求校验 -->
            <div class="need-validation">
              <div class="need-header">
                <span><strong>用户需求:</strong> {{ recommendationResult.user_need }}</span>
                <el-button 
                  size="small" 
                  @click="showNeedEdit = true"
                  class="edit-button"
                >
                  <Edit /> 修正
                </el-button>
              </div>
              
              <div v-if="showNeedEdit" class="need-edit">
                <el-input
                  v-model="userNeedEdit"
                  type="textarea"
                  :rows="2"
                  class="edit-textarea"
                ></el-input>
                <div class="edit-actions">
                  <el-button size="small" @click="confirmNeedEdit">
                    <Check /> 确认
                  </el-button>
                  <el-button size="small" @click="showNeedEdit = false">取消</el-button>
                </div>
              </div>
            </div>
            
            <p class="task-type-line">{{ recommendationResult.llm_result.task_type }}</p>
            <ul class="requirement-list">
              <template v-for="(req, index) in recommendationResult.llm_result.key_requirements" :key="index">
                <li v-if="req">{{ req }}</li>
              </template>
            </ul>
            
            <div class="weights-section">
              <h4 class="content-heading">评估维度与权重</h4>
              <div id="weights-bar-chart" class="chart chart-weights"></div>
            </div>
          </div>
          
          <el-divider></el-divider>
          
          <!-- 项目详情 -->
          <div class="project-details">
            <h3 class="section-title">项目详情</h3>
            <div 
              v-for="(project, index) in recommendationResult.projects" 
              :key="index" 
              class="project-card"
              :class="{ 'recommended': index === 0 }"
            >
              <el-card 
                shadow="hover"
                :class="{ 'recommended-card': index === 0 }"
              >
                <template #header>
                  <div class="project-header">
                    <div class="project-title">
                      <span class="project-name">{{ index + 1 }}. {{ project.name }}</span>
                      <el-tag 
                        :type="index === 0 ? 'success' : index === 1 ? 'primary' : 'info'"
                        class="recommend-tag"
                      >
                        {{ index === 0 ? '推荐' : index === 1 ? '次推荐' : '备选' }}
                      </el-tag>
                    </div>
                    <el-button 
                      :icon="'Star'"
                      :type="isFavorite(project) ? 'danger' : 'default'"
                      circle
                      @click="toggleFavorite(project)"
                      class="favorite-button"
                    />
                  </div>
                </template>
                <div class="project-info">
                  <!-- 项目核心信息 -->
                  <div class="project-core-info">
                    <p><strong>描述:</strong> {{ project.description }}</p>
                    
                    <!-- 项目链接 -->
                    <div class="project-links">
                      <p v-if="project.html_url">
                        <el-tooltip content="点击访问GitHub仓库" placement="top">
                          <a :href="project.html_url" target="_blank" class="project-link">
                            <el-icon><Link /></el-icon> GitHub仓库
                          </a>
                        </el-tooltip>
                      </p>
                      <p v-if="project.pypi_url">
                        <el-tooltip content="点击访问PyPI页面" placement="top">
                          <a :href="project.pypi_url" target="_blank" class="project-link">
                            <el-icon><Download /></el-icon> PyPI页面
                          </a>
                        </el-tooltip>
                      </p>
                      <p v-if="project.doc_url">
                        <el-tooltip content="点击访问官方文档" placement="top">
                          <a :href="project.doc_url" target="_blank" class="project-link">
                            <el-icon><Document /></el-icon> 官方文档
                          </a>
                        </el-tooltip>
                      </p>
                    </div>
                    
                    <!-- 核心数据 -->
                    <div class="core-data">
                      <el-tooltip :content="parseProjectData(project).totalScore.explanation" placement="top">
                        <p><strong>总分:</strong> {{ parseProjectData(project).totalScore.display }}</p>
                      </el-tooltip>
                      <p v-if="project.forks"><strong>Fork数:</strong> {{ project.forks }}</p>
                      <p v-if="project.last_update"><strong>最后更新:</strong> {{ project.last_update }}</p>
                      <p v-if="project.monthly_downloads"><strong>月下载量:</strong> {{ project.monthly_downloads }}</p>
                    </div>
                  </div>
                  
                  <!-- 各维度得分 -->
                  <div class="dimension-scores">
                    <h4 class="content-heading">各维度得分</h4>
                    <p class="dimension-scores-lead">
                      下表列出各评估维度；左侧为维度名称与<strong>标准含义</strong>，右侧条形图为该项目在该维度上的得分（0–1，一般越高越好）。可悬停维度名查看完整说明，悬停「得分含义」查看本条分数的解读。
                    </p>
                    <div 
                      v-for="(score, dimension) in sortedDimensions(project)" 
                      :key="dimension" 
                      class="score-item"
                    >
                      <div class="dimension-col">
                        <div class="dimension-label-row">
                          <el-tooltip
                            :content="dimensionDefinitionText(dimension)"
                            placement="top"
                            :show-after="300"
                          >
                            <span class="dimension">{{ dimension }}</span>
                          </el-tooltip>
                          <el-tooltip
                            :content="parseProjectData(project).dimensionScores[dimension].explanation"
                            placement="top"
                          >
                            <span class="score-hint">得分含义</span>
                          </el-tooltip>
                        </div>
                        <p class="dimension-hint">{{ dimensionDefinitionShort(dimension) }}</p>
                      </div>
                      <el-progress 
                        :percentage="score * 100" 
                        :format="() => parseProjectData(project).dimensionScores[dimension].display"
                        :stroke-width="10"
                      />
                    </div>
                  </div>
                  
                  <!-- 项目分析 -->
                  <div class="project-analysis">
                    <h4 class="content-heading">项目分析</h4>
                    <ul class="analysis-list">
                      <li v-for="(item, idx) in generateProjectAnalysis(project, index)" :key="idx">
                        {{ item }}
                      </li>
                    </ul>
                  </div>
                  
                  <!-- 二创方向和建议 -->
                  <div class="project-suggestions">
                    <h4 class="content-heading">二创方向和建议</h4>
                    <ul class="suggestions-list">
                      <li v-for="(item, idx) in generateProjectSuggestions(project, index)" :key="idx">
                        {{ item }}
                      </li>
                    </ul>
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </el-card>
      </section>
      
      <!-- 历史记录 -->
      <section v-if="history.length > 0" class="history-section">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="panel-title">历史记录</span>
              <el-icon class="panel-title-icon"><Clock /></el-icon>
            </div>
          </template>
          <el-scrollbar max-height="200px">
            <div class="history-list">
              <div 
                v-for="item in history" 
                :key="item.id"
                class="history-item"
                @click="loadFromHistory(item)"
              >
                <div class="history-need">{{ item.need }}</div>
                <div class="history-time">{{ item.timestamp }}</div>
              </div>
            </div>
          </el-scrollbar>
        </el-card>
      </section>
    </main>
    
    <!-- 回到顶部按钮 -->
    <el-button 
      v-if="showBackToTop" 
      type="primary" 
      circle 
      class="back-to-top"
      @click="backToTop"
    >
      <Top />
    </el-button>
    
    <footer class="footer">
      <div class="footer-content">
        <div class="footer-section">
          <h4>项目说明</h4>
          <p>开源项目智能选型助手基于LLM驱动的动态加权推荐系统，帮助开发者快速找到适合的开源项目。</p>
        </div>
        <div class="footer-section">
          <h4>相关链接</h4>
          <a href="https://github.com" target="_blank">GitHub</a>
          <a href="https://pypi.org" target="_blank">PyPI</a>
          <a href="https://npmjs.com" target="_blank">NPM</a>
        </div>
        <div class="footer-section">
          <h4>版权信息</h4>
          <p>© 2026 开源项目智能选型助手</p>
          <p>保留所有权利</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app {
  --font-ui: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  --font-heading: 'Noto Serif SC', 'Noto Sans SC', 'PingFang SC', serif;
  --font-hero: 'ZCOOL XiaoWei', 'Noto Serif SC', serif;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #64748b;
  --text-faint: #94a3b8;
  --surface-page: #eef2f7;
  --surface-card: #ffffff;
  --surface-muted: #f1f5f9;
  --surface-accent: #eff6ff;
  --border-subtle: #e2e8f0;
  --border-strong: #cbd5e1;
  --accent: #3b6fd8;
  --accent-soft: rgba(59, 111, 216, 0.12);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
  --shadow-md: 0 4px 20px rgba(15, 23, 42, 0.07);
  --content-max: 1120px;
  --prose-width: 65ch;

  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--surface-page);
  font-family: var(--font-ui);
  font-size: 15px;
  line-height: 1.65;
  font-weight: 400;
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
}

/* Element Plus 卡片：统一圆角与标题区层次 */
:deep(.el-card) {
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-sm);
}

:deep(.el-card__header) {
  padding: 1rem 1.35rem;
  border-bottom: 1px solid var(--border-subtle);
  background: linear-gradient(180deg, #fafbfc 0%, #f8fafc 100%);
}

:deep(.el-card__body) {
  padding: 1.35rem 1.5rem 1.5rem;
}

:deep(.el-divider) {
  margin: 1.75rem 0;
}

.header {
  position: relative;
  overflow: hidden;
  color: #f1f5f9;
  padding: 2.75rem clamp(1rem, 4vw, 2rem) 2.75rem;
  text-align: center;
  box-shadow: var(--shadow-md);
}

.header-backdrop {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 120% 80% at 50% -20%, rgba(124, 142, 245, 0.35), transparent 55%),
    linear-gradient(165deg, #0f172a 0%, #1e293b 42%, #312e81 100%);
  pointer-events: none;
}

.header-backdrop::after {
  content: '';
  position: absolute;
  inset: 0;
  opacity: 0.07;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}

.header-content {
  position: relative;
  z-index: 1;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 0 clamp(0.75rem, 3vw, 1.5rem);
}

.brand-row {
  display: flex;
  justify-content: center;
  margin-bottom: 0.75rem;
}

.brand-logo-mark {
  display: flex;
  justify-content: center;
}

.hero-title {
  /* 覆盖全局 style.css 中 h1 的默认外边距与大字号层级 */
  margin: 0 auto;
  max-width: 22em;
  font-family: var(--font-hero);
  font-size: clamp(1.6rem, 4vw, 2.25rem);
  font-weight: 600;
  line-height: 1.38;
  letter-spacing: 0.1em;
  text-wrap: balance;
  background: linear-gradient(180deg, #ffffff 0%, #e2e8f0 55%, #94a3b8 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 2px 20px rgba(15, 23, 42, 0.35));
}

.hero-subtitle {
  margin: 1.1rem 0 0;
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 500;
  letter-spacing: 0.22em;
  text-transform: none;
  color: rgba(226, 232, 240, 0.82);
}

.main {
  flex: 1;
  padding: clamp(1.25rem, 4vw, 2.25rem) clamp(1rem, 4vw, 2rem);
  max-width: calc(var(--content-max) + 4rem);
  margin: 0 auto;
  width: 100%;
}

/* 输入区样式 */
.input-section {
  margin-bottom: 2rem;
}

.input-card {
  transition: all 0.3s ease;
}

.input-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.15);
}

.input-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.input-textarea {
  resize: vertical;
  font-size: 15px;
  line-height: 1.6;
}

:deep(.input-textarea textarea) {
  font-family: var(--font-ui);
  line-height: 1.65;
}

.hot-questions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.hot-tag {
  cursor: pointer;
  transition: all 0.3s ease;
}

.hot-tag:hover {
  transform: scale(1.05);
}

.recommend-button {
  align-self: flex-start;
  padding: 0.75rem 2rem;
  font-size: 16px;
  background: linear-gradient(135deg, #409EFF 0%, #667eea 100%);
  border: none;
  transition: all 0.3s ease;
}

.recommend-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px 0 rgba(64, 158, 255, 0.4);
}

/* 结果区样式 */
.result-section {
  margin-top: 2rem;
}

.result-card {
  transition: all 0.3s ease;
}

.result-card:hover {
  box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.panel-title {
  font-family: var(--font-heading);
  font-size: 1.0625rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--text-primary);
}

.panel-title-icon {
  font-size: 1.125rem;
  color: var(--text-muted);
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.action-button {
  transition: all 0.3s ease;
}

.action-button:hover {
  transform: translateY(-1px);
}

.need-analysis {
  margin-bottom: 2rem;
}

.section-title {
  font-family: var(--font-heading);
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1.35;
  margin: 0 0 1.25rem;
  padding-bottom: 0.65rem;
  color: var(--text-primary);
  border-bottom: 2px solid var(--accent-soft);
  box-shadow: 0 1px 0 0 rgba(59, 111, 216, 0.08);
}

.content-heading {
  font-family: var(--font-heading);
  font-size: 1.0625rem;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: 0.03em;
  margin: 1.5rem 0 0.75rem;
  color: var(--text-primary);
}

.content-heading:first-child {
  margin-top: 0;
}

.weights-section > .content-heading {
  margin-top: 0;
}

.need-validation {
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  padding: 1.1rem 1.2rem;
  border-radius: var(--radius-md);
  margin-bottom: 1.25rem;
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.need-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  text-align: left;
}

.need-header > span {
  flex: 1;
  min-width: 0;
  font-size: 0.9375rem;
  line-height: 1.65;
  color: var(--text-secondary);
  word-break: break-word;
}

.need-header strong {
  font-weight: 600;
  color: var(--text-primary);
}

.edit-button {
  transition: all 0.3s ease;
}

.edit-button:hover {
  transform: scale(1.05);
}

.need-edit {
  margin-top: 1rem;
}

.edit-textarea {
  margin-bottom: 0.5rem;
}

.edit-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.task-type-line {
  margin: 1rem 0 0.5rem;
  font-family: var(--font-heading);
  font-size: 1.0625rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.55;
  max-width: var(--prose-width);
}

.requirement-list {
  padding-left: 1.25rem;
  margin: 0.35rem 0 1.25rem;
  max-width: var(--prose-width);
  color: var(--text-secondary);
  font-size: 0.9375rem;
}

.weights-section {
  margin-top: 1.75rem;
  padding-top: 0.25rem;
}

.chart {
  width: 100%;
  height: 400px;
  margin-top: 1rem;
}

.chart-weights {
  height: 380px;
  min-height: 280px;
}

/* 正文与分点统一左对齐 */
.need-analysis,
.project-details,
.project-info {
  text-align: left;
}

.requirement-list,
.analysis-list,
.suggestions-list {
  text-align: left;
  list-style-position: outside;
  padding-left: 1.35rem;
  margin-left: 0;
}

.analysis-list li,
.suggestions-list li,
.requirement-list li {
  text-align: left;
  line-height: 1.65;
}

.project-analysis,
.project-suggestions {
  text-align: left;
}

.project-analysis .content-heading,
.project-suggestions .content-heading,
.dimension-scores .content-heading {
  text-align: left;
}

.project-core-info p,
.core-data p {
  text-align: left;
}

.project-details {
  margin-top: 0.5rem;
}

.project-card {
  margin-bottom: 1.75rem;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.project-card:hover {
  transform: translateY(-2px);
}

.recommended-card {
  border: 2px solid rgba(34, 197, 94, 0.55) !important;
  box-shadow: 0 4px 24px rgba(34, 197, 94, 0.12);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.75rem;
}

.project-title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 0.65rem;
  text-align: left;
}

.project-name {
  font-family: var(--font-heading);
  font-size: 1.125rem;
  font-weight: 700;
  line-height: 1.4;
  letter-spacing: 0.02em;
  color: var(--text-primary);
}

.recommend-tag {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.favorite-button {
  transition: all 0.3s ease;
}

.favorite-button:hover {
  transform: scale(1.1);
}

.project-info {
  margin-top: 1.1rem;
}

.project-core-info {
  margin-bottom: 1.5rem;
}

.project-core-info > p {
  font-size: 0.9375rem;
  line-height: 1.75;
  color: var(--text-secondary);
  max-width: var(--prose-width);
}

.project-core-info strong {
  font-weight: 600;
  color: var(--text-primary);
}

.project-links {
  margin: 0.75rem 0;
}

.project-links p {
  margin: 0.35rem 0;
  font-size: 0.875rem;
}

.project-link {
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.project-link:hover {
  color: #2563eb;
  text-decoration: underline;
}

.core-data {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0.45rem 1rem;
  margin-top: 1rem;
  padding: 1rem 1.1rem;
  background: var(--surface-muted);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  font-size: 0.875rem;
  line-height: 1.55;
  color: var(--text-secondary);
}

@media (min-width: 520px) {
  .core-data {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.core-data p {
  margin: 0;
}

.core-data strong {
  font-weight: 600;
  color: var(--text-primary);
}

.dimension-scores {
  margin-top: 1.5rem;
  padding-top: 0.25rem;
}

.dimension-scores-lead {
  margin: 0 0 1rem;
  font-size: 0.8125rem;
  line-height: 1.65;
  color: var(--text-muted);
  text-align: left;
}

.dimension-scores-lead strong {
  font-weight: 700;
  color: var(--text-secondary);
}

.score-item {
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.4rem;
}

@media (min-width: 560px) {
  .score-item {
    flex-direction: row;
    align-items: flex-start;
    gap: 0.75rem 1rem;
  }
}

.score-item :deep(.el-progress) {
  flex: 1;
  min-width: 0;
  padding-top: 0.15rem;
}

.dimension-col {
  flex: 0 0 auto;
  min-width: 0;
}

@media (min-width: 560px) {
  .dimension-col {
    flex: 0 0 13.5rem;
    max-width: 42%;
  }
}

.dimension-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.dimension {
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.4;
  cursor: default;
  border-bottom: 1px dashed var(--border-strong);
}

.score-hint {
  flex-shrink: 0;
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: var(--accent);
  opacity: 0.9;
  cursor: help;
}

.dimension-hint {
  margin: 0.2rem 0 0;
  font-size: 0.75rem;
  line-height: 1.55;
  color: var(--text-muted);
  text-align: left;
}

.project-analysis {
  margin-top: 1.5rem;
  padding: 1.15rem 1.2rem;
  background: linear-gradient(165deg, #f0fdf4 0%, #ecfdf5 100%);
  border-radius: var(--radius-md);
  border: 1px solid rgba(34, 197, 94, 0.18);
}

.analysis-list {
  padding-left: 1.2rem;
  margin-top: 0.5rem;
}

.analysis-list li {
  margin-bottom: 0.55rem;
}

.project-suggestions {
  margin-top: 1.5rem;
  padding: 1.15rem 1.2rem;
  background: linear-gradient(165deg, #eff6ff 0%, #f0f9ff 100%);
  border-radius: var(--radius-md);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.suggestions-list {
  padding-left: 1.2rem;
  margin-top: 0.5rem;
}

.suggestions-list li {
  margin-bottom: 0.55rem;
}

.history-section {
  margin-top: 2rem;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.history-item {
  padding: 0.9rem 1rem;
  background: var(--surface-muted);
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
  text-align: left;
}

.history-item:hover {
  background: var(--surface-card);
  border-color: var(--border-subtle);
  transform: translateX(4px);
  box-shadow: var(--shadow-sm);
}

.history-need {
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.55;
  color: var(--text-primary);
  margin-bottom: 0.35rem;
}

.history-time {
  font-size: 0.75rem;
  letter-spacing: 0.02em;
  color: var(--text-faint);
}

/* 回到顶部按钮 */
.back-to-top {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  transition: all 0.3s ease;
  z-index: 100;
}

.back-to-top:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px 0 rgba(64, 158, 255, 0.4);
}

.footer {
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  color: #e2e8f0;
  padding: 2.5rem 0;
  margin-top: 2.5rem;
  border-top: 1px solid rgba(148, 163, 184, 0.15);
}

.footer-content {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 0 clamp(1rem, 4vw, 2rem);
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 2rem 2.5rem;
}

.footer-section {
  flex: 1;
  min-width: 220px;
  text-align: left;
}

.footer-section h4 {
  font-family: var(--font-heading);
  font-size: 0.875rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  margin-bottom: 0.75rem;
  color: #93c5fd;
}

.footer-section p {
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  line-height: 1.65;
  color: #cbd5e1;
  max-width: 42ch;
}

.footer-section a {
  color: #e2e8f0;
  text-decoration: none;
  margin-right: 1.1rem;
  font-size: 0.875rem;
  font-weight: 500;
  transition: color 0.2s ease;
}

.footer-section a:hover {
  color: #93c5fd;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main {
    padding: 1rem;
  }
  
  .hero-title {
    letter-spacing: 0.08em;
  }
  
  .chart {
    height: 300px;
  }
  
  .chart-weights {
    height: 300px;
  }
  
  .footer-content {
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .back-to-top {
    bottom: 1rem;
    right: 1rem;
  }
}
</style>
