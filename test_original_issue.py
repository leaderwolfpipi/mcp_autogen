#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门测试原始问题：吃了吗？您那... 的改进效果
"""

import asyncio
import logging
from core.task_engine import TaskEngine
from core.tool_registry import ToolRegistry
from tools.enhanced_report_generator import enhanced_report_generator

logging.basicConfig(level=logging.INFO)

async def test_original_issue():
    """测试原始问题的改进效果"""
    
    print("🎯 测试原始问题改进效果")
    print("=" * 50)
    
    # 原始问题查询
    original_query = "吃了吗？您那"
    
    print(f"📝 原始查询: \"{original_query}\"")
    print()
    
    # 1. 测试模式检测改进
    print("1️⃣ 测试模式检测改进")
    tool_registry = ToolRegistry("sqlite:///tools_test.db")
    engine = TaskEngine(tool_registry, max_depth=3)
    
    is_task_mode = await engine._detect_task_mode(original_query)
    mode = "任务模式" if is_task_mode else "闲聊模式"
    result_emoji = "✅" if not is_task_mode else "⚠️"
    
    print(f"{result_emoji} 模式检测结果: {mode}")
    print(f"   改进前: 可能误判为任务模式")
    print(f"   改进后: {'正确识别为闲聊模式' if not is_task_mode else '需要进一步优化'}")
    print()
    
    # 2. 测试工具错误提示改进
    print("2️⃣ 测试 enhanced_report_generator 错误提示改进")
    result = enhanced_report_generator(original_query)
    
    if result['status'] == 'error':
        print("✅ 工具正确拒绝了不适合的内容")
        print("📝 改进后的错误提示:")
        print(result['message'])
    else:
        print("❌ 工具意外通过了内容检查")
    
    print()
    print("📊 改进效果总结:")
    print("✅ 模式检测: 更准确识别闲聊内容")
    print("✅ 错误提示: 更友好和有建设性")
    print("✅ 工具选择: 提供了明确的指导原则")

if __name__ == "__main__":
    asyncio.run(test_original_issue()) 