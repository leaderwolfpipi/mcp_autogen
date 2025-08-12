#!/usr/bin/env python3
"""
测试工具生成和注册修复
"""

import asyncio
import logging
from core.smart_pipeline_engine import SmartPipelineEngine
from core.unified_tool_manager import get_unified_tool_manager

# 设置日志
logging.basicConfig(level=logging.INFO)

async def test_tool_generation():
    """测试工具生成和注册"""
    print("🧪 测试工具生成和注册修复")
    print("=" * 50)
    
    # 初始化引擎
    engine = SmartPipelineEngine(use_llm=False)
    print("✅ 智能Pipeline引擎初始化成功")
    
    # 获取统一工具管理器
    tool_manager = get_unified_tool_manager()
    print(f"✅ 统一工具管理器初始化成功，发现 {len(tool_manager.tools)} 个工具")
    
    # 检查smart_search工具是否存在
    if 'smart_search' in tool_manager.tools:
        print("✅ smart_search工具已正确发现")
        smart_search_tool = tool_manager.tools['smart_search']
        print(f"   - 来源: {smart_search_tool.source.value}")
        print(f"   - 函数: {smart_search_tool.function is not None}")
        print(f"   - 异步: {smart_search_tool.is_async}")
    else:
        print("❌ smart_search工具未发现")
    
    # 测试工具获取
    smart_search_func = await tool_manager.get_tool('smart_search')
    if smart_search_func and callable(smart_search_func):
        print("✅ smart_search工具函数获取成功")
        print(f"   - 函数名: {smart_search_func.__name__}")
        print(f"   - 可调用: {callable(smart_search_func)}")
    else:
        print("❌ smart_search工具函数获取失败")
    
    # 测试工具执行
    try:
        result = await tool_manager.execute_tool('smart_search', query="测试查询", max_results=3)
        print("✅ smart_search工具执行成功")
        print(f"   - 结果类型: {type(result)}")
        print(f"   - 结果内容: {result}")
    except Exception as e:
        print(f"❌ smart_search工具执行失败: {e}")
    
    print("\n🎯 测试完成")

if __name__ == "__main__":
    asyncio.run(test_tool_generation()) 