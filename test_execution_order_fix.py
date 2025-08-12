#!/usr/bin/env python3
"""
测试修复后的执行顺序构建功能
"""

import logging
from core.placeholder_resolver import PlaceholderResolver

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_execution_order_fix():
    """测试修复后的执行顺序构建功能"""
    print("🧪 测试修复后的执行顺序构建功能")
    print("=" * 60)
    
    # 初始化解析器
    resolver = PlaceholderResolver()
    
    # 测试用例：模拟你提供的pipeline
    test_cases = [
        {
            "name": "测试用例1: 娄建学资料查询pipeline",
            "components": [
                {
                    "id": "search_node",
                    "tool_type": "smart_search",
                    "params": {
                        "query": "娄建学的资料",
                        "max_results": 3
                    },
                    "output": {
                        "type": "object",
                        "fields": {
                            "data.primary": "搜索结果列表",
                            "data.secondary": "次要输出数据",
                            "metadata": "工具元信息",
                            "paths": "搜索源信息",
                            "status": "执行状态",
                            "message": "执行消息"
                        }
                    }
                },
                {
                    "id": "report_node",
                    "tool_type": "enhanced_report_generator",
                    "params": {
                        "content": "$search_node.output.data.primary",
                        "format": "markdown",
                        "title": "娄建学的资料",
                        "max_words": 800,
                        "style": "professional"
                    },
                    "output": {
                        "type": "object",
                        "fields": {
                            "status": "执行状态",
                            "data.primary": "生成的报告内容",
                            "message": "执行消息"
                        }
                    }
                },
                {
                    "id": "file_writer_node",
                    "tool_type": "file_writer",
                    "params": {
                        "file_path": "report.md",
                        "text": "$report_node.output.data.primary"
                    },
                    "output": {
                        "type": "object",
                        "fields": {
                            "status": "执行状态",
                            "message": "执行消息",
                            "paths": "文件路径"
                        }
                    }
                },
                {
                    "id": "upload_node",
                    "tool_type": "minio_uploader",
                    "params": {
                        "bucket_name": "kb-dev",
                        "file_path": "$file_writer_node.output.paths"
                    },
                    "output": {
                        "type": "object",
                        "fields": {
                            "status": "执行状态",
                            "data.primary": "上传后的URL或URL列表",
                            "data.secondary": "详细上传结果",
                            "data.counts": "上传统计",
                            "metadata": "工具元信息",
                            "paths": "上传文件路径列表",
                            "message": "执行消息",
                            "error": "错误信息"
                        }
                    }
                }
            ],
            "expected_order": ["search_node", "report_node", "file_writer_node", "upload_node"]
        },
        {
            "name": "测试用例2: 简单依赖链",
            "components": [
                {
                    "id": "node_a",
                    "tool_type": "smart_search",
                    "params": {"query": "test"},
                    "output": {"type": "object", "fields": {"data.primary": "结果"}}
                },
                {
                    "id": "node_b",
                    "tool_type": "enhanced_report_generator",
                    "params": {"content": "$node_a.output.data.primary"},
                    "output": {"type": "object", "fields": {"data.primary": "报告"}}
                },
                {
                    "id": "node_c",
                    "tool_type": "file_writer",
                    "params": {"text": "$node_b.output.data.primary"},
                    "output": {"type": "object", "fields": {"data.primary": "文件"}}
                }
            ],
            "expected_order": ["node_a", "node_b", "node_c"]
        },
        {
            "name": "测试用例3: 无依赖关系",
            "components": [
                {
                    "id": "independent_node_1",
                    "tool_type": "smart_search",
                    "params": {"query": "test1"},
                    "output": {"type": "object", "fields": {"data.primary": "结果1"}}
                },
                {
                    "id": "independent_node_2",
                    "tool_type": "smart_search",
                    "params": {"query": "test2"},
                    "output": {"type": "object", "fields": {"data.primary": "结果2"}}
                }
            ],
            "expected_order": ["independent_node_1", "independent_node_2"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 {test_case['name']}")
        print("-" * 50)
        
        components = test_case["components"]
        expected_order = test_case["expected_order"]
        
        # 显示组件信息
        print("组件列表:")
        for comp in components:
            print(f"  - {comp['id']} ({comp['tool_type']})")
        
        # 构建执行顺序
        print(f"\n🔍 构建执行顺序...")
        try:
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
            if len(execution_order) == len(expected_order):
                print(f"✅ 所有节点都被正确解析")
            else:
                print(f"❌ 节点解析不完整，期望 {len(expected_order)} 个节点，实际 {len(execution_order)} 个")
            
            # 检查执行顺序是否正确
            if execution_order == expected_order:
                print("🎉 执行顺序完全正确！")
            else:
                print(f"⚠️ 执行顺序与期望不同:")
                print(f"  期望: {' -> '.join(expected_order)}")
                print(f"  实际: {' -> '.join(execution_order)}")
                
        except Exception as e:
            print(f"❌ 构建执行顺序失败: {e}")
        
        print()

def test_heuristic_fallback():
    """测试启发式回退机制"""
    print("\n🔬 测试启发式回退机制")
    print("=" * 60)
    
    resolver = PlaceholderResolver()
    
    # 创建一个有循环依赖的pipeline（用于测试回退机制）
    components = [
        {
            "id": "node_a",
            "tool_type": "smart_search",
            "params": {"query": "test", "content": "$node_b.output.data.primary"},  # 循环依赖
            "output": {"type": "object", "fields": {"data.primary": "结果"}}
        },
        {
            "id": "node_b",
            "tool_type": "enhanced_report_generator",
            "params": {"content": "$node_a.output.data.primary"},  # 循环依赖
            "output": {"type": "object", "fields": {"data.primary": "报告"}}
        },
        {
            "id": "node_c",
            "tool_type": "file_writer",
            "params": {"text": "$node_b.output.data.primary"},
            "output": {"type": "object", "fields": {"data.primary": "文件"}}
        }
    ]
    
    print("组件列表（包含循环依赖）:")
    for comp in components:
        print(f"  - {comp['id']} ({comp['tool_type']})")
    
    # 构建执行顺序
    print(f"\n🔍 构建执行顺序（应该触发启发式回退）...")
    try:
        execution_order = resolver.build_execution_order(components)
        print(f"✅ 执行顺序: {' -> '.join(execution_order)}")
        
        # 验证执行顺序
        validation_errors = resolver.validate_execution_order(components, execution_order)
        if validation_errors:
            print("⚠️ 启发式排序验证警告:")
            for error in validation_errors:
                print(f"  - {error}")
        else:
            print("✅ 启发式排序验证通过")
            
    except Exception as e:
        print(f"❌ 构建执行顺序失败: {e}")

if __name__ == "__main__":
    test_execution_order_fix()
    test_heuristic_fallback() 