#!/usr/bin/env python3
"""
测试前端闲聊回答功能
"""

import asyncio
import json
import os
from api.api import execute_task_with_streaming_async

async def test_frontend_chat():
    """测试前端闲聊回答功能"""
    
    # 测试闲聊输入
    user_input = "你好"
    
    print(f"📝 用户输入: {user_input}")
    print("🔄 开始流式处理...")
    print("=" * 60)
    
    try:
        # 模拟前端接收流式数据
        async for message in execute_task_with_streaming_async(user_input):
            try:
                data = json.loads(message)
                status = data.get("status")
                step = data.get("step")
                message_text = data.get("message")
                
                print(f"📤 [{status}] {step}: {message_text}")
                
                # 检查是否是闲聊回答
                if step == "chat_response":
                    chat_data = data.get("data", {})
                    chat_response = chat_data.get("chat_response", "")
                    print(f"💬 闲聊回答: {chat_response}")
                    print(f"⏱️ 执行时间: {chat_data.get('execution_time', 0):.2f}秒")
                    print("✅ 前端应该直接显示这个闲聊回答")
                
                # 检查最终结果
                elif step == "completed":
                    final_data = data.get("data", {})
                    final_output = final_data.get("final_output", "")
                    if final_output:
                        print(f"📤 最终输出: {final_output}")
                        print("✅ 前端也应该能从这个字段获取闲聊回答")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析错误: {e}")
                print(f"原始消息: {message}")
                
    except Exception as e:
        print(f"❌ 流式处理异常: {e}")
    
    print("\n🎉 前端闲聊回答测试完成!")

if __name__ == "__main__":
    asyncio.run(test_frontend_chat()) 