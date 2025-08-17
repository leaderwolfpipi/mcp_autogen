// SSE管理器 - 处理Server-Sent Events通信
export interface SSEMessage {
  type: string
  session_id?: string
  message?: string
  mode?: string
  execution_time?: number
  step?: any
  step_data?: any
  steps?: any[]
  mermaid_diagram?: string
  error?: string
  iteration?: number
  tool_name?: string
  plan?: any
  step_index?: number
  total_steps?: number
  status?: string
  timestamp?: number
  step_id?: string
  data?: any  // SSE特有的数据字段
  partial_content?: string // 新增用于流式聊天
  accumulated_content?: string // 新增用于流式聊天
}

export interface SSECallbacks {
  onConnect?: () => void
  onModeDetection?: (mode: string, sessionId: string, message: string) => void
  onChatResponse?: (message: string, executionTime?: number, isStreaming?: boolean) => void
  onTaskPlanning?: (message: string) => void
  onTaskStart?: (message: string, mermaidDiagram?: string, plan?: any) => void
  onToolStart?: (message: string, toolName?: string, stepIndex?: number, totalSteps?: number, stepId?: string) => void
  onToolResult?: (stepData: any, status?: string, toolName?: string) => void
  onTaskComplete?: (message: string, executionTime?: number, mermaidDiagram?: string, steps?: any[], isStreaming?: boolean) => void
  onError?: (message: string, iteration?: number) => void
  onDisconnect?: () => void
}

export class SSEManager {
  private sseUrl: string
  private callbacks: SSECallbacks
  private abortController: AbortController | null = null
  private isConnected = false
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(baseUrl: string, callbacks: SSECallbacks) {
    this.sseUrl = `${baseUrl}/mcp/sse`
    this.callbacks = callbacks
  }

  async connect(): Promise<void> {
    console.log('�� 尝试建立SSE连接...')
    // SSE是无状态的，只要API服务可用就算连接成功
    this.isConnected = true
    this.callbacks.onConnect?.()
  }

  async sendMessage(userInput: string, sessionId?: string): Promise<void> {
    // 如果有正在进行的连接，先中断
    if (this.abortController) {
      this.abortController.abort()
    }

    this.abortController = new AbortController()

    try {
      // 构造MCP标准请求
      const request = {
        mcp_version: "1.0",
        session_id: sessionId || `sse_session_${Date.now()}`,
        request_id: `req_${Date.now()}`,
        user_query: userInput,
        context: {}
      }

      console.log('📤 发送SSE请求:', request)

      // 发送POST请求到SSE端点
      const response = await fetch(this.sseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache'
        },
        body: JSON.stringify(request),
        signal: this.abortController.signal
      })

      if (!response.ok) {
        throw new Error(`SSE请求失败: ${response.status} ${response.statusText}`)
      }

      if (!response.body) {
        throw new Error('SSE响应体为空')
      }

      this.isConnected = true
      this.reconnectAttempts = 0

