#!/usr/bin/env python3
"""
测试聊天集成脚本
验证前端与MCP标准API的WebSocket连接和流式输出
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_connection():
    """测试WebSocket连接和消息流"""
    uri = "ws://localhost:8000/ws/mcp/chat"
    
    try:
        logger.info(f"🔗 连接到 {uri}")
        async with websockets.connect(uri) as websocket:
            logger.info("✅ WebSocket连接成功")
            
            # 测试闲聊模式
            chat_message = {
                "message": "你好",
                "session_id": "test_session_chat"
            }
            
            logger.info("📤 发送闲聊消息: 你好")
            await websocket.send(json.dumps(chat_message))
            
            # 接收响应
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    logger.info(f"📥 收到消息: {data['type']} - {data.get('message', '')[:50]}...")
                    
                    if data['type'] == 'chat_response':
                        logger.info("✅ 闲聊模式测试完成")
                        break
                        
                except asyncio.TimeoutError:
                    logger.warning("⏰ 等待响应超时")
                    break
            
            # 测试任务模式
            await asyncio.sleep(1)
            
            task_message = {
                "message": "搜索Python编程教程",
                "session_id": "test_session_task"
            }
            
            logger.info("📤 发送任务消息: 搜索Python编程教程")
            await websocket.send(json.dumps(task_message))
            
            # 接收任务流式响应
            step_count = 0
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)
                    logger.info(f"📥 收到消息: {data['type']} - {data.get('message', '')[:50]}...")
                    
                    if data['type'] == 'mode_detection':
                        logger.info(f"🎯 模式检测: {data.get('mode')}")
                    elif data['type'] == 'task_start':
                        logger.info("🚀 任务开始")
                    elif data['type'] == 'tool_start':
                        logger.info(f"🔧 工具开始: {data.get('tool_name')}")
                    elif data['type'] == 'tool_result':
                        step_count += 1
                        logger.info(f"✅ 工具完成 ({step_count})")
                    elif data['type'] == 'task_complete':
                        logger.info("🎉 任务完成")
                        break
                    elif data['type'] == 'error':
                        logger.error(f"❌ 错误: {data.get('message')}")
                        break
                        
                except asyncio.TimeoutError:
                    logger.warning("⏰ 等待任务响应超时")
                    break
            
            logger.info("✅ 所有测试完成")
            
    except ConnectionRefusedError:
        logger.error("❌ 无法连接到WebSocket服务器，请确保MCP标准API服务正在运行")
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")

async def main():
    """主测试函数"""
    logger.info("🧪 开始测试前端-API集成")
    await test_websocket_connection()

if __name__ == "__main__":
    asyncio.run(main()) 