#!/usr/bin/env python3
"""
调试占位符解析
"""

import re
import logging
from core.placeholder_resolver import PlaceholderResolver, NodeOutput

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def debug_placeholder_pattern():
    """调试占位符模式匹配"""
    print("🔍 调试占位符模式匹配")
    print("=" * 50)
    
    # 创建占位符解析器
    resolver = PlaceholderResolver()
    
    # 测试占位符
    test_placeholders = [
        "$rotate_node.output.primary",
        "$rotate_node.output.data.primary", 
        "$rotate_node.output.paths",
        "$rotate_node.output.status"
    ]
    
    print(f"占位符模式: {resolver.placeholder_pattern}")
    print()
    
    for placeholder in test_placeholders:
        print(f"测试占位符: {placeholder}")
        matches = list(re.finditer(resolver.placeholder_pattern, placeholder))
        
        if matches:
            for i, match in enumerate(matches):
                print(f"  匹配 {i+1}:")
                print(f"    完整匹配: {match.group(0)}")
                print(f"    节点ID: {match.group(1)}")
                print(f"    输出键: {match.group(2)}")
        else:
            print("  ❌ 没有匹配")
        print()

def debug_placeholder_resolution():
    """调试占位符解析"""
    print("🔧 调试占位符解析")
    print("=" * 50)
    
    # 创建占位符解析器
    resolver = PlaceholderResolver()
    
    # 模拟节点输出
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
    
    # 测试参数
    test_params = {
        "image_directory": "$rotate_node.output.primary",
        "scale_factor": 3
    }
    
    print(f"原始参数: {test_params}")
    print(f"节点输出: {rotate_node_output.value}")
    print()
    
    # 解析占位符
    resolved_params = resolver.resolve_placeholders(test_params, node_outputs)
    print(f"解析后参数: {resolved_params}")
    
    # 检查是否成功解析
    if resolved_params["image_directory"] == test_params["image_directory"]:
        print("❌ 占位符没有被解析")
    else:
        print("✅ 占位符解析成功")

if __name__ == "__main__":
    debug_placeholder_pattern()
    debug_placeholder_resolution() 