# 前端与MCP标准API集成指南

本指南说明如何将前端`mcp_chat`应用与MCP标准API集成，并实现流式输出功能。

## 🎯 集成概述

### 架构改进
1. **统一API端点**: 前端连接到MCP标准API (`localhost:8000`)
2. **流式WebSocket**: 新增专门的聊天WebSocket端点 (`/ws/mcp/chat`)
3. **实时反馈**: 支持工具执行的实时状态更新
4. **智能模式检测**: 自动区分闲聊和任务模式

### 主要变更
- ✅ 前端配置更新为连接MCP标准API
- ✅ 新增聊天专用WebSocket端点
- ✅ 实现流式工具执行反馈
- ✅ 优化的enhanced_report_generator工具（避免误触发）

## 🚀 启动步骤

### 1. 启动后端API服务

```bash
# 在项目根目录下
python start_mcp_standard_api.py
```

服务将在以下端点启动：
- 🌐 主API: http://localhost:8000
- 💬 聊天WebSocket: ws://localhost:8000/ws/mcp/chat
- 🔗 标准WebSocket: ws://localhost:8000/ws/mcp/standard
- 📺 演示页面: http://localhost:8000/demo/standard

### 2. 启动前端应用

```bash
# 进入前端目录
cd frontend/mcp_chat

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:5173 启动

## 🔧 配置说明

### 后端配置
- **端口**: 默认8000（可通过环境变量`PORT`修改）
- **主机**: 默认0.0.0.0（可通过环境变量`HOST`修改）

### 前端配置
位置：`frontend/mcp_chat/src/config.ts`

```typescript
export const config = {
  websocket: {
    url: 'ws://localhost:8000/ws/mcp/chat',  // WebSocket端点
    // ... 其他配置
  },
  api: {
    baseUrl: 'http://localhost:8000'  // API基础URL
  }
}
```

## 📡 WebSocket消息流

### 闲聊模式流程
1. `mode_detection` - 模式检测结果
2. `chat_response` - LLM聊天回复

### 任务模式流程
1. `mode_detection` - 模式检测结果  
2. `task_start` - 任务开始
3. `tool_start` - 工具开始执行（新增）
4. `tool_result` - 工具执行结果
5. `task_complete` - 任务完成

### 错误处理
- `error` - 执行错误
- `tool_error` - 工具执行错误

## 🧪 测试验证

### 运行集成测试
```bash
# 确保后端API服务正在运行
python test_chat_integration.py
```

### 手动测试
1. 在前端发送闲聊消息（如"你好"）
2. 验证快速回复，无工具调用
3. 发送任务消息（如"搜索Python教程"）
4. 观察流式执行过程

## 🛠️ 流式输出特性

### 实时工具状态
- ⏳ 工具开始执行时显示"正在执行"状态
- 🔧 工具完成后更新为最终结果
- 📊 显示执行时间和输出数据

### 智能内容过滤
enhanced_report_generator工具现在会智能拒绝：
- 简单历史查询（如"秦始皇之死"）
- 单纯人名查询（如"诸葛亮"）
- 闲聊对话
- 搜索请求

## 🎨 前端增强

### 新增功能
1. **工具执行状态显示**: 实时显示工具开始执行
2. **步骤状态更新**: loading状态 → 完成状态
3. **优化的消息流**: 更流畅的用户体验

### 用户界面改进
- 实时状态指示器
- 工具执行进度
- 优化的错误提示

## 🔍 调试指南

### 常见问题

1. **WebSocket连接失败**
   - 检查后端API是否运行在正确端口
   - 验证防火墙设置

2. **工具不执行**
   - 检查工具注册是否成功
   - 查看后端日志

3. **前端无响应**
   - 检查浏览器控制台
   - 验证WebSocket连接状态

### 日志查看
- **后端**: 控制台输出，级别INFO
- **前端**: 浏览器开发者工具 → Console

## 📈 性能优化

### 已实现优化
1. **智能工具选择**: 避免不必要的工具调用
2. **流式响应**: 降低用户等待时间
3. **状态管理**: 高效的前端状态更新

### 建议配置
- 生产环境建议使用反向代理（如Nginx）
- 考虑使用Redis进行会话存储
- 启用日志轮转

## 🚨 注意事项

1. **API密钥**: 确保OpenAI API密钥已正确配置
2. **依赖版本**: 前端依赖可能需要更新
3. **浏览器兼容**: 建议使用现代浏览器
4. **网络环境**: WebSocket需要稳定的网络连接

---

🎉 现在您的前端应用已成功集成到MCP标准API中，享受流式输出和实时反馈的强大功能！ 