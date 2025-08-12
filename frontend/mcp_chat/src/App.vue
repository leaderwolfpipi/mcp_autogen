<template>
  <div class="app">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ 'sidebar-open': sidebarOpen }">
      <div class="sidebar-header">
        <div class="logo">
          <div class="logo-icon">🦜</div>
          <span class="logo-text">QiQi</span>
        </div>
        <button class="new-chat-btn" @click="startNewChat">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 1V15M1 8H15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          开启新对话
        </button>
      </div>
      
      <div class="chat-history">
        <div v-for="(group, date) in groupedHistory" :key="date" class="history-group">
          <div class="history-date">{{ date }}</div>
          <div v-for="chat in group" :key="chat.id" 
               class="history-item" 
               :class="{ active: currentChatId === chat.id }"
               @click="loadChat(chat.id)">
            <div class="history-title">{{ chat.title }}</div>
            <div class="history-time">{{ formatTime(chat.createdAt) }}</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- 主聊天区域 -->
    <main class="main-content" :class="{ 'search-panel-open': showSearchPanel }">
      <!-- 移动端侧边栏遮罩 -->
      <div class="sidebar-overlay" 
           :class="{ active: sidebarOpen }" 
           @click="sidebarOpen = false"></div>

      <!-- 顶部工具栏 -->
      <header class="chat-header">
        <button class="sidebar-toggle" @click="sidebarOpen = !sidebarOpen">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M3 7H17M3 13H17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
        <div class="chat-title">{{ currentChat?.title || '鹦鹉学舌' }}</div>
      </header>

      <!-- 对话区域 -->
      <div class="chat-container" ref="chatContainer">
        <!-- 欢迎界面 -->
        <div v-if="!currentChat || currentChat.messages.length === 0" class="welcome-screen">
          <div class="welcome-content">
            <div class="welcome-header">
              <div class="welcome-main">
                <div class="welcome-avatar">
                  <div class="avatar-icon">🦜</div>
                </div>
                <h1 class="welcome-title">我是QiQi，很高兴见到你!</h1>
              </div>
              <p class="welcome-subtitle">我可以帮你写代码、读文件、写作各种创意内容，请把你的任务交给我吧～</p>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-else class="messages-container">
          <TransitionGroup name="message" tag="div" class="messages-list">
            <div v-for="message in currentChat.messages" :key="message.id" class="message-wrapper">
              <div class="message" :class="{ 'user-message': message.role === 'user', 'ai-message': message.role === 'assistant', 'has-task': message.mode === 'task' }">
                <!-- 只为AI消息显示头像 -->
                <div v-if="message.role === 'assistant'" class="message-avatar">
                  <div class="ai-avatar">🦜</div>
                </div>
                <div class="message-content" :class="{ 'user-no-avatar': message.role === 'user' }">
                  <!-- 用户消息 -->
                  <div v-if="message.role === 'user'" class="message-text">
                    {{ message.content }}
                  </div>
                  
                  <!-- AI消息 -->
                  <div v-else>
                    <!-- 加载动画 -->
                    <div v-if="(!message.content || message.content.trim() === '') && message.isStreaming" class="typing-animation">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                    
                    <!-- 闲聊模式 - 简洁显示 -->
                    <div v-else-if="message.mode === 'chat'" class="chat-message-content">
                      <!-- 闲聊头部 -->
                      <div class="chat-header">
                        <span class="chat-icon">💬</span>
                        <span class="chat-title">闲聊模式</span>
                      </div>
                      
                      <div class="message-text" :class="{ 'streaming': message.isStreaming }">
                        {{ message.content }}
                      </div>
                      <div v-if="message.executionTime && message.executionTime > 0" class="execution-time">
                        响应时间: {{ message.executionTime.toFixed(2) }}秒
                      </div>
                    </div>
                    
                    <!-- 任务模式 - 完整显示 -->
                    <div v-else-if="message.mode === 'task'" class="task-message-content">
                      <!-- 任务头部 -->
                      <div class="task-header">
                        <span class="task-icon">🔧</span>
                        <span class="task-title">任务模式</span>
                        <div class="task-progress" v-if="message.nodeResults && message.nodeResults.length > 0">
                          开始执行
                      </div>
                      </div>
                      
                      <!-- ASCII 流程图显示 -->
                      <div v-if="message.asciiDiagram" class="ascii-container">
                        <div class="ascii-header">
                          <span class="ascii-icon">📊</span>
                          <span class="ascii-title">执行流程</span>
                          </div>
                        <div class="ascii-diagram">
                          <pre>{{ message.asciiDiagram }}</pre>
                        </div>
                      </div>
                      
                      <!-- 最终结果 -->
                      <div v-if="message.finalResult" class="final-result" v-html="message.finalResult"></div>
                    </div>
                    
                    <!-- 兼容旧格式 -->
                  <div v-else class="message-text" :class="{ 'streaming': message.isStreaming }">
                    {{ message.content }}
                  </div>
                  </div>
                  
                  <!-- 旧版工具执行结果展示 -->
                  <div v-if="message.toolResults && message.toolResults.length > 0" class="tool-results">
                    <div class="tool-results-header">
                      <span class="tool-results-title">🔧 工具执行结果</span>
                      <span class="tool-results-count">{{ message.toolResults.length }} 个工具</span>
                    </div>
                    <div v-for="tool in message.toolResults" :key="tool.node_id" class="tool-result-item">
                      <div class="tool-result-header">
                        <div class="tool-result-info">
                          <span class="tool-result-type">{{ tool.tool_type }}</span>
                          <span class="tool-result-time">{{ tool.execution_time.toFixed(2) }}秒</span>
                          <span class="tool-result-status" :class="tool.status">{{ tool.status }}</span>
                        </div>
                      </div>
                      <div class="tool-result-summary">{{ tool.result_summary }}</div>
                      <div v-if="tool.output && typeof tool.output === 'string' && tool.output.length > 0" class="tool-result-output">
                        <div class="tool-result-output-header">📄 输出内容:</div>
                        <div class="tool-result-output-content">{{ tool.output }}</div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 旧版搜索结果展示 -->
                  <div v-if="message.searchResults" class="search-results">
                    <div class="search-header" @click="toggleSearchPanel">
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M7 13A6 6 0 1 0 7 1a6 6 0 0 0 0 12zM15 15l-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                      </svg>
                      已搜索到 {{ message.searchResults.length }} 个网页 
                      <span class="search-toggle-icon" :class="{ 'open': showSearchPanel }">&gt;</span>
                    </div>
                    <div class="search-sites">
                      <div v-for="site in message.searchResults" :key="site.id" class="search-site">
                        <img :src="site.logo" :alt="site.name" class="site-logo">
                        <span class="site-name">{{ site.name }}</span>
                      </div>
                    </div>
                  </div>
                </div> <!-- message-content 结束 -->
              </div> <!-- message 结束 -->
            </div> <!-- v-for 结束 -->
          </TransitionGroup>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-container" :class="{ 'centered': !currentChat || currentChat.messages.length === 0 }">
        <div class="input-wrapper">
          <div class="input-box">
            <textarea 
              v-model="inputMessage"
              placeholder="给QiQi发送消息"
              class="message-input"
              @keydown.enter.prevent="handleSendMessage"
              @input="adjustTextarea"
              ref="messageInput"
              rows="1"
            ></textarea>
            
            <div class="input-bottom">
              <!-- 工具按钮放在输入框内部底部 -->
              <div class="input-tools">
                <button class="tool-btn" :class="{ active: deepThinkMode }" @click="deepThinkMode = !deepThinkMode">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M8 2V14M2 8H14" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                  深度思考 (R1)
                </button>
                <button class="tool-btn" :class="{ active: webSearchMode }" @click="webSearchMode = !webSearchMode">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M2 8h12M8 2c2.5 0 4.5 2.7 4.5 6s-2 6-4.5 6-4.5-2.7-4.5-6 2-6 4.5-6z" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                  联网搜索
                </button>
              </div>
              
              <div class="input-actions">
                <button class="attach-btn" @click="handleFileUpload">
                  📎
                </button>
                <button class="send-btn" @click="handleSendMessage" :disabled="!inputMessage.trim()">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M18 2L9 11M18 2L12 18L9 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <div class="input-footer">
          <span class="footer-text">内容由 AI 生成，请仔细甄别</span>
        </div>
      </div>
    </main>

    <!-- 右侧搜索面板 -->
    <aside class="search-panel" :class="{ 'search-panel-open': showSearchPanel }">
      <div class="search-panel-header">
        <h3 class="search-panel-title">搜索结果</h3>
        <button class="search-panel-close" @click="toggleSearchPanel">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
      <div class="search-panel-content">
        <div v-for="result in currentSearchResults" :key="result.id" class="search-result-item">
          <div class="search-result-header">
            <div class="search-result-source">
              <img :src="result.logo" :alt="result.source" class="search-result-logo">
              <span class="search-result-source-name">{{ result.source }}</span>
              <span class="search-result-date">{{ result.date }}</span>
            </div>
            <div class="search-result-number">{{ result.number }}</div>
          </div>
          <div class="search-result-title">{{ result.title }}</div>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick, onMounted, onUnmounted, shallowRef, markRaw } from 'vue'
