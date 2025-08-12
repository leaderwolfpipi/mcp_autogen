#!/usr/bin/env python3
"""
测试通用性依赖解析方案
"""

import asyncio
import logging
from core.placeholder_resolver import PlaceholderResolver

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_universal_dependency_resolution():
    """测试通用性依赖解析方案"""
    print("🧪 测试通用性依赖解析方案")
    print("=" * 60)
    
    # 初始化解析器
    resolver = PlaceholderResolver()
    
    # 测试用例：模拟LLM生成的不一致节点ID
    test_cases = [
        {
            "name": "测试用例1: 不一致的节点ID引用",
            "components": [
                {
                    "id": "search_node",
                    "tool_type": "smart_search",
                    "params": {"query": "常州天目湖景区旅游信息", "max_results": 3},
                    "output": {"type": "object", "fields": {"data.primary": "搜索结果列表"}}
                },
                {
                    "id": "report_node",
                    "tool_type": "enhanced_report_generator",
                    "params": {"content": "$search_node.output.data.primary", "format": "markdown"},
                    "output": {"type": "object", "fields": {"data.primary": "生成的报告内容"}}
                },
                {
                    "id": "file_node",
                    "tool_type": "file_writer",
                    "params": {"file_path": "tianmu_lake_tour.md", "text": "$enhanced_report_node.output.data.primary"},
                    "output": {"type": "object", "fields": {"data.primary": "文件写入结果"}}
                },
                {
                    "id": "upload_node",
                    "tool_type": "minio_uploader",
                    "params": {"bucket_name": "kb-dev", "file_path": "tianmu_lake_tour.md"},
                    "output": {"type": "object", "fields": {"data.primary": "上传后的URL"}}
                }
            ]
        },
        {
            "name": "测试用例2: 完全不同的节点ID命名",
            "components": [
                {
                    "id": "web_search_tool",
                    "tool_type": "smart_search",
                    "params": {"query": "常州天目湖景区旅游信息", "max_results": 3},
                    "output": {"type": "object", "fields": {"data.primary": "搜索结果列表"}}
                },
                {
                    "id": "report_generator",
                    "tool_type": "enhanced_report_generator",
                    "params": {"content": "$search_results_node.output.data.primary", "format": "markdown"},
                    "output": {"type": "object", "fields": {"data.primary": "生成的报告内容"}}
                },
                {
                    "id": "file_processor",
                    "tool_type": "file_writer",
                    "params": {"file_path": "tianmu_lake_tour.md", "text": "$report_generator_node.output.data.primary"},
                    "output": {"type": "object", "fields": {"data.primary": "文件写入结果"}}
                },
                {
                    "id": "cloud_uploader",
                    "tool_type": "minio_uploader",
                    "params": {"bucket_name": "kb-dev", "file_path": "tianmu_lake_tour.md"},
                    "output": {"type": "object", "fields": {"data.primary": "上传后的URL"}}
                }
            ]
        },
        {
            "name": "测试用例3: 混合命名模式",
            "components": [
                {
                    "id": "smart_search",
                    "tool_type": "smart_search",
                    "params": {"query": "常州天目湖景区旅游信息", "max_results": 3},
                    "output": {"type": "object", "fields": {"data.primary": "搜索结果列表"}}
                },
                {
                    "id": "enhanced_report",
                    "tool_type": "enhanced_report_generator",
                    "params": {"content": "$search_results_node.output.data.primary", "format": "markdown"},
                    "output": {"type": "object", "fields": {"data.primary": "生成的报告内容"}}
                },
                {
                    "id": "file_writer",
                    "tool_type": "file_writer",
                    "params": {"file_path": "tianmu_lake_tour.md", "text": "$enhanced_report_node.output.data.primary"},
                    "output": {"type": "object", "fields": {"data.primary": "文件写入结果"}}
                },
                {
                    "id": "minio_uploader",
                    "tool_type": "minio_uploader",
                    "params": {"bucket_name": "kb-dev", "file_path": "tianmu_lake_tour.md"},
                    "output": {"type": "object", "fields": {"data.primary": "上传后的URL"}}
                }
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 {test_case['name']}")
        print("-" * 50)
        
        components = test_case["components"]
        
        # 显示组件信息
        print("组件列表:")
        for comp in components:
            print(f"  - {comp['id']} ({comp['tool_type']})")
        
        # 构建执行顺序
        print(f"\n🔍 构建执行顺序...")
        execution_order = resolver.build_execution_order(components)
        print(f"✅ 执行顺序: {' -> '.join(execution_order)}")
        
        # 验证执行顺序
        print(f"\n🔍 验证执行顺序...")
        validation_errors = resolver.validate_execution_order(components, execution_order)
        if validation_errors:
            print("❌ 验证失败:")
            for error in validation_errors:
                print(f"  - {error}")
        else:
            print("✅ 执行顺序验证通过")
        
        # 检查是否所有节点都被正确解析
        expected_order = ['search_node', 'report_node', 'file_node', 'upload_node']
        if len(execution_order) == len(expected_order):
            print(f"✅ 所有节点都被正确解析")
        else:
            print(f"❌ 节点解析不完整，期望 {len(expected_order)} 个节点，实际 {len(execution_order)} 个")
        
        print()

def test_semantic_analysis():
    """测试语义依赖分析"""
    print("\n🔬 测试语义依赖分析")
    print("=" * 60)
    
    resolver = PlaceholderResolver()
    
    # 测试语义依赖分析
    components = [
        {
            "id": "search_tool",
            "tool_type": "smart_search",
            "params": {"query": "test"},
            "output": {"type": "object", "fields": {"data.primary": "搜索结果"}}
        },
        {
            "id": "report_generator",
            "tool_type": "enhanced_report_generator",
            "params": {"content": "$search_results.output.data.primary"},
            "output": {"type": "object", "fields": {"data.primary": "报告内容"}}
        },
        {
            "id": "file_writer",
            "tool_type": "file_writer",
            "params": {"text": "$report_generator.output.data.primary"},
            "output": {"type": "object", "fields": {"data.primary": "文件路径"}}
        }
    ]
    
    print("组件列表:")
    for comp in components:
        print(f"  - {comp['id']} ({comp['tool_type']})")
    
    # 分析语义依赖
    dependencies = resolver.semantic_analyzer.analyze_dependencies(components)
    
    print(f"\n📊 发现的语义依赖关系:")
    for dep in dependencies:
        print(f"  {dep.source_node_id} -> {dep.target_node_id} ({dep.dependency_type}, 置信度: {dep.confidence:.2f})")
        print(f"    证据: {dep.evidence}")
    
    # 构建执行顺序
    execution_order = resolver.semantic_analyzer.build_execution_order(components)
    print(f"\n✅ 语义分析执行顺序: {' -> '.join(execution_order)}")

if __name__ == "__main__":
    asyncio.run(test_universal_dependency_resolution())
    test_semantic_analysis() 