      // 处理SSE流
      await this.processSSEStream(response.body)

    } catch (error: any) {
      console.error('❌ SSE请求失败:', error)
      
      if (error.name === 'AbortError') {
        console.log('📋 SSE请求被中断')
        return
      }

      this.callbacks.onError?.(error.message || '未知错误')
      
      // 尝试重连
      this.attemptReconnect()
    } finally {
      // SSE是无状态的，不需要在每次请求后断开连接状态
      // this.isConnected = false  // 移除这行，保持连接状态
      this.abortController = null
    }
  }

  private async processSSEStream(body: ReadableStream<Uint8Array>): Promise<void> {
    const reader = body.getReader()
    const decoder = new TextDecoder()

    // 新增：按SSE规范的事件解析缓冲
    let buffer = ''
    let currentEventType: string | null = null
    let dataBuffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          // 结束前若还有未提交的数据，补一次提交
          if (dataBuffer.trim().length > 0) {
            try {
              const dataText = dataBuffer.trimEnd()
              let parsed: any
              try {
                parsed = JSON.parse(dataText)
              } catch {
                parsed = { message: dataText }
              }
              const payload = currentEventType && !parsed.type
                ? { type: currentEventType, data: parsed }
                : parsed
              this.handleSSEEvent(payload)
            } catch (e) {
              console.error('❌ SSE结束前解析失败:', e)
            }
          }

          console.log('✅ SSE流处理完成')
          break
        }

        buffer += decoder.decode(value, { stream: true })

        // 按行处理，遇到空行提交一个完整事件
        let idx: number
        while ((idx = buffer.indexOf('\n')) !== -1) {
          const rawLine = buffer.slice(0, idx)
          buffer = buffer.slice(idx + 1)
          const line = rawLine.trimEnd()

          if (line.startsWith('event:')) {
            currentEventType = line.slice(6).trim()
          } else if (line.startsWith('data:')) {
            // data: 可能多行，按规范应在空行处合并提交
            dataBuffer += line.slice(5).trimStart() + '\n'
          } else if (line === '') {
            // 空行：一个事件结束，进行提交
            if (dataBuffer.trim().length > 0) {
              try {
                const dataText = dataBuffer.trimEnd()
                let parsed: any
                try {
                  parsed = JSON.parse(dataText)
                } catch {
                  parsed = { message: dataText }
                }
                const payload = currentEventType && !parsed.type
                  ? { type: currentEventType, data: parsed }
                  : parsed
                this.handleSSEEvent(payload)
              } catch (e) {
                console.error('❌ SSE数据解析失败:', e, '原始数据块:', dataBuffer)
              }
            }
            // 重置事件缓冲
            currentEventType = null
            dataBuffer = ''
          } else if (line.startsWith(':')) {
            // 注释行，忽略
          } else {
            // 其他行（容错处理）：直接忽略或按需记录
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }

  private handleSSEEvent(data: SSEMessage) {
    console.log('📨 收到SSE消息:', data.type, data)

    // 优先处理兼容的WebSocket消息格式
    if (data.type === 'chat_response' || data.type === 'mode_detection' || data.type === 'task_start' || 
        data.type === 'tool_start' || data.type === 'tool_result' || data.type === 'task_complete') {
      console.log('🔄 使用兼容模式处理:', data.type)
      this.handleCompatibleEvent(data)
      return
    }

    // 处理标准SSE事件类型
    switch (data.type) {
      case 'status':
        this.handleStatusEvent(data)
        break
      
      case 'result':
        this.handleResultEvent(data)
        break
      
      case 'error':
        this.handleErrorEvent(data)
        break
      
      case 'heartbeat':
        this.handleHeartbeatEvent(data)
        break
      
      default:
        console.log('⚠️ 未知事件类型，尝试兼容处理:', data.type)
        // 兼容原有的WebSocket消息格式
        this.handleCompatibleEvent(data)
    }
  }

  private handleStatusEvent(data: SSEMessage) {
    const statusData = data.data || data
    const message = statusData.message || '处理中...'
    const statusType = statusData.type || statusData.status
    
    console.log('📊 处理状态事件:', statusType, message)
    
    // 处理流式聊天内容
    if (statusType === 'chat_streaming') {
      const partialContent = statusData.partial_content || ''
      const accumulatedContent = statusData.accumulated_content || ''
      
      console.log('🌊 流式聊天内容:', partialContent, '累计:', accumulatedContent.length)
      
      // 触发流式聊天响应回调，实时更新UI（第三参标记为流式）
      this.callbacks.onChatResponse?.(accumulatedContent, undefined, true)
      return
    }
    
    // 🎯 处理任务模式流式内容
    if (statusType === 'task_streaming') {
      const partialContent = statusData.partial_content || ''
      const accumulatedContent = statusData.accumulated_content || ''
      
      console.log('🔧 流式任务内容:', partialContent, '累计:', accumulatedContent.length)
      
      // 触发任务完成回调，实时更新任务结果
      this.callbacks.onTaskComplete?.(accumulatedContent, undefined, undefined, undefined, true) // 最后一个参数表示是流式更新
      return
    }
    
    if (statusData.status === 'processing') {
      // 可以触发任务规划或开始事件
      this.callbacks.onTaskPlanning?.(message)
    } else if (statusData.status === 'completed') {
      // 对于completed状态，我们不应该覆盖之前的响应
      // 因为真正的响应内容已经在result事件中处理了
      console.log('✅ 任务状态已完成，但不覆盖已有响应')
      // 注释掉这行，避免覆盖聊天响应
      // this.callbacks.onTaskComplete?.(message, data.execution_time)
    }
  }

  private handleResultEvent(data: SSEMessage) {
    const resultData = data.data || data
    
    console.log('🔍 处理结果事件:', data)
    
    // 检查是否是MCP任务响应格式 (需要同时具备mcp_version, final_response和非空的steps数组)
    if (resultData.mcp_version && resultData.final_response && resultData.steps && resultData.steps.length > 0) {
      // 这是任务模式的MCP响应
      console.log('📋 识别为任务完成响应')
      this.callbacks.onTaskComplete?.(
        resultData.final_response,
        resultData.execution_time,
        undefined,
        resultData.steps
      )
    } else {
      // 这是闲聊模式的响应或其他结果类型
      console.log('💬 识别为聊天响应')
      const message = resultData.final_response || resultData.message || JSON.stringify(resultData, null, 2)
      this.callbacks.onChatResponse?.(message, resultData.execution_time)
    }
  }

  private handleErrorEvent(data: SSEMessage) {
    const errorData = data.data || data
    const errorMessage = errorData.error?.message || errorData.message || '未知错误'
    this.callbacks.onError?.(errorMessage)
  }

  private handleHeartbeatEvent(data: SSEMessage) {
    console.log('💓 收到心跳事件:', data)
    // 心跳事件通常不需要特殊处理，除非需要记录或触发回调
  }

  private handleCompatibleEvent(data: SSEMessage) {
    // 兼容原有的WebSocket消息格式
    switch (data.type) {
      case 'mode_detection':
        this.callbacks.onModeDetection?.(
          data.mode || 'task',
          data.session_id || '',
          data.message || ''
        )
        break

      case 'chat_response':
        this.callbacks.onChatResponse?.(data.message || '', data.execution_time)
        break

      case 'task_planning':
        this.callbacks.onTaskPlanning?.(data.message || '')
        break

      case 'task_start':
        this.callbacks.onTaskStart?.(
          data.message || '',
          data.mermaid_diagram,
          data.plan
        )
        break

      case 'tool_start':
        this.callbacks.onToolStart?.(
          data.message || '',
          data.tool_name,
          data.step_index,
          data.total_steps,
          data.step_id
        )
        break

      case 'tool_result':
        this.callbacks.onToolResult?.(
          data.step_data || data.step,
          data.status,
          data.tool_name
        )
        break

      case 'task_complete':
        this.callbacks.onTaskComplete?.(
          data.message || '',
          data.execution_time,
          data.mermaid_diagram,
          data.steps
        )
        break

      case 'error':
        this.callbacks.onError?.(data.message || '', data.iteration)
        break

      default:
        console.warn('⚠️ 未知的SSE消息类型:', data.type)
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`🔄 尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
      
      setTimeout(() => {
        // SSE不需要预先建立连接，重连将在下次发送消息时进行
        console.log('📡 SSE重连准备就绪')
      }, this.reconnectDelay * this.reconnectAttempts)
    } else {
      console.error('❌ SSE重连次数已达上限')
      this.callbacks.onDisconnect?.()
    }
  }

  disconnect() {
    console.log('🔌 断开SSE连接')
    
    if (this.abortController) {
      this.abortController.abort()
      this.abortController = null
    }
    
    this.isConnected = false
    this.callbacks.onDisconnect?.()
  }

  isActive(): boolean {
    return this.isConnected
  }

  getConnectionInfo(): object {
    return {
      type: 'SSE',
      connected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      url: this.sseUrl
    }
  }
}