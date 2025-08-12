#!/usr/bin/env python3
"""
测试image_rotator和image_scaler的集成问题
验证多图片处理时的数据传递
"""

import asyncio
import logging
import tempfile
import os
import json
from PIL import Image

from tools.image_rotator import image_rotator
from tools.image_scaler import image_scaler
from core.placeholder_resolver import PlaceholderResolver, NodeOutput
from core.tool_adapter import get_tool_adapter

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_test_images():
    """创建测试图片"""
    test_dir = "./test_integration_images"
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

def test_rotator_output_structure():
    """测试image_rotator的输出结构"""
    print("🧪 测试image_rotator的输出结构")
    print("=" * 50)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 测试旋转
    result = image_rotator(image_paths, angle=45)
    
    print(f"输入: {len(image_paths)} 个文件路径")
    print(f"输出状态: {result['status']}")
    print(f"输出结构: {list(result.keys())}")
    
    if result['status'] == 'success':
        print(f"总图片数: {result.get('total_images', 'N/A')}")
        print(f"成功处理: {result.get('successful_count', 'N/A')}")
        print(f"temp_paths: {result.get('temp_paths', 'N/A')}")
        print(f"temp_path: {result.get('temp_path', 'N/A')}")
        print(f"results: {len(result.get('results', []))} 个结果")
        
        # 显示详细结果
        for i, res in enumerate(result.get('results', [])):
            print(f"  结果 {i}: {res}")
    
    return result

def test_placeholder_resolution():
    """测试占位符解析"""
    print("\n🧪 测试占位符解析")
    print("=" * 50)
    
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
    
    # 模拟第二个节点的参数
    scale_params = {
        "image_path": "$rotate_images_node.output.temp_paths",
        "scale_factor": 3
    }
    
    print(f"原始参数: {scale_params}")
    print(f"rotate_images_node输出: {rotator_result}")
    
    # 解析占位符
    node_outputs = {"rotate_images_node": rotator_output}
    resolved_params = resolver.resolve_placeholders(scale_params, node_outputs)
    
    print(f"解析后的参数: {resolved_params}")
    
    # 验证结果
    expected_paths = rotator_result.get('temp_paths', [])
    actual_paths = resolved_params.get('image_path', '')
    
    print(f"期望的路径: {expected_paths}")
    print(f"实际的路径: {actual_paths}")
    
    if actual_paths == expected_paths:
        print("✅ 占位符解析成功！")
    else:
        print("❌ 占位符解析失败！")
    
    return resolved_params

def test_auto_adapt_output():
    """测试自动适配输出"""
    print("\n🧪 测试自动适配输出")
    print("=" * 50)
    
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
    
    # 目标期望
    target_expectation = {
        "image_path": "expected_type"
    }
    
    print(f"源输出: {rotator_result}")
    print(f"目标期望: {target_expectation}")
    
    # 自动适配
    adapted_output = adapter.auto_adapt_output(rotator_output, target_expectation)
    
    print(f"适配后的输出: {adapted_output}")
    
    # 验证结果
    if isinstance(adapted_output, dict) and "image_path" in adapted_output:
        print("✅ 自动适配成功！")
        print(f"  找到键: image_path")
        print(f"  值: {adapted_output['image_path']}")
    else:
        print("❌ 自动适配失败！")
    
    return adapted_output

def test_direct_integration():
    """测试直接集成"""
    print("\n🧪 测试直接集成")
    print("=" * 50)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 第一步：旋转图片
    print("第一步：旋转图片")
    rotator_result = image_rotator(image_paths, angle=45)
    
    if rotator_result['status'] == 'success':
        print(f"旋转成功，处理了 {rotator_result.get('successful_count', 0)} 个图片")
        
        # 获取旋转后的图片路径
        rotated_paths = rotator_result.get('temp_paths', [])
        print(f"旋转后的图片路径: {rotated_paths}")
        
        # 第二步：缩放图片
        print("\n第二步：缩放图片")
        scaler_result = image_scaler(rotated_paths, scale_factor=2.0)
        
        print(f"缩放结果: {scaler_result['status']}")
        if scaler_result['status'] == 'success':
            print(f"缩放成功，处理了 {scaler_result.get('successful_count', 0)} 个图片")
            print(f"缩放后的图片路径: {scaler_result.get('temp_paths', [])}")
        else:
            print(f"缩放失败: {scaler_result.get('error', 'Unknown error')}")
    else:
        print(f"旋转失败: {rotator_result.get('error', 'Unknown error')}")

def test_string_list_parsing():
    """测试字符串列表解析"""
    print("\n🧪 测试字符串列表解析")
    print("=" * 50)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 执行image_rotator
    rotator_result = image_rotator(image_paths, angle=45)
    
    # 获取temp_paths并转换为字符串形式
    temp_paths = rotator_result.get('temp_paths', [])
    string_paths = str(temp_paths)
    
    print(f"原始路径列表: {temp_paths}")
    print(f"字符串形式: {string_paths}")
    
    # 测试image_scaler是否能正确解析
    print("\n测试image_scaler解析字符串形式列表:")
    scaler_result = image_scaler(string_paths, scale_factor=1.5)
    
    print(f"解析结果: {scaler_result['status']}")
    if scaler_result['status'] == 'success':
        print(f"成功处理: {scaler_result.get('successful_count', 0)} 个图片")
        print(f"处理后的路径: {scaler_result.get('temp_paths', [])}")
    else:
        print(f"解析失败: {scaler_result.get('error', 'Unknown error')}")

def test_pipeline_simulation():
    """模拟完整的pipeline执行"""
    print("\n🧪 模拟完整的pipeline执行")
    print("=" * 50)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 模拟pipeline执行
    print("模拟pipeline执行流程:")
    
    # 1. 加载图片（模拟）
    print("1. 加载图片...")
    loaded_images = image_paths  # 简化，实际应该是PIL Image对象
    
    # 2. 旋转图片
    print("2. 旋转图片...")
    rotator_result = image_rotator(loaded_images, angle=45)
    
    if rotator_result['status'] != 'success':
        print(f"❌ 旋转失败: {rotator_result.get('error', 'Unknown error')}")
        return
    
    # 3. 获取旋转后的路径
    rotated_paths = rotator_result.get('temp_paths', [])
    print(f"   旋转完成，获得 {len(rotated_paths)} 个路径")
    
    # 4. 缩放图片
    print("3. 缩放图片...")
    scaler_result = image_scaler(rotated_paths, scale_factor=2.0)
    
    if scaler_result['status'] == 'success':
        print(f"✅ 缩放完成，处理了 {scaler_result.get('successful_count', 0)} 个图片")
        scaled_paths = scaler_result.get('temp_paths', [])
        print(f"   最终获得 {len(scaled_paths)} 个缩放后的图片")
        
        # 显示所有路径
        for i, path in enumerate(scaled_paths):
            print(f"   图片 {i+1}: {path}")
    else:
        print(f"❌ 缩放失败: {scaler_result.get('error', 'Unknown error')}")

def main():
    """主测试函数"""
    print("🚀 image_rotator和image_scaler集成测试")
    print("=" * 80)
    
    # 运行所有测试
    test_rotator_output_structure()
    test_placeholder_resolution()
    test_auto_adapt_output()
    test_direct_integration()
    test_string_list_parsing()
    test_pipeline_simulation()
    
    print("\n🎯 所有测试完成！")
    
    # 清理测试文件
    print("\n🧹 清理测试文件...")
    import shutil
    test_dir = "./test_integration_images"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"✅ {test_dir} 已清理")

if __name__ == "__main__":
    main() 