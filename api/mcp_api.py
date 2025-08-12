#!/usr/bin/env python3
"""
MCP协议API接口
实现标准的MCP（Model Context Protocol）协议接口
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mcp_protocol_engine import get_mcp_engine
from core.database_manager import get_database_manager
from cmd.import_tools import import_tools


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 请求/响应模型
class MCPChatRequest(BaseModel):
    user_input: str
    session_id: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None


class MCPChatResponse(BaseModel):
    session_id: str
    message: str
    mode: str  # "chat" or "task"
    execution_time: Optional[float] = None
    steps: Optional[list] = None
    mermaid_diagram: Optional[str] = None


# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 启动MCP协议API服务")
    
    # 初始化数据库
    db_manager = get_database_manager()
    
    # 导入工具
    try:
        import_tools()
        logger.info("✅ 工具导入完成")
    except Exception as e:
        logger.warning(f"⚠️ 工具导入失败: {e}")
    
    # 初始化MCP引擎
    llm_config = {
        "type": "openai",  # 或 "ernie"
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4-turbo",
        "base_url": os.getenv("OPENAI_BASE_URL")
    }
    
    mcp_engine = get_mcp_engine(llm_config, db_manager)
    app.state.mcp_engine = mcp_engine
    
    logger.info("🎉 MCP协议API服务启动完成")
    
    yield
    
    logger.info("🛑 MCP协议API服务关闭")


# 创建FastAPI应用
app = FastAPI(
    title="MCP AutoGen API",
    description="基于MCP协议的智能工具调用系统",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "MCP AutoGen API v2.0",
        "protocol": "MCP (Model Context Protocol)",
        "description": "智能工具调用系统，支持标准MCP协议"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "protocol": "MCP"
    }


@app.get("/tools")
async def list_tools():
    """获取可用工具列表"""
    try:
        mcp_engine = app.state.mcp_engine
        tools = await mcp_engine._get_available_tools()
        
        return {
            "tools": [
                {
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "parameters": tool["function"]["parameters"]
                }
                for tool in tools
            ],
            "count": len(tools)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {str(e)}")


@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """获取会话历史"""
    try:
        mcp_engine = app.state.mcp_engine
        history = mcp_engine.get_session_history(session_id)
        
        return {
            "session_id": session_id,
            "history": history,
            "message_count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话历史失败: {str(e)}")


@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """清除会话"""
    try:
        mcp_engine = app.state.mcp_engine
        mcp_engine.clear_session(session_id)
        
        return {
            "message": f"会话 {session_id} 已清除"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除会话失败: {str(e)}")


@app.websocket("/ws/mcp/chat")
async def mcp_chat_websocket(websocket: WebSocket):
    """
    MCP协议WebSocket聊天接口
    实现标准的MCP对话流程，支持实时流式输出
    """
    await websocket.accept()
    logger.info("🔗 MCP WebSocket连接已建立")
    
    try:
        mcp_engine = app.state.mcp_engine
        
        while True:
            # 接收客户端消息
            try:
                data = await websocket.receive_text()
                request_data = json.loads(data)
                
                user_input = request_data.get("user_input", "")
                session_id = request_data.get("session_id")
                
                if not user_input.strip():
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "用户输入不能为空"
                    }, ensure_ascii=False))
                    continue
                
                logger.info(f"📝 收到用户输入: {user_input[:50]}...")
                
                # 执行MCP对话流程
                async for result in mcp_engine.execute_conversation(user_input, session_id):
                    # 发送流式结果
                    await websocket.send_text(json.dumps(result, ensure_ascii=False))
                
                logger.info("✅ MCP对话流程完成")
                
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
        logger.info("🔌 MCP WebSocket连接断开")
    except Exception as e:
        logger.error(f"❌ MCP WebSocket错误: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"WebSocket错误: {str(e)}"
            }, ensure_ascii=False))
        except:
            pass


@app.websocket("/ws/mcp/stream")
async def mcp_stream_websocket(websocket: WebSocket):
    """
    MCP协议流式WebSocket接口
    支持更细粒度的流式控制
    """
    await websocket.accept()
    logger.info("🌊 MCP流式WebSocket连接已建立")
    
    try:
        mcp_engine = app.state.mcp_engine
        
        while True:
            try:
                data = await websocket.receive_text()
                request_data = json.loads(data)
                
                user_input = request_data.get("user_input", "")
                session_id = request_data.get("session_id")
                
                if not user_input.strip():
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "用户输入不能为空"
                    }, ensure_ascii=False))
                    continue
                
                # 发送开始信号
                await websocket.send_text(json.dumps({
                    "type": "stream_start",
                    "session_id": session_id,
                    "user_input": user_input
                }, ensure_ascii=False))
                
                # 执行流式对话
                async for chunk in mcp_engine.execute_conversation(user_input, session_id):
                    await websocket.send_text(json.dumps({
                        "type": "stream_chunk",
                        "data": chunk
                    }, ensure_ascii=False))
                
                # 发送结束信号
                await websocket.send_text(json.dumps({
                    "type": "stream_end",
                    "session_id": session_id
                }, ensure_ascii=False))
                
            except json.JSONDecodeError as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"JSON解析错误: {str(e)}"
                }, ensure_ascii=False))
                
            except Exception as e:
                logger.error(f"❌ MCP流式处理失败: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"处理失败: {str(e)}"
                }, ensure_ascii=False))
                
    except WebSocketDisconnect:
        logger.info("🔌 MCP流式WebSocket连接断开")
    except Exception as e:
        logger.error(f"❌ MCP流式WebSocket错误: {e}")


# 静态文件服务
@app.get("/demo")
async def demo_page():
    """演示页面"""
    demo_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP AutoGen 演示</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 10px 0; }
        .chat-container { height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user-message { background-color: #e3f2fd; text-align: right; }
        .ai-message { background-color: #f1f8e9; }
        .task-message { background-color: #fff3e0; border-left: 4px solid #ff9800; }
        .input-container { display: flex; gap: 10px; }
        .input-container input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
        .input-container button { padding: 10px 20px; background-color: #2196f3; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .mermaid-diagram { text-align: center; margin: 20px 0; }
        .status { padding: 5px 10px; border-radius: 3px; font-size: 12px; margin: 5px 0; }
        .status.success { background-color: #d4edda; color: #155724; }
        .status.error { background-color: #f8d7da; color: #721c24; }
        .status.info { background-color: #d1ecf1; color: #0c5460; }
    </style>
</head>
<body>
    <h1>🚀 MCP AutoGen 演示</h1>
    <p>基于MCP协议的智能工具调用系统</p>
    
    <div class="container">
        <h3>💬 对话界面</h3>
        <div id="chatContainer" class="chat-container"></div>
        <div class="input-container">
            <input type="text" id="userInput" placeholder="输入您的问题..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">发送</button>
            <button onclick="clearChat()">清空</button>
        </div>
        <div id="status" class="status info">准备就绪</div>
    </div>
    
    <div class="container">
        <h3>🔧 可用工具</h3>
        <div id="toolsList">加载中...</div>
    </div>

    <script>
        let ws = null;
        let currentSessionId = null;
        
        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws/mcp/chat`);
            
            ws.onopen = function() {
                updateStatus('WebSocket连接已建立', 'success');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };
            
            ws.onclose = function() {
                updateStatus('WebSocket连接已断开', 'error');
                setTimeout(initWebSocket, 3000); // 3秒后重连
            };
            
            ws.onerror = function(error) {
                updateStatus('WebSocket连接错误', 'error');
            };
        }
        
        function handleWebSocketMessage(data) {
            const chatContainer = document.getElementById('chatContainer');
            
            switch(data.type) {
                case 'mode_detection':
                    currentSessionId = data.session_id;
                    addMessage('system', `🔍 ${data.message}`, 'ai-message');
                    break;
                    
                case 'chat_response':
                    addMessage('assistant', data.message, 'ai-message');
                    updateStatus('对话完成', 'success');
                    break;
                    
                case 'task_start':
                    addMessage('system', '🔧 开始任务执行...', 'task-message');
                    break;
                    
                case 'tool_result':
                    const step = data.step;
                    const stepMessage = `✅ 执行工具: ${step.tool_name}\\n⏱️ 用时: ${step.execution_time.toFixed(2)}秒`;
                    addMessage('tool', stepMessage, 'task-message');
                    
                    if (data.mermaid_diagram) {
                        addMermaidDiagram(data.mermaid_diagram);
                    }
                    break;
                    
                case 'task_complete':
                    addMessage('assistant', data.message, 'ai-message');
                    if (data.mermaid_diagram) {
                        addMermaidDiagram(data.mermaid_diagram);
                    }
                    updateStatus(`任务完成，用时: ${data.execution_time.toFixed(2)}秒`, 'success');
                    break;
                    
                case 'error':
                    addMessage('system', `❌ 错误: ${data.message}`, 'ai-message');
                    updateStatus('执行失败', 'error');
                    break;
            }
        }
        
        function addMessage(role, content, className) {
            const chatContainer = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${className}`;
            messageDiv.innerHTML = `<strong>${role}:</strong><br>${content.replace(/\\n/g, '<br>')}`;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function addMermaidDiagram(diagramCode) {
            const chatContainer = document.getElementById('chatContainer');
            const diagramDiv = document.createElement('div');
            diagramDiv.className = 'message ai-message mermaid-diagram';
            diagramDiv.innerHTML = `<div class="mermaid">${diagramCode}</div>`;
            chatContainer.appendChild(diagramDiv);
            
            // 渲染Mermaid图表
            mermaid.init(undefined, diagramDiv.querySelector('.mermaid'));
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            
            if (!message) return;
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                updateStatus('WebSocket连接未建立', 'error');
                return;
            }
            
            // 显示用户消息
            addMessage('user', message, 'user-message');
            
            // 发送消息
            ws.send(JSON.stringify({
                user_input: message,
                session_id: currentSessionId
            }));
            
            input.value = '';
            updateStatus('处理中...', 'info');
        }
        
        function clearChat() {
            document.getElementById('chatContainer').innerHTML = '';
            currentSessionId = null;
            updateStatus('对话已清空', 'info');
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        function updateStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = `status ${type}`;
        }
        
        // 加载可用工具
        async function loadTools() {
            try {
                const response = await fetch('/tools');
                const data = await response.json();
                const toolsList = document.getElementById('toolsList');
                
                if (data.tools && data.tools.length > 0) {
                    toolsList.innerHTML = data.tools.map(tool => 
                        `<div style="margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                            <strong>${tool.name}</strong><br>
                            <small>${tool.description}</small>
                        </div>`
                    ).join('');
                } else {
                    toolsList.innerHTML = '<p>暂无可用工具</p>';
                }
            } catch (error) {
                document.getElementById('toolsList').innerHTML = `<p>加载工具失败: ${error.message}</p>`;
            }
        }
        
        // 初始化
        document.addEventListener('DOMContentLoaded', function() {
            mermaid.initialize({ startOnLoad: false, theme: 'default' });
            initWebSocket();
            loadTools();
        });
    </script>
</body>
</html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=demo_html)


if __name__ == "__main__":
    import uvicorn
    
    # 获取端口
    port = int(os.getenv("PORT", 8001))
    
    # 启动服务
    uvicorn.run(
        "mcp_api:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # 生产环境关闭自动重载
        log_level="info"
    ) 