#!/usr/bin/env python3
"""
最简单的FastAPI WebSocket测试
"""
from fastapi import FastAPI, WebSocket
import json

app = FastAPI()

@app.websocket("/ws/test")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket连接已建立")
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            print(f"收到消息: {message_data}")
            
            # 发送回复
            response = {
                "type": "echo",
                "message": f"收到: {message_data.get('message', 'empty')}"
            }
            await websocket.send_text(json.dumps(response))
            
    except Exception as e:
        print(f"WebSocket错误: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info") 