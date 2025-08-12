#!/usr/bin/env python3
"""
测试通用性节点ID解析方案
"""

import asyncio
import logging
from core.placeholder_resolver import PlaceholderResolver

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_universal_node_resolution():
    """测试通用性节点ID解析方案"""
    print("🧪 测试通用性节点ID解析方案")
    print("=" * 60)
    
    # 初始化解析器
    resolver = PlaceholderResolver()
    
    # 测试用例1: 各种不同的节点ID引用模式
    test_cases = [
        {
            "name": "测试用例1: 基本模式匹配",
            "components": [
                {"id": "search_node", "tool_type": "smart_search", "params": {"query": "test"}},
                {"id": "report_node", "tool_type": "enhanced_report_generator", "params": {"content": "$search_node.output.data.primary"}},
                {"id": "file_writer_node", "tool_type": "file_writer", "params": {"text": "$enhanced_report_node.output.data.primary"}},
                {"id": "upload_node", "tool_type": "minio_uploader", "params": {"file_path": "$file_writer_node.output.data.primary"}}
            ]
        },
        {
            "name": "测试用例2: 语义相似性匹配",
            "components": [
                {"id": "web_search_tool", "tool_type": "smart_search", "params": {"query": "test"}},
                {"id": "report_generator", "tool_type": "enhanced_report_generator", "params": {"content": "$search_results_node.output.data.primary"}},
                {"id": "file_processor", "tool_type": "file_writer", "params": {"text": "$report_generator_node.output.data.primary"}},
                {"id": "cloud_uploader", "tool_type": "minio_uploader", "params": {"file_path": "$file_processor_node.output.data.primary"}}
            ]
        },
        {
            "name": "测试用例3: 启发式匹配",
            "components": [
                {"id": "image_processor", "tool_type": "image_processor", "params": {"image": "test.jpg"}},
                {"id": "text_handler", "tool_type": "text_processor", "params": {"content": "$image_processor_node.output.text"}},
                {"id": "data_processor", "tool_type": "data_processor", "params": {"data": "$text_handler_node.output.data"}},
                {"id": "file_writer", "tool_type": "file_writer", "params": {"text": "$data_processor_node.output.result"}}
            ]
        },
        {
            "name": "测试用例4: 混合模式",
            "components": [
                {"id": "smart_search", "tool_type": "smart_search", "params": {"query": "test"}},
                {"id": "enhanced_report", "tool_type": "enhanced_report_generator", "params": {"content": "$search_results_node.output.data.primary"}},
                {"id": "file_writer", "tool_type": "file_writer", "params": {"text": "$enhanced_report_node.output.data.primary"}},
                {"id": "minio_uploader", "tool_type": "minio_uploader", "params": {"file_path": "$file_writer_node.output.data.primary"}}
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 {test_case['name']}")
        print("-" * 40)
        
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
        expected_order = ['search_node', 'report_node', 'file_writer_node', 'upload_node']
        if len(execution_order) == len(expected_order):
            print(f"✅ 所有节点都被正确解析")
        else:
            print(f"❌ 节点解析不完整，期望 {len(expected_order)} 个节点，实际 {len(execution_order)} 个")
        
        print()

def test_node_id_resolution_strategies():
    """测试各种节点ID解析策略"""
    print("\n🔬 测试节点ID解析策略")
    print("=" * 60)
    
    resolver = PlaceholderResolver()
    
    # 测试数据
    available_node_ids = {
        'search_node', 'report_node', 'file_writer_node', 'upload_node',
        'image_processor', 'text_processor', 'data_processor'
    }
    
    test_references = [
        # 模糊匹配测试
        ('enhanced_report_node', 'report_node'),
        ('search_results_node', 'search_node'),
        ('file_output_node', 'file_writer_node'),
        ('upload_output_node', 'upload_node'),
        
        # 语义匹配测试
        ('web_search_tool', 'search_node'),
        ('report_generator', 'report_node'),
        ('file_processor', 'file_writer_node'),
        ('cloud_uploader', 'upload_node'),
        
        # 启发式匹配测试
        ('image_processor_node', 'image_processor'),
        ('text_handler_node', 'text_processor'),
        ('data_processor_node', 'data_processor'),
        
        # 混合模式测试
        ('smart_search', 'search_node'),
        ('enhanced_report', 'report_node'),
        ('file_writer', 'file_writer_node'),
        ('minio_uploader', 'upload_node'),
    ]
    
    print("节点ID解析测试结果:")
    print("-" * 50)
    
    for referenced_id, expected_id in test_references:
        resolved_id = resolver._resolve_node_id_reference(referenced_id, available_node_ids)
        status = "✅" if resolved_id == expected_id else "❌"
        print(f"{status} {referenced_id:25} -> {resolved_id:20} (期望: {expected_id})")

def test_similarity_calculation():
    """测试相似度计算"""
    print("\n📊 测试相似度计算")
    print("=" * 60)
    
    resolver = PlaceholderResolver()
    
    test_pairs = [
        ('enhanced_report_node', 'report_node'),
        ('search_results_node', 'search_node'),
        ('file_output_node', 'file_writer_node'),
        ('web_search_tool', 'search_node'),
        ('report_generator', 'report_node'),
        ('image_processor_node', 'image_processor'),
    ]
    
    print("相似度计算结果:")
    print("-" * 40)
    
    for id1, id2 in test_pairs:
        keywords1 = resolver._extract_keywords(id1)
        keywords2 = resolver._extract_keywords(id2)
        similarity = resolver._calculate_similarity_score(keywords1, keywords2)
        
        print(f"{id1:25} vs {id2:20} -> {similarity:.3f}")
        print(f"  关键词1: {keywords1}")
        print(f"  关键词2: {keywords2}")
        print()

if __name__ == "__main__":
    asyncio.run(test_universal_node_resolution())
    test_node_id_resolution_strategies()
    test_similarity_calculation() 