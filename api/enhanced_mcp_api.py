"""
增强版MCP API
集成执行状态管理器，支持实时状态推送和前端同步
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from contextlib import asynccontextmanager

from core.execution_status_manager import global_status_manager
try:
    from core.tool_registry import ToolRegistry
except ImportError:
    # 创建一个简单的工具注册表替代
    class ToolRegistry:
        def __init__(self):
            self.tools = {}
        def discover_tools(self):
            pass
        def list_tools(self):
            return ["smart_search", "web_search", "data_analyzer"]
        def get_tool_info(self, name):
            return {"description": f"Mock tool: {name}", "parameters": {}}


# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("🚀 启动增强版MCP API服务")
    
    # 初始化工具注册表
    tool_registry = ToolRegistry()
    tool_registry.discover_tools()
    
    # 将引擎存储到应用状态
    app.state.tool_registry = tool_registry
    
    yield
    
    # 关闭时清理
    logger.info("🛑 关闭增强版MCP API服务")


# 创建应用
app = FastAPI(
    title="增强版MCP API",
    description="支持实时状态推送的MCP协议API",
    version="2.0.0",
    lifespan=lifespan
)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """建立连接"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.logger.info(f"WebSocket连接建立: {session_id}")
    
    def disconnect(self, session_id: str):
        """断开连接"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            self.logger.info(f"WebSocket连接断开: {session_id}")
    
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """发送消息"""
        if session_id in self.active_connections:
            try:
                websocket = self.active_connections[session_id]
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                self.logger.error(f"发送消息失败 {session_id}: {e}")
                self.disconnect(session_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """广播消息"""
        for session_id in list(self.active_connections.keys()):
            await self.send_message(session_id, message)


# 全局连接管理器
connection_manager = ConnectionManager()


@app.websocket("/ws/mcp/enhanced")
async def enhanced_mcp_websocket(websocket: WebSocket):
    """
    增强版MCP WebSocket接口
    支持实时状态推送和前端同步
    """
    session_id = None
    
    try:
        # 接受连接
        await websocket.accept()
        logger.info("🌐 增强版MCP WebSocket连接已建立")
        
        # 获取增强版引擎
        enhanced_engine = app.state.enhanced_engine
        
        while True:
            try:
                # 接收客户端消息
                data = await websocket.receive_text()
                request_data = json.loads(data)
                
                user_input = request_data.get("user_input", "")
                session_id = request_data.get("session_id", "")
                
                if not user_input.strip():
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "用户输入不能为空"
                    }, ensure_ascii=False))
                    continue
                
                logger.info(f"📝 收到用户输入: {user_input[:50]}...")
                
                # 设置WebSocket回调
                async def websocket_send_func(message: Dict[str, Any]):
                    """WebSocket发送函数"""
                    try:
                        await websocket.send_text(json.dumps(message, ensure_ascii=False))
                    except Exception as e:
                        logger.error(f"WebSocket发送失败: {e}")
                
                # 为当前会话设置回调
                enhanced_engine.setup_websocket_callback(websocket_send_func)
                
                # 执行增强版对话流程
                async for result in enhanced_engine.execute_conversation_with_status(
                    user_input, session_id
                ):
                    # 结果已通过状态管理器自动发送，这里不需要额外发送
                    pass
                
                logger.info("✅ 增强版MCP对话流程完成")
                
            except json.JSONDecodeError as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"JSON解析错误: {str(e)}"
                }, ensure_ascii=False))
                
            except Exception as e:
                logger.error(f"❌ MCP对话处理失败: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"处理失败: {str(e)}"
                }, ensure_ascii=False))
                
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket连接断开")
        if session_id:
            connection_manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"❌ WebSocket连接异常: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"连接异常: {str(e)}"
            }, ensure_ascii=False))
        except:
            pass


@app.get("/api/status/current")
async def get_current_status():
    """获取当前执行状态"""
    try:
        current_plan = global_status_manager.get_current_plan()
        if current_plan:
            return {
                "success": True,
                "plan": current_plan.to_dict()
            }
        else:
            return {
                "success": True,
                "plan": None,
                "message": "当前没有执行中的任务"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/status/plan/{plan_id}")
async def get_plan_status(plan_id: str):
    """获取指定计划的状态"""
    try:
        plan = global_status_manager.get_plan_by_id(plan_id)
        if plan:
            return {
                "success": True,
                "plan": plan.to_dict()
            }
        else:
            return {
                "success": False,
                "error": f"未找到计划: {plan_id}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/tools/list")
async def list_available_tools():
    """获取可用工具列表"""
    try:
        tool_registry = app.state.tool_registry
        tools = []
        
        for tool_name in tool_registry.list_tools():
            tool_info = tool_registry.get_tool_info(tool_name)
            if tool_info:
                tools.append({
                    "name": tool_name,
                    "description": tool_info.get("description", ""),
                    "parameters": tool_info.get("parameters", {}),
                    "source": tool_info.get("source", "unknown")
                })
        
        return {
            "success": True,
            "tools": tools,
            "count": len(tools)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/demo/enhanced")
async def demo_enhanced_page():
    """增强版演示页面"""
    demo_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>增强版MCP演示</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
            background: #f8fafc;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 16px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .chat-container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.1);
            height: 600px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .chat-header {
            background: #f8fafc;
            padding: 20px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .message {
            max-width: 85%;
            padding: 16px 20px;
            border-radius: 20px;
            line-height: 1.5;
            word-wrap: break-word;
        }
        .message.user {
            align-self: flex-end;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .message.assistant {
            align-self: flex-start;
            background: #f1f5f9;
            color: #334155;
        }
        .message.system {
            align-self: center;
            background: #fef3c7;
            color: #92400e;
            border: 1px solid #fcd34d;
            font-size: 0.9em;
            text-align: center;
        }
        .message.error {
            align-self: center;
            background: #fee2e2;
            color: #dc2626;
            border: 1px solid #fca5a5;
        }
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        .status-dot.connected { background: #10b981; }
        .status-dot.disconnected { background: #ef4444; }
        .status-dot.processing { background: #f59e0b; }
        .chat-input {
            border-top: 1px solid #e2e8f0;
            padding: 20px;
            display: flex;
            gap: 12px;
        }
        .chat-input input {
            flex: 1;
            padding: 14px 18px;
            border: 2px solid #e2e8f0;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        .chat-input input:focus {
            border-color: #667eea;
        }
        .chat-input button {
            padding: 14px 28px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        .chat-input button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        .chat-input button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .execution-status {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
            margin: 16px 0;
            font-family: 'SF Mono', monospace;
            font-size: 14px;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 增强版MCP演示</h1>
        <p>实时状态推送 + 动态执行流程 + 前端状态同步</p>
    </div>
    
    <div class="chat-container">
        <div class="chat-header">
            <div>
                <strong>🤖 智能助手 v2.0</strong>
                <div class="execution-status" id="executionStatus" style="display: none;"></div>
            </div>
            <div class="status-indicator">
                <div class="status-dot disconnected" id="statusDot"></div>
                <span id="statusText">未连接</span>
            </div>
        </div>
        
        <div id="chatMessages" class="chat-messages">
            <div class="message system">
                👋 欢迎使用增强版MCP演示！现在支持实时状态推送和动态执行流程展示。
            </div>
        </div>
        
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="输入您的问题或任务..." onkeypress="handleKeyPress(event)">
            <button id="sendButton" onclick="sendMessage()" disabled>发送</button>
        </div>
    </div>

    <script>
        let ws = null;
        let isProcessing = false;
        let currentSessionId = null;
        
        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws/mcp/enhanced`);
            
            ws.onopen = function() {
                updateStatus('connected', '已连接');
                document.getElementById('sendButton').disabled = false;
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };
            
            ws.onclose = function() {
                updateStatus('disconnected', '连接断开');
                document.getElementById('sendButton').disabled = true;
                setTimeout(initWebSocket, 3000);
            };
            
            ws.onerror = function(error) {
                updateStatus('disconnected', '连接错误');
                console.error('WebSocket error:', error);
            };
        }
        
        function handleMessage(data) {
            const statusDiv = document.getElementById('executionStatus');
            
            switch(data.type) {
                case 'mode_detection':
                    currentSessionId = data.session_id;
                    addMessage('system', `🔍 模式检测: ${data.message}`);
                    break;
                    
                case 'task_planning':
                    addMessage('system', `📋 ${data.message}`);
                    if (data.plan) {
                        showExecutionPlan(data.plan);
                    }
                    break;
                    
                case 'task_start':
                    addMessage('system', `🚀 ${data.message}`);
                    showExecutionPlan(data.plan);
                    break;
                    
                case 'tool_start':
                    addMessage('system', `🔧 ${data.message}`);
                    updateExecutionStatus(`正在执行: ${data.tool_name}`);
                    break;
                    
                case 'tool_result':
                    const step = data.step_data;
                    const icon = step.status === 'success' ? '✅' : '❌';
                    addMessage('system', `${icon} 工具完成: ${step.tool_name} (${step.execution_time?.toFixed(2)}s)`);
                    break;
                    
                case 'task_complete':
                    addMessage('assistant', data.message);
                    addMessage('system', `✅ 任务完成，用时 ${data.execution_time?.toFixed(2)} 秒`);
                    hideExecutionStatus();
                    setProcessing(false);
                    break;
                    
                case 'chat_response':
                    addMessage('assistant', data.message);
                    setProcessing(false);
                    break;
                    
                case 'error':
                    addMessage('error', '❌ ' + data.message);
                    hideExecutionStatus();
                    setProcessing(false);
                    break;
            }
        }
        
        function addMessage(type, content) {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.textContent = content;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function showExecutionPlan(plan) {
            const statusDiv = document.getElementById('executionStatus');
            statusDiv.style.display = 'block';
            statusDiv.innerHTML = `
                <strong>执行计划:</strong><br>
                查询: ${plan.query}<br>
                步骤数: ${plan.steps.length}<br>
                状态: ${plan.status}
            `;
        }
        
        function updateExecutionStatus(message) {
            const statusDiv = document.getElementById('executionStatus');
            statusDiv.style.display = 'block';
            statusDiv.innerHTML = `<strong>执行状态:</strong> ${message}`;
        }
        
        function hideExecutionStatus() {
            const statusDiv = document.getElementById('executionStatus');
            statusDiv.style.display = 'none';
        }
        
        function updateStatus(status, text) {
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            statusDot.className = `status-dot ${status}`;
            statusText.textContent = text;
        }
        
        function setProcessing(processing) {
            isProcessing = processing;
            const sendButton = document.getElementById('sendButton');
            
            if (processing) {
                sendButton.disabled = true;
                sendButton.textContent = '处理中...';
                updateStatus('processing', '处理中');
            } else {
                sendButton.disabled = false;
                sendButton.textContent = '发送';
                updateStatus('connected', '已连接');
            }
        }
        
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || !ws || ws.readyState !== WebSocket.OPEN || isProcessing) {
                return;
            }
            
            addMessage('user', message);
            
            ws.send(JSON.stringify({
                user_input: message,
                session_id: currentSessionId
            }));
            
            input.value = '';
            setProcessing(true);
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter' && !isProcessing) {
                sendMessage();
            }
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            initWebSocket();
        });
    </script>
</body>
</html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=demo_html)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 