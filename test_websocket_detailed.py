#!/usr/bin/env python3
import asyncio
import websockets
import json
import time
from datetime import datetime

async def test_websocket_detailed():
    """详细测试WebSocket状态推送"""
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
            max_timeout = 10  # 增加等待时间
            all_messages = []
            
            while timeout_count < max_timeout:
                try:
                    # 设置超时时间为3秒
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(message)
                    message_count += 1
                    
                    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    msg_type = data.get('type', 'unknown')
                    msg_content = data.get('message', '')
                    
                    print(f"📨 [{timestamp}] {message_count:2d}. {msg_type:15s} - {msg_content[:80]}...")
                    
                    # 记录完整消息
                    all_messages.append({
                        'timestamp': timestamp,
                        'count': message_count,
                        'type': msg_type,
                        'data': data
                    })
                    
                    # 如果收到任务完成消息，等待一下再结束
                    if msg_type == 'task_complete':
                        print("✅ 任务完成，再等待2秒看是否有其他消息...")
                        try:
                            final_message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                            final_data = json.loads(final_message)
                            message_count += 1
                            final_timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                            print(f"📨 [{final_timestamp}] {message_count:2d}. {final_data.get('type', 'unknown'):15s} - {final_data.get('message', '')[:80]}...")
                            all_messages.append({
                                'timestamp': final_timestamp,
                                'count': message_count,
                                'type': final_data.get('type', 'unknown'),
                                'data': final_data
                            })
                        except asyncio.TimeoutError:
                            pass
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
            
            print(f"\n📊 测试完成，共收到 {message_count} 条消息")
            print("\n📋 消息类型统计:")
            type_counts = {}
            for msg in all_messages:
                msg_type = msg['type']
                type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
            
            for msg_type, count in type_counts.items():
                print(f"  - {msg_type:15s}: {count} 条")
            
            # 显示详细消息内容
            print("\n📝 详细消息内容:")
            for msg in all_messages:
                print(f"\n[{msg['timestamp']}] {msg['count']:2d}. {msg['type']}:")
                print(f"   {json.dumps(msg['data'], ensure_ascii=False, indent=2)}")
                
    except Exception as e:
        print(f"❌ WebSocket连接失败: {e}")

if __name__ == "__main__":
    print("🚀 开始详细WebSocket状态推送测试...")
    asyncio.run(test_websocket_detailed()) 