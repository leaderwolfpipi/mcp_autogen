export interface MessageState {
  content: string
  isStreaming: boolean
  isLoading: boolean
  hasError: boolean
  progressSteps: string[]
  isChatMode: boolean  // 标识是否为闲聊模式
  isTaskMode: boolean  // 新增：标识是否为任务模式
  mermaidDiagram?: string  // 新增：Mermaid 流程图
  nodeResults: any[]  // 新增：节点执行结果
}

export class MessageHandler {
  private state: MessageState
  private updateCallback: (state: MessageState) => void
  private scrollCallback: () => void

  constructor(
    updateCallback: (state: MessageState) => void,
    scrollCallback: () => void
  ) {
    this.state = {
      content: '', // 初始为空，这样会显示动画
      isStreaming: true,
      isLoading: true,
      hasError: false,
      progressSteps: [],
      isChatMode: false,  // 初始为false
      isTaskMode: false,  // 初始为false
      nodeResults: []  // 初始为空数组
    }
    this.updateCallback = updateCallback
    this.scrollCallback = scrollCallback
  }

  // 初始化连接
  initConnection() {
    this.updateState({
      content: '', // 保持为空，显示动画
      isStreaming: true,
      isLoading: true,
      hasError: false,
      progressSteps: [],
      isChatMode: false,
      isTaskMode: false,
      nodeResults: []
    })
  }

  // 连接成功
  connectionSuccess() {
    // 连接成功后不立即显示信息，等待模式确定
    console.log('WebSocket 连接成功')
  }

  // 处理闲聊模式
  setChatMode(chatResponse: string, executionTime?: number) {
    this.state.isChatMode = true
    this.state.isTaskMode = false
    this.state.isLoading = false
    
    // 实现流式输出效果
    this.streamChatResponse(chatResponse)
  }

  // 处理任务模式开始
  setTaskMode(message: string, mermaidDiagram?: string) {
    this.state.isChatMode = false
    this.state.isTaskMode = true
    this.state.mermaidDiagram = mermaidDiagram
    this.state.content = this.parseMarkdown(message)
    this.state.isLoading = true
    this.state.nodeResults = []
    
    this.updateState(this.state)
    this.scrollCallback()
  }

  // 添加节点执行结果
  addNodeResult(nodeResult: any) {
    if (!this.state.isTaskMode) return
    
    // 将节点结果添加到数组中，包含 markdown 消息内容
    const processedNodeResult = {
      ...nodeResult,
      markdownContent: nodeResult.message || '', // 保存格式化的 markdown 内容
      timestamp: new Date().toISOString()
    }
    
    this.state.nodeResults.push(processedNodeResult)
    this.updateState(this.state)
    this.scrollCallback()
  }

  // 任务完成
  taskComplete(message: string, executionTime?: number) {
    if (!this.state.isTaskMode) return
    
    this.state.content += '\n\n' + this.parseMarkdown(message)
    this.state.isStreaming = false
    this.state.isLoading = false
    
    this.updateState(this.state)
    this.scrollCallback()
  }

  // 流式显示闲聊回答
  private streamChatResponse(chatResponse: string) {
    let currentIndex = 0
    const streamInterval = setInterval(() => {
      if (currentIndex < chatResponse.length) {
        // 每次添加一个字符
        const currentContent = chatResponse.substring(0, currentIndex + 1)
        this.state.content = currentContent
        this.updateState({
          ...this.state,
          isStreaming: true
        })
        currentIndex++
        this.scrollCallback()
      } else {
        // 流式输出完成
        clearInterval(streamInterval)
        this.state.content = chatResponse
        this.updateState({
          ...this.state,
          isStreaming: false
        })
    }
    }, 30) // 每30毫秒输出一个字符
  }

