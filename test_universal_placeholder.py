#!/usr/bin/env python3
"""
测试真正通用的占位符解析
"""

import logging
from core.placeholder_resolver import PlaceholderResolver, NodeOutput

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_universal_placeholder_resolution():
    """测试真正通用的占位符解析"""
    print("🌐 测试真正通用的占位符解析")
    print("=" * 60)
    
    resolver = PlaceholderResolver()
    
    # 测试各种不同类型的输出
    test_cases = [
        {
            "name": "图片处理输出",
            "output": {
                'status': 'success',
                'temp_path': '/path/to/image.jpg',
                'file_path': '/path/to/file.jpg',
                'rotated_image': '<PIL.Image.Image object>'
            },
            "output_type": "any",
            "output_key": "rotated_image",
            "expected": "/path/to/image.jpg"  # 应该选择temp_path
        },
        {
            "name": "文件上传输出",
            "output": {
                'status': 'success',
                'upload_url': 'https://example.com/file.txt',
                'file_location': '/cloud/storage/file.txt'
            },
            "output_type": "any",
            "output_key": "upload_result",
            "expected": "https://example.com/file.txt"  # 应该选择upload_url
        },
        {
            "name": "文本处理输出",
            "output": {
                'status': 'success',
                'translated_text': 'Hello World',
                'content': 'Some content'
            },
            "output_type": "any",
            "output_key": "translated_text",
            "expected": "Hello World"  # 应该使用output_key
        },
        {
            "name": "数据分析输出",
            "output": {
                'status': 'success',
                'analysis_result': {'mean': 10.5},
                'data_path': '/path/to/data.csv'
            },
            "output_type": "any",
            "output_key": "analysis_result",
            "expected": {'mean': 10.5}  # 应该使用output_key
        },
        {
            "name": "通用处理输出",
            "output": {
                'status': 'success',
                'result': 'Final result',
                'output': 'Processed output'
            },
            "output_type": "any",
            "output_key": "processed_result",
            "expected": "Final result"  # 应该选择第一个非None值
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 测试 {i}: {test_case['name']}")
        
        node_output = NodeOutput(
            node_id=f"test_node_{i}",
            output_type=test_case["output_type"],
            output_key=test_case["output_key"],
            value=test_case["output"],
            description=test_case["name"]
        )
        
        node_outputs = {f"test_node_{i}": node_output}
        
        test_params = {
            "param": f"$test_node_{i}.output"
        }
        
        resolved_params = resolver.resolve_placeholders(test_params, node_outputs)
        actual_value = resolved_params["param"]
        
        print(f"  输出: {test_case['output']}")
        print(f"  输出键: {test_case['output_key']}")
        print(f"  期望值: {test_case['expected']}")
        print(f"  实际值: {actual_value}")
        
        if actual_value == test_case['expected']:
            print("  ✅ 通过")
        else:
            print("  ❌ 失败")

def test_specific_key_reference():
    """测试指定键的引用"""
    print(f"\n🎯 测试指定键的引用")
    print("=" * 60)
    
    resolver = PlaceholderResolver()
    
    # 模拟复杂的输出
    complex_output = {
        'status': 'success',
        'temp_path': '/path/to/temp.jpg',
        'file_path': '/path/to/file.jpg',
        'upload_url': 'https://example.com/file.jpg',
        'metadata': {
            'size': 1024,
            'format': 'jpg'
        }
    }
    
    node_output = NodeOutput(
        node_id="complex_node",
        output_type="any",
        output_key="result",
        value=complex_output,
        description="复杂输出"
    )
    
    node_outputs = {"complex_node": node_output}
    
    # 测试不同的引用方式
    test_params = {
        "path_param": "$complex_node.output",  # 通用引用
        "temp_param": "$complex_node.output.temp_path",  # 指定键引用
        "url_param": "$complex_node.output.upload_url",  # 指定键引用
        "metadata_param": "$complex_node.output.metadata"  # 指定键引用
    }
    
    resolved_params = resolver.resolve_placeholders(test_params, node_outputs)
    
    print("原始参数:", test_params)
    print("解析后参数:", resolved_params)
    
    # 验证结果
    expected_results = {
        "path_param": "/path/to/temp.jpg",  # 应该选择temp_path
        "temp_param": "/path/to/temp.jpg",
        "url_param": "https://example.com/file.jpg",
        "metadata_param": {'size': 1024, 'format': 'jpg'}
    }
    
    for key, expected in expected_results.items():
        actual = resolved_params[key]
        if actual == expected:
            print(f"✅ {key}: {actual}")
        else:
            print(f"❌ {key}: 期望 {expected}, 实际 {actual}")

if __name__ == "__main__":
    test_universal_placeholder_resolution()
    test_specific_key_reference() 