import { WebSocketManager } from './websocket-manager'
import { config } from './config'
import { MessageHandler } from './message-handler'
// 引入 Markdown 库
import { marked } from 'marked'

// 配置 Marked 选项
marked.setOptions({
  gfm: true,
  breaks: true
})

// 自定义渲染器，为链接添加样式和属性
const renderer = new marked.Renderer()

// 自定义链接渲染
renderer.link = function(token: any): string {
  const href = token.href || ''
  const title = token.title || ''
  const text = token.text || ''
  
  // 检测是否是下载链接
  const isDownloadLink = href && (
    href.includes('minio.') || 
    href.includes('amazonaws.com') || 
    href.includes('.s3.') ||
    href.includes('download') ||
    href.match(/\.(jpg|jpeg|png|gif|pdf|doc|docx|zip|mp4|mp3|txt|csv|json|xml)(\?|$)/i)
  )
  
  let linkClass = 'markdown-link'
  let attributes = ''
  
  if (isDownloadLink) {
    linkClass += ' download-link'
    attributes = ' target="_blank" rel="noopener noreferrer" download'
  } else {
    attributes = ' target="_blank" rel="noopener noreferrer"'
  }
  
  const titleAttr = title ? ` title="${title}"` : ''
  
  return `<a href="${href}" class="${linkClass}"${attributes}${titleAttr}>${text}</a>`
}

marked.setOptions({ renderer })


// 执行计划管理器
class ExecutionPlanManager {
  private plan: any = null
  private currentStep: string = ''
  private stepStates: Map<string, 'pending' | 'running' | 'success' | 'error'> = new Map()
  
  constructor() {
    this.reset()
  }
  
  // 初始化执行计划
  initPlan(planData: any) {
    this.plan = planData
    this.stepStates.clear()
    
    // 初始化所有步骤为pending状态
    if (planData && planData.steps) {
      planData.steps.forEach((step: any, index: number) => {
        const stepId = step.id || step.tool_name || step.name || `step_${index}`
        this.stepStates.set(stepId, 'pending')
      })
    }
  }
  
  // 从消息内容中智能解析执行计划
  parseExecutionPlan(message: string): any | null {
    try {
      // 尝试匹配常见的执行计划格式
      const patterns = [
        // 匹配 "步骤1: xxx" 格式
        /(\d+)[\.\:：]\s*([^\n\r]+)/g,
        // 匹配 "- xxx" 格式  
        /^\s*[-\*]\s*([^\n\r]+)/gm,
        // 匹配带编号的列表
        /^\s*\d+\.\s*([^\n\r]+)/gm
      ]
      
      let steps: any[] = []
      let stepIndex = 0
      
      for (const pattern of patterns) {
        const matches = Array.from(message.matchAll(pattern))
        if (matches.length > 0) {
          steps = matches.map((match, index) => {
            const description = match[2] || match[1] || match[0]
            const toolName = this.extractToolName(description)
            return {
              id: `step_${index}`,
              tool_name: toolName,
              description: description.trim(),
              index: index
            }
          })
          break
        }
      }
      
      // 如果没有找到明确的步骤，创建默认计划
      if (steps.length === 0 && (message.includes('执行') || message.includes('任务') || message.includes('处理'))) {
        steps = [
          { id: 'step_0', tool_name: 'task_analysis', description: '分析任务需求' },
          { id: 'step_1', tool_name: 'data_processing', description: '处理相关数据' },
          { id: 'step_2', tool_name: 'result_generation', description: '生成执行结果' }
        ]
      }
      
      return steps.length > 0 ? { steps } : null
      
    } catch (error) {
      console.warn('执行计划解析失败:', error)
      return null
    }
  }
  
  // 从描述中提取工具名称
  private extractToolName(description: string): string {
    const toolMap: { [key: string]: string } = {
      '搜索': 'web_search',
      '查找': 'web_search', 
      '检索': 'web_search',
      '读取': 'file_read',
      '读': 'file_read',
      '写入': 'file_write',
      '写': 'file_write',
      '保存': 'file_write',
      '执行': 'code_execute',
      '运行': 'code_execute',
      '分析': 'data_analysis',
      '处理': 'data_processing',
      '计算': 'calculation',
      '调用': 'api_call',
      '请求': 'api_call'
    }
    
    for (const [keyword, toolName] of Object.entries(toolMap)) {
      if (description.includes(keyword)) {
        return toolName
      }
    }
    
    return 'generic_tool'
  }
  
  // 更新步骤状态
  updateStepState(stepId: string, state: 'pending' | 'running' | 'success' | 'error') {
    this.stepStates.set(stepId, state)
    this.currentStep = state === 'running' ? stepId : this.currentStep
    
    // 如果步骤不存在，动态添加
    if (!this.stepStates.has(stepId) && this.plan) {
      const newStep = {
        id: stepId,
        tool_name: stepId,
        description: `执行 ${stepId}`,
        index: this.plan.steps?.length || 0
      }
      
      if (!this.plan.steps) {
        this.plan.steps = []
      }
      this.plan.steps.push(newStep)
    }
  }
  
  // 获取执行进度
  getProgress(): { completed: number, total: number, percentage: number } {
    const total = this.stepStates.size
    const completed = Array.from(this.stepStates.values()).filter(state => state === 'success').length
    const percentage = total > 0 ? Math.round((completed / total) * 100) : 0
    
    return { completed, total, percentage }
  }
  
  // 生成动态ASCII流程图
  generateAsciiDiagram(): string {
    if (!this.plan || !this.plan.steps || this.plan.steps.length === 0) {
      return this.generateInitialDiagram()
    }
    
    let diagram = ''
    
    // 分析当前执行状态
    const stepStates = this.analyzeStepStates()
    
    // 根据执行进度决定显示的步骤数
    const visibleSteps = this.getVisibleSteps(stepStates)
    
    // 构建基础结构
    diagram += this.buildBasicStructure()
    
    // 如果有可见步骤，构建工具执行部分
    if (visibleSteps.length > 0) {
      diagram += this.buildToolsSection(visibleSteps, stepStates)
    }
    
    // 构建最终状态
    diagram += this.buildFinalStatus(stepStates)
    
    return diagram
  }
  
  // 生成初始状态图表
  generateInitialDiagram(): string {
    return `    👤 用户输入
         │
         ▼
    🧠 LLM分析
         │
         ▼
    📋 准备就绪`
  }
  
  // 分析步骤执行状态
  analyzeStepStates() {
    let currentRunningIndex = -1
    let lastCompletedIndex = -1
    let hasError = false
    let totalCompleted = 0
    
    this.plan.steps.forEach((step: any, index: number) => {
      const stepId = step.tool_name || step.id || `step_${index}`
      const state = this.stepStates.get(stepId) || 'pending'
      
      if (state === 'running') {
        currentRunningIndex = index
      } else if (state === 'success') {
        lastCompletedIndex = Math.max(lastCompletedIndex, index)
        totalCompleted++
      } else if (state === 'error') {
        hasError = true
        lastCompletedIndex = Math.max(lastCompletedIndex, index)
      }
    })
    
    const allCompleted = totalCompleted === this.plan.steps.length
    const hasRunning = currentRunningIndex >= 0
    
    return {
      currentRunningIndex,
      lastCompletedIndex,
      hasError,
      allCompleted,
      hasRunning,
      totalCompleted
    }
  }
  
  // 获取可见的步骤（已执行 + 正在执行 + 下一个待执行）
  getVisibleSteps(stepStates: any) {
    const { currentRunningIndex, lastCompletedIndex } = stepStates
    
    // 显示到当前运行步骤，或最后完成步骤 + 1
    let showUpToIndex = -1
    
    if (currentRunningIndex >= 0) {
      showUpToIndex = currentRunningIndex
    } else if (lastCompletedIndex >= 0) {
      showUpToIndex = Math.min(lastCompletedIndex + 1, this.plan.steps.length - 1)
        } else {
      showUpToIndex = 0 // 至少显示第一个步骤
    }
    
    return this.plan.steps.slice(0, showUpToIndex + 1)
  }
  
  // 构建基础结构（用户输入 -> LLM分析）
  buildBasicStructure(): string {
    return `    👤 用户输入
         │
         ▼
    🧠 LLM分析\n`
        }
  
  // 构建工具执行部分
  buildToolsSection(visibleSteps: any[], stepStates: any): string {
    let section = ''
    
    if (visibleSteps.length === 1) {
      // 单工具场景
      section += this.buildSingleToolFlow(visibleSteps[0], 0, stepStates)
      } else {
      // 多工具场景 - 采用流水线式显示
      section += this.buildPipelineFlow(visibleSteps, stepStates)
    }
    
    return section
  }
  
  // 构建单工具流程
  buildSingleToolFlow(step: any, index: number, stepStates: any): string {
    const stepId = step.tool_name || step.id || `step_${index}`
    const state = this.stepStates.get(stepId) || 'pending'
    
    const stateIcon = this.getStateIcon(state)
    const toolIcon = this.getToolIcon(step.tool_name || stepId)
    const toolName = this.getCleanToolName(step.tool_name || stepId)
    const connectionLine = this.getConnectionLine(state)
    
    return `         │
         ▼
  ${stateIcon} ${toolIcon} ${toolName}
         ${connectionLine}
         ▼\n`
  }
  
