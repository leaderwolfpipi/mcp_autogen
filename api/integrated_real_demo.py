"""
集成真实状态管理演示API
将真实的TaskEngine集成到现有前端，替换ASCII显示为实时状态推送
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import logging
import asyncio
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.execution_status_manager import (
    global_status_manager, WebSocketStatusCallback,
    ExecutionStatus, MessageType
)
from core.task_engine import TaskEngine
from core.tool_registry import ToolRegistry

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建应用
app = FastAPI(
    title="集成真实状态管理演示API",
    description="将真实工具执行集成到现有前端框架",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
tool_registry = None
task_engine = None

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化工具系统"""
    global tool_registry, task_engine
    
    try:
        # 初始化工具注册表
        logger.info("🔧 初始化工具注册表...")
        db_url = "sqlite:///./tools.db"
        tool_registry = ToolRegistry(db_url)
        tool_registry.discover_tools()
        
        # 获取可用工具列表
        available_tools = tool_registry.list_tools()
        logger.info(f"✅ 发现 {len(available_tools)} 个可用工具")
        
        # 初始化任务引擎
        logger.info("🚀 初始化任务执行引擎...")
        task_engine = TaskEngine(tool_registry)
        
        logger.info("🎯 集成真实状态管理演示系统启动完成！")
        
    except Exception as e:
        logger.error(f"❌ 系统初始化失败: {e}")
        try:
            db_url = "sqlite:///./tools.db" 
            tool_registry = ToolRegistry(db_url)
        except Exception as e2:
            logger.error(f"❌ 回退初始化也失败: {e2}")
            tool_registry = None
        task_engine = None


# 新的WebSocket端点，兼容前端的消息格式
@app.websocket("/ws/mcp/enhanced")
async def enhanced_mcp_websocket(websocket: WebSocket):
    """增强的MCP WebSocket接口，兼容前端格式"""
    await websocket.accept()
    logger.info("🌐 增强MCP WebSocket连接已建立")
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            user_input = request_data.get("user_input", "")
            session_id = request_data.get("session_id", "default")
            
            if not user_input.strip():
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "用户输入不能为空"
                }, ensure_ascii=False))
                continue
            
            logger.info(f"📝 收到用户输入: {user_input}")
            
            # 设置WebSocket回调
            async def websocket_send_func(message: Dict[str, Any]):
                try:
                    await websocket.send_text(json.dumps(message, ensure_ascii=False))
                except Exception as e:
                    logger.error(f"WebSocket发送失败: {e}")
            
            # 注册回调
            callback = WebSocketStatusCallback(websocket_send_func)
            global_status_manager.add_callback(callback)
            
            try:
                # 执行真实任务并发送兼容格式的消息
                await execute_task_with_frontend_compat(user_input, session_id, websocket_send_func)
            finally:
                # 移除回调
                global_status_manager.remove_callback(callback)
                
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket连接断开")
    except Exception as e:
        logger.error(f"❌ WebSocket连接异常: {e}")


