#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

async def test_websocket_exact_demo():
    """完全按照demo.html的WebSocket测试"""
    
    # 参照demo.html中的URL构建逻辑
    protocol = "ws"  # 本地连接使用ws
    host = "localhost:8000"
    url = f"{protocol}://{host}/ws/execute_task"
    
    print(f"正在连接到: {url}")
    print("参照demo.html的实现...")
    
    try:
        # 连接WebSocket（参照demo.html的connect()函数）
        websocket = await websockets.connect(url)
        print("✅ WebSocket连接成功!")
        
        # 等待连接稳定（参照demo.html的onopen事件）
        await asyncio.sleep(1)
        
        # 发送任务请求（参照demo.html的execute()函数）
        task_input = "请帮我翻译这段文字：Hello, how are you?"
        payload = {
            "user_input": task_input,
            "input_data": None
        }
        
        print(f"发送任务: {json.dumps(payload, ensure_ascii=False)}")
        await websocket.send(json.dumps(payload))
        print("任务已发送")
        
        # 接收响应（参照demo.html的onmessage事件）
        print("等待响应...")
        message_count = 0
        
        while True:
            try:
                # 设置合理的超时时间
                response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                message_count += 1
                
                print(f"📨 收到消息 {message_count}: {response}")
                
                try:
                    data = json.loads(response)
                    step = data.get('step', 'unknown')
                    message = data.get('message', 'no message')
                    status = data.get('status', 'info')
                    
                    print(f"   步骤: {step}")
                    print(f"   消息: {message}")
                    print(f"   状态: {status}")
                    
                    # 如果收到完成或错误状态，退出循环
                    if status in ['success', 'error', 'completed']:
                        print("✅ 任务完成或出错，退出接收循环")
                        break
                        
                except json.JSONDecodeError:
                    print(f"   原始消息: {response}")
                    
            except asyncio.TimeoutError:
                print("⏰ 等待响应超时")
                break
            except websockets.exceptions.ConnectionClosed:
                print("🔌 连接已关闭")
                break
        
        # 关闭连接（参照demo.html的onclose事件）
        await websocket.close()
        print("🔌 WebSocket连接已关闭")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_websocket_exact_demo()) 