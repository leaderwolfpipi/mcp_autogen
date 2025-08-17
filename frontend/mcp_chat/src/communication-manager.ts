// 通信管理器 - 统一管理WebSocket和SSE两种通信方式
import { WebSocketManager, type WebSocketCallbacks } from './websocket-manager'
import { SSEManager, type SSECallbacks } from './sse-manager'
import { config } from './config'

export type CommunicationMode = 'websocket' | 'sse' | 'auto'

export interface CommunicationCallbacks {
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
  onModeSwitch?: (newMode: CommunicationMode, reason?: string) => void
}

export class CommunicationManager {
  private mode: CommunicationMode
  private wsManager: WebSocketManager | null = null
  private sseManager: SSEManager | null = null
  private callbacks: CommunicationCallbacks
  private currentSessionId: string | null = null
  private isConnected = false

  constructor(callbacks: CommunicationCallbacks, initialMode?: CommunicationMode) {
    this.mode = initialMode || config.communication.mode as CommunicationMode
    this.callbacks = callbacks
    
    console.log(`🔄 初始化通信管理器，模式: ${this.mode}`)
  }

  async initialize(): Promise<void> {
    await this.setupCommunication()
  }

  private async setupCommunication(): Promise<void> {
    // 清理现有连接
    this.cleanup()

    switch (this.mode) {
      case 'sse':
        await this.setupSSE()
        break
      
      case 'websocket':
        await this.setupWebSocket()
        break
      
      case 'auto':
        await this.setupAuto()
        break
      
      default:
        console.error('❌ 未知的通信模式:', this.mode)
        // 降级到SSE
        this.mode = 'sse'
        await this.setupSSE()
    }
  }

  private async setupSSE(): Promise<void> {
    console.log('🌐 设置SSE通信...')
    
    const sseCallbacks: SSECallbacks = {
      onConnect: () => {
        this.isConnected = true
        console.log('✅ SSE连接成功')
        this.callbacks.onConnect?.()
      },
      onModeDetection: this.callbacks.onModeDetection,
      onChatResponse: this.callbacks.onChatResponse,
      onTaskPlanning: this.callbacks.onTaskPlanning,
      onTaskStart: this.callbacks.onTaskStart,
      onToolStart: this.callbacks.onToolStart,
      onToolResult: this.callbacks.onToolResult,
      onTaskComplete: this.callbacks.onTaskComplete,
      onError: (message, iteration) => {
        console.error('❌ SSE错误:', message)
        this.callbacks.onError?.(message, iteration)
        
        // 如果允许降级，尝试切换到WebSocket
        if (config.communication.allowFallback) {
          this.fallbackToWebSocket('SSE连接失败')
        }
      },
      onDisconnect: () => {
        this.isConnected = false
        console.log('🔌 SSE连接断开')
        this.callbacks.onDisconnect?.()
      }
    }

    this.sseManager = new SSEManager(config.api.baseUrl, sseCallbacks)
    await this.sseManager.connect()
  }

  private async setupWebSocket(): Promise<void> {
    console.log('🔗 设置WebSocket通信...')
    
    const wsCallbacks: WebSocketCallbacks = {
      onConnect: () => {
        this.isConnected = true
        console.log('✅ WebSocket连接成功')
        this.callbacks.onConnect?.()
      },
      onModeDetection: this.callbacks.onModeDetection,
      onChatResponse: this.callbacks.onChatResponse,
      onTaskPlanning: this.callbacks.onTaskPlanning,
      onTaskStart: this.callbacks.onTaskStart,
      onToolStart: this.callbacks.onToolStart,
      onToolResult: this.callbacks.onToolResult,
      onTaskComplete: this.callbacks.onTaskComplete,
      onError: (message, iteration) => {
        console.error('❌ WebSocket错误:', message)
        this.callbacks.onError?.(message, iteration)
        
        // 如果允许降级，尝试切换到SSE
        if (config.communication.allowFallback) {
          this.fallbackToSSE('WebSocket连接失败')
        }
      },
      onDisconnect: (code, reason) => {
        this.isConnected = false
        console.log('🔌 WebSocket连接断开:', code, reason)
        this.callbacks.onDisconnect?.()
      }
    }

    this.wsManager = new WebSocketManager(config.websocket.url, wsCallbacks)
    await this.wsManager.connect()
  }

