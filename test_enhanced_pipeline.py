#!/usr/bin/env python3
"""
测试增强版Pipeline系统
"""

import asyncio
import logging
from core.smart_pipeline_engine import SmartPipelineEngine

# 设置日志
logging.basicConfig(level=logging.INFO)

async def test_enhanced_pipeline():
    """测试增强版Pipeline系统"""
    print("🧪 测试增强版Pipeline系统")
    print("=" * 50)
    
    # 初始化引擎
    engine = SmartPipelineEngine(use_llm=False)
    print("✅ 智能Pipeline引擎初始化成功")
    
    # 模拟Pipeline执行
    print("\n📋 模拟增强版Pipeline流程:")
    
    # 1. 执行增强搜索
    print("1. 执行增强搜索...")
    from tools.smart_search import smart_search
    search_result = smart_search("李自成生平经历", 2)
    print(f"   搜索结果: {len(search_result['results'])} 个")
    for i, result in enumerate(search_result['results']):
        print(f"   - 结果 {i+1}: {result['title']}")
        print(f"     内容长度: {result.get('content_length', 0)} 字符")
        print(f"     内容预览: {result.get('full_content', result.get('snippet', ''))[:100]}...")
    
    # 2. 执行文本格式化
    print("\n2. 执行文本格式化...")
    from tools.text_formatter import text_formatter
    formatted_result = text_formatter(search_result['results'])
    print(f"   格式化结果: {len(formatted_result['formatted_text'])} 字符")
    print(f"   格式化预览: {formatted_result['formatted_text'][:200]}...")
    
    # 3. 执行报告生成
    print("\n3. 执行报告生成...")
    from tools.report_generator import report_generator
    report_result = report_generator(formatted_result['formatted_text'], "structured")
    print(f"   报告生成: {len(report_result['report_content'])} 字符")
    print(f"   报告预览: {report_result['report_content'][:200]}...")
    
    # 4. 执行文件写入
    print("\n4. 执行文件写入...")
    from tools.file_writer import file_writer
    file_result = file_writer("test_enhanced.txt", report_result['report_content'])
    print(f"   文件写入: {file_result['status']}")
    
    # 验证数据流
    print("\n🔍 验证数据流:")
    print(f"   search_node.output.results: {'✓' if 'results' in search_result else '✗'}")
    print(f"   text_formatter_node.output.formatted_text: {'✓' if 'formatted_text' in formatted_result else '✗'}")
    print(f"   report_generator_node.output.report_content: {'✓' if 'report_content' in report_result else '✗'}")
    print(f"   file_writer_node.output.status: {'✓' if 'status' in file_result else '✗'}")
    
    # 显示最终结果
    print(f"\n📄 最终文件内容预览:")
    try:
        with open("test_enhanced.txt", "r", encoding="utf-8") as f:
            content = f.read()
            print(f"   文件大小: {len(content)} 字符")
            print(f"   内容预览: {content[:300]}...")
    except Exception as e:
        print(f"   读取文件失败: {e}")
    
    print("\n🎯 测试完成")

if __name__ == "__main__":
    asyncio.run(test_enhanced_pipeline()) 