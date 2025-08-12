#!/usr/bin/env python3
"""
测试Schema驱动的数据解析器
演示如何根据工具的实际输出Schema来适配数据，而不是要求工具适配固定的Pipeline格式
"""

import asyncio
import logging
from core.schema_driven_resolver import SchemaDrivenResolver
from tools.smart_search import smart_search
from tools.text_formatter import text_formatter
from tools.report_generator import report_generator

# 设置日志
logging.basicConfig(level=logging.INFO)

def test_schema_driven_resolver():
    """测试Schema驱动的数据解析器"""
    print("🧪 测试Schema驱动的数据解析器")
    print("=" * 60)
    
    # 初始化Schema解析器
    resolver = SchemaDrivenResolver()
    print("✅ Schema驱动解析器初始化成功")
    
    # 注册工具的Schema
    print("\n📝 注册工具Schema:")
    
    # 注册smart_search的Schema
    resolver.register_tool_schema("smart_search", smart_search)
    print("✅ smart_search Schema已注册")
    
    # 注册text_formatter的Schema
    resolver.register_tool_schema("text_formatter", text_formatter)
    print("✅ text_formatter Schema已注册")
    
    # 注册report_generator的Schema
    resolver.register_tool_schema("report_generator", report_generator)
    print("✅ report_generator Schema已注册")
    
    # 测试工具的自然输出
    print("\n🔍 测试工具的自然输出:")
    
    # 1. 测试smart_search的自然输出
    print("1. 测试smart_search:")
    search_results = smart_search("李自成生平", 1)
    print(f"   自然输出类型: {type(search_results)}")
    print(f"   输出内容: {len(search_results)} 个结果")
    if search_results:
        print(f"   第一个结果标题: {search_results[0].get('title', 'N/A')}")
    
    # 2. 测试text_formatter的自然输出
    print("\n2. 测试text_formatter:")
    formatted_text = text_formatter(search_results)
    print(f"   自然输出类型: {type(formatted_text)}")
    print(f"   输出内容长度: {len(formatted_text)} 字符")
    print(f"   内容预览: {formatted_text[:100]}...")
    
    # 3. 测试report_generator的自然输出
    print("\n3. 测试report_generator:")
    report_content = report_generator(formatted_text, "structured")
    print(f"   自然输出类型: {type(report_content)}")
    print(f"   输出内容长度: {len(report_content)} 字符")
    print(f"   内容预览: {report_content[:100]}...")
    
    # 测试Schema驱动的数据提取
    print("\n🔧 测试Schema驱动的数据提取:")
    
    # 1. 从smart_search输出中提取"results"字段
    print("1. 从smart_search提取'results'字段:")
    extracted_results = resolver.extract_output_data("smart_search", search_results, ["results"])
    print(f"   提取结果: {extracted_results}")
    
    # 2. 从text_formatter输出中提取"formatted_text"字段
    print("\n2. 从text_formatter提取'formatted_text'字段:")
    extracted_text = resolver.extract_output_data("text_formatter", formatted_text, ["formatted_text"])
    print(f"   提取结果: {extracted_text}")
    
    # 3. 从report_generator输出中提取"report_content"字段
    print("\n3. 从report_generator提取'report_content'字段:")
    extracted_report = resolver.extract_output_data("report_generator", report_content, ["report_content"])
    print(f"   提取结果: {extracted_report}")
    
    # 测试Pipeline适配
    print("\n🔄 测试Pipeline适配:")
    
    # 模拟Pipeline期望的字段
    pipeline_expectations = {
        "search_node": ["results"],
        "text_formatter_node": ["formatted_text"],
        "report_generator_node": ["report_content"]
    }
    
    # 使用Schema解析器适配输出
    adapted_outputs = {}
    
    # 适配search_node输出
    adapted_outputs["search_node"] = resolver.extract_output_data(
        "smart_search", search_results, pipeline_expectations["search_node"]
    )
    
    # 适配text_formatter_node输出
    adapted_outputs["text_formatter_node"] = resolver.extract_output_data(
        "text_formatter", formatted_text, pipeline_expectations["text_formatter_node"]
    )
    
    # 适配report_generator_node输出
    adapted_outputs["report_generator_node"] = resolver.extract_output_data(
        "report_generator", report_content, pipeline_expectations["report_generator_node"]
    )
    
    print("Pipeline适配结果:")
    for node_name, adapted_output in adapted_outputs.items():
        print(f"   {node_name}: {adapted_output}")
    
    # 验证适配结果
    print("\n✅ 验证适配结果:")
    for node_name, expected_fields in pipeline_expectations.items():
        adapted_output = adapted_outputs[node_name]
        for field in expected_fields:
            if field in adapted_output:
                print(f"   ✓ {node_name}.{field} 适配成功")
            else:
                print(f"   ✗ {node_name}.{field} 适配失败")
    
    print("\n🎯 测试完成")
    print("\n💡 架构优势:")
    print("   1. 工具保持自然的输出格式，无需强制适配Pipeline")
    print("   2. Pipeline根据工具的Schema自动适配数据")
    print("   3. 支持智能字段映射和类型转换")
    print("   4. 提高了系统的灵活性和可维护性")

if __name__ == "__main__":
    test_schema_driven_resolver() 