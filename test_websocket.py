#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_websocket():
    """测试WebSocket连接"""
    try:
        uri = "ws://localhost:8000/ws/execute_task"
        print(f"正在连接到: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功!")
            
            # 发送测试消息
            test_message = {
                "user_input": "测试消息",
                "input_data": None
            }
            
            print(f"发送消息: {test_message}")
            await websocket.send(json.dumps(test_message))
            
            # 接收响应
            response = await websocket.recv()
            print(f"收到响应: {response}")
            
    except Exception as e:
        print(f"❌ WebSocket连接失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 