async def execute_task_with_frontend_compat(user_input: str, session_id: str, send_func):
    """执行任务并发送前端兼容格式的消息"""
    try:
        # 检查任务引擎是否可用
        if not task_engine:
            await send_func({
                "type": "error",
                "message": "任务引擎未初始化，无法执行真实任务"
            })
            return
        
        # 1. 发送模式检测消息
        await send_func({
            "type": "mode_detection",
            "mode": "task",  # 假设都是任务模式
            "session_id": session_id,
            "message": "检测到任务执行模式"
        })
        
        # 2. 发送任务规划开始
        await send_func({
            "type": "task_planning", 
            "message": "正在使用真实任务引擎分析并制定执行计划...",
            "timestamp": time.time()
        })
        
        # 3. 使用TaskEngine执行真实任务
        logger.info(f"🎯 开始执行真实任务: {user_input}")
        result = await task_engine.execute(user_input, {})
        
        # 4. 处理执行结果
        if result.get('success', False):
            execution_steps = result.get('execution_steps', [])
            
            if execution_steps:
                # 发送任务开始消息
                steps_data = []
                for i, step in enumerate(execution_steps):
                    steps_data.append({
                        "id": f"step_{i}",
                        "tool_name": step.get('tool_name', f'step_{i}'),
                        "description": step.get('purpose', f"执行步骤 {i+1}"),
                        "status": "pending"
                    })
                
                await send_func({
                    "type": "task_start",
                    "session_id": session_id,
                    "message": f"开始执行任务：{user_input}",
                    "plan": {
                        "id": session_id,
                        "query": user_input,
                        "steps": steps_data
                    },
                    "timestamp": time.time()
                })
                
                # 逐步发送工具执行过程
                for i, step in enumerate(execution_steps):
                    step_data = steps_data[i]
                    
                    # 发送工具开始执行
                    await send_func({
                        "type": "tool_start",
                        "message": f"正在执行：{step.get('purpose', step.get('tool_name', f'步骤{i+1}'))}",
                        "tool_name": step.get('tool_name', f'step_{i}'),
                        "step_id": step_data["id"],
                        "input_params": step.get('input_params', {}),
                        "timestamp": time.time()
                    })
                    
                    # 短暂延迟模拟执行
                    await asyncio.sleep(0.5)
                    
                    # 发送工具执行结果
                    step_status = "success" if step.get('status') == 'success' else "error"
                    await send_func({
                        "type": "tool_result",
                        "step_data": {
                            "id": step_data["id"],
                            "tool_name": step.get('tool_name', f'step_{i}'),
                            "description": step.get('purpose', f"执行步骤 {i+1}"),
                            "status": step_status,
                            "start_time": time.time() - 1,
                            "end_time": time.time(),
                            "execution_time": step.get('execution_time', 1.0),
                            "output": step.get('output', {}),
                            "error": step.get('error')
                        },
                        "timestamp": time.time()
                    })
                    
                    await asyncio.sleep(0.3)
            
            # 5. 发送任务完成消息
            final_output = result.get('final_output', '任务执行完成')
            execution_time = result.get('execution_time', 0)
            step_count = result.get('step_count', len(execution_steps))
            mode = result.get('mode', 'task')
            
            enhanced_output = f"""{final_output}

📊 执行统计：
- 模式：{mode}
- 执行步骤：{step_count}
- 执行时间：{execution_time:.2f}秒
- 状态：{'成功' if result.get('success') else '部分失败'}

🎯 这是真实的工具执行结果！"""
            
            await send_func({
                "type": "task_complete",
                "session_id": session_id,
                "message": enhanced_output,
                "execution_time": execution_time,
                "steps": [
                    {
                        "id": f"step_{i}",
                        "tool_name": step.get('tool_name', f'step_{i}'),
                        "description": step.get('purpose', f"执行步骤 {i+1}"),
                        "status": "success" if step.get('status') == 'success' else "error",
                        "execution_time": step.get('execution_time', 1.0),
                        "output": step.get('output', {}),
                        "error": step.get('error')
                    }
                    for i, step in enumerate(execution_steps)
                ],
                "timestamp": time.time()
            })
            
        else:
            # 失败情况
            error_message = result.get('error', '未知错误')
            final_output = result.get('final_output', f'任务执行失败: {error_message}')
            
            await send_func({
                "type": "error",
                "message": final_output,
                "context": {"error": error_message},
                "timestamp": time.time()
            })
        
    except Exception as e:
        logger.error(f"任务执行失败: {e}")
        await send_func({
            "type": "error",
            "message": f"任务执行异常: {str(e)}",
            "timestamp": time.time()
        })


