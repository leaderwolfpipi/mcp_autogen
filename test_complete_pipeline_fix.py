#!/usr/bin/env python3
"""
测试完整Pipeline系统修复
"""

import asyncio
import logging
from core.smart_pipeline_engine import SmartPipelineEngine
from core.unified_tool_manager import get_unified_tool_manager

# 设置日志
logging.basicConfig(level=logging.INFO)

async def test_complete_pipeline():
    """测试完整Pipeline系统"""
    print("🧪 测试完整Pipeline系统修复")
    print("=" * 50)
    
    # 初始化引擎
    engine = SmartPipelineEngine(use_llm=False)
    print("✅ 智能Pipeline引擎初始化成功")
    
    # 获取统一工具管理器
    tool_manager = get_unified_tool_manager()
    print(f"✅ 统一工具管理器初始化成功，发现 {len(tool_manager.tools)} 个工具")
    
    # 验证关键工具是否存在
    key_tools = ['smart_search', 'text_formatter', 'file_writer', 'report_generator']
    for tool_name in key_tools:
        if tool_name in tool_manager.tools:
            print(f"✅ {tool_name} 工具已发现")
        else:
            print(f"❌ {tool_name} 工具未发现")
    
    # 验证工具函数格式
    print("\n🔍 验证工具函数格式:")
    
    # 测试 smart_search
    smart_search_func = await tool_manager.get_tool('smart_search')
    if smart_search_func:
        result = smart_search_func("测试查询", 2)
        if isinstance(result, dict) and 'results' in result:
            print("✅ smart_search 返回格式正确")
        else:
            print("❌ smart_search 返回格式错误")
    
    # 测试 text_formatter
    text_formatter_func = await tool_manager.get_tool('text_formatter')
    if text_formatter_func:
        result = text_formatter_func("测试文本")
        if isinstance(result, dict) and 'formatted_text' in result:
            print("✅ text_formatter 返回格式正确")
        else:
            print("❌ text_formatter 返回格式错误")
    
    # 测试 report_generator
    report_generator_func = await tool_manager.get_tool('report_generator')
    if report_generator_func:
        result = report_generator_func("测试内容", "structured")
        if isinstance(result, dict) and 'report_content' in result:
            print("✅ report_generator 返回格式正确")
        else:
            print("❌ report_generator 返回格式错误")
    
    # 测试 file_writer
    file_writer_func = await tool_manager.get_tool('file_writer')
    if file_writer_func:
        result = file_writer_func("test.txt", "测试内容")
        if isinstance(result, dict) and 'status' in result:
            print("✅ file_writer 返回格式正确")
        else:
            print("❌ file_writer 返回格式错误")
    
    # 模拟完整Pipeline流程
    print("\n📋 模拟完整Pipeline流程:")
    
    # 1. 搜索
    print("1. 执行搜索...")
    search_result = smart_search_func("李自成生平", 2)
    print(f"   搜索结果: {len(search_result['results'])} 个")
    
    # 2. 文本格式化
    print("2. 执行文本格式化...")
    formatted_result = text_formatter_func(search_result['results'])
    print(f"   格式化结果: {len(formatted_result['formatted_text'])} 字符")
    
    # 3. 报告生成
    print("3. 执行报告生成...")
    report_result = report_generator_func(formatted_result['formatted_text'], "structured")
    print(f"   报告生成: {len(report_result['report_content'])} 字符")
    
    # 4. 文件写入
    print("4. 执行文件写入...")
    file_result = file_writer_func("test_complete.txt", report_result['report_content'])
    print(f"   文件写入: {file_result['status']}")
    
    # 验证数据流
    print("\n🔍 验证数据流:")
    print(f"   search_node.output.results: {'✓' if 'results' in search_result else '✗'}")
    print(f"   text_formatter_node.output.formatted_text: {'✓' if 'formatted_text' in formatted_result else '✗'}")
    print(f"   report_generator_node.output.report_content: {'✓' if 'report_content' in report_result else '✗'}")
    print(f"   file_writer_node.output.status: {'✓' if 'status' in file_result else '✗'}")
    
    print("\n🎯 测试完成")

if __name__ == "__main__":
    asyncio.run(test_complete_pipeline()) 