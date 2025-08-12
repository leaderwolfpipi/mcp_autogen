// WebSocket管理器
export interface WebSocketMessage {
  type: string
  session_id?: string
  message?: string
  mode?: string
  execution_time?: number
  step?: any
  steps?: any[]
  mermaid_diagram?: string
  error?: string
  iteration?: number
  tool_name?: string  // 新增：工具名称
}

export interface WebSocketCallbacks {
  onConnect?: () => void
  onModeDetection?: (mode: string, sessionId: string, message: string) => void
  onChatResponse?: (message: string, executionTime?: number) => void
  onTaskStart?: (message: string, mermaidDiagram?: string) => void
  onToolStart?: (message: string, toolName?: string) => void  // 新增：工具开始执行
  onToolResult?: (step: any, mermaidDiagram?: string) => void
  onTaskComplete?: (message: string, executionTime?: number, mermaidDiagram?: string, steps?: any[]) => void
  onError?: (message: string, iteration?: number) => void
  onDisconnect?: (code: number, reason: string) => void
}

export class WebSocketManager {
  private ws: WebSocket | null = null
  private url: string
  private callbacks: WebSocketCallbacks
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(url: string, callbacks: WebSocketCallbacks) {
    this.url = url
    this.callbacks = callbacks
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url)

        this.ws.onopen = () => {
          console.log('🔗 MCP WebSocket连接成功')
          this.reconnectAttempts = 0
          this.callbacks.onConnect?.()
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data: WebSocketMessage = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (error) {
            console.error('❌ WebSocket消息解析失败:', error)
          }
        }

        this.ws.onclose = (event) => {
          console.log('🔌 MCP WebSocket连接关闭:', event.code, event.reason)
          this.callbacks.onDisconnect?.(event.code, event.reason)
          
          // 尝试重连
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++
            console.log(`🔄 尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
            setTimeout(() => {
              this.connect()
            }, this.reconnectDelay * this.reconnectAttempts)
          }
        }

        this.ws.onerror = (error) => {
          console.error('❌ MCP WebSocket连接错误:', error)
          reject(error)
        }

      } catch (error) {
        reject(error)
      }
    })
  }

  private handleMessage(data: WebSocketMessage) {
    console.log('📨 收到MCP消息:', data.type, data)

    switch (data.type) {
      case 'mode_detection':
        this.callbacks.onModeDetection?.(
          data.mode || 'chat',
          data.session_id || '',
          data.message || ''
        )
        break

      case 'chat_response':
        this.callbacks.onChatResponse?.(
          data.message || '',
          data.execution_time
        )
        break

      case 'task_start':
        this.callbacks.onTaskStart?.(
          data.message || '开始任务执行',
          data.mermaid_diagram
        )
        break

      case 'tool_start':
        this.callbacks.onToolStart?.(
          data.message || '工具开始执行',
          data.tool_name
        )
        break

      case 'tool_result':
        this.callbacks.onToolResult?.(
          data.step,
          data.mermaid_diagram
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

      case 'tool_error':
        this.callbacks.onError?.(
          `工具执行失败: ${data.error || '未知错误'}`
        )
        break

      case 'error':
        this.callbacks.onError?.(
          data.message || '执行失败',
          data.iteration
        )
        break

      case 'max_iterations_reached':
        this.callbacks.onError?.(
          data.message || '达到最大迭代次数'
        )
        break

      default:
        console.warn('⚠️ 未知的MCP消息类型:', data.type)
        break
    }
  }

  send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.error('❌ WebSocket未连接，无法发送消息')
      throw new Error('WebSocket未连接')
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
} 