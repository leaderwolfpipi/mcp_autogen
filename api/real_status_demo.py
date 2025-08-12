"""
真实状态管理演示API
使用真实的工具执行系统，提供完整的任务执行流程
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
from core.task_engine import TaskEngine
from core.tool_registry import ToolRegistry

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建应用
app = FastAPI(
    title="真实状态管理演示API",
    description="使用真实工具执行的实时状态推送功能",
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
        # 使用SQLite数据库
        db_url = "sqlite:///./tools.db"
        tool_registry = ToolRegistry(db_url)
        tool_registry.discover_tools()
        
        # 获取可用工具列表
        available_tools = tool_registry.list_tools()
        logger.info(f"✅ 发现 {len(available_tools)} 个可用工具")
        
        # 打印工具名称列表
        tool_names = [tool.get('tool_id', 'unknown') for tool in available_tools]
        logger.info(f"工具列表: {', '.join(tool_names)}")
        
        # 初始化任务引擎
        logger.info("🚀 初始化任务执行引擎...")
        task_engine = TaskEngine(tool_registry)
        
        logger.info("🎯 真实状态管理演示系统启动完成！")
        
    except Exception as e:
        logger.error(f"❌ 系统初始化失败: {e}")
        # 创建一个基础的工具注册表作为回退
        try:
            db_url = "sqlite:///./tools.db" 
            tool_registry = ToolRegistry(db_url)
        except Exception as e2:
            logger.error(f"❌ 回退初始化也失败: {e2}")
            tool_registry = None
        task_engine = None


@app.websocket("/ws/demo")
async def demo_websocket(websocket: WebSocket):
    """真实执行演示WebSocket接口"""
    await websocket.accept()
    logger.info("🌐 真实执行WebSocket连接已建立")
    
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
                # 使用真实的任务执行流程
                await execute_real_task(user_input)
            finally:
                # 移除回调
                global_status_manager.remove_callback(callback)
                
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket连接断开")
    except Exception as e:
        logger.error(f"❌ WebSocket连接异常: {e}")


async def execute_real_task(user_input: str):
    """执行真实的任务流程"""
    try:
        # 检查任务引擎是否可用
        if not task_engine:
            await global_status_manager.report_error("任务引擎未初始化，无法执行真实任务")
            return
        
        # 1. 发送任务规划开始
        await global_status_manager.update_planning("正在使用真实任务引擎分析并制定执行计划...")
        
        # 2. 使用TaskEngine执行真实任务
        logger.info(f"🎯 开始执行真实任务: {user_input}")
        
        # 调用TaskEngine的execute方法
        result = await task_engine.execute(user_input, {})
        
        # 3. 处理执行结果
        if result.get('success', False):
            # 成功情况：提取执行步骤信息
            execution_steps = result.get('execution_steps', [])
            
            if execution_steps:
                # 创建执行计划（基于真实的执行步骤）
                steps_data = []
                for i, step in enumerate(execution_steps):
                    steps_data.append({
                        "tool_name": step.get('tool_name', f'step_{i}'),
                        "description": step.get('purpose', f"执行步骤 {i+1}"),
                        "input_params": step.get('input_params', {})
                    })
                
                # 启动执行计划（用于前端显示）
                execution_plan = await global_status_manager.start_task(user_input, steps_data)
                
                # 模拟步骤执行过程（基于真实结果）
                for i, step in enumerate(execution_steps):
                    plan_step = execution_plan.steps[i] if i < len(execution_plan.steps) else None
                    
                    if plan_step:
                        # 开始工具执行
                        await global_status_manager.start_tool(
                            plan_step.id, 
                            step.get('tool_name', plan_step.tool_name), 
                            step.get('input_params', {})
                        )
                        
                        # 短暂延迟以显示执行过程
                        await asyncio.sleep(0.5)
                        
                        # 完成工具执行（使用真实结果）
                        step_status = ExecutionStatus.SUCCESS if step.get('status') == 'success' else ExecutionStatus.ERROR
                        await global_status_manager.complete_tool(
                            plan_step.id,
                            step.get('tool_name', plan_step.tool_name),
                            step.get('output', {}),
                            step_status,
                            step.get('error')
                        )
                        
                        await asyncio.sleep(0.3)  # 步骤间隔
            else:
                # 如果是闲聊模式，创建一个简单的计划
                steps_data = [{
                    "tool_name": "chat_processor",
                    "description": "智能对话处理",
                    "input_params": {"query": user_input}
                }]
                
                execution_plan = await global_status_manager.start_task(user_input, steps_data)
                
                # 模拟闲聊处理
                step = execution_plan.steps[0]
                await global_status_manager.start_tool(step.id, step.tool_name, step.input_params)
                await asyncio.sleep(1)
                await global_status_manager.complete_tool(
                    step.id, step.tool_name, 
                    {"result": result.get('final_output', '处理完成')}, 
                    ExecutionStatus.SUCCESS
                )
            
            # 4. 完成任务（使用真实的最终输出）
            final_output = result.get('final_output', '任务执行完成')
            
            # 添加执行统计信息
            execution_time = result.get('execution_time', 0)
            step_count = result.get('step_count', 0)
            mode = result.get('mode', 'unknown')
            
            enhanced_output = f"""{final_output}

