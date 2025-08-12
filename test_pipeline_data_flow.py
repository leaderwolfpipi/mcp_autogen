#!/usr/bin/env python3
"""
测试Pipeline数据流修复
"""

import asyncio
import logging
from core.smart_pipeline_engine import SmartPipelineEngine

# 设置日志
logging.basicConfig(level=logging.INFO)

async def test_pipeline_data_flow():
    """测试Pipeline数据流"""
    print("🧪 测试Pipeline数据流修复")
    print("=" * 50)
    
    # 初始化引擎
    engine = SmartPipelineEngine(use_llm=False)
    print("✅ 智能Pipeline引擎初始化成功")
    
    # 模拟Pipeline执行
    print("\n📋 模拟Pipeline执行流程:")
    
    # 1. 执行搜索
    print("1. 执行 smart_search...")
    from tools.smart_search import smart_search
    search_result = smart_search("李自成生平经历和事迹", 2)
    print(f"   搜索结果: {len(search_result['results'])} 个结果")
    
    # 2. 执行文本格式化
    print("2. 执行 text_formatter...")
    from tools.text_formatter import text_formatter
    formatted_result = text_formatter(search_result['results'])
    print(f"   格式化结果: {len(formatted_result['formatted_text'])} 字符")
    
    # 3. 执行文件写入
    print("3. 执行 file_writer...")
    from tools.file_writer import file_writer
    file_result = file_writer("test_report.txt", formatted_result['formatted_text'])
    print(f"   文件写入结果: {file_result['status']}")
    
    # 验证数据流
    print("\n🔍 验证数据流:")
    print(f"   search_node.output.results: {'✓' if 'results' in search_result else '✗'}")
    print(f"   text_formatter_node.output.formatted_text: {'✓' if 'formatted_text' in formatted_result else '✗'}")
    print(f"   file_writer_node.output.status: {'✓' if 'status' in file_result else '✗'}")
    
    # 显示最终结果
    print(f"\n📄 最终文件内容预览:")
    try:
        with open("test_report.txt", "r", encoding="utf-8") as f:
            content = f.read()
            print(f"   文件大小: {len(content)} 字符")
            print(f"   内容预览: {content[:200]}...")
    except Exception as e:
        print(f"   读取文件失败: {e}")
    
    print("\n🎯 测试完成")

if __name__ == "__main__":
    asyncio.run(test_pipeline_data_flow()) 