  // 构建流水线式流程（适用于多工具）
  buildPipelineFlow(visibleSteps: any[], stepStates: any): string {
    let section = ''
    
    visibleSteps.forEach((step: any, index: number) => {
      const stepId = step.tool_name || step.id || `step_${index}`
      const state = this.stepStates.get(stepId) || 'pending'
      
      const stateIcon = this.getStateIcon(state)
      const toolIcon = this.getToolIcon(step.tool_name || stepId)
      const toolName = this.getCleanToolName(step.tool_name || stepId)
      const connectionLine = this.getConnectionLine(state)
      
      if (index === 0) {
        section += `         │
         ▼\n`
      }
      
      // 工具执行节点
      section += `  ${stateIcon} ${toolIcon} ${toolName}\n`
      
      // 如果不是最后一个步骤，添加连接线
      if (index < visibleSteps.length - 1) {
        section += `         ${connectionLine}
         ▼\n`
        } else {
        // 最后一个步骤，准备连接到最终状态
        section += `         ${connectionLine}
         ▼\n`
        }
    })
    
    return section
  }
  
  // 获取连接线样式（根据状态）
  getConnectionLine(state: string): string {
    switch (state) {
      case 'running':
        return '┆┆┆'  // 动态虚线，表示数据流动
      case 'success':
        return '│'    // 实线，表示已完成
      case 'error':
        return '╋'    // 错误标记
      default:
        return '┇'    // 等待状态的虚线
    }
  }
  
  // 构建最终状态
  buildFinalStatus(stepStates: any): string {
    const { allCompleted, hasError, hasRunning } = stepStates
    
    if (allCompleted && !hasError) {
      return `    ✅ 任务完成`
    } else if (hasError) {
      return `    ⚠️ 部分完成`
    } else if (hasRunning) {
      return `    🔄 执行中...`
    } else {
      return `    ⏳ 准备输出`
    }
  }
  
  // 获取工具图标
  getToolIcon(toolName: string): string {
    const toolIcons: { [key: string]: string } = {
      'web_search': '🔍',
      'smart_search': '🔍',
      'minio_uploader': '📦',
      'image_uploader': '🖼️',
      'file_reader': '📄',
      'file_writer': '✏️',
      'data_analyzer': '📊',
      'task_analyzer': '🧠',
      'code_executor': '⚡',
      'api_caller': '🌐',
      'result_generator': '📋',
      'text_processor': '📝',
      'image_processor': '🎨',
      'audio_processor': '🔊',
      'video_processor': '🎬',
      'database_query': '🗄️',
      'email_sender': '📧',
      'calendar_manager': '📅',
      'notification_sender': '🔔',
      'generic_tool': '🔧'
    }
    return toolIcons[toolName] || '🔧'
  }
  
  // 获取状态图标
  getStateIcon(state: string): string {
    const stateIcons: { [key: string]: string } = {
      'pending': '⏳',
      'running': '🔄',
      'success': '✅',
      'error': '❌'
    }
    return stateIcons[state] || '⏳'
  }
  
  // 获取清理后的工具名称
  getCleanToolName(toolName: string): string {
    const toolNameMap: { [key: string]: string } = {
      'web_search': 'Web Search',
      'smart_search': 'Smart Search',
      'minio_uploader': 'MinIO Upload',
      'image_uploader': 'Image Upload', 
      'file_reader': 'File Reader',
      'file_writer': 'File Writer',
      'data_analyzer': 'Data Analysis',
      'task_analyzer': 'Task Analysis',
      'code_executor': 'Code Execute',
      'api_caller': 'API Call',
      'result_generator': 'Generate Result',
      'text_processor': 'Text Process',
      'image_processor': 'Image Process',
      'audio_processor': 'Audio Process',
      'video_processor': 'Video Process',
      'database_query': 'DB Query',
      'email_sender': 'Send Email',
      'calendar_manager': 'Calendar',
      'notification_sender': 'Notify'
    }
    
    const mappedName = toolNameMap[toolName]
    if (mappedName) {
      return mappedName.length > 14 ? mappedName.substring(0, 14) + '...' : mappedName
    }
    
    // 默认清理逻辑
    return toolName
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (l: string) => l.toUpperCase())
      .substring(0, 14)
  }
  
  // 重置状态
  reset() {
    this.plan = null
    this.currentStep = ''
    this.stepStates.clear()
  }
  
  // 获取步骤图标
  private getStepIcon(toolName: string, state: string): string {
    const stateIcons = {
      pending: '⏳',
      running: '🔄',
      success: '✅',
      error: '❌'
    }
    
    const toolIcons: { [key: string]: string } = {
      'web_search': '🔍',
      'file_read': '📄',
      'file_write': '✏️',
      'code_execute': '⚡',
      'data_analysis': '📊',
      'api_call': '🌐',
      'task_analysis': '🧠',
      'data_processing': '⚙️',
      'result_generation': '📋',
      'generic_tool': '🔧'
    }
    
    if (state === 'running') {
      return stateIcons.running
    }
    
    if (state === 'error') {
      return stateIcons.error
    }
    
    if (state === 'success') {
      return stateIcons.success
    }
    
    return toolIcons[toolName] || stateIcons.pending
  }
}

// 创建执行计划管理器实例
const executionPlanManager = new ExecutionPlanManager()


// 添加动态动画到mermaid节点

// 更新执行计划图表
const updateExecutionPlan = async (messageId: string, plan?: any, stepId?: string, stepState?: string) => {
  console.log('🔄 updateExecutionPlan 调用:', { messageId, plan, stepId, stepState })
  
  // 如果有新的计划数据，初始化执行计划
  if (plan) {
    console.log('📋 初始化执行计划:', plan)
    executionPlanManager.initPlan(plan)
  }
  
  // 更新步骤状态
  if (stepId && stepState) {
    console.log('📊 更新步骤状态:', { stepId, stepState })
    executionPlanManager.updateStepState(stepId, stepState as 'pending' | 'running' | 'success' | 'error')
  }
  
  // 生成最新的ASCII图表
  const diagramCode = executionPlanManager.generateAsciiDiagram()
  console.log('📊 生成的ASCII图表:', diagramCode)
  
  // 更新消息中的ASCII图表
  if (currentChat.value) {
    const currentMessage = currentChat.value.messages.find(m => m.id === messageId)
    if (currentMessage) {
      console.log('💾 更新消息中的ASCII图表')
      updateMessage(currentChat.value.id, messageId, {
        asciiDiagram: diagramCode
      })
      
      // 延迟渲染，确保DOM已更新
      await nextTick()
      setTimeout(() => {
        console.log('✅ ASCII图表更新完成')
      }, 100)
    }
  }
}

// 消息接口
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  searchResults?: SearchResult[]
  toolResults?: ToolResult[]  // 旧版工具执行结果
  isStreaming?: boolean       // 是否正在流式输出
  mode?: 'chat' | 'task'     // 新增：消息模式
  asciiDiagram?: string      // ASCII 图表
  nodeResults?: any[]        // 新增：节点执行结果
  finalResult?: string       // 新增：最终结果
  executionTime?: number     // 新增：执行时间
}

// 新增：工具执行结果接口
interface ToolResult {
  node_id: string
  tool_type: string
  result_summary: string
  execution_time: number
  output: any
  status: string
  timestamp: Date
}

interface SearchResult {
  id: string
  name: string
  logo: string
  url: string
  source?: string
  date?: string
  number?: string
  title?: string
}

interface Chat {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
}

// 响应式数据
const sidebarOpen = ref(false)
const inputMessage = ref('')
const isLoading = ref(false)
const deepThinkMode = ref(false)
const webSearchMode = ref(false)
const currentChatId = ref<string | null>(null)
const messageInput = ref<HTMLTextAreaElement>()
const chatContainer = ref<HTMLElement>()
const showSearchPanel = ref(false)

// 聊天记录 - 使用响应式数组
const chats = reactive<Chat[]>([])

// 搜索结果数据
const currentSearchResults = ref<SearchResult[]>([])

// 消息更新函数 - 用于稳定地更新消息
const updateMessage = (chatId: string, messageId: string, updates: Partial<Message>) => {
  const chat = chats.find(c => c.id === chatId)
  if (chat) {
    const messageIndex = chat.messages.findIndex(m => m.id === messageId)
    if (messageIndex !== -1) {
      // 创建新的消息对象，保持响应式
      const updatedMessage = { ...chat.messages[messageIndex], ...updates }
      chat.messages[messageIndex] = updatedMessage
    }
  }
}

// WebSocket管理器
let wsManager: WebSocketManager | null = null

// 消息处理器
let messageHandler: MessageHandler | null = null

// 计算属性
const currentChat = computed(() => {
  return chats.find((chat: Chat) => chat.id === currentChatId.value) || null
})

const groupedHistory = computed(() => {
  const groups: Record<string, Chat[]> = {}
  
  chats.forEach((chat: Chat) => {
    const date = formatDate(chat.createdAt)
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(chat)
  })
  
  return groups
})

// 方法
const startNewChat = () => {
  const newChat: Chat = {
    id: Date.now().toString(),
    title: '新对话',
    messages: [],
    createdAt: new Date()
  }
  chats.unshift(newChat)
  currentChatId.value = newChat.id
  sidebarOpen.value = false
}

