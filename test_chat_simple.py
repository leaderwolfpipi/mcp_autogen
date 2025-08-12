#!/usr/bin/env python3
"""
简单测试闲聊功能
"""

import asyncio
import os
from core.smart_pipeline_engine import SmartPipelineEngine

async def test_chat_simple():
    """简单测试闲聊功能"""
    
    # 初始化引擎
    engine = SmartPipelineEngine(
        use_llm=True,
        llm_config={
            "llm_model": "gpt-4o",
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "api_base": os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        }
    )
    
    # 测试一个简单的闲聊输入
    user_input = "你好"
    
    print(f"📝 用户输入: {user_input}")
    print("🔄 正在处理...")
    
    try:
        result = await engine.execute_from_natural_language(user_input)
        
        print(f"✅ 执行成功: {result['success']}")
        print(f"⏱️ 执行时间: {result.get('execution_time', 0):.2f}秒")
        
        # 检查是否是闲聊
        if result.get("final_output") and not result.get("node_results"):
            print(f"💬 闲聊回答: {result['final_output']}")
        else:
            print(f"🔧 执行节点: {len(result.get('node_results', []))} 个")
            for node in result.get('node_results', []):
                print(f"   - {node['tool_type']}: {node.get('status', 'unknown')}")
        
        # 显示最终输出
        if result.get("final_output"):
            print(f"📤 最终输出: {result['final_output']}")
        else:
            print("❌ 没有最终输出")
            
    except Exception as e:
        print(f"❌ 异常: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat_simple()) 