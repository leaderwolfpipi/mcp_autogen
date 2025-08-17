#!/usr/bin/env python3
"""
简单的MCP状态推送测试
直接使用MCP工具系统，绕过真实工具系统
"""
import asyncio
import websockets
import json
import time

async def test_mcp_status():
    """测试MCP工具系统的状态推送"""
    uri = "ws://localhost:8000/ws/mcp/chat"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 WebSocket连接成功")
            
            # 发送测试查询 - 使用明确的任务关键词
            test_message = {
                "user_input": "搜索张良的资料",  # 明确包含"搜索"关键词
                "session_id": f"test_session_{int(time.time())}"
            }
            
            print(f"📤 发送测试消息: {test_message}")
            await websocket.send(json.dumps(test_message))
            
            # 接收消息
            message_count = 0
            timeout_count = 0
            max_timeout = 10
            
            while timeout_count < max_timeout:
                try:
                    # 等待消息，5秒超时
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    message_count += 1
                    print(f"📨 [{time.strftime('%H:%M:%S')}] {message_count:2d}. {data.get('type', 'unknown'):15s} - {data.get('message', '')[:50]}...")
                    
                    # 如果收到最终完成消息，结束测试
                    if data.get('type') in ['task_complete', 'error']:
                        print(f"\n✅ 收到最终状态: {data.get('type')}")
                        print(f"📝 完整消息: {json.dumps(data, ensure_ascii=False, indent=2)}")
                        break
                        
                except asyncio.TimeoutError:
                    timeout_count += 1
                    print(f"⏰ 等待消息超时 ({timeout_count}/{max_timeout})")
                except Exception as e:
                    print(f"❌ 接收消息失败: {e}")
                    break
            
            print(f"\n📊 测试完成，共收到 {message_count} 条消息")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_status()) 