const loadChat = (chatId: string) => {
  currentChatId.value = chatId
  sidebarOpen.value = false
  nextTick(() => {
    scrollToBottom()
  })
}

const handleSendMessage = async () => {
  if (!inputMessage.value.trim()) return
  
  const userInput = inputMessage.value.trim()
  
  // 确保有当前聊天
  if (!currentChat.value) {
    startNewChat()
    // 等待下一个tick确保聊天已创建
    await nextTick()
  }
  
  // 创建用户消息 - 使用稳定的ID
  const userMessage: Message = {
    id: `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    role: 'user',
    content: userInput,
    timestamp: new Date()
  }
  
  // 添加用户消息
  currentChat.value!.messages.push(userMessage)
  
  // 更新聊天标题
  if (currentChat.value!.title === '新对话') {
    currentChat.value!.title = userInput.slice(0, 20) + (userInput.length > 20 ? '...' : '')
  }
  
  // 清空输入框并调整高度
  inputMessage.value = ''
  adjustTextarea()
  
  // 滚动到底部
  nextTick(() => {
    scrollToBottom()
  })
  
  // 显示加载动画
  isLoading.value = true
  
  // 创建AI消息用于流式输出 - 使用稳定的ID
  const aiMessage: Message = {
    id: `ai_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    role: 'assistant',
    content: '', // 初始为空，这样会显示动画
    timestamp: new Date(),
    isStreaming: true,
    toolResults: [],
    nodeResults: []
  }
  
  // 添加AI消息
  currentChat.value!.messages.push(aiMessage)
  
  // 滚动到底部
  nextTick(() => {
    scrollToBottom()
  })
  
  try {
    // 创建WebSocket管理器
    wsManager = new WebSocketManager(config.websocket.url, {
      onConnect: () => {
        console.log('🔗 MCP WebSocket连接成功')
        
        // 发送用户输入
        try {
          wsManager?.send({
            user_input: userInput,
            session_id: null  // 让服务端生成新的session_id
          })
        } catch (error) {
          updateMessage(currentChat.value!.id, aiMessage.id, {
            content: `❌ 发送消息失败: ${error}`,
            isStreaming: false
          })
          isLoading.value = false
        }
      },
      
      onModeDetection: (mode: string, sessionId: string, message: string) => {
        // 模式检测结果
        if (currentChat.value) {
          updateMessage(currentChat.value.id, aiMessage.id, {
            mode: mode as 'chat' | 'task',
            content: message,
            isStreaming: true
          })
        }
      },
      
      onChatResponse: (chatResponse: string, executionTime?: number) => {
        // 闲聊模式处理
        if (currentChat.value) {
          updateMessage(currentChat.value.id, aiMessage.id, {
            mode: 'chat',
            content: '',
            isStreaming: true,
            executionTime: executionTime
          })
          
          // 模拟流式输出效果
          let currentIndex = 0
          const streamInterval = setInterval(() => {
            if (currentIndex < chatResponse.length) {
              const currentContent = chatResponse.substring(0, currentIndex + 1)
              updateMessage(currentChat.value!.id, aiMessage.id, {
                content: currentContent,
                isStreaming: true
              })
              currentIndex++
              
              nextTick(() => {
                scrollToBottom()
              })
            } else {
              clearInterval(streamInterval)
              updateMessage(currentChat.value!.id, aiMessage.id, {
                content: chatResponse,
                isStreaming: false
              })
              isLoading.value = false
            }
          }, 30)
        }
      },
      
      onTaskStart: (message: string, asciiDiagram?: string) => {
        // 任务模式开始
        if (currentChat.value) {
          // 异步处理 Markdown 解析
          const processMarkdown = async () => {
            const parsedContent = await marked.parse(message)
            
            // 尝试从消息中解析执行计划
            let planData = null
            try {
              // 使用智能解析功能
              planData = executionPlanManager.parseExecutionPlan(message)
              
              console.log('📋 解析到的执行计划:', planData)
              
            } catch (error) {
              console.warn('执行计划解析失败:', error)
            }
            
            updateMessage(currentChat.value!.id, aiMessage.id, {
              mode: 'task',
              content: parsedContent,
              asciiDiagram: asciiDiagram,
              isStreaming: true,
              nodeResults: []
            })
            
            // 初始化动态执行计划
            if (planData) {
              await updateExecutionPlan(aiMessage.id, planData)
            } else if (asciiDiagram) {
              // 如果有 ASCII 图表但没有计划数据，使用原来的渲染方式
              await nextTick()
              setTimeout(() => {
              }, 100)
            }
          }
          
          processMarkdown()
        }
      },
      
      onToolStart: (message: string, toolName?: string) => {
        console.log('🔧 工具开始执行:', { toolName, message })
        
        // 工具开始执行
        if (currentChat.value) {
          const currentMessage = currentChat.value.messages.find(m => m.id === aiMessage.id)
          if (currentMessage) {
            // 确保nodeResults存在
            if (!currentMessage.nodeResults) {
              currentMessage.nodeResults = []
            }
            
            // 添加一个"正在执行"的步骤状态
            const runningStep = {
              tool_name: toolName || '工具',
              status: 'running',  // 改为running状态
              message: message,
              execution_time: 0,
              markdownContent: `### 🔄 ${toolName || '工具'}\n\n**状态**: 正在执行...\n**信息**: ${message}`
            }
            
            currentMessage.nodeResults.push(runningStep)
            
            // 更新执行计划图表 - 设置当前工具为运行状态
            console.log('📊 更新执行计划状态:', { toolName, state: 'running' })
            updateExecutionPlan(aiMessage.id, undefined, toolName || 'step1', 'running')
            
            // 强制触发Vue响应式更新
            updateMessage(currentChat.value.id, aiMessage.id, {
              nodeResults: [...currentMessage.nodeResults]
            })
            
            // 滚动到底部显示最新工具状态
            nextTick(() => {
              scrollToBottom()
            })
          }
        }
      },
      
      onToolResult: (stepData: any, asciiDiagram?: string) => {
        console.log('✅ 工具执行完成:', { stepData })
        
        // 工具执行结果
        if (currentChat.value) {
          const currentMessage = currentChat.value.messages.find(m => m.id === aiMessage.id)
          if (currentMessage && currentMessage.nodeResults) {
            // 查找是否有对应的running步骤需要更新
            const runningStepIndex = currentMessage.nodeResults.findIndex(
              step => step.tool_name === stepData.tool_name && step.status === 'running'
            )
            
            // 为步骤数据添加markdown内容
            const stepWithMarkdown = {
              ...stepData,
              markdownContent: `### ${stepData.status === 'success' ? '✅' : '❌'} ${stepData.tool_name}\n\n**状态**: ${stepData.status === 'success' ? '完成' : '失败'}\n**用时**: ${stepData.execution_time?.toFixed(2) || '0.00'}秒\n\n**执行结果**:\n\`\`\`json\n${JSON.stringify(stepData.output, null, 2)}\n\`\`\``
            }
            
            if (runningStepIndex !== -1) {
              // 更新现有的running步骤
              currentMessage.nodeResults[runningStepIndex] = stepWithMarkdown
            } else {
              // 没有找到对应的running步骤，直接添加
              currentMessage.nodeResults.push(stepWithMarkdown)
            }
            
            // 更新执行计划图表 - 设置工具执行状态
            const stepState = stepData.status === 'success' ? 'success' : 
                            stepData.status === 'error' ? 'error' : 'success'
            
            console.log('📊 更新工具完成状态:', { toolName: stepData.tool_name, stepState })
            updateExecutionPlan(aiMessage.id, undefined, stepData.tool_name, stepState)
            
            // 强制触发Vue响应式更新
              updateMessage(currentChat.value.id, aiMessage.id, {
                nodeResults: [...currentMessage.nodeResults]
              })
          }
        }
      },
      
      onTaskComplete: (message: string, executionTime?: number, asciiDiagram?: string, steps?: any[]) => {
        console.log('🏁 任务完成:', { message, executionTime, steps })
        
        // 任务完成
        if (currentChat.value) {
          const currentMessage = currentChat.value.messages.find(m => m.id === aiMessage.id)
          if (currentMessage) {
            // 异步处理 Markdown 解析
            const processMarkdown = async () => {
              const parsedResult = await marked.parse(message)
              const updates: any = {
                finalResult: parsedResult,
                executionTime: executionTime,
                isStreaming: false
              }
              
              // 如果有最终的ASCII图表，使用它
              if (asciiDiagram) {
                updates.asciiDiagram = asciiDiagram
              } else {
                // 处理后端传来的真实steps数据
                if (steps && steps.length > 0) {
                  console.log('📊 处理真实steps数据:', steps)
                  
                  // 首先初始化执行计划（使用真实的步骤数据）
                  const realPlan = { steps: steps }
                  console.log('🔄 初始化真实执行计划:', realPlan)
                  await updateExecutionPlan(aiMessage.id, realPlan)
                  
                  // 将所有步骤标记为成功
                  for (const step of steps) {
                    const toolName = step.tool_name || step.id
                    console.log('✅ 标记步骤完成:', toolName)
                    await updateExecutionPlan(aiMessage.id, undefined, toolName, 'success')
                  }
                  
                  // 生成最终的ASCII图表
                  const finalDiagram = executionPlanManager.generateAsciiDiagram()
                  console.log('📋 生成最终ASCII图表:', finalDiagram)
                  updates.asciiDiagram = finalDiagram
                } else {
                  // 如果没有steps数据，生成简单的完成图表
                  const completedDiagram = `    👤 用户输入
         │
         ▼
    🧠 LLM分析
         │
         ▼
    ✅ 任务完成`
                  
                  updates.asciiDiagram = completedDiagram
                }
              }
              
              // 更新消息
              updateMessage(currentChat.value!.id, aiMessage.id, updates)
              
              // 滚动到底部
              nextTick(() => {
                scrollToBottom()
              })
            }
            
            processMarkdown()
          }
        }
        
        isLoading.value = false
      },
      
      onError: (message: string, iteration?: number) => {
        let errorMessage = `❌ 执行错误: ${message}`
        if (iteration) {
          errorMessage += ` (迭代 ${iteration})`
        }
        
        updateMessage(currentChat.value!.id, aiMessage.id, {
          content: errorMessage,
          isStreaming: false
        })
        isLoading.value = false
      },
      
      onDisconnect: (code, reason) => {
        console.log('🔌 MCP WebSocket连接关闭:', code, reason)
        isLoading.value = false
      }
    })
    
    // 连接WebSocket
    await wsManager.connect()
    
  } catch (error) {
    console.error('发送消息失败:', error)
    aiMessage.content = `❌ 连接失败: ${error instanceof Error ? error.message : String(error)}`
    aiMessage.isStreaming = false
    isLoading.value = false
  }
}

