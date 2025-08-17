#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查LLM可用性和流式输出条件
"""

import os
from core.task_engine import TaskEngine
from core.tool_registry import ToolRegistry

def test_llm_availability():
    """测试LLM可用性"""
    
    print("🔍 检查LLM可用性和流式输出条件")
    print("=" * 60)
    
    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE")
    model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
    
    print("📋 环境变量检查:")
    print(f"  OPENAI_API_KEY: {'✅ 已设置' if api_key else '❌ 未设置'}")
    print(f"  OPENAI_API_BASE: {base_url or '未设置'}")
    print(f"  OPENAI_MODEL: {model}")
    
    # 初始化TaskEngine
    tool_registry = ToolRegistry("sqlite:///test.db")
    task_engine = TaskEngine(tool_registry)
    
    print(f"\n🤖 TaskEngine LLM状态:")
    print(f"  self.llm: {task_engine.llm}")
    print(f"  LLM可用: {'✅ 是' if task_engine.llm else '❌ 否'}")
    
    if task_engine.llm:
        print(f"  支持generate: {'✅ 是' if hasattr(task_engine.llm, 'generate') else '❌ 否'}")
        print(f"  支持generate_streaming: {'✅ 是' if hasattr(task_engine.llm, 'generate_streaming') else '❌ 否'}")
    
    print(f"\n🎯 流式输出条件分析:")
    
    # 模拟_handle_chat_mode中的条件判断
    has_streaming = task_engine.llm and hasattr(task_engine.llm, 'generate_streaming')
    has_generate = task_engine.llm and hasattr(task_engine.llm, 'generate')
    
    if has_streaming:
        print("✅ 满足真正流式输出条件")
        print("   - 将使用LLM的generate_streaming方法")
        print("   - 内容会逐字符实时生成")
    elif has_generate:
        print("⚠️ 满足普通LLM生成条件") 
        print("   - 将使用LLM的generate方法")
        print("   - 内容一次性生成，但有LLM智能回复")
    else:
        print("❌ 不满足LLM生成条件")
        print("   - 将使用规则回复(_generate_rule_based_chat_response)")
        print("   - 内容是预设的规则回复，一次性返回")
        print("   - 这就是为什么看到'一股脑输出'的原因！")
    
    print(f"\n💡 解决方案:")
    if not api_key:
        print("1. 设置OPENAI_API_KEY环境变量")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        print("2. 或者在.env文件中添加:")
        print("   OPENAI_API_KEY=your-api-key-here")
        print("3. 重启应用程序")
        print("\n设置后将获得真正的流式打字效果！")
    else:
        print("✅ API Key已设置，应该有流式效果")
        print("如果仍无流式效果，请检查API Key是否有效")

if __name__ == "__main__":
    test_llm_availability() 