  private async setupAuto(): Promise<void> {
    console.log('🤖 自动选择通信模式...')
    
    // 按照配置的优先级尝试连接
    for (const preferredMode of config.communication.autoModePreference) {
      try {
        this.mode = preferredMode as CommunicationMode
        console.log(`🔄 尝试 ${preferredMode} 模式...`)
        
        if (preferredMode === 'sse') {
          await this.setupSSE()
        } else if (preferredMode === 'websocket') {
          await this.setupWebSocket()
        }
        
        console.log(`✅ 自动选择了 ${preferredMode} 模式`)
        this.callbacks.onModeSwitch?.(this.mode, '自动选择')
        return
        
      } catch (error) {
        console.warn(`⚠️ ${preferredMode} 模式失败:`, error)
        continue
      }
    }
    
    // 如果所有模式都失败，抛出错误
    throw new Error('所有通信模式都不可用')
  }

  async sendMessage(userInput: string, sessionId?: string): Promise<void> {
    if (!this.isActive()) {
      throw new Error('通信连接未建立')
    }

    // 更新会话ID
    if (sessionId) {
      this.currentSessionId = sessionId
    }

    try {
      if (this.mode === 'sse' && this.sseManager) {
        await this.sseManager.sendMessage(userInput, this.currentSessionId || undefined)
      } else if (this.mode === 'websocket' && this.wsManager) {
        this.wsManager.send({
          user_input: userInput,
          session_id: this.currentSessionId || undefined
        })
      } else {
        throw new Error('没有可用的通信管理器')
      }
    } catch (error) {
      console.error('❌ 发送消息失败:', error)
      
      // 如果允许降级，尝试切换模式
      if (config.communication.allowFallback) {
        await this.attemptFallback('发送消息失败')
        // 重试发送
        await this.sendMessage(userInput, sessionId)
      } else {
        throw error
      }
    }
  }

  private async fallbackToSSE(reason: string): Promise<void> {
    if (this.mode !== 'sse') {
      console.log('🔄 降级到SSE模式:', reason)
      this.mode = 'sse'
      await this.setupSSE()
      this.callbacks.onModeSwitch?.(this.mode, reason)
    }
  }

  private async fallbackToWebSocket(reason: string): Promise<void> {
    if (this.mode !== 'websocket') {
      console.log('🔄 降级到WebSocket模式:', reason)
      this.mode = 'websocket'
      await this.setupWebSocket()
      this.callbacks.onModeSwitch?.(this.mode, reason)
    }
  }

  private async attemptFallback(reason: string): Promise<void> {
    if (this.mode === 'sse') {
      await this.fallbackToWebSocket(reason)
    } else if (this.mode === 'websocket') {
      await this.fallbackToSSE(reason)
    }
  }

  async switchMode(newMode: CommunicationMode): Promise<void> {
    if (newMode === this.mode) {
      console.log(`ℹ️ 已经是 ${newMode} 模式`)
      return
    }

    console.log(`🔄 手动切换到 ${newMode} 模式`)
    this.mode = newMode
    await this.setupCommunication()
    this.callbacks.onModeSwitch?.(this.mode, '手动切换')
  }

  disconnect(): void {
    console.log('🔌 断开通信连接')
    this.cleanup()
    this.isConnected = false
  }

  private cleanup(): void {
    if (this.wsManager) {
      this.wsManager.disconnect()
      this.wsManager = null
    }
    
    if (this.sseManager) {
      this.sseManager.disconnect()
      this.sseManager = null
    }
  }

  isActive(): boolean {
    if (this.mode === 'sse' && this.sseManager) {
      return this.sseManager.isActive()
    } else if (this.mode === 'websocket' && this.wsManager) {
      return this.wsManager.isConnected()
    }
    return false
  }

  getCurrentMode(): CommunicationMode {
    return this.mode
  }

  getConnectionInfo(): object {
    const baseInfo = {
      mode: this.mode,
      connected: this.isConnected,
      sessionId: this.currentSessionId
    }

    if (this.mode === 'sse' && this.sseManager) {
      return { ...baseInfo, ...this.sseManager.getConnectionInfo() }
    } else if (this.mode === 'websocket' && this.wsManager) {
      return { ...baseInfo, type: 'WebSocket', url: config.websocket.url }
    }

    return baseInfo
  }

  setSessionId(sessionId: string): void {
    this.currentSessionId = sessionId
  }

  getSessionId(): string | null {
    return this.currentSessionId
  }
}