const adjustTextarea = () => {
  if (messageInput.value) {
    messageInput.value.style.height = 'auto'
    messageInput.value.style.height = Math.min(messageInput.value.scrollHeight, 120) + 'px'
  }
}

const scrollToBottom = () => {
  if (chatContainer.value) {
    chatContainer.value.scrollTo({
      top: chatContainer.value.scrollHeight,
      behavior: 'smooth'
    })
  }
}

const formatTime = (date: Date) => {
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const formatDate = (date: Date) => {
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  
  if (date.toDateString() === today.toDateString()) {
    return '今天'
  } else if (date.toDateString() === yesterday.toDateString()) {
    return '昨天'
  } else {
    return date.toLocaleDateString('zh-CN', { 
      month: '2-digit', 
      day: '2-digit' 
    })
  }
}

const toggleSearchPanel = () => {
  showSearchPanel.value = !showSearchPanel.value
}

// 解析 Markdown 内容
const parseMarkdown = async (markdown: string) => {
  if (!markdown) return ''
  try {
    return await marked.parse(markdown)
  } catch (error) {
    console.error('Markdown parsing error:', error)
    return markdown
  }
}

// 文件上传处理函数
const handleFileUpload = () => {
  // 创建文件输入元素
  const fileInput = document.createElement('input')
  fileInput.type = 'file'
  fileInput.multiple = true
  fileInput.accept = '.txt,.md,.js,.ts,.py,.java,.cpp,.c,.html,.css,.json,.xml,.csv,.pdf,.doc,.docx'
  
  fileInput.onchange = (event) => {
    const files = (event.target as HTMLInputElement).files
    if (files && files.length > 0) {
      // 处理文件上传
      console.log('文件上传:', files)
      // 这里可以添加文件处理逻辑
      alert(`已选择 ${files.length} 个文件`)
    }
  }
  
  fileInput.click()
}

// 初始化
onMounted(() => {
  // 默认创建第一个聊天
  if (chats.length === 0) {
    startNewChat()
  }
})

onUnmounted(() => {
  // 清理WebSocket连接
  if (wsManager) {
    wsManager.disconnect()
    wsManager = null
  }
  
  // 清理消息处理器
  if (messageHandler) {
    messageHandler = null
  }
})
</script>

<style scoped>
/* 消息过渡动画 - 优化闪烁问题 */
.message-enter-active,
.message-leave-active {
  transition: all 0.3s ease;
}

.message-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.message-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.message-move {
  transition: transform 0.3s ease;
}

/* 消息容器 */
.messages-container {
  max-width: 1000px; /* 保持最大宽度 */
  margin-left: auto; /* 向右推 */
  margin-right: 20px; /* 与右边缘对齐，假设距离屏幕边缘20px */
  width: 100%;
  padding: 0; /* 移除内部内边距，让消息内容处理 */
  /* 确保容器与右侧边界对齐 */
  box-sizing: border-box;
}

/* 消息列表优化 */
.messages-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 0 20px -5px; /* 向左移动5个像素 */
  overflow-y: auto;
  scroll-behavior: smooth;
  width: 100%;
  /* 确保列表充分利用容器宽度 */
  box-sizing: border-box;
}

/* 消息包装器优化 - 防止闪烁 */
.message-wrapper {
  will-change: transform, opacity;
  transform: translateZ(0);
  backface-visibility: hidden;
  contain: layout style paint;
  /* 添加稳定的布局 */
  min-height: 36px;
  width: 100%;
  margin-bottom: 24px;
  /* 确保包装器充分利用宽度 */
  box-sizing: border-box;
}

/* 消息样式优化 */
.message {
  display: flex;
  gap: 12px;
  min-height: 36px; /* 确保最小高度，防止布局跳动 */
  /* 添加稳定的布局 */
  align-items: flex-start;
  margin-bottom: 24px;
  width: 100%; /* 确保消息占满容器宽度 */
}

/* AI消息样式 - 左侧显示 */
.ai-message {
  justify-content: flex-start;
  /* 确保AI消息能够充分利用空间 */
  width: 100%;
}

/* 用户消息样式 - 右侧显示 */
.user-message {
  justify-content: flex-end;
  /* 确保用户消息右对齐 */
  width: 100%;
}

.message-avatar {
  flex-shrink: 0;
  width: 36px; /* 固定宽度，防止布局跳动 */
  height: 36px; /* 固定高度，防止布局跳动 */
}

.user-avatar,
.ai-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  /* 防止头像闪烁 */
  flex-shrink: 0;
}

.user-avatar {
  background: #e0e7ff; /* 更浅的颜色 */
}

.ai-avatar {
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe); /* 更浅的颜色 */
  color: #4f46e5; /* 深色文字 */
}

.message-content {
  flex: 1;
  min-width: 0;
  /* 确保内容区域稳定 */
  display: flex;
  flex-direction: column;
  /* 防止内容区域跳动 */
  min-height: 20px;
  max-width: 70%;
}

.message-content.user-no-avatar {
  margin-left: 0;
  padding-left: 0;
}

/* AI消息内容 - 左对齐 */
.ai-message .message-content {
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
  max-width: 95%; /* 进一步增加AI消息最大宽度 */
  /* margin-left: 12px; /* 移除左边距，依靠gap属性控制头像和内容间距 */
}

/* 用户消息内容 - 右对齐 */
.user-message .message-content {
  display: flex;
  justify-content: flex-end;
  align-items: flex-end;
  max-width: 70%; /* 保持用户消息的宽度 */
}

.user-message .message-text {
  background: #4f46e5;
  color: white;
  padding: 12px 16px;
  border-radius: 18px 18px 4px 18px;
  max-width: 100%;
  word-wrap: break-word;
  /* 防止文本变化时的布局跳动 */
  min-height: 20px;
  line-height: 1.5;
  white-space: pre-wrap;
  /* 添加稳定的布局 */
  display: inline-block;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.ai-message .message-text {
  background: white;
  color: #1e293b;
  padding: 16px;
  border-radius: 4px 18px 18px 18px;
  /* border: 1px solid #e2e8f0; 移除边框 */
  white-space: pre-wrap;
  line-height: 1.6;
  /* 防止文本变化时的布局跳动 */
  min-height: 20px;
  word-wrap: break-word;
  /* 添加稳定的布局 */
  display: inline-block;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); /* 调整阴影效果 */
  width: 100%; /* 让AI消息文本占满整个内容区域 */
  /* 优化长文本显示 */
  text-align: left;
  font-size: 14px;
  /* 移除右侧的蓝色边框 */
  border-right: none;
  /* 确保与右侧边界对齐 */
  max-width: none;
}

/* 优化AI消息中的列表和格式化内容 */
.ai-message .message-text ul,
.ai-message .message-text ol {
  margin: 8px 0;
  padding-left: 20px;
}

.ai-message .message-text li {
  margin: 4px 0;
  line-height: 1.5;
}

.ai-message .message-text h1,
.ai-message .message-text h2,
.ai-message .message-text h3,
.ai-message .message-text h4 {
  margin: 16px 0 8px 0;
  font-weight: 600;
  color: #1e293b;
}

.ai-message .message-text p {
  margin: 8px 0;
  line-height: 1.6;
}

/* 打字动画优化 */
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 修复打字指示器样式 */
.typing-indicator {
  animation: blink 1s infinite;
  font-weight: bold;
  color: #4f46e5;
  display: inline-block;
  width: 2px;
  height: 1.2em;
  background-color: #4f46e5;
  margin-left: 2px;
  vertical-align: middle;
  /* 防止指示器导致布局跳动 */
  flex-shrink: 0;
}

/* 移除streaming状态的右侧边框 */
.message-text.streaming {
  border-right: none !important; /* 移除蓝色竖线 */
  animation: none; /* 移除闪烁动画，使用更平滑的指示器 */
}

