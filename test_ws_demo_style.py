#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

async def test_websocket_demo_style():
    """基于demo.html的WebSocket测试"""
    uri = "ws://localhost:8000/ws/execute_task"
    print(f"正在连接到: {uri}")
    
    try:
        # 连接WebSocket
        websocket = await websockets.connect(uri)
        print("✅ WebSocket连接成功!")
        
        # 等待一下确保连接稳定
        await asyncio.sleep(1)
        
        # 发送任务请求（参照demo.html的格式）
        task_payload = {
            "user_input": "请帮我翻译这段文字：Hello, how are you?",
            "input_data": None
        }
        
        print(f"发送任务: {json.dumps(task_payload, ensure_ascii=False)}")
        await websocket.send(json.dumps(task_payload))
        
        # 接收响应
        print("等待响应...")
        message_count = 0
        max_messages = 10  # 最多接收10条消息
        
        while message_count < max_messages:
            try:
                # 设置超时
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                message_count += 1
                
                try:
                    data = json.loads(response)
                    print(f"📨 消息 {message_count}: {data.get('step', 'unknown')} - {data.get('message', 'no message')}")
                    
                    # 如果收到完成或错误状态，退出循环
                    if data.get('status') in ['success', 'error', 'completed']:
                        print("✅ 任务完成或出错，退出接收循环")
                        break
                        
                except json.JSONDecodeError:
                    print(f"📨 原始消息 {message_count}: {response}")
                    
            except asyncio.TimeoutError:
                print("⏰ 等待响应超时")
                break
            except websockets.exceptions.ConnectionClosed:
                print("🔌 连接已关闭")
                break
        
        # 关闭连接
        await websocket.close()
        print("🔌 WebSocket连接已关闭")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_websocket_demo_style()) 