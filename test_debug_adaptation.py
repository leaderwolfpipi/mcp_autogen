#!/usr/bin/env python3
"""
调试适配问题
重现实际pipeline中的问题并查看详细日志
"""

import asyncio
import logging
import tempfile
import os
from PIL import Image

from tools.image_rotator import image_rotator
from tools.image_scaler import image_scaler
from core.placeholder_resolver import PlaceholderResolver, NodeOutput
from core.tool_adapter import get_tool_adapter

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_test_images():
    """创建测试图片"""
    test_dir = "./test_debug_images"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建几个测试图片
    image_paths = []
    for i in range(2):
        img = Image.new('RGB', (100 + i*20, 100 + i*20), color=f'rgb({i*80}, {i*60}, {i*40})')
        img_path = os.path.join(test_dir, f"test_image_{i}.png")
        img.save(img_path)
        image_paths.append(img_path)
        print(f"创建测试图片: {img_path}")
    
    return image_paths

def test_actual_problem():
    """重现实际pipeline中的问题"""
    print("🧪 重现实际pipeline中的问题")
    print("=" * 60)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 第一步：执行image_rotator（模拟rotate_images_node）
    print("第一步：执行image_rotator")
    rotator_result = image_rotator(image_paths, angle=45)
    
    print(f"rotator_result: {rotator_result}")
    print(f"rotator_result类型: {type(rotator_result)}")
    print(f"rotator_result键: {list(rotator_result.keys())}")
    
    # 创建NodeOutput对象（模拟实际pipeline中的情况）
    rotator_output = NodeOutput(
        node_id="rotate_images_node",
        output_type="any",
        output_key="rotated_images",  # 这个键可能不匹配
        value=rotator_result,
        description="旋转后的图片"
    )
    
    print(f"\nNodeOutput信息:")
    print(f"  node_id: {rotator_output.node_id}")
    print(f"  output_key: {rotator_output.output_key}")
    print(f"  value类型: {type(rotator_output.value)}")
    print(f"  value: {rotator_output.value}")
    
    # 第二步：模拟占位符解析（模拟scale_images_node的参数解析）
    print("\n第二步：模拟占位符解析")
    resolver = PlaceholderResolver()
    
    # 模拟scale_images_node的参数
    scale_params = {
        "image_path": "$rotate_images_node.output.temp_paths",
        "scale_factor": 3
    }
    
    print(f"原始参数: {scale_params}")
    
    node_outputs = {"rotate_images_node": rotator_output}
    
    # 解析占位符
    resolved_params = resolver.resolve_placeholders(scale_params, node_outputs)
    
    print(f"解析后的参数: {resolved_params}")
    print(f"image_path类型: {type(resolved_params.get('image_path'))}")
    print(f"image_path值: {resolved_params.get('image_path')}")

def test_auto_adapt_output():
    """测试auto_adapt_output方法"""
    print("\n🧪 测试auto_adapt_output方法")
    print("=" * 60)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 执行image_rotator
    rotator_result = image_rotator(image_paths, angle=45)
    
    # 创建NodeOutput对象
    rotator_output = NodeOutput(
        node_id="rotate_images_node",
        output_type="any",
        output_key="rotated_images",
        value=rotator_result,
        description="旋转后的图片"
    )
    
    # 获取工具适配器
    adapter = get_tool_adapter()
    
    # 目标期望（模拟scale_images_node期望的键）
    target_expectation = {
        "image_path": "expected_type"
    }
    
    print(f"源输出: {rotator_result}")
    print(f"目标期望: {target_expectation}")
    
    # 自动适配
    print("\n开始自动适配...")
    adapted_output = adapter.auto_adapt_output(rotator_output, target_expectation)
    
    print(f"适配后的输出: {adapted_output}")
    print(f"适配后输出类型: {type(adapted_output)}")

def test_key_matching():
    """测试键匹配逻辑"""
    print("\n🧪 测试键匹配逻辑")
    print("=" * 60)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 执行image_rotator
    rotator_result = image_rotator(image_paths, angle=45)
    
    # 获取工具适配器
    adapter = get_tool_adapter()
    
    # 测试不同的目标键
    target_keys = ["image_path", "images", "temp_paths", "rotated_images", "data"]
    source_keys = list(rotator_result.keys())
    
    print(f"源字典键: {source_keys}")
    print(f"源字典值: {rotator_result}")
    
    for target_key in target_keys:
        print(f"\n测试目标键: {target_key}")
        best_match = adapter._find_best_key_match(target_key, source_keys)
        similarity = adapter._calculate_key_similarity(target_key, best_match) if best_match else 0
        print(f"  最佳匹配: {best_match}")
        print(f"  相似度: {similarity}")
        if best_match:
            print(f"  匹配值: {rotator_result[best_match]}")

def test_placeholder_resolution_with_different_keys():
    """测试不同键的占位符解析"""
    print("\n🧪 测试不同键的占位符解析")
    print("=" * 60)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 执行image_rotator
    rotator_result = image_rotator(image_paths, angle=45)
    
    # 创建NodeOutput对象
    rotator_output = NodeOutput(
        node_id="rotate_images_node",
        output_type="any",
        output_key="rotated_images",
        value=rotator_result,
        description="旋转后的图片"
    )
    
    # 创建占位符解析器
    resolver = PlaceholderResolver()
    
    # 测试不同的占位符
    test_cases = [
        "$rotate_images_node.output.temp_paths",
        "$rotate_images_node.output.temp_path",
        "$rotate_images_node.output.rotated_image_path",
        "$rotate_images_node.output.successful_count",
        "$rotate_images_node.output.total_images"
    ]
    
    node_outputs = {"rotate_images_node": rotator_output}
    
    for placeholder in test_cases:
        print(f"\n测试占位符: {placeholder}")
        params = {"image_path": placeholder, "scale_factor": 3}
        
        resolved_params = resolver.resolve_placeholders(params, node_outputs)
        image_path = resolved_params.get('image_path')
        
        print(f"  解析结果: {image_path}")
        print(f"  结果类型: {type(image_path)}")

def main():
    """主测试函数"""
    print("🚀 调试适配问题")
    print("=" * 80)
    
    # 运行所有测试
    test_actual_problem()
    test_auto_adapt_output()
    test_key_matching()
    test_placeholder_resolution_with_different_keys()
    
    print("\n🎯 调试完成！")
    
    # 清理测试文件
    print("\n🧹 清理测试文件...")
    import shutil
    test_dir = "./test_debug_images"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"✅ {test_dir} 已清理")

if __name__ == "__main__":
    main() 