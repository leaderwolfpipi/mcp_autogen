#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys

async def debug_ws():
    """调试WebSocket连接"""
    uri = "ws://localhost:8000/ws/test"  # 修改为测试端点
    print(f"尝试连接到: {uri}")
    
    try:
        # 尝试连接
        websocket = await websockets.connect(uri)
        print("✅ WebSocket连接成功!")
        
        # 发送简单消息
        message = {"message": "Hello from Python"}
        print(f"发送消息: {json.dumps(message, ensure_ascii=False)}")
        await websocket.send(json.dumps(message))
        
        # 等待响应
        print("等待响应...")
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            print(f"收到响应: {response}")
        except asyncio.TimeoutError:
            print("❌ 等待响应超时")
        
        await websocket.close()
        
    except websockets.exceptions.InvalidURI as e:
        print(f"❌ 无效的URI: {e}")
    except websockets.exceptions.InvalidMessage as e:
        print(f"❌ 无效消息: {e}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ 连接关闭: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_ws()) 