/* 加载动画优化 */
.typing-animation {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 16px;
  /* 防止动画导致布局跳动 */
  min-height: 20px;
  /* 确保动画与AI消息内容区域对齐 */
  width: 100%;
  background: white;
  /* border: 1px solid #e2e8f0; 移除边框 */
  border-radius: 4px 18px 18px 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); /* 调整阴影效果 */
  /* 确保动画显示在头像右侧 */
  margin-left: 0;
}

.typing-animation span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4f46e5;
  animation: typing 1.4s infinite ease-in-out;
  /* 防止动画元素导致布局跳动 */
  flex-shrink: 0;
}

.typing-animation span:nth-child(1) { animation-delay: -0.32s; }
.typing-animation span:nth-child(2) { animation-delay: -0.16s; }
.typing-animation span:nth-child(3) { animation-delay: 0s; }

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.app {
  display: flex;
  height: 100vh;
  background: #f8fafc;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 侧边栏样式 */
.sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe); /* 更浅的颜色 */
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  /* 去掉外围圆圈效果 */
  border: none;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.new-chat-btn {
  width: 100%;
  padding: 12px 16px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.new-chat-btn:hover {
  background: #4338ca;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.history-group {
  margin-bottom: 24px;
}

.history-date {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 8px;
  padding: 0 8px;
}

.history-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}

.history-item:hover {
  background: #f1f5f9;
}

.history-item.active {
  background: #e0e7ff;
  border-left: 3px solid #4f46e5;
}

.history-title {
  font-size: 14px;
  color: #1e293b;
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-time {
  font-size: 12px;
  color: #64748b;
}

/* 主内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: margin-right 0.3s ease-in-out;
  /* 确保主内容区域占满剩余空间 */
  height: 100vh;
  overflow: hidden;
}

.main-content.search-panel-open {
  margin-right: 350px;
}

.chat-header {
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 16px;
  /* 确保头部固定在顶部 */
  flex-shrink: 0;
}

.sidebar-toggle {
  display: none;
  background: none;
  border: none;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  color: #64748b;
}

.sidebar-toggle:hover {
  background: #f1f5f9;
}

.chat-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  /* 确保聊天容器可以滚动 */
  min-height: 0;
}

/* 欢迎界面 */
.welcome-screen {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: 0 24px;
  padding-top: 15%;
}

.welcome-content {
  max-width: 600px;
  width: 100%;
}

.welcome-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
  text-align: center;
}

.welcome-main {
  display: flex;
  align-items: center;
  gap: 20px;
  justify-content: center;
}

.welcome-avatar {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe); /* 更浅的颜色 */
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.1); /* 更浅的阴影 */
  /* 去掉外围圆圈效果 */
  border: none;
}

.welcome-avatar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.1) 50%, transparent 70%);
  animation: shimmer 3s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% {
    transform: translateX(-100%);
  }
  50% {
    transform: translateX(100%);
  }
}

.welcome-title {
  font-size: 24px;
  font-weight: 600;
  color: #1a202c;
  line-height: 1.3;
  letter-spacing: -0.01em;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  margin: 0;
}

.welcome-subtitle {
  font-size: 14px;
  color: #374151;
  line-height: 1.5;
  font-weight: 400;
  max-width: 800px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  opacity: 0.9;
  margin: 0;
  white-space: nowrap;
}

/* 消息容器 */
.messages-container {
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

/* 消息列表优化 */
.messages-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  overflow-y: auto;
  scroll-behavior: smooth;
  width: 100%;
}

/* 消息包装器优化 - 防止闪烁 */
.message-wrapper {
  will-change: transform, opacity;
  transform: translateZ(0);
  backface-visibility: hidden;
  contain: layout style paint;
  /* 添加稳定的布局 */
  min-height: 36px;
  width: 100%;
  margin-bottom: 24px;
}

.message-time {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 8px;
  text-align: right;
}

.ai-message .message-time {
  text-align: left;
}

/* 搜索结果样式 */
.search-results {
  margin-top: 16px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.search-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #64748b;
  margin-bottom: 12px;
  cursor: pointer;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 8px;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.search-header:hover {
  background: #f1f5f9;
  border-color: #e2e8f0;
  color: #4f46e5;
}

.search-header:active {
  transform: scale(0.98);
}

.search-toggle-icon {
  transition: transform 0.2s ease;
  font-weight: bold;
  color: #64748b;
}

.search-toggle-icon.open {
  transform: rotate(90deg);
  color: #4f46e5;
}

.search-sites {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.search-site {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  font-size: 12px;
  color: #64748b;
}

.site-logo {
  width: 14px;
  height: 14px;
  border-radius: 2px;
  flex-shrink: 0;
}

/* 工具执行结果样式 */
.tool-results {
  margin-top: 16px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.tool-results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}

.tool-results-title {
  font-weight: 600;
  color: #1e293b;
  font-size: 14px;
}

.tool-results-count {
  font-size: 12px;
  color: #64748b;
  background: #e2e8f0;
  padding: 2px 8px;
  border-radius: 12px;
}

.tool-result-item {
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}

.tool-result-item:last-child {
  border-bottom: none;
}

.tool-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.tool-result-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-result-type {
  font-weight: 600;
  color: #1e293b;
  font-size: 13px;
  background: #e0e7ff;
  padding: 2px 8px;
  border-radius: 6px;
}

.tool-result-time {
  font-size: 12px;
  color: #64748b;
}

.tool-result-status {
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  text-transform: uppercase;
}

.tool-result-status.success {
  background-color: #dcfce7;
  color: #166534;
}

.tool-result-status.error {
  background-color: #fef2f2;
  color: #dc2626;
}

.tool-result-summary {
  font-size: 13px;
  color: #374151;
  line-height: 1.5;
  margin-bottom: 8px;
}

.tool-result-output {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 10px;
  font-size: 12px;
  color: #1e293b;
  line-height: 1.6;
  margin-top: 8px;
}

.tool-result-output-header {
  font-weight: 600;
  margin-bottom: 6px;
  color: #4f46e5;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tool-result-output-content {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: #ffffff;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  max-height: 200px;
  overflow-y: auto;
}

/* 输入区域样式 - 完全按照DeepSeek设计 */
.input-container {
  padding: 24px;
  background: white;
  border-top: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  /* 确保输入框始终在底部 */
  position: relative;
  bottom: 0;
  left: 0;
  right: 0;
  /* 确保输入容器固定在底部 */
  flex-shrink: 0;
  z-index: 10;
}

.input-container.centered {
  /* 新对话页面居中显示 */
  position: absolute;
  bottom: 20%;
  left: 50%;
  transform: translate(-50%, 0);
  width: calc(100% - 48px);
  max-width: 800px; /* 增加最大宽度 */
  border: none;
  border-radius: 0;
  box-shadow: none;
  background: transparent;
}

.input-wrapper {
  max-width: 900px; /* 增加最大宽度 */
  margin: 0 auto;
}

.input-box {
  display: flex;
  flex-direction: column;
  background: #ffffff; /* 纯白色背景 */
  border: 1px solid #e5e7eb; /* 更浅的边框 */
  border-radius: 12px;
  transition: border-color 0.2s;
  min-height: 120px;
  padding: 16px;
}

.input-box:focus-within {
  border-color: #6366f1; /* 深紫色边框 */
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.input-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.input-tools {
  display: flex;
  gap: 8px;
  margin-bottom: 0;
}

.tool-btn {
  padding: 6px 12px;
  background: #f9fafb; /* 更浅的背景 */
  border: 1px solid #e5e7eb; /* 更浅的边框 */
  border-radius: 20px;
  font-size: 13px;
  color: #6b7280; /* 中灰色文字 */
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.tool-btn:hover {
  background: #f3f4f6; /* 更浅的悬停背景 */
}

.tool-btn.active {
  background: #6366f1; /* 深紫色背景 */
  color: white;
  border-color: #6366f1;
}

.message-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  color: #1e293b;
  min-height: 24px;
  max-height: 200px;
  font-family: inherit;
  padding: 0;
}

.message-input::placeholder {
  color: #9ca3af; /* 更浅的占位符文字 */
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.attach-btn,
.send-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 16px;
}

.attach-btn {
  background: none;
  color: #6b7280; /* 中灰色 */
  font-size: 18px;
}

.attach-btn:hover {
  background: #f3f4f6; /* 更浅的悬停背景 */
  color: #6366f1; /* 深紫色 */
}

.send-btn {
  background: #6366f1; /* 深紫色背景 */
  color: white;
}

.send-btn:hover:not(:disabled) {
  background: #5855eb; /* 稍深的紫色 */
}

.send-btn:disabled {
  background: #d1d5db; /* 更浅的禁用背景 */
  cursor: not-allowed;
}

.input-footer {
  text-align: center;
  margin-top: 12px;
}

.footer-text {
  font-size: 12px;
  color: #9ca3af; /* 更浅的底部文字 */
}

/* 欢迎界面样式 - 完全按照DeepSeek设计 */
.welcome-screen {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: 0 24px;
  background: #f8fafc; /* 浅灰色背景 */
}

.welcome-content {
  max-width: 800px;
  width: 100%;
}

.welcome-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-bottom: 60px;
  text-align: center;
}

.welcome-main {
  display: flex;
  align-items: center;
  gap: 16px;
  justify-content: center;
}

.welcome-avatar {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6); /* 深紫色背景 */
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
  border: none;
}

.welcome-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937; /* 深灰色文字 */
  line-height: 1.3;
  letter-spacing: -0.01em;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  margin: 0;
}

