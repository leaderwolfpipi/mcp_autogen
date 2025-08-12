#!/usr/bin/env python3
"""
简单测试占位符解析修复
"""

import logging
from core.placeholder_resolver import PlaceholderResolver, NodeOutput

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_nested_placeholder_resolution():
    """测试嵌套占位符解析"""
    print("🧪 测试嵌套占位符解析")
    print("=" * 50)
    
    # 创建占位符解析器
    resolver = PlaceholderResolver()
    
    # 模拟节点输出（使用标准化的输出结构）
    rotate_output = {
        'status': 'success',
        'data': {
            'primary': ['/tmp/rotated_image_1.png', '/tmp/rotated_image_2.png'],
            'secondary': {'results': []},
            'counts': {'total': 2, 'successful': 2, 'failed': 0}
        },
        'metadata': {'tool_name': 'image_rotator_directory'},
        'paths': ['/tmp/rotated_image_1.png', '/tmp/rotated_image_2.png'],
        'message': 'Processed 2/2 images with rotation angle 45'
    }
    
    # 创建NodeOutput对象
    rotate_node_output = NodeOutput(
        node_id="rotate_node",
        output_type="any",
        output_key="output",
        value=rotate_output,
        description="旋转后的图片"
    )
    
    node_outputs = {"rotate_node": rotate_node_output}
    
    # 测试不同的占位符格式
    test_cases = [
        {
            "name": "嵌套占位符 - data.primary",
            "params": {
                "image_directory": "$rotate_node.output.data.primary",
                "scale_factor": 3
            },
            "expected": ['/tmp/rotated_image_1.png', '/tmp/rotated_image_2.png']
        },
        {
            "name": "简单占位符 - paths",
            "params": {
                "image_directory": "$rotate_node.output.paths",
                "scale_factor": 3
            },
            "expected": ['/tmp/rotated_image_1.png', '/tmp/rotated_image_2.png']
        },
        {
            "name": "状态占位符 - status",
            "params": {
                "status": "$rotate_node.output.status",
                "scale_factor": 3
            },
            "expected": "success"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   原始参数: {test_case['params']}")
        
        # 解析占位符
        resolved_params = resolver.resolve_placeholders(test_case['params'], node_outputs)
        print(f"   解析后参数: {resolved_params}")
        
        # 验证结果
        key = list(test_case['params'].keys())[0]  # 获取第一个键
        actual_value = resolved_params[key]
        expected_value = test_case['expected']
        
        if actual_value == expected_value:
            print(f"   ✅ 测试通过")
        else:
            print(f"   ❌ 测试失败")
            print(f"      期望: {expected_value}")
            print(f"      实际: {actual_value}")
    
    print("\n🎯 测试完成！")

if __name__ == "__main__":
    test_nested_placeholder_resolution() 