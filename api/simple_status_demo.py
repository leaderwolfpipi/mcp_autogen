"""
简单的状态管理演示API
测试执行状态管理器的实时推送功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import logging
import asyncio
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from core.execution_status_manager import (
    global_status_manager, WebSocketStatusCallback,
    ExecutionStatus, MessageType
)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建应用
app = FastAPI(
    title="状态管理演示API",
    description="测试实时状态推送功能",
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


@app.websocket("/ws/demo")
async def demo_websocket(websocket: WebSocket):
    """演示WebSocket接口"""
    await websocket.accept()
    logger.info("🌐 演示WebSocket连接已建立")
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            user_input = request_data.get("user_input", "")
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
                # 模拟任务执行流程
                await simulate_task_execution(user_input)
            finally:
                # 移除回调
                global_status_manager.remove_callback(callback)
                
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket连接断开")
    except Exception as e:
        logger.error(f"❌ WebSocket连接异常: {e}")


async def simulate_task_execution(user_input: str):
    """模拟任务执行过程"""
    try:
        # 1. 发送任务规划开始
        await global_status_manager.update_planning("正在分析任务并制定执行计划...")
        await asyncio.sleep(1)  # 模拟规划时间
        
        # 2. 创建执行计划
        if "搜索" in user_input:
            steps_data = [
                {
                    "tool_name": "smart_search",
                    "description": f"智能搜索：{user_input}",
                    "input_params": {"query": user_input, "max_results": 5}
                }
            ]
        elif "分析" in user_input:
            steps_data = [
                {
                    "tool_name": "data_analyzer",
                    "description": "数据分析",
                    "input_params": {"data": user_input}
                },
                {
                    "tool_name": "report_generator",
                    "description": "生成报告",
                    "input_params": {"format": "markdown"}
                }
            ]
        else:
            steps_data = [
                {
                    "tool_name": "smart_processor",
                    "description": f"智能处理：{user_input}",
                    "input_params": {"input": user_input}
                }
            ]
        
        # 3. 启动执行计划
        execution_plan = await global_status_manager.start_task(user_input, steps_data)
        await asyncio.sleep(0.5)  # 短暂延迟
        
        # 4. 执行每个步骤
        for step in execution_plan.steps:
            # 开始工具执行
            await global_status_manager.start_tool(
                step.id, step.tool_name, step.input_params
            )
            
            # 模拟工具执行时间
            execution_time = 1.5 if "search" in step.tool_name else 2.0
            await asyncio.sleep(execution_time)
            
            # 模拟执行结果
            mock_result = {
                "tool_name": step.tool_name,
                "status": "success",
                "result": f"模拟{step.tool_name}执行结果：{step.description}",
                "data": f"这是{step.tool_name}返回的模拟数据",
                "execution_time": execution_time
            }
            
            # 完成工具执行
            await global_status_manager.complete_tool(
                step.id, step.tool_name, mock_result, ExecutionStatus.SUCCESS
            )
            
            await asyncio.sleep(0.3)  # 步骤间隔
        
        # 5. 生成最终结果
        final_result = f"""任务执行完成！

根据您的请求「{user_input}」，我执行了以下操作：

""" + "\n".join([f"✅ {step.description}" for step in execution_plan.steps]) + f"""

📊 执行统计：
- 总步骤数：{len(execution_plan.steps)}
- 执行时间：{time.time() - execution_plan.start_time:.2f}秒
- 状态：全部成功

🎯 这是一个演示系统，展示了实时状态推送的完整流程。"""
        
        # 6. 完成任务
        await global_status_manager.complete_task(final_result)
        
    except Exception as e:
        logger.error(f"任务执行失败: {e}")
        await global_status_manager.report_error(f"任务执行失败: {str(e)}")


@app.get("/")
async def demo_page():
    """演示页面"""
    demo_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 状态管理演示</title>
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
            height: 500px;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 状态管理演示系统</h1>
            <p>实时状态推送 + 动态执行流程展示</p>
        </div>
        
        <div class="demo-area">
            <!-- 聊天面板 -->
            <div class="chat-panel">
                <div class="panel-title">💬 对话测试</div>
                
                <div class="connection-status disconnected" id="connectionStatus">
                    ❌ 未连接
                </div>
                
                <div class="quick-tests">
                    <div class="quick-btn" onclick="sendQuick('搜索人工智能')">搜索测试</div>
                    <div class="quick-btn" onclick="sendQuick('分析销售数据')">分析测试</div>
                    <div class="quick-btn" onclick="sendQuick('生成报告')">复杂任务</div>
                </div>
                
                <div class="chat-messages" id="chatMessages">
                    <div class="message system">
                        🚀 系统已就绪，等待连接...
                    </div>
                </div>
                
                <div class="input-area">
                    <input type="text" id="messageInput" placeholder="输入测试消息..." onkeypress="handleKeyPress(event)">
                    <button id="sendButton" onclick="sendMessage()" disabled>发送</button>
                </div>
            </div>
            
            <!-- 状态面板 -->
            <div class="status-panel">
                <div class="panel-title">📊 实时状态监控</div>
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
        
        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws/demo`);
            
            ws.onopen = function() {
                updateConnectionStatus(true);
                addStatusEntry('✅ WebSocket连接成功');
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
                case 'task_planning':
                    addChatMessage('system', `📋 ${data.message}`);
                    break;
                    
                case 'task_start':
                    addChatMessage('system', `🚀 ${data.message}`);
                    break;
                    
                case 'tool_start':
                    addChatMessage('system', `🔧 ${data.message}`);
                    break;
                    
                case 'tool_result':
                    const step = data.step_data;
                    const icon = step.status === 'success' ? '✅' : '❌';
                    addChatMessage('system', `${icon} ${step.tool_name} 完成 (${step.execution_time?.toFixed(2)}s)`);
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
            
            ws.send(JSON.stringify({
                user_input: message
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
    logger.info("🎯 启动状态管理演示服务...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info") 