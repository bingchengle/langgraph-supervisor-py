<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import { 
  ElButton, ElInput, ElLoading, ElMessage, ElCard, ElTag, 
  ElProgress, ElDivider, ElSelect, ElOption, ElTooltip, 
  ElBadge, ElIcon, ElPopconfirm, ElScrollbar
} from 'element-plus'
import { Star, Download, Top, Edit, Check, Link, Calendar, Document } from '@element-plus/icons-vue'

// 响应式数据
const userNeed = ref('')
const loading = ref(false)
const recommendationResult = ref(null)
const activeDimension = ref('total')
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

// 推荐等级配色
const recommendColors = {
  0: '#67C23A', // 推荐 - 绿色
  1: '#409EFF', // 次推荐 - 蓝色
  2: '#909399'  // 备选 - 灰色
}

// 维度定义
const dimensionDefinitions = {
  '流行度': '项目的受欢迎程度，基于Star数、下载量等指标',
  '成熟度': '项目的稳定程度，基于版本历史、维护频率等指标',
  '生态': '项目的生态系统丰富程度，基于插件、扩展等指标',
  '风险': '项目的风险程度，基于安全漏洞、依赖等指标',
  '上手难度': '项目的学习曲线陡峭程度，基于文档、示例等指标',
  '性能': '项目的运行效率，基于速度、资源占用等指标',
  '体积': '项目的大小，基于安装包大小、依赖数量等指标',
  '文档友好度': '项目文档的质量和完整性'
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

// 渲染图表
const renderCharts = () => {
  if (!recommendationResult.value || !recommendationResult.value.projects || recommendationResult.value.projects.length === 0) {
    return
  }
  
  // 渲染项目对比柱状图
  renderComparisonChart()
  
  // 渲染雷达图（3项目对比）
  renderRadarChart()
}

// 渲染项目对比柱状图
const renderComparisonChart = () => {
  const comparisonChartDom = document.getElementById('comparison-chart')
  if (comparisonChartDom) {
    const myChart = echarts.init(comparisonChartDom)
    
    const projectNames = recommendationResult.value.projects.map(p => p.name)
    let scores
    
    if (activeDimension.value === 'total') {
      scores = recommendationResult.value.projects.map(p => p.total_score)
    } else {
      scores = recommendationResult.value.projects.map(p => p.dimension_scores[activeDimension.value] || 0)
    }
    
    const option = {
      title: {
        text: activeDimension.value === 'total' ? '项目总分对比' : `${activeDimension.value}维度对比`,
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: function(params) {
          const index = params[0].dataIndex
          const project = recommendationResult.value.projects[index]
          if (activeDimension.value === 'total') {
            const parsed = parseProjectData(project)
            return `${project.name}<br/>总分: ${parsed.totalScore.display}<br/>${parsed.totalScore.explanation}`
          } else {
            const parsed = parseProjectData(project)
            const dimScore = parsed.dimensionScores[activeDimension.value]
            return `${project.name}<br/>${activeDimension.value}: ${dimScore.display}<br/>${dimScore.explanation}`
          }
        }
      },
      xAxis: {
        type: 'category',
        data: projectNames
      },
      yAxis: {
        type: 'value',
        max: 1,
        axisLabel: {
          formatter: '{value}'
        }
      },
      series: [{
        data: scores.map((score, index) => ({
          value: score,
          itemStyle: {
            color: recommendColors[index] || '#909399'
          }
        })),
        type: 'bar',
        label: {
          show: true,
          position: 'top',
          formatter: function(params) {
            const index = params.dataIndex
            return `${index + 1}. ${params.data.toFixed(3)}`
          }
        }
      }]
    }
    
    myChart.setOption(option)
    
    // 响应式调整
    window.addEventListener('resize', () => {
      myChart.resize()
    })
  }
}

// 渲染雷达图（3项目对比）
const renderRadarChart = () => {
  const radarChartDom = document.getElementById('radar-chart')
  if (radarChartDom) {
    const myChart = echarts.init(radarChartDom)
    
    const dimensions = Object.keys(recommendationResult.value.projects[0].dimension_scores)
    const series = recommendationResult.value.projects.map((project, index) => ({
      name: project.name,
      type: 'radar',
      data: [{
        value: Object.values(project.dimension_scores),
        name: project.name,
        itemStyle: {
          color: recommendColors[index] || '#909399'
        }
      }]
    }))
    
    const option = {
      title: {
        text: '项目维度对比',
        left: 'center'
      },
      tooltip: {
        formatter: function(params) {
          const projectName = params[0].name
          const project = recommendationResult.value.projects.find(p => p.name === projectName)
          const parsed = parseProjectData(project)
          let html = `<div><strong>${projectName}</strong></div>`
          params.forEach(param => {
            const dim = param.name
            const score = param.value
            const dimScore = parsed.dimensionScores[dim]
            html += `<div>${dim}: ${dimScore.display} (${dimScore.explanation})</div>`
          })
          return html
        }
      },
      legend: {
        data: recommendationResult.value.projects.map(p => p.name),
        bottom: 0
      },
      radar: {
        indicator: dimensions.map(dim => ({
          name: dim,
          max: 1
        }))
      },
      series: series
    }
    
    myChart.setOption(option)
    
    // 响应式调整
    window.addEventListener('resize', () => {
      myChart.resize()
    })
  }
}

// 解析项目核心数据
const parseProjectData = (project) => {
  // 解析Star数
  const parseStars = (stars) => {
    if (!stars) return { display: '0', explanation: '暂无Star数据' }
    if (stars >= 10000) {
      return { display: `${(stars / 10000).toFixed(1)}k`, explanation: '行业顶级热度，社区活跃' }
    } else if (stars >= 1000) {
      return { display: `${(stars / 1000).toFixed(1)}k`, explanation: '高热度项目，社区支持良好' }
    } else {
      return { display: stars.toString(), explanation: '新兴项目，有一定社区基础' }
    }
  }
  
  // 解析下载量
  const parseDownloads = (downloads) => {
    if (!downloads) return { display: '0', explanation: '暂无下载数据' }
    if (downloads >= 1000000) {
      return { display: `${(downloads / 1000000).toFixed(1)}M`, explanation: 'Python生态主流库' }
    } else if (downloads >= 1000) {
      return { display: `${(downloads / 1000).toFixed(1)}k`, explanation: '常用库，有稳定用户群' }
    } else {
      return { display: downloads.toString(), explanation: '小众库，适合特定场景' }
    }
  }
  
  // 解析版本号
  const parseVersion = (version) => {
    if (!version) return { display: '未知', explanation: '暂无版本信息' }
    // 简单判断版本成熟度
    const versionParts = version.replace('v', '').split('.')
    const major = parseInt(versionParts[0]) || 0
    if (major >= 1) {
      return { display: version, explanation: '稳定版本，适合生产环境' }
    } else {
      return { display: version, explanation: '开发版本，功能可能不稳定' }
    }
  }
  
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
    stars: parseStars(project.stars),
    weeklyDownloads: parseDownloads(project.weekly_downloads),
    version: parseVersion(project.version),
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

// 处理维度切换
const handleDimensionChange = () => {
  renderComparisonChart()
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
      <div class="header-content">
        <div class="logo">
          <Star class="logo-icon" />
          <h1>开源项目智能选型助手</h1>
        </div>
        <p>基于LLM驱动的动态加权推荐系统</p>
      </div>
    </header>
    
    <main class="main">
      <section class="input-section">
        <el-card shadow="hover" class="input-card">
          <template #header>
            <div class="card-header">
              <span>输入您的需求</span>
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
              <span>推荐结果</span>
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
            
            <p><strong>需求定位:</strong> {{ recommendationResult.llm_result.task_type }}</p>
            <p><strong>关键需求点:</strong></p>
            <ul class="requirement-list">
              <li v-for="(req, index) in recommendationResult.llm_result.key_requirements" :key="index" v-if="req">{{ req }}</li>
            </ul>
            
            <!-- 评估维度与权重 -->
            <div class="weights-section">
              <h4 class="subsection-title">评估维度与权重</h4>
              <div class="weights-container">
                <div 
                  v-for="(weight, dimension) in recommendationResult.llm_result.weights" 
                  :key="dimension" 
                  class="weight-item"
                >
                  <el-tooltip :content="dimensionDefinitions[dimension]" placement="top">
                    <span class="dimension">{{ dimension }}</span>
                  </el-tooltip>
                  <div class="weight-circle">
                    <el-progress 
                      type="circle" 
                      :percentage="weight * 100" 
                      :format="() => `${(weight * 100).toFixed(1)}%`"
                      :stroke-width="8"
                      :width="80"
                    />
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 权重说明 -->
            <div class="weight-explanation">
              <h4 class="subsection-title">权重说明</h4>
              <ul class="explanation-list">
                <li v-if="recommendationResult.llm_result.prefer_beginner_friendly">
                  上手难度权重较高，因您需求为适合新手
                </li>
                <li v-if="recommendationResult.llm_result.prefer_mature_project">
                  成熟度和风险权重较高，因您需求为稳定可靠
                </li>
                <li v-if="recommendationResult.llm_result.prefer_small_project">
                  体积和性能权重较高，因您需求为轻量快速
                </li>
                <li>
                  生态权重根据您对功能全面性的需求进行了调整
                </li>
              </ul>
            </div>
          </div>
          
          <el-divider></el-divider>
          
          <!-- 项目对比 -->
          <div class="project-comparison">
            <div class="comparison-header">
              <h3 class="section-title">项目对比</h3>
              <el-select 
                v-model="activeDimension" 
                @change="handleDimensionChange"
                class="dimension-select"
              >
                <el-option value="total" label="总分"></el-option>
                <el-option 
                  v-for="(weight, dimension) in recommendationResult.llm_result.weights" 
                  :key="dimension"
                  :value="dimension"
                  :label="dimension"
                ></el-option>
              </el-select>
            </div>
            <div id="comparison-chart" class="chart"></div>
            <div class="chart-explanation">
              <p>评分区间：0-1分，越高越好</p>
              <div class="color-legend">
                <span class="legend-item"><span class="color-box" style="background-color: #67C23A;"></span> 推荐</span>
                <span class="legend-item"><span class="color-box" style="background-color: #409EFF;"></span> 次推荐</span>
                <span class="legend-item"><span class="color-box" style="background-color: #909399;"></span> 备选</span>
              </div>
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
                      <el-tooltip :content="parseProjectData(project).stars.explanation" placement="top">
                        <p><strong>Star数:</strong> {{ parseProjectData(project).stars.display }}</p>
                      </el-tooltip>
                      <el-tooltip :content="parseProjectData(project).weeklyDownloads.explanation" placement="top">
                        <p><strong>周下载量:</strong> {{ parseProjectData(project).weeklyDownloads.display }}</p>
                      </el-tooltip>
                      <el-tooltip :content="parseProjectData(project).version.explanation" placement="top">
                        <p><strong>最新版本:</strong> {{ parseProjectData(project).version.display }}</p>
                      </el-tooltip>
                      <p v-if="project.forks"><strong>Fork数:</strong> {{ project.forks }}</p>
                      <p v-if="project.last_update"><strong>最后更新:</strong> {{ project.last_update }}</p>
                      <p v-if="project.monthly_downloads"><strong>月下载量:</strong> {{ project.monthly_downloads }}</p>
                    </div>
                  </div>
                  
                  <!-- 各维度得分 -->
                  <div class="dimension-scores">
                    <h4 class="subsection-title">各维度得分:</h4>
                    <div 
                      v-for="(score, dimension) in sortedDimensions(project)" 
                      :key="dimension" 
                      class="score-item"
                    >
                      <el-tooltip :content="parseProjectData(project).dimensionScores[dimension].explanation" placement="top">
                        <span class="dimension">{{ dimension }}:</span>
                      </el-tooltip>
                      <el-progress 
                        :percentage="score * 100" 
                        :format="() => parseProjectData(project).dimensionScores[dimension].display"
                        :stroke-width="10"
                      />
                    </div>
                  </div>
                  
                  <!-- 项目分析 -->
                  <div class="project-analysis">
                    <h4 class="subsection-title">项目分析:</h4>
                    <ul class="analysis-list">
                      <li v-for="(item, idx) in generateProjectAnalysis(project, index)" :key="idx">
                        {{ item }}
                      </li>
                    </ul>
                  </div>
                  
                  <!-- 二创方向和建议 -->
                  <div class="project-suggestions">
                    <h4 class="subsection-title">二创方向和建议:</h4>
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
          
          <!-- 雷达图对比 -->
          <div class="radar-section">
            <h3 class="section-title">维度对比雷达图</h3>
            <div id="radar-chart" class="chart"></div>
          </div>
        </el-card>
      </section>
      
      <!-- 历史记录 -->
      <section v-if="history.length > 0" class="history-section">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>历史记录</span>
              <el-icon><Star /></el-icon>
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
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
  font-family: 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
}

/* 头部样式 */
.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem 0;
  text-align: center;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.logo-icon {
  font-size: 2.5rem;
}

.header h1 {
  margin: 0;
  font-size: 2.5rem;
  font-weight: 600;
}

.header p {
  margin: 0.5rem 0 0;
  font-size: 1.2rem;
  opacity: 0.9;
}

/* 主内容样式 */
.main {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
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
  font-size: 16px;
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

/* 需求分析区样式 */
.need-analysis {
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #303133;
}

.subsection-title {
  font-size: 1.2rem;
  font-weight: 500;
  margin: 1.5rem 0 0.5rem;
  color: #409EFF;
}

.need-validation {
  background-color: #f0f9eb;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.need-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.requirement-list {
  padding-left: 1.5rem;
  margin: 0.5rem 0 1rem;
}

.weights-section {
  margin-top: 1.5rem;
}

.weights-container {
  display: flex;
  flex-wrap: wrap;
  gap: 2rem;
  margin-top: 1rem;
}

.weight-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  min-width: 100px;
}

.weight-circle {
  display: flex;
  justify-content: center;
}

.weight-explanation {
  margin-top: 1.5rem;
  background-color: #ecf5ff;
  padding: 1rem;
  border-radius: 4px;
}

.explanation-list {
  padding-left: 1.5rem;
  margin-top: 0.5rem;
}

/* 项目对比区样式 */
.project-comparison {
  margin-bottom: 2rem;
}

.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.dimension-select {
  width: 150px;
}

.chart {
  width: 100%;
  height: 400px;
  margin-top: 1rem;
}

.chart-explanation {
  margin-top: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #606266;
}

.color-legend {
  display: flex;
  gap: 1rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.color-box {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

/* 项目详情区样式 */
.project-details {
  margin-top: 2rem;
}

.project-card {
  margin-bottom: 2rem;
  transition: all 0.3s ease;
}

.project-card:hover {
  transform: translateY(-2px);
}

.recommended-card {
  border: 2px solid #67C23A;
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.project-name {
  font-size: 1.2rem;
  font-weight: 600;
}

.recommend-tag {
  font-size: 12px;
}

.favorite-button {
  transition: all 0.3s ease;
}

.favorite-button:hover {
  transform: scale(1.1);
}

.project-info {
  margin-top: 1rem;
}

.project-core-info {
  margin-bottom: 1.5rem;
}

.project-link {
  color: #409EFF;
  text-decoration: none;
  transition: all 0.3s ease;
}

.project-link:hover {
  text-decoration: underline;
  color: #667eea;
}

.dimension-scores {
  margin-top: 1.5rem;
}

.score-item {
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.dimension {
  display: inline-block;
  width: 100px;
  font-weight: 500;
}

.project-analysis {
  margin-top: 1.5rem;
  padding: 1rem;
  background-color: #f0f9eb;
  border-radius: 4px;
}

.analysis-list {
  padding-left: 1.5rem;
  margin-top: 0.5rem;
}

.analysis-list li {
  margin-bottom: 0.5rem;
}

.project-suggestions {
  margin-top: 1.5rem;
  padding: 1rem;
  background-color: #ecf5ff;
  border-radius: 4px;
}

.suggestions-list {
  padding-left: 1.5rem;
  margin-top: 0.5rem;
}

.suggestions-list li {
  margin-bottom: 0.5rem;
}

/* 雷达图区样式 */
.radar-section {
  margin-top: 2rem;
}

/* 历史记录区样式 */
.history-section {
  margin-top: 2rem;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.history-item {
  padding: 1rem;
  background-color: #f5f7fa;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.history-item:hover {
  background-color: #ecf5ff;
  transform: translateX(5px);
}

.history-need {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.history-time {
  font-size: 12px;
  color: #909399;
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

/* 页脚样式 */
.footer {
  background-color: #333;
  color: white;
  padding: 2rem 0;
  margin-top: 2rem;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 2rem;
}

.footer-section {
  flex: 1;
  min-width: 250px;
}

.footer-section h4 {
  margin-bottom: 1rem;
  color: #409EFF;
}

.footer-section p {
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

.footer-section a {
  color: white;
  text-decoration: none;
  margin-right: 1rem;
  transition: all 0.3s ease;
}

.footer-section a:hover {
  color: #409EFF;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main {
    padding: 1rem;
  }
  
  .header h1 {
    font-size: 2rem;
  }
  
  .logo-icon {
    font-size: 2rem;
  }
  
  .weights-container {
    gap: 1rem;
  }
  
  .chart {
    height: 300px;
  }
  
  .comparison-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
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
