#!/usr/bin/env python3
"""
测试UI修复效果
"""

import asyncio
import json
import logging
from api.api import execute_task_with_streaming_async

# 设置日志
logging.basicConfig(level=logging.INFO)

async def test_chat_mode():
    """测试闲聊模式"""
    print("=" * 60)
    print("🧪 测试闲聊模式")
    print("=" * 60)
    
    user_input = "你好"
    print(f"用户输入: {user_input}")
    print("\n后端输出:")
    
    async for response in execute_task_with_streaming_async(user_input):
        try:
            data = json.loads(response)
            print(f"模式: {data.get('mode', 'unknown')}")
            print(f"状态: {data.get('status', 'unknown')}")
            print(f"步骤: {data.get('step', 'unknown')}")
            print(f"消息长度: {len(data.get('message', ''))}")
            if data.get('message'):
                print(f"消息预览: {data['message'][:100]}...")
            print("---")
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"原始数据: {response[:200]}...")

async def test_task_mode():
    """测试任务模式"""
    print("=" * 60)
    print("🧪 测试任务模式")
    print("=" * 60)
    
    user_input = "帮我搜索一下李鸿章的信息"
    print(f"用户输入: {user_input}")
    print("\n后端输出:")
    
    async for response in execute_task_with_streaming_async(user_input):
        try:
            data = json.loads(response)
            print(f"模式: {data.get('mode', 'unknown')}")
            print(f"状态: {data.get('status', 'unknown')}")
            print(f"步骤: {data.get('step', 'unknown')}")
            
            if data.get('step') == 'pipeline_start':
                mermaid = data.get('data', {}).get('mermaid_diagram', '')
                print(f"Mermaid图表长度: {len(mermaid)}")
                if mermaid:
                    print("Mermaid图表预览:")
                    print(mermaid[:200] + "..." if len(mermaid) > 200 else mermaid)
            
            elif data.get('step') == 'node_result':
                node_data = data.get('data', {})
                print(f"节点ID: {node_data.get('node_id', 'unknown')}")
                print(f"工具类型: {node_data.get('tool_type', 'unknown')}")
                print(f"执行时间: {node_data.get('execution_time', 0):.2f}秒")
                message = data.get('message', '')
                print(f"节点消息长度: {len(message)}")
                if message:
                    print("节点消息预览:")
                    print(message[:300] + "..." if len(message) > 300 else message)
            
            elif data.get('step') == 'completed':
                message = data.get('message', '')
                print(f"最终结果长度: {len(message)}")
                if message:
                    print("最终结果预览:")
                    print(message[:200] + "..." if len(message) > 200 else message)
            
            print("---")
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"原始数据: {response[:200]}...")

async def main():
    """主测试函数"""
    print("🚀 开始测试UI修复效果\n")
    
    # 测试闲聊模式
    await test_chat_mode()
    
    print("\n" + "="*80 + "\n")
    
    # 测试任务模式
    await test_task_mode()
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    asyncio.run(main()) 