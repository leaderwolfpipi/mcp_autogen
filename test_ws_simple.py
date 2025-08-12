#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_ws():
    """简单的WebSocket测试"""
    uri = "ws://localhost:8000/ws/execute_task"
    print(f"连接到: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ 连接成功!")
            
            # 发送测试消息
            message = {
                "user_input": "测试消息",
                "input_data": None
            }
            
            print(f"发送: {json.dumps(message, ensure_ascii=False)}")
            await websocket.send(json.dumps(message))
            
            # 接收响应
            print("等待响应...")
            response = await websocket.recv()
            print(f"收到: {response}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws()) 