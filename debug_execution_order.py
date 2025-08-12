#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试管道执行顺序问题
分析为什么upload_node会最先执行
"""

import asyncio
import logging
from core.placeholder_resolver import PlaceholderResolver
from core.requirement_parser import RequirementParser

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_execution_order():
    """分析执行顺序问题"""
    print("🔍 分析管道执行顺序问题")
    print("=" * 60)
    
    resolver = PlaceholderResolver()
    
    # 模拟您日志中的pipeline组件
    components = [
        {
            "id": "upload_node",
            "tool_type": "minio_uploader",
            "params": {
                "bucket_name": "kb-dev",
                "file_path": "zhuge_liang_report.pdf"
            },
            "output": {
                "type": "object",
                "fields": {
                    "file_path": "上传的文件路径",
                    "status": "执行状态",
                    "message": "执行消息"
                }
            }
        },
        {
            "id": "search_node",
            "tool_type": "smart_search",
            "params": {
                "query": "诸葛亮背景",
                "max_results": 3
            },
            "output": {
                "type": "object",
                "fields": {
                    "results": "搜索结果列表",
                    "status": "执行状态",
                    "message": "执行消息"
                }
            }
        },
        {
            "id": "report_node",
            "tool_type": "report_generator",
            "params": {
                "search_results": "$search_node.output.results",
                "template": "standard"
            },
            "output": {
                "type": "object",
                "fields": {
                    "report_content": "生成的报告内容",
                    "status": "执行状态"
                }
            }
        },
        {
            "id": "file_writer_node",
            "tool_type": "file_writer",
            "params": {
                "file_path": "zhuge_liang_report.pdf",
                "text": "$report_node.output.report_content"
            },
            "output": {
                "type": "object",
                "fields": {
                    "file_path": "输出文件路径",
                    "status": "执行状态"
                }
            }
        }
    ]
    
    print("📋 Pipeline组件定义:")
    for i, comp in enumerate(components):
        print(f"\n组件 {i+1}: {comp['id']}")
        print(f"  工具类型: {comp['tool_type']}")
        print(f"  参数: {comp['params']}")
    
    # 分析依赖关系
    print(f"\n🔗 分析依赖关系:")
    dependencies = {}
    node_ids = {comp["id"] for comp in components}
    
    for component in components:
        node_id = component["id"]
        dependencies[node_id] = set()
        
        # 检查该节点依赖的其他节点
        params = component.get("params", {})
        placeholder_refs = resolver._extract_placeholder_references(params)
        
        print(f"\n{node_id} 的占位符引用:")
        for ref in placeholder_refs:
            print(f"  - 引用节点: {ref['node_id']}")
            print(f"    输出键: {ref['output_key']}")
            if ref["node_id"] in node_ids:
                dependencies[node_id].add(ref["node_id"])
                print(f"    ✓ 依赖关系建立")
            else:
                print(f"    ✗ 引用的节点不存在")
    
    print(f"\n📊 依赖关系图:")
    for node_id, deps in dependencies.items():
        if deps:
            print(f"  {node_id} 依赖: {list(deps)}")
        else:
            print(f"  {node_id} 无依赖")
    
    # 构建执行顺序
    print(f"\n📋 构建执行顺序:")
    execution_order = resolver.build_execution_order(components)
    print(f"执行顺序: {' -> '.join(execution_order)}")
    
    # 分析问题
    print(f"\n🔍 问题分析:")
    print("从日志来看，upload_node 最先执行，这可能是因为:")
    print("1. upload_node 没有依赖其他节点")
    print("2. 其他节点可能依赖 upload_node 的输出")
    print("3. 或者依赖关系配置有问题")
    
    # 检查正确的执行顺序应该是怎样的
    print(f"\n✅ 正确的执行顺序应该是:")
    print("1. search_node (搜索诸葛亮背景)")
    print("2. report_node (基于搜索结果生成报告)")
    print("3. file_writer_node (将报告写入文件)")
    print("4. upload_node (上传生成的文件)")
    
    # 修复建议
    print(f"\n🔧 修复建议:")
    print("1. 确保 upload_node 依赖 file_writer_node:")
    print("   upload_node.params.file_path = '$file_writer_node.output.file_path'")
    print("2. 或者重新设计pipeline，让upload_node在最后执行")
    print("3. 检查占位符引用是否正确配置")

def test_corrected_pipeline():
    """测试修正后的pipeline"""
    print(f"\n🧪 测试修正后的Pipeline")
    print("=" * 60)
    
    resolver = PlaceholderResolver()
    
    # 修正后的pipeline组件
    corrected_components = [
        {
            "id": "search_node",
            "tool_type": "smart_search",
            "params": {
                "query": "诸葛亮背景",
                "max_results": 3
            },
            "output": {
                "type": "object",
                "fields": {
                    "results": "搜索结果列表",
                    "status": "执行状态",
                    "message": "执行消息"
                }
            }
        },
        {
            "id": "report_node",
            "tool_type": "report_generator",
            "params": {
                "search_results": "$search_node.output.results",
                "template": "standard"
            },
            "output": {
                "type": "object",
                "fields": {
                    "report_content": "生成的报告内容",
                    "status": "执行状态"
                }
            }
        },
        {
            "id": "file_writer_node",
            "tool_type": "file_writer",
            "params": {
                "file_path": "zhuge_liang_report.pdf",
                "text": "$report_node.output.report_content"
            },
            "output": {
                "type": "object",
                "fields": {
                    "file_path": "输出文件路径",
                    "status": "执行状态"
                }
            }
        },
        {
            "id": "upload_node",
            "tool_type": "minio_uploader",
            "params": {
                "bucket_name": "kb-dev",
                "file_path": "$file_writer_node.output.file_path"  # 修正：依赖file_writer_node的输出
            },
            "output": {
                "type": "object",
                "fields": {
                    "file_path": "上传的文件路径",
                    "status": "执行状态",
                    "message": "执行消息"
                }
            }
        }
    ]
    
    print("📋 修正后的Pipeline组件:")
    for i, comp in enumerate(corrected_components):
        print(f"\n组件 {i+1}: {comp['id']}")
        print(f"  工具类型: {comp['tool_type']}")
        print(f"  参数: {comp['params']}")
    
    # 验证依赖关系
    print(f"\n🔗 验证修正后的依赖关系:")
    validation_errors = resolver.validate_pipeline_dependencies(corrected_components)
    if validation_errors:
        print("❌ 验证失败:")
        for error in validation_errors:
            print(f"  - {error}")
    else:
        print("✅ 依赖关系验证通过")
    
    # 构建执行顺序
    print(f"\n📋 修正后的执行顺序:")
    execution_order = resolver.build_execution_order(corrected_components)
    print(f"执行顺序: {' -> '.join(execution_order)}")
    
    print(f"\n✅ 现在upload_node会在最后执行，这是正确的！")

def main():
    """主函数"""
    analyze_execution_order()
    test_corrected_pipeline()

if __name__ == "__main__":
    main() 