.welcome-subtitle {
  font-size: 16px;
  color: #6b7280; /* 中灰色文字 */
  line-height: 1.5;
  font-weight: 400;
  max-width: 500px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  margin: 0;
}

/* 右侧搜索面板样式 */
.search-panel {
  position: fixed;
  top: 0;
  right: -350px;
  width: 350px;
  height: 100vh;
  background: white;
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
  transition: right 0.3s ease-in-out;
  z-index: 100;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 20px;
  box-sizing: border-box;
}

.search-panel-open {
  right: 0;
}

.search-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e2e8f0;
}

.search-panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.search-panel-close {
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  color: #64748b;
}

.search-panel-close:hover {
  color: #4f46e5;
}

.search-panel-content {
  flex: 1;
}

.search-result-item {
  padding: 15px 0;
  border-bottom: 1px solid #f1f5f9;
}

.search-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
  color: #64748b;
}

.search-result-source {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-result-logo {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  flex-shrink: 0;
}

.search-result-source-name {
  font-weight: 500;
  color: #1e293b;
}

.search-result-date {
  font-weight: 400;
}

.search-result-number {
  font-size: 14px;
  font-weight: 600;
  color: #4f46e5;
}

.search-result-title {
  font-size: 15px;
  font-weight: 500;
  color: #1e293b;
  line-height: 1.4;
  margin-bottom: 4px;
}

/* 移动端样式 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    z-index: 1000;
    transform: translateX(-100%);
  }
  
  .sidebar-open {
    transform: translateX(0);
  }
  
  .sidebar-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 999;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
  }
  
  .sidebar-overlay.active {
    opacity: 1;
    visibility: visible;
  }
  
  .sidebar-toggle {
    display: flex;
  }
  
  .chat-container {
    padding: 12px;
  }
  
  .input-container {
    padding: 12px;
  }
  
  .input-container.centered {
    width: calc(100% - 24px);
    bottom: 25%;
    max-width: none;
  }
  
  /* 移动端消息样式优化 */
  .message-content {
    max-width: 100% !important;
  }
  
  .ai-message .message-content {
    max-width: 100% !important;
    margin-left: 0;
  }
  
  .user-message .message-content {
    max-width: 85% !important;
  }
  
  .user-message .message-text {
    max-width: 100%;
    padding: 10px 12px;
    font-size: 14px;
  }
  
  .ai-message .message-text {
    max-width: 100%;
    padding: 12px 14px;
    font-size: 14px;
    line-height: 1.5;
  }
  
  /* 移动端容器优化 */
  .messages-container {
    max-width: 100%;
    padding: 0 8px;
    margin: 0;
  }
  
  /* 移动端消息列表优化 */
  .messages-list {
    padding: 16px 0;
    gap: 12px;
  }
  
  .ai-message .message-content {
    max-width: 100% !important;
    margin-left: 0;
  }
  
  .input-tools {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .tool-btn {
    padding: 6px 10px;
    font-size: 12px;
  }
  
  .welcome-screen {
    padding: 0 16px;
    padding-top: 15%;
  }
  
  .welcome-header {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
  
  .welcome-main {
    flex-direction: column;
    gap: 8px;
  }
  
  .welcome-title {
    font-size: 18px;
    line-height: 1.3;
  }
  
  .welcome-subtitle {
    font-size: 13px;
    white-space: nowrap;
    max-width: 100%;
    line-height: 1.4;
  }
  
  .welcome-avatar {
    width: 44px;
    height: 44px;
    font-size: 16px;
  }

  .main-content.search-panel-open {
    margin-right: 0;
  }

  .search-panel {
    width: 100%;
    right: -100%;
    top: 0;
    height: 100vh;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  }

  .search-panel-open {
    right: 0;
  }
  
  /* 移动端输入框优化 */
  .input-wrapper {
    max-width: 100%;
    width: 100%;
  }
  
  .input-box {
    min-height: 100px;
    padding: 12px;
  }
  
  .message-input {
    font-size: 14px;
  }
  
  .input-bottom {
    margin-top: 10px;
    padding-top: 10px;
    gap: 8px;
  }
  
  .input-actions {
    gap: 6px;
  }
  
  .attach-btn,
  .send-btn {
    width: 32px;
    height: 32px;
    font-size: 16px;
  }
  
  /* 移动端头部优化 */
  .chat-header {
    padding: 12px 16px;
    gap: 12px;
  }
  
  .chat-title {
    font-size: 16px;
    flex: 1;
    text-align: center;
  }
  
  /* 移动端底部文字优化 */
  .footer-text {
    font-size: 11px;
    padding: 0 8px;
  }
}

/* 滚动条样式 */
.chat-history::-webkit-scrollbar,
.chat-container::-webkit-scrollbar {
  width: 6px;
}

.chat-history::-webkit-scrollbar-track,
.chat-container::-webkit-scrollbar-track {
  background: transparent;
}

.chat-history::-webkit-scrollbar-thumb,
.chat-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.chat-history::-webkit-scrollbar-thumb:hover,
.chat-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 新增：闲聊模式样式 */
.chat-message-content {
  width: 100%;
}

.chat-message-content .message-text {
  background: white;
  color: #1e293b;
  padding: 16px;
  border-radius: 4px 18px 18px 18px;
  white-space: pre-wrap;
  line-height: 1.6;
  min-height: 20px;
  word-wrap: break-word;
  display: inline-block;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  width: 100%;
  font-size: 14px;
  border-right: none;
  max-width: none;
  font-weight: 400;
}

.chat-message-content .message-text.streaming {
  background: white;
  color: #1e293b;
}

.execution-time {
  margin-top: 8px;
  font-size: 12px;
  color: #64748b;
  text-align: right;
  opacity: 0.8;
}

/* 新增：任务模式样式 */
.task-message-content {
  width: 100%;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  /* overflow: hidden; */ /* REMOVED: This was the primary cause of clipping */
}

.task-header {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  color: white;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
}

.task-icon {
  font-size: 16px;
}

.task-title {
  flex: 1;
}

/* 闲聊头部样式 */
.chat-header {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #f8fafc;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
}

.chat-icon {
  font-size: 16px;
  color: #ffffff;
}

.chat-title {
  flex: 1;
  color: #f8fafc;
}

/* 新增：Markdown 内容样式 */
.markdown-content {
  padding: 16px;
  background: white;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  margin: 16px 0 8px 0;
  color: #2d3748;
  font-weight: 600;
}

.markdown-content h1 { font-size: 1.5em; }
.markdown-content h2 { font-size: 1.3em; }
.markdown-content h3 { font-size: 1.1em; }

.markdown-content p {
  margin: 8px 0;
  line-height: 1.6;
  color: #374151;
}

.markdown-content code {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 0.9em;
  color: #e53e3e;
}

.markdown-content pre {
  background: #f8fafc;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
  border: 1px solid #e2e8f0;
}

.markdown-content pre code {
  background: none;
  padding: 0;
  color: #1e293b;
}

.markdown-content blockquote {
  border-left: 4px solid #667eea;
  padding-left: 16px;
  color: #4a5568;
  font-style: italic;
  margin: 12px 0;
}

.markdown-content ul,
.markdown-content ol {
  margin: 8px 0;
  padding-left: 20px;
}

.markdown-content li {
  margin: 4px 0;
  line-height: 1.5;
}

.markdown-content strong {
  font-weight: 600;
  color: #1e293b;
}

.markdown-content em {
  font-style: italic;
}


.mermaid-diagram {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.mermaid-diagram svg {
  max-width: 90%;
  height: auto;
  display: block;
  margin: 0 auto;
}

/* 动态执行计划动画效果 */
.mermaid-diagram svg g.node[data-state="running"] {
  animation: pulse 2s infinite;
}

.mermaid-diagram svg g.node[data-state="pending"] {
  opacity: 0.7;
}

.mermaid-diagram svg g.node[data-state="success"] {
  animation: bounceIn 0.6s ease-out forwards;
}

.mermaid-diagram svg g.node[data-state="error"] {
  animation: shake 0.6s ease-in-out 3;
}

/* 确保图表在容器中居中 */
.mermaid-diagram > div {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 新增：边连接线的动画效果 */
.mermaid-diagram svg g.edgePath path {
  transition: all 0.3s ease;
}

/* 虚线流动动画 - 用于正在执行和待执行的连接线 */
.mermaid-diagram svg g.edgePath path[stroke-dasharray] {
  stroke-dasharray: 8 4 !important;
  animation: dashFlow 2s linear infinite !important;
}

/* 实线连接 - 用于已完成的连接 */
.mermaid-diagram svg g.edgePath path:not([stroke-dasharray]) {
  stroke-width: 2px;
  opacity: 1;
}

/* 连接线标签样式增强 */
.mermaid-diagram svg .edgeLabel,
.mermaid-diagram svg .edgeLabel rect {
  background: rgba(255, 255, 255, 0.95) !important;
  fill: rgba(255, 255, 255, 0.95) !important;
  border-radius: 4px;
  font-size: 11px !important;
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.mermaid-diagram svg .edgeLabel text {
  font-size: 11px !important;
  font-weight: 500 !important;
  fill: #374151 !important;
}

/* 节点文本增强 */
.mermaid-diagram svg .node rect,
.mermaid-diagram svg .node circle,
.mermaid-diagram svg .node polygon {
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
  transition: all 0.3s ease;
}

.mermaid-diagram svg .node text {
  font-weight: 500 !important;
  font-size: 13px !important;
}

/* 新增：流动动画效果 */
@keyframes dashFlow {
  0% {
    stroke-dashoffset: 0;
  }
  100% {
    stroke-dashoffset: -16;
  }
}

/* 新增：反向流动动画 - 用于工具处理反馈 */
@keyframes dashFlowReverse {
  0% {
    stroke-dashoffset: 0;
  }
  100% {
    stroke-dashoffset: 16;
  }
}

/* 新增：LLM节点脉冲动画 */
@keyframes llmPulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.02);
    opacity: 0.95;
  }
}

/* 新增：渐入动画 */
@keyframes fadeIn {
  0% {
    opacity: 0;
    transform: scale(0.9);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

/* 新增：实线脉冲效果 */
@keyframes solidPulse {
  0%, 100% {
    opacity: 1;
    stroke-width: 2px;
  }
  50% {
    opacity: 0.8;
    stroke-width: 3px;
  }
}

/* 脉冲动画 - 用于正在执行的步骤 */
@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.9;
  }
}

/* 弹入动画 - 用于成功完成的步骤 */
@keyframes bounceIn {
  0% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  60% {
    transform: scale(1.05);
    opacity: 0.9;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 摇晃动画 - 用于失败的步骤 */
@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  10%, 30%, 50%, 70%, 90% {
    transform: translateX(-3px);
  }
  20%, 40%, 60%, 80% {
    transform: translateX(3px);
  }
}

/* 虚线边框动画 - 用于正在执行的连接线 */
@keyframes dash {
  to {
    stroke-dashoffset: -10;
  }
}

/* Mermaid图表内的执行状态指示器 */
.mermaid-diagram svg .edgePath.running {
  animation: dash 1s linear infinite;
}

/* 执行计划标题样式 */
.execution-plan-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 600;
  font-size: 14px;
  border-radius: 8px 8px 0 0;
  margin-bottom: 0;
}

.execution-plan-icon {
  font-size: 16px;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 新增：节点执行结果样式 */
.node-results {
  border-top: 1px solid #e2e8f0;
  background: white;
}

.node-result-item {
  padding: 16px;
  border-bottom: 1px solid #f1f5f9;
  background: #fafbfc;
  margin: 8px 0;
  border-radius: 8px;
  border-left: 4px solid #4f46e5;
}

.node-result-item:last-child {
  border-bottom: none;
}

.node-result-markdown {
  font-size: 14px;
  line-height: 1.6;
  color: #374151;
}

.node-result-markdown h3 {
  color: #1e293b;
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-result-markdown p {
  margin: 8px 0;
}

.node-result-markdown strong {
  color: #1e293b;
  font-weight: 600;
}

.node-result-markdown code {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  color: #e53e3e;
}

.node-result-markdown pre {
  background: #f8fafc;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
  border: 1px solid #e2e8f0;
}

.node-result-markdown pre code {
  background: none;
  padding: 0;
  color: #1e293b;
}

.node-result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

/* 新增：最终结果样式 */
.final-result {
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  margin-top: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.final-result h1,
.final-result h2,
.final-result h3,
.final-result h4,
.final-result h5,
.final-result h6 {
  color: white;
  margin: 16px 0 12px 0;
  font-weight: 600;
}

.final-result h2 {
  font-size: 1.5em;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.final-result h3 {
  font-size: 1.2em;
  margin: 20px 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.final-result p {
  margin: 8px 0;
  line-height: 1.6;
}

.final-result strong {
  color: #f8fafc;
  font-weight: 600;
}

.final-result code {
  background: rgba(255, 255, 255, 0.2);
  color: #f8fafc;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', monospace;
}

.final-result pre {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #f8fafc;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.final-result ul,
.final-result ol {
  margin: 12px 0;
  padding-left: 20px;
}

.final-result li {
  margin: 6px 0;
  line-height: 1.5;
}

.final-result a {
  color: #bfdbfe;
  text-decoration: underline;
}

.final-result a:hover {
  color: #dbeafe;
}

/* 搜索结果特殊样式 */
.final-result .search-result-item {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  margin: 8px 0;
  border-left: 4px solid rgba(255, 255, 255, 0.3);
}

.final-result .search-result-title {
  font-weight: 600;
  font-size: 1.1em;
  margin-bottom: 4px;
}

.final-result .search-result-url {
  font-size: 0.9em;
  opacity: 0.8;
  margin-bottom: 6px;
}

.final-result .search-result-snippet {
  font-size: 0.95em;
  line-height: 1.4;
  opacity: 0.9;
}

/* Critical Fix: Allow task messages to use the full width */
.message.has-task .message-content {
  max-width: 100%;
}

/* 新增：任务进度指示器 */
.task-progress {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 8px;
  border-radius: 12px;
  font-weight: 500;
}

/* 新增：任务初始化内容 */
.task-init-content {
  padding: 16px;
  background: #f8fafc;
  border-radius: 0 0 8px 8px;
}

/* 简化的动画效果 */
.mermaid-diagram svg .node {
  transition: transform 0.2s ease;
}

.mermaid-diagram svg .node:hover {
  transform: scale(1.05);
}

/* 任务进度指示器 */
.task-progress {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 8px;
  border-radius: 12px;
  font-weight: 500;
}

/* 任务初始化内容 */
.task-init-content {
  padding: 16px;
  background: #f8fafc;
  border-radius: 0 0 8px 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    z-index: 1000;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  .sidebar.mobile-open {
    transform: translateX(0);
  }
  
  .main-content {
    margin-left: 0;
    width: 100%;
  }
  
  .mobile-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 999;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
  }
  
  .mobile-overlay.show {
    opacity: 1;
    visibility: visible;
  }
  
  .search-panel {
    width: 90%;
    left: 5%;
  }
}

/* Markdown 链接样式 */
.markdown-link {
  color: #3b82f6;
  text-decoration: none;
  transition: all 0.2s ease;
  font-weight: 500;
  border-radius: 4px;
  padding: 2px 4px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.markdown-link:hover {
  color: #1d4ed8;
  background-color: rgba(59, 130, 246, 0.1);
  text-decoration: underline;
}

/* 下载链接特殊样式 */
.download-link {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 8px 12px;
  margin: 4px 2px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #374151;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.download-link:hover {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #3b82f6;
  color: #1d4ed8;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
  text-decoration: none;
}

.download-link:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.2);
}

/* 为下载链接添加下载图标 */
.download-link::after {
  content: "⬇️";
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.download-link:hover::after {
  opacity: 1;
}

/* 确保链接在消息中的布局 */
.final-result .markdown-link,
.message-text .markdown-link {
  margin: 2px 0;
}

/* 文件列表中的下载链接 */
.final-result .download-link {
  margin: 4px 0;
  width: auto;
  max-width: 100%;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .download-link {
    max-width: 250px;
    padding: 6px 10px;
    font-size: 14px;
  }
}

/* ASCII 流程图显示 - 增强动态效果 */
.ascii-container {
  width: 100%;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  padding: 20px;
  margin: 16px 0;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.ascii-container:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.ascii-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}

.ascii-icon {
  font-size: 18px;
  color: #4f46e5;
  animation: pulse 2s infinite;
}

.ascii-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.ascii-diagram {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  position: relative;
}

.ascii-diagram pre {
  margin: 0;
  padding: 0;
  font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.8;
  color: #374151;
  white-space: pre;
  overflow-x: auto;
  font-feature-settings: "liga" 0;
  font-variant-ligatures: none;
  
  /* 为动态内容添加动画 */
  animation: fadeInUp 0.5s ease-out;
}

/* 动画效果定义 */
@keyframes fadeInUp {
  0% {
    opacity: 0;
    transform: translateY(10px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

@keyframes flowingDots {
  0% {
    opacity: 0.3;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0.3;
  }
}

@keyframes statusBlink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

/* 为特定Unicode字符添加动画效果 */
.ascii-diagram pre {
  /* 设置基础样式，允许内容动态更新 */
  transition: all 0.3s ease;
}

/* 当图表内容更新时的过渡效果 */
.ascii-diagram[data-updating="true"] pre {
  opacity: 0.7;
  transform: scale(0.98);
}

.ascii-diagram[data-updating="false"] pre {
  opacity: 1;
  transform: scale(1);
}

/* 响应式设计增强 */
@media (max-width: 768px) {
  .ascii-diagram pre {
    font-size: 12px;
    line-height: 1.6;
  }
  
  .ascii-container {
    padding: 16px;
    margin: 12px 0;
  }
  
  .ascii-header {
    margin-bottom: 12px;
  }
}

/* 为状态指示器添加特殊样式 */
.ascii-diagram pre {
  /* 确保emoji和Unicode符号正确显示 */
  font-variant-emoji: emoji;
}

/* 添加悬停交互效果 */
.ascii-container:hover .ascii-diagram {
  border-color: #c7d2fe;
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.1);
}
</style>