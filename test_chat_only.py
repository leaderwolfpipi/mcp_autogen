#!/usr/bin/env python3
"""
测试闲聊功能
"""

import asyncio
import os
from core.smart_pipeline_engine import SmartPipelineEngine

async def test_chat_only():
    """测试闲聊功能"""
    
    # 初始化引擎
    engine = SmartPipelineEngine(
        use_llm=True,
        llm_config={
            "llm_model": "gpt-4o",
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "api_base": os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        }
    )
    
    # 测试闲聊输入
    chat_inputs = [
        "你好",
        "今天天气怎么样？",
        "你是谁？",
        "谢谢你的帮助",
        "再见"
    ]
    
    print("🧪 开始测试闲聊功能...")
    
    for user_input in chat_inputs:
        print(f"\n📝 用户输入: {user_input}")
        
        try:
            result = await engine.execute_from_natural_language(user_input)
            
            if result["success"]:
                print(f"✅ 成功: {result['final_output']}")
            else:
                print(f"❌ 失败: {result['errors']}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    print("\n🎉 闲聊功能测试完成!")

if __name__ == "__main__":
    asyncio.run(test_chat_only()) 