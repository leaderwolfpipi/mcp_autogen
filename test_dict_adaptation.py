#!/usr/bin/env python3
"""
测试字典到文件路径的适配功能
"""

import logging
from core.placeholder_resolver import PlaceholderResolver

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_dict_to_file_path_adaptation():
    """测试字典到文件路径的适配功能"""
    print("🧪 测试字典到文件路径的适配功能")
    print("=" * 60)
    
    # 初始化解析器
    resolver = PlaceholderResolver()
    
    # 测试用例：模拟你的问题场景
    test_cases = [
        {
            "name": "测试用例1: 嵌套字典文件路径",
            "params": {
                "file_path": {
                    "file_path": "lou_jian_xue_report.txt",
                    "file_size": 1163
                },
                "bucket_name": "kb-dev"
            },
            "tool_type": "minio_uploader",
            "expected_adaptation": "file_path should be extracted from dict"
        },
        {
            "name": "测试用例2: 简单字典文件路径",
            "params": {
                "file_path": {
                    "file_path": "test.md",
                    "status": "success"
                },
                "bucket_name": "kb-dev"
            },
            "tool_type": "minio_uploader",
            "expected_adaptation": "file_path should be extracted from dict"
        },
        {
            "name": "测试用例3: 其他键名的文件路径",
            "params": {
                "file_path": {
                    "path": "document.pdf",
                    "size": 2048
                },
                "bucket_name": "kb-dev"
            },
            "tool_type": "minio_uploader",
            "expected_adaptation": "file_path should be extracted from path key"
        },
        {
            "name": "测试用例4: 正常字符串文件路径",
            "params": {
                "file_path": "normal_file.txt",
                "bucket_name": "kb-dev"
            },
            "tool_type": "minio_uploader",
            "expected_adaptation": "no adaptation needed"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 {test_case['name']}")
        print("-" * 50)
        
        params = test_case["params"]
        tool_type = test_case["tool_type"]
        
        print(f"原始参数: {params}")
        print(f"工具类型: {tool_type}")
        
        # 分析参数不匹配
        mismatches = resolver.parameter_adapter.analyze_parameter_mismatch(params, tool_type)
        
        if mismatches:
            print(f"发现 {len(mismatches)} 个参数不匹配:")
            for mismatch in mismatches:
                print(f"  - {mismatch['param_name']}: {mismatch['issue']}")
                print(f"    当前语义: {mismatch['param_semantic']}")
                print(f"    期望语义: {mismatch['expected_semantics']}")
        
        # 建议修复方案
        suggestions = resolver.parameter_adapter.suggest_parameter_fixes(mismatches, tool_type)
        
        if suggestions:
            print(f"建议的修复方案:")
            for suggestion in suggestions:
                print(f"  - {suggestion['param_name']}: {suggestion['description']}")
                print(f"    置信度: {suggestion['confidence']:.2f}")
        
        # 执行智能参数适配
        adapted_params = resolver.parameter_adapter.adapt_parameters(params, tool_type, {})
        
        print(f"适配后参数: {adapted_params}")
        
        # 检查是否有变化
        if adapted_params != params:
            print("✅ 参数适配成功")
            
            # 检查文件路径是否正确提取
            if "file_path" in adapted_params:
                file_path = adapted_params["file_path"]
                if isinstance(file_path, str) and file_path.endswith(('.txt', '.md', '.pdf')):
                    print(f"✅ 文件路径正确提取: {file_path}")
                else:
                    print(f"❌ 文件路径提取失败: {file_path}")
        else:
            print("ℹ️ 无需参数适配")
        
        print()

def test_integration_with_placeholder_resolution():
    """测试与占位符解析的集成"""
    print("\n🔗 测试与占位符解析的集成")
    print("=" * 60)
    
    resolver = PlaceholderResolver()
    
    # 模拟节点输出（包含字典结构）
    node_outputs = {
        "file_node": resolver.create_node_output(
            "file_node",
            {"type": "object", "fields": {"data.primary": "文件信息"}},
            {
                "file_path": "lou_jian_xue_report.txt",
                "file_size": 1163
            }
        )
    }
    
    # 测试参数（包含占位符和字典结构）
    params = {
        "file_path": "$file_node.output.data.primary",  # 占位符引用
        "bucket_name": "kb-dev"
    }
    
    print(f"原始参数: {params}")
    
    # 解析占位符并适配参数
    resolved_params = resolver.resolve_placeholders(params, node_outputs)
    
    print(f"解析和适配后参数: {resolved_params}")
    
    # 检查结果
    if "file_path" in resolved_params:
        file_path = resolved_params["file_path"]
        if isinstance(file_path, str) and file_path.endswith('.txt'):
            print("✅ 占位符解析和字典适配集成成功")
        else:
            print(f"❌ 集成测试失败，文件路径: {file_path}")
    else:
        print("❌ 集成测试失败，缺少file_path参数")

def test_extract_file_path_from_dict():
    """测试从字典中提取文件路径的功能"""
    print("\n🔍 测试从字典中提取文件路径")
    print("=" * 60)
    
    resolver = PlaceholderResolver()
    
    # 测试用例
    test_cases = [
        {
            "name": "嵌套字典",
            "data": {
                "file_path": {
                    "file_path": "test.txt",
                    "size": 1024
                }
            },
            "expected": "test.txt"
        },
        {
            "name": "简单字典",
            "data": {
                "file_path": "document.md",
                "status": "success"
            },
            "expected": "document.md"
        },
        {
            "name": "其他键名",
            "data": {
                "path": "report.pdf",
                "size": 2048
            },
            "expected": "report.pdf"
        },
        {
            "name": "复杂嵌套",
            "data": {
                "result": {
                    "file_info": {
                        "file_path": "nested.txt"
                    }
                }
            },
            "expected": "nested.txt"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 {test_case['name']}")
        print(f"输入: {test_case['data']}")
        
        result = resolver._extract_file_path_from_dict(test_case['data'])
        expected = test_case['expected']
        
        print(f"提取结果: {result}")
        print(f"期望结果: {expected}")
        
        if result == expected:
            print("✅ 提取成功")
        else:
            print("❌ 提取失败")

if __name__ == "__main__":
    test_dict_to_file_path_adaptation()
    test_integration_with_placeholder_resolution()
    test_extract_file_path_from_dict() 