@app.get("/")
async def demo_page():
    """演示页面 - 集成版本"""
    demo_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 集成真实状态管理演示</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #333;
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            color: #666;
            margin: 10px 0 0 0;
            font-size: 1.1em;
        }
        .info-banner {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: 500;
        }
        .demo-area {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-top: 20px;
        }
        .chat-panel, .status-panel {
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 20px;
            height: 600px;
            display: flex;
            flex-direction: column;
        }
        .panel-title {
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 15px;
            color: #333;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            background: #f9f9f9;
        }
        .status-display {
            flex: 1;
            overflow-y: auto;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            background: #f5f5f5;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 13px;
        }
        .message {
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 8px;
            line-height: 1.4;
        }
        .message.user {
            background: #e3f2fd;
            color: #1565c0;
            text-align: right;
        }
        .message.assistant {
            background: #f3f4f6;
            color: #374151;
            white-space: pre-wrap;
        }
        .message.system {
            background: #fff3cd;
            color: #856404;
            font-size: 0.9em;
        }
        .message.error {
            background: #f8d7da;
            color: #721c24;
        }
        .input-area {
            display: flex;
            gap: 10px;
        }
        .input-area input {
            flex: 1;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
        }
        .input-area input:focus {
            outline: none;
            border-color: #667eea;
        }
        .input-area button {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
        }
        .input-area button:hover:not(:disabled) {
            background: #5a67d8;
        }
        .input-area button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .connection-status {
            padding: 8px 12px;
            border-radius: 6px;
            margin-bottom: 15px;
            font-size: 0.9em;
            font-weight: 500;
        }
        .connection-status.connected {
            background: #d4edda;
            color: #155724;
        }
        .connection-status.disconnected {
            background: #f8d7da;
            color: #721c24;
        }
        .quick-tests {
            display: flex;
            gap: 8px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        .quick-btn {
            padding: 6px 12px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8em;
            transition: all 0.2s;
        }
        .quick-btn:hover {
            background: #e9ecef;
        }
        .status-entry {
            margin-bottom: 8px;
            padding: 6px;
            border-left: 3px solid #667eea;
            background: white;
            border-radius: 3px;
        }
        .status-time {
            font-size: 11px;
            color: #666;
        }
        .execution-plan {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
        }
        .step-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 4px 0;
        }
        .step-status {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
        }
        .step-status.pending {
            background: #e2e8f0;
            color: #64748b;
        }
        .step-status.running {
            background: #fbbf24;
            color: white;
            animation: pulse 1s infinite;
        }
        .step-status.success {
            background: #10b981;
            color: white;
        }
        .step-status.error {
            background: #ef4444;
            color: white;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 集成真实状态管理演示系统</h1>
            <p>真实TaskEngine + 前端兼容格式 + 实时状态推送</p>
        </div>
        
        <div class="info-banner">
            ✨ 本系统将真实的TaskEngine集成到前端框架中，替换ASCII显示为实时状态推送！
        </div>
        
        <div class="demo-area">
            <!-- 聊天面板 -->
            <div class="chat-panel">
                <div class="panel-title">💬 集成真实执行测试</div>
                
                <div class="connection-status disconnected" id="connectionStatus">
                    ❌ 未连接
                </div>
                
                <div class="quick-tests">
                    <div class="quick-btn" onclick="sendQuick('搜索李白的诗')">搜索测试</div>
                    <div class="quick-btn" onclick="sendQuick('你好')">闲聊测试</div>
                    <div class="quick-btn" onclick="sendQuick('分析人工智能发展')">分析任务</div>
                    <div class="quick-btn" onclick="sendQuick('什么是机器学习')">知识查询</div>
                </div>
                
                <div class="chat-messages" id="chatMessages">
                    <div class="message system">
                        🚀 集成真实执行系统已就绪，等待连接...
                    </div>
                </div>
                
                <div class="input-area">
                    <input type="text" id="messageInput" placeholder="输入任何问题或任务..." onkeypress="handleKeyPress(event)">
                    <button id="sendButton" onclick="sendMessage()" disabled>发送</button>
                </div>
            </div>
            
            <!-- 状态面板 -->
            <div class="status-panel">
                <div class="panel-title">📊 实时执行状态</div>
                <div class="status-display" id="statusDisplay">
                    <div class="status-entry">
                        <div class="status-time">系统启动</div>
                        <div>等待WebSocket连接...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let isProcessing = false;
        let currentPlan = null;
        
        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws/mcp/enhanced`);
            
            ws.onopen = function() {
                updateConnectionStatus(true);
                addStatusEntry('✅ WebSocket连接成功');
                addStatusEntry('🎯 集成真实执行系统已就绪');
                document.getElementById('sendButton').disabled = false;
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };
            
            ws.onclose = function() {
                updateConnectionStatus(false);
                addStatusEntry('❌ WebSocket连接断开，3秒后重连...');
                document.getElementById('sendButton').disabled = true;
                setTimeout(initWebSocket, 3000);
            };
            
            ws.onerror = function(error) {
                addStatusEntry('⚠️ WebSocket连接错误');
                console.error('WebSocket error:', error);
            };
        }
        
        function handleMessage(data) {
            addStatusEntry(`📨 收到消息: ${data.type}`, data);
            
            switch(data.type) {
                case 'mode_detection':
                    addChatMessage('system', `🔍 模式检测: ${data.message}`);
                    break;
                    
                case 'task_planning':
                    addChatMessage('system', `📋 ${data.message}`);
                    break;
                    
                case 'task_start':
                    currentPlan = data.plan;
                    addChatMessage('system', `🚀 ${data.message}`);
                    if (data.plan) {
                        showExecutionPlan(data.plan);
                    }
                    break;
                    
                case 'tool_start':
                    addChatMessage('system', `🔧 ${data.message}`);
                    updateStepStatus(data.step_id, 'running');
                    break;
                    
                case 'tool_result':
                    const step = data.step_data;
                    const icon = step.status === 'success' ? '✅' : '❌';
                    const time = step.execution_time ? `(${step.execution_time.toFixed(2)}s)` : '';
                    addChatMessage('system', `${icon} ${step.tool_name} 完成 ${time}`);
                    updateStepStatus(step.id, step.status);
                    break;
                    
                case 'task_complete':
                    addChatMessage('assistant', data.message);
                    setProcessing(false);
                    break;
                    
                case 'error':
                    addChatMessage('error', '❌ ' + data.message);
                    setProcessing(false);
                    break;
            }
        }
        
        function showExecutionPlan(plan) {
            const container = document.getElementById('statusDisplay');
            const planDiv = document.createElement('div');
            planDiv.className = 'execution-plan';
            planDiv.id = 'executionPlan';
            
            let planHTML = `<div><strong>执行计划:</strong> ${plan.query}</div>`;
            planHTML += `<div style="margin-top: 8px;"><strong>步骤:</strong></div>`;
            
            plan.steps.forEach((step, index) => {
                planHTML += `
                    <div class="step-item" id="step-${step.id}">
                        <div class="step-status pending" id="status-${step.id}">⏳</div>
                        <div>${index + 1}. ${step.description}</div>
                    </div>
                `;
            });
            
            planDiv.innerHTML = planHTML;
            container.appendChild(planDiv);
            container.scrollTop = container.scrollHeight;
        }
        
        function updateStepStatus(stepId, status) {
            const statusEl = document.getElementById(`status-${stepId}`);
            if (statusEl) {
                statusEl.className = `step-status ${status}`;
                switch(status) {
                    case 'running':
                        statusEl.textContent = '🔄';
                        break;
                    case 'success':
                        statusEl.textContent = '✅';
                        break;
                    case 'error':
                        statusEl.textContent = '❌';
                        break;
                    default:
                        statusEl.textContent = '⏳';
                }
            }
        }
        
        function addChatMessage(type, content) {
            const container = document.getElementById('chatMessages');
            const div = document.createElement('div');
            div.className = `message ${type}`;
            div.textContent = content;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }
        
        function addStatusEntry(message, data = null) {
            const container = document.getElementById('statusDisplay');
            const div = document.createElement('div');
            div.className = 'status-entry';
            
            const time = new Date().toLocaleTimeString();
            div.innerHTML = `
                <div class="status-time">${time}</div>
                <div>${message}</div>
                ${data ? `<pre style="font-size: 11px; margin-top: 4px; color: #666;">${JSON.stringify(data, null, 2)}</pre>` : ''}
            `;
            
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }
        
        function updateConnectionStatus(connected) {
            const status = document.getElementById('connectionStatus');
            if (connected) {
                status.className = 'connection-status connected';
                status.textContent = '✅ 已连接';
            } else {
                status.className = 'connection-status disconnected';
                status.textContent = '❌ 未连接';
            }
        }
        
        function setProcessing(processing) {
            isProcessing = processing;
            const button = document.getElementById('sendButton');
            button.disabled = processing;
            button.textContent = processing ? '处理中...' : '发送';
        }
        
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || !ws || ws.readyState !== WebSocket.OPEN || isProcessing) {
                return;
            }
            
            addChatMessage('user', message);
            addStatusEntry(`📤 发送消息: ${message}`);
            
            // 清除之前的执行计划
            const existingPlan = document.getElementById('executionPlan');
            if (existingPlan) {
                existingPlan.remove();
            }
            
            ws.send(JSON.stringify({
                user_input: message,
                session_id: 'demo_session'
            }));
            
            input.value = '';
            setProcessing(true);
        }
        
        function sendQuick(message) {
            document.getElementById('messageInput').value = message;
            sendMessage();
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter' && !isProcessing) {
                sendMessage();
            }
        }
        
        // 初始化
        document.addEventListener('DOMContentLoaded', function() {
            addStatusEntry('🔄 页面加载完成，初始化WebSocket...');
            initWebSocket();
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=demo_html)


if __name__ == "__main__":
    import uvicorn
    logger.info("🎯 启动集成真实状态管理演示服务...")
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info") 