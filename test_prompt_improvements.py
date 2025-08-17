#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试提示词改进效果
"""

import asyncio
import logging
from core.task_engine import TaskEngine
from core.tool_registry import ToolRegistry

logging.basicConfig(level=logging.INFO)

async def test_mode_detection():
    """测试模式检测改进效果"""
    # 初始化工具注册表
    tool_registry = ToolRegistry("sqlite:///tools_test.db")
    
    # 初始化任务引擎
    engine = TaskEngine(tool_registry, max_depth=3)
    
    # 测试用例
    test_cases = [
        # 应该被识别为闲聊的查询
        ("你好", "闲聊"),
        ("吃了吗？", "闲聊"),
        ("吃了吗？您那怎么样", "闲聊"),
        ("最近忙不忙", "闲聊"),
        ("工作怎么样", "闲聊"),
        ("您好，休息一下吧", "闲聊"),
        ("谢谢你", "闲聊"),
        ("好的", "闲聊"),
        ("你是机器人吗", "闲聊"),
        ("你能做什么", "闲聊"),
        
        # 应该被识别为任务的查询
        ("谁是李白", "任务"),
        ("什么是人工智能", "任务"),
        ("搜索天气信息", "任务"),
        ("翻译这段文字", "任务"),
        ("生成一个报告", "任务"),
        ("帮我分析数据", "任务"),
        ("如何学习编程", "任务"),
        ("北京的人口是多少", "任务"),
    ]
    
    print("🧪 测试模式检测改进效果\n")
    
    correct_count = 0
    total_count = len(test_cases)
    
    for query, expected in test_cases:
        try:
            # 测试模式检测
            is_task_mode = await engine._detect_task_mode(query)
            detected = "任务" if is_task_mode else "闲聊"
            
            result = "✅" if detected == expected else "❌"
            status_color = "\033[32m" if detected == expected else "\033[31m"  # 绿色或红色
            reset_color = "\033[0m"
            
            print(f"{result} {status_color}查询: \"{query}\"{reset_color}")
            print(f"   预期: {expected} | 检测: {detected}")
            
            if detected == expected:
                correct_count += 1
            print()
            
        except Exception as e:
            print(f"❌ 查询: \"{query}\" 检测失败: {e}")
            print()
    
    accuracy = correct_count / total_count * 100
    print(f"📊 模式检测准确率: {correct_count}/{total_count} ({accuracy:.1f}%)")
    
    return accuracy

async def test_enhanced_report_generator():
    """测试 enhanced_report_generator 改进的错误提示"""
    from tools.enhanced_report_generator import enhanced_report_generator
    
    print("\n🧪 测试 enhanced_report_generator 错误提示改进\n")
    
    test_queries = [
        "你好",
        "吃了吗？",
        "谁是李白",
        "最近忙不忙"
    ]
    
    for query in test_queries:
        print(f"🔍 测试查询: \"{query}\"")
        result = enhanced_report_generator(query)
        
        if result['status'] == 'error':
            print("✅ 正确拒绝不适合的内容")
            print(f"📝 错误信息: {result['message']}")
        else:
            print("❌ 意外通过了内容检查")
            
        print("-" * 50)

async def test_full_pipeline():
    """测试完整的任务执行流水线"""
    print("\n🧪 测试完整任务执行流水线\n")
    
    # 初始化工具注册表
    tool_registry = ToolRegistry("sqlite:///tools_test.db")
    
    # 初始化任务引擎
    engine = TaskEngine(tool_registry, max_depth=3)
    
    test_cases = [
        "吃了吗？您那怎么样",  # 应该被识别为闲聊
        "谁是诸葛亮",         # 应该被识别为任务，但不应该用 enhanced_report_generator
    ]
    
    for query in test_cases:
        print(f"🎯 测试查询: \"{query}\"")
        
        try:
            result = await engine.execute(query, {})
            
            print(f"执行模式: {result.get('mode', '未知')}")
            print(f"成功状态: {result.get('success', False)}")
            print(f"最终输出: {result.get('final_output', '无输出')[:100]}...")
            
            if result.get('execution_steps'):
                print("执行步骤:")
                for i, step in enumerate(result['execution_steps']):
                    tool_name = step.get('tool_name', '未知工具')
                    status = step.get('status', '未知状态')
                    print(f"  {i+1}. {tool_name} - {status}")
            
        except Exception as e:
            print(f"❌ 执行失败: {e}")
        
        print("=" * 60)

async def main():
    """主测试函数"""
    print("🚀 开始测试提示词改进效果\n")
    
    # 测试模式检测
    accuracy = await test_mode_detection()
    
    # 测试错误提示改进
    await test_enhanced_report_generator()
    
    # 测试完整流水线
    await test_full_pipeline()
    
    print(f"\n📋 测试总结:")
    print(f"• 模式检测准确率: {accuracy:.1f}%")
    print("• 错误提示已改善为更友好的格式")
    print("• 工具选择指导原则已加入计划生成提示词")

if __name__ == "__main__":
    asyncio.run(main()) 