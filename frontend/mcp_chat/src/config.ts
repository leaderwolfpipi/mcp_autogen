// 生产环境配置
export const config = {
  // WebSocket配置
  websocket: {
    url: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/mcp/chat', // 指向MCP标准API
    reconnectAttempts: 3,
    reconnectDelay: 1000,
    connectionTimeout: 5000,
    heartbeatInterval: 30000,
  },
  
  // API配置
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000' // 指向MCP标准API
  },
  
  // 应用配置
  app: {
    name: 'QiQi Chat',
    version: '1.0.0',
    maxMessageLength: 4000,
    maxHistoryItems: 100,
  },
  
  // 功能开关
  features: {
    webSearch: true,
    deepThinking: true,
    fileUpload: true,
    toolExecution: true,
  }
}

// 环境变量类型定义
declare global {
  interface Window {
    __APP_CONFIG__: typeof config
  }
}

// 在开发环境中，可以通过window对象访问配置
if (import.meta.env.DEV) {
  window.__APP_CONFIG__ = config
} 