📊 执行统计：
- 模式：{mode}
- 执行步骤：{step_count}
- 执行时间：{execution_time:.2f}秒
- 状态：{'成功' if result.get('success') else '部分失败'}

🎯 这是真实的工具执行结果！"""
            
            await global_status_manager.complete_task(enhanced_output)
            
        else:
            # 失败情况
            error_message = result.get('error', '未知错误')
            final_output = result.get('final_output', f'任务执行失败: {error_message}')
            
            # 创建一个错误步骤
            steps_data = [{
                "tool_name": "error_handler",
                "description": "错误处理",
                "input_params": {"error": error_message}
            }]
            
            execution_plan = await global_status_manager.start_task(user_input, steps_data)
            step = execution_plan.steps[0]
            
            await global_status_manager.start_tool(step.id, step.tool_name, step.input_params)
            await asyncio.sleep(0.5)
            await global_status_manager.complete_tool(
                step.id, step.tool_name, 
                {"error": error_message}, 
                ExecutionStatus.ERROR,
                error_message
            )
            
            await global_status_manager.complete_task(final_output)
        
    except Exception as e:
        logger.error(f"真实任务执行失败: {e}")
        await global_status_manager.report_error(f"任务执行异常: {str(e)}")


@app.get("/")
async def demo_page():
    """演示页面"""
    demo_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 真实状态管理演示</title>
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 真实状态管理演示系统</h1>
            <p>使用真实工具执行 + 实时状态推送 + 动态执行流程展示</p>
        </div>
        
        <div class="info-banner">
            ✨ 本系统使用真实的TaskEngine和工具注册表，提供完整的任务执行体验！
        </div>
        
        <div class="demo-area">
            <!-- 聊天面板 -->
            <div class="chat-panel">
                <div class="panel-title">💬 真实任务执行测试</div>
                
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
                        🚀 真实执行系统已就绪，等待连接...
                    </div>
                </div>
                
                <div class="input-area">
                    <input type="text" id="messageInput" placeholder="输入任何问题或任务..." onkeypress="handleKeyPress(event)">
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
                addStatusEntry('🎯 真实执行系统已就绪');
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
                    const time = step.execution_time ? `(${step.execution_time.toFixed(2)}s)` : '';
                    addChatMessage('system', `${icon} ${step.tool_name} 完成 ${time}`);
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


@app.get("/tools")
async def list_available_tools():
    """获取可用工具列表"""
    if not tool_registry:
        return {"error": "工具注册表未初始化"}
    
    try:
        tools = tool_registry.list_tools()  # 这返回的是字典列表
        tool_details = []
        
        for tool_info in tools:
            tool_details.append({
                "name": tool_info.get("tool_id", "unknown"),
                "description": tool_info.get("description", "无描述"),
                "source": tool_info.get("source", "unknown"),
                "input_type": tool_info.get("input_type", "unknown"),
                "output_type": tool_info.get("output_type", "unknown")
            })
        
        return {
            "success": True,
            "tools": tool_details,
            "count": len(tool_details)
        }
    except Exception as e:
        return {"error": f"获取工具列表失败: {e}"}


if __name__ == "__main__":
    import uvicorn
    logger.info("🎯 启动真实状态管理演示服务...")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info") 