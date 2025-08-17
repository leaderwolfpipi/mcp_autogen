#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

async def test_websocket_status():
    """测试WebSocket状态推送"""
    uri = "ws://localhost:8000/ws/mcp/chat"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 WebSocket连接成功")
            
            # 发送测试查询
            test_message = {
                "user_input": "张良是谁",
                "session_id": f"test_session_{int(time.time())}"
            }
            
            print(f"📤 发送测试消息: {test_message}")
            await websocket.send(json.dumps(test_message))
            
            # 接收消息
            message_count = 0
            timeout_count = 0
            max_timeout = 5  # 最大等待5次超时
            
            while timeout_count < max_timeout:
                try:
                    # 设置超时时间为5秒
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    message_count += 1
                    
                    print(f"📨 [{message_count}] 收到消息: {data.get('type', 'unknown')} - {data.get('message', '')[:100]}...")
                    
                    # 如果收到任务完成消息，结束测试
                    if data.get('type') == 'task_complete':
                        print("✅ 任务完成，测试结束")
                        break
                        
                except asyncio.TimeoutError:
                    timeout_count += 1
                    print(f"⏰ 等待消息超时 ({timeout_count}/{max_timeout})")
                    if timeout_count >= max_timeout:
                        print("⚠️ 超过最大等待时间，结束测试")
                        break
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析错误: {e}")
                    
                except Exception as e:
                    print(f"❌ 接收消息错误: {e}")
                    break
            
            print(f"📊 测试完成，共收到 {message_count} 条消息")
            
    except Exception as e:
        print(f"❌ WebSocket连接失败: {e}")

if __name__ == "__main__":
    print("🚀 开始WebSocket状态推送测试...")
    asyncio.run(test_websocket_status()) 