#!/usr/bin/env python3
"""
测试闲聊功能 - 验证LLM判断
"""

import asyncio
import os
from core.smart_pipeline_engine import SmartPipelineEngine

async def test_chat_llm_only():
    """测试闲聊功能 - 验证LLM判断"""
    
    # 初始化引擎，强制使用LLM
    engine = SmartPipelineEngine(
        use_llm=True,  # 强制使用LLM
        llm_config={
            "llm_model": "gpt-4o",
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "api_base": os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        }
    )
    
    # 测试各种输入类型
    test_inputs = [
        # 闲聊类型
        "你好",
        "今天天气怎么样？",
        "你是谁？",
        "谢谢你的帮助",
        "再见",
        "在吗？",
        
        # 任务类型
        "搜索人工智能的最新发展",
        "帮我旋转这张图片90度",
        "翻译这段英文文本",
        "生成一份项目报告"
    ]
    
    print("🧪 开始测试LLM闲聊判断功能...")
    print("=" * 60)
    
    for user_input in test_inputs:
        print(f"\n📝 用户输入: {user_input}")
        
        try:
            result = await engine.execute_from_natural_language(user_input)
            
            if result["success"]:
                # 检查是否是闲聊
                if result.get("final_output") and not result.get("node_results"):
                    print(f"💬 闲聊判断: {result['final_output']}")
                else:
                    print(f"🔧 任务执行: 执行了 {len(result.get('node_results', []))} 个节点")
                    for node in result.get('node_results', []):
                        print(f"   - {node['tool_type']}: {node.get('status', 'unknown')}")
            else:
                print(f"❌ 失败: {result['errors']}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    print("\n🎉 LLM闲聊判断功能测试完成!")

if __name__ == "__main__":
    asyncio.run(test_chat_llm_only()) 