  // 简单的 Markdown 解析（基础支持）
  private parseMarkdown(text: string): string {
    if (!text) return ''
    
    // 基础 Markdown 转换
    return text
      .replace(/^### (.*$)/gm, '<h3>$1</h3>')
      .replace(/^## (.*$)/gm, '<h2>$1</h2>')
      .replace(/^# (.*$)/gm, '<h1>$1</h1>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/```\n([\s\S]*?)\n```/g, '<pre><code>$1</code></pre>')
      .replace(/\n/g, '<br>')
  }

  // 添加进度消息（兼容旧版本）
  addProgress(message: string) {
    // 在闲聊模式下不显示进度信息
    if (this.state.isChatMode) {
      return
    }
    
    // 避免重复消息
    if (!this.state.progressSteps.includes(message)) {
      this.state.progressSteps.push(message)
      this.state.content = this.state.progressSteps.join('\n')
      this.updateState(this.state)
      
      // 延迟滚动，确保DOM更新完成
      setTimeout(() => {
        this.scrollCallback()
      }, 50)
    }
  }

  // 流式显示内容（兼容旧版本）
  streamContent(content: string) {
    const lines = content.split('\n')
    let currentIndex = 0
    
    const streamNextLine = () => {
      if (currentIndex < lines.length) {
        this.state.progressSteps.push(lines[currentIndex])
        this.state.content = this.state.progressSteps.join('\n')
        this.updateState(this.state)
        this.scrollCallback()
        currentIndex++
        
        // 继续下一行
        setTimeout(streamNextLine, 100)
      }
    }
    
    // 开始流式显示
    streamNextLine()
  }

  // 任务成功完成（兼容旧版本）
  taskSuccess(message: string, data?: any) {
    if (data) {
      // 检查是否是闲聊回答
      const finalOutput = data.final_output || data.data?.final_output
      if (finalOutput && (!data.node_results || data.node_results.length === 0)) {
        // 这是闲聊回答，设置为闲聊模式并直接显示回答
        this.setChatMode(finalOutput)
        return
      }
    }
    
    // 非闲聊模式，显示完成信息
    if (!this.state.isChatMode) {
      this.addProgress('✅ 任务执行完成！')
    }
    
    if (data) {
      const formattedData = this.formatTaskResult(data)
      if (formattedData) {
        // 流式显示结果
        this.streamContent(`📊 执行结果:\n${formattedData}`)
      }
    }
  }

  // 任务执行错误
  taskError(message: string) {
    this.addProgress(`❌ 执行错误: ${message}`)
    this.updateState({
      ...this.state,
      isStreaming: false,
      isLoading: false,
      hasError: true
    })
  }

  // 连接断开
  connectionDisconnect(code: number, reason: string) {
    if (code === 1000) {
      this.addProgress('✅ 连接正常关闭')
    } else {
      this.addProgress(`❌ 连接异常断开 (代码: ${code})`)
    }
    
    this.updateState({
      ...this.state,
      isStreaming: false,
      isLoading: false
    })
  }

  // 格式化任务结果（兼容旧版本）
  private formatTaskResult(data: any): string {
    try {
      // 处理嵌套的数据结构
      const result = data.data || data
      
      // 如果是pipeline_result结构
      if (result.pipeline_result) {
        const pipeline = result.pipeline_result
        let formatted = ''
        
        // 显示用户输入
        if (result.user_input) {
          formatted += `📝 用户输入: ${result.user_input}\n`
        }
        
        // 显示pipeline状态
        if (pipeline.success !== undefined) {
          formatted += `✅ Pipeline状态: ${pipeline.success ? '成功' : '失败'}\n`
        }
        
        // 显示节点执行结果
        if (pipeline.node_results && Array.isArray(pipeline.node_results)) {
          formatted += `\n🔧 执行节点:\n`
          pipeline.node_results.forEach((node: any, index: number) => {
            formatted += `  ${index + 1}. ${node.tool_type || node.node_id}\n`
            
            // 显示输入参数
            if (node.input_params) {
              const params = Object.entries(node.input_params)
                .map(([key, value]) => `${key}: ${value}`)
                .join(', ')
              formatted += `     输入: ${params}\n`
            }
            
            // 显示输出状态
            if (node.output && node.output.status) {
              const status = node.output.status === 'success' ? '✅ 成功' : '❌ 失败'
              formatted += `     状态: ${status}\n`
            }
            
            // 显示错误信息
            if (node.output && node.output.status === 'error' && node.output.data) {
              formatted += `     错误: ${JSON.stringify(node.output.data)}\n`
            }
          })
        }
        
        return formatted
      }
      
      // 如果是简单的消息结构
      if (result.message) {
        return `📄 ${result.message}`
      }
      
      // 默认返回简化的JSON
      return JSON.stringify(result, null, 2)
      
    } catch (error) {
      console.error('格式化任务结果失败:', error)
      return '无法格式化结果数据'
    }
  }

  private updateState(newState: MessageState) {
    this.state = newState
    this.updateCallback(this.state)
  }

  // 获取当前状态
  getState(): MessageState {
    return this.state
  }

  // 处理闲聊回答（兼容旧版本）
  handleChatResponse(chatResponse: string) {
    this.setChatMode(chatResponse)
  }
} 