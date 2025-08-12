#!/usr/bin/env python3
"""
简化的API服务，用于测试WebSocket连接
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import asyncio
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Simple API Test")

@app.get("/")
async def root():
    """根路径，返回简单的HTML页面"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket测试</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            textarea { width: 100%; height: 100px; margin: 10px 0; }
            button { padding: 10px 20px; margin: 5px; }
            .output { background: #f5f5f5; padding: 15px; margin: 10px 0; height: 300px; overflow-y: auto; }
            .log { margin: 5px 0; padding: 5px; border-left: 3px solid #ddd; }
            .success { border-left-color: #4caf50; }
            .error { border-left-color: #f44336; }
            .progress { border-left-color: #2196f3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>WebSocket连接测试</h1>
            <div>
                <label>测试消息:</label>
                <textarea id="messageInput" placeholder="请输入测试消息">Hello, WebSocket!</textarea>
            </div>
            <div>
                <button onclick="connect()">连接WebSocket</button>
                <button onclick="sendMessage()">发送消息</button>
                <button onclick="clear()">清空日志</button>
            </div>
            <div id="status">未连接</div>
            <div class="output" id="output"></div>
        </div>

        <script>
            let ws = null;
            let connected = false;
            
            function log(message, type = 'info') {
                const output = document.getElementById('output');
                const div = document.createElement('div');
                div.className = `log ${type}`;
                div.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
                output.appendChild(div);
                output.scrollTop = output.scrollHeight;
            }
            
            function connect() {
                if (connected) {
                    log('已经连接', 'error');
                    return;
                }
                
                const url = `ws://${window.location.host}/ws/test`;
                ws = new WebSocket(url);
                
                ws.onopen = () => {
                    connected = true;
                    document.getElementById('status').textContent = '已连接';
                    log('WebSocket连接成功', 'success');
                };
                
                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        log(`收到消息: ${data.message}`, 'success');
                    } catch (e) {
                        log(`收到消息: ${event.data}`, 'success');
                    }
                };
                
                ws.onclose = () => {
                    connected = false;
                    document.getElementById('status').textContent = '未连接';
                    log('WebSocket连接断开', 'error');
                };
                
                ws.onerror = (error) => {
                    log('WebSocket错误: ' + error, 'error');
                };
            }
            
            function sendMessage() {
                if (!connected) {
                    log('请先连接WebSocket', 'error');
                    return;
                }
                
                const message = document.getElementById('messageInput').value;
                const payload = {
                    message: message,
                    timestamp: new Date().toISOString()
                };
                
                ws.send(JSON.stringify(payload));
                log('消息已发送', 'progress');
            }
            
            function clear() {
                document.getElementById('output').innerHTML = '';
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    """简单的WebSocket测试端点"""
    await websocket.accept()
    logger.info("WebSocket连接已建立")
    
    try:
        # 发送欢迎消息
        await websocket.send_text(json.dumps({
            "message": "WebSocket连接成功！",
            "type": "welcome"
        }))
        
        # 监听消息
        while True:
            data = await websocket.receive_text()
            logger.info(f"收到消息: {data}")
            
            try:
                message_data = json.loads(data)
                response = {
                    "message": f"收到消息: {message_data.get('message', 'Unknown')}",
                    "timestamp": message_data.get('timestamp'),
                    "type": "echo"
                }
            except json.JSONDecodeError:
                response = {
                    "message": f"收到文本: {data}",
                    "type": "echo"
                }
            
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        logger.info("WebSocket连接断开")

@app.websocket("/ws/execute_task")
async def execute_task_websocket(websocket: WebSocket):
    """模拟任务执行WebSocket端点"""
    await websocket.accept()
    logger.info("任务执行WebSocket连接已建立")
    
    try:
        # 接收任务请求
        data = await websocket.receive_text()
        request_data = json.loads(data)
        user_input = request_data.get("user_input", "")
        
        logger.info(f"收到任务请求: {user_input}")
        
        # 模拟执行流程
        steps = [
            {"step": "import_tools", "message": "正在导入工具集合...", "status": "progress"},
            {"step": "smart_pipeline_execution", "message": "正在使用智能Pipeline引擎执行任务...", "status": "progress"},
            {"step": "node_result", "message": "工具执行完成", "status": "progress", "data": {
                "node_id": "test_node",
                "tool_type": "test_tool",
                "result_summary": "测试工具执行成功",
                "execution_time": 1.5,
                "output": "这是一个测试输出内容",
                "status": "success"
            }},
            {"step": "pipeline_executed", "message": "智能Pipeline执行完成", "status": "progress"},
            {"step": "completed", "message": "任务执行完成", "status": "success"}
        ]
        
        for step in steps:
            await websocket.send_text(json.dumps(step, ensure_ascii=False))
            await asyncio.sleep(1)  # 模拟处理时间
            
    except WebSocketDisconnect:
        logger.info("任务执行WebSocket连接断开")
    except Exception as e:
        logger.error(f"WebSocket执行失败: {e}")
        await websocket.send_text(json.dumps({
            "status": "error",
            "step": "websocket_error",
            "message": f"WebSocket执行失败: {str(e)}"
        }, ensure_ascii=False))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 