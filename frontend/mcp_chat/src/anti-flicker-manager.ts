import { ref, nextTick, type Ref } from 'vue'

export interface AntiFlickerMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isStreaming?: boolean
  toolResults?: any[]
}

export class AntiFlickerManager {
  private messages: Ref<AntiFlickerMessage[]> = ref([])
  private updateQueue: (() => void)[] = []
  private isUpdating = false

  constructor() {
    this.processQueue()
  }

  // 添加用户消息 - 防闪烁
  addUserMessage(content: string): AntiFlickerMessage {
    const message: AntiFlickerMessage = {
      id: `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      role: 'user',
      content,
      timestamp: new Date()
    }

    this.queueUpdate(() => {
      this.messages.value = [...this.messages.value, message]
    })

    return message
  }

  // 添加AI消息 - 防闪烁
  addAIMessage(initialContent: string = '🤖 正在处理您的请求...'): AntiFlickerMessage {
    const message: AntiFlickerMessage = {
      id: `ai_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      role: 'assistant',
      content: initialContent,
      timestamp: new Date(),
      isStreaming: true,
      toolResults: []
    }

    this.queueUpdate(() => {
      this.messages.value = [...this.messages.value, message]
    })

    return message
  }

  // 更新AI消息内容 - 防闪烁
  updateAIMessage(messageId: string, content: string, isStreaming: boolean = true) {
    this.queueUpdate(() => {
      const index = this.messages.value.findIndex(msg => msg.id === messageId)
      if (index !== -1) {
        const updatedMessages = [...this.messages.value]
        updatedMessages[index] = {
          ...updatedMessages[index],
          content,
          isStreaming
        }
        this.messages.value = updatedMessages
      }
    })
  }

  // 完成AI消息 - 防闪烁
  completeAIMessage(messageId: string, finalContent: string) {
    this.queueUpdate(() => {
      const index = this.messages.value.findIndex(msg => msg.id === messageId)
      if (index !== -1) {
        const updatedMessages = [...this.messages.value]
        updatedMessages[index] = {
          ...updatedMessages[index],
          content: finalContent,
          isStreaming: false
        }
        this.messages.value = updatedMessages
      }
    })
  }

  // 获取消息列表
  getMessages(): Ref<AntiFlickerMessage[]> {
    return this.messages
  }

  // 清空消息
  clearMessages() {
    this.queueUpdate(() => {
      this.messages.value = []
    })
  }

  // 队列更新 - 防止频繁更新导致的闪烁
  private queueUpdate(updateFn: () => void) {
    this.updateQueue.push(updateFn)
    
    if (!this.isUpdating) {
      this.processQueue()
    }
  }

  // 处理更新队列
  private async processQueue() {
    if (this.isUpdating || this.updateQueue.length === 0) {
      return
    }

    this.isUpdating = true

    while (this.updateQueue.length > 0) {
      const updateFn = this.updateQueue.shift()
      if (updateFn) {
        updateFn()
        // 等待下一个tick确保DOM更新完成
        await nextTick()
      }
    }

    this.isUpdating = false
  }

  // 批量更新 - 一次性更新多个消息
  batchUpdate(updates: Array<{ messageId: string; content: string; isStreaming?: boolean }>) {
    this.queueUpdate(() => {
      const updatedMessages = [...this.messages.value]
      
      updates.forEach(({ messageId, content, isStreaming }) => {
        const index = updatedMessages.findIndex(msg => msg.id === messageId)
        if (index !== -1) {
          updatedMessages[index] = {
            ...updatedMessages[index],
            content,
            isStreaming: isStreaming ?? updatedMessages[index].isStreaming
          }
        }
      })

      this.messages.value = updatedMessages
    })
  }
} 