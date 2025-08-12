#!/usr/bin/env python3
"""
简单的WebSocket测试脚本
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/mcp/chat"
    
    try:
        print(f"连接到 {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功!")
            
            # 发送测试消息
            test_message = {
                "message": "你好",
                "session_id": "test_session"
            }
            
            print("发送测试消息...")
            await websocket.send(json.dumps(test_message))
            
            # 接收响应
            print("等待响应...")
            response = await websocket.recv()
            data = json.loads(response)
            print(f"收到响应: {data}")
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 