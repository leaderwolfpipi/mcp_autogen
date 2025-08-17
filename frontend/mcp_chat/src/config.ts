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
  
  // SSE配置
  sse: {
    url: import.meta.env.VITE_SSE_URL || 'http://localhost:8000/mcp/sse', // SSE端点
    reconnectAttempts: 5,
    reconnectDelay: 1000,
    timeout: 30000,
  },
  
  // API配置
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000' // 指向MCP标准API
  },
  
  // 通信模式配置
  communication: {
    // 可选值: 'websocket', 'sse', 'auto'
    mode: import.meta.env.VITE_COMM_MODE || 'sse',  // 默认使用SSE
    // 自动模式下的优先级: 'sse' > 'websocket'
    autoModePreference: ['sse', 'websocket'],
    // 是否允许在模式间切换
    allowFallback: true,
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
    // 新增：协议切换功能
    protocolSwitching: true,
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