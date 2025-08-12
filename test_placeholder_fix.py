#!/usr/bin/env python3
"""
测试占位符解析修复
验证列表类型的数据传递
"""

import asyncio
import logging
import tempfile
import os
from PIL import Image

from tools.image_rotator import image_rotator
from tools.image_scaler import image_scaler
from core.placeholder_resolver import PlaceholderResolver, NodeOutput

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_test_images():
    """创建测试图片"""
    test_dir = "./test_placeholder_fix_images"
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

def test_placeholder_resolution_fix():
    """测试占位符解析修复"""
    print("🧪 测试占位符解析修复")
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
    
    # 测试不同的占位符格式
    test_cases = [
        {
            "name": "完整占位符 - temp_paths",
            "params": {
                "image_path": "$rotate_images_node.output.temp_paths",
                "scale_factor": 3
            }
        },
        {
            "name": "完整占位符 - temp_path",
            "params": {
                "image_path": "$rotate_images_node.output.temp_path",
                "scale_factor": 3
            }
        },
        {
            "name": "混合占位符",
            "params": {
                "image_path": "$rotate_images_node.output.temp_paths",
                "scale_factor": 3,
                "description": "处理图片: $rotate_images_node.output.total_images"
            }
        }
    ]
    
    node_outputs = {"rotate_images_node": rotator_output}
    
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        print(f"原始参数: {test_case['params']}")
        
        # 解析占位符
        resolved_params = resolver.resolve_placeholders(test_case['params'], node_outputs)
        
        print(f"解析后的参数: {resolved_params}")
        
        # 验证结果
        image_path = resolved_params.get('image_path')
        
        if isinstance(image_path, list):
            print("✅ 成功解析为列表类型")
            print(f"  列表长度: {len(image_path)}")
            print(f"  列表内容: {image_path}")
            
            # 测试是否能被image_scaler正确处理
            print("  测试image_scaler处理...")
            scaler_result = image_scaler(image_path, scale_factor=1.5)
            if scaler_result['status'] == 'success':
                print(f"  ✅ image_scaler处理成功，处理了 {scaler_result.get('successful_count', 0)} 个图片")
            else:
                print(f"  ❌ image_scaler处理失败: {scaler_result.get('error', 'Unknown error')}")
                
        elif isinstance(image_path, str):
            print("✅ 成功解析为字符串类型")
            print(f"  字符串内容: {image_path}")
            
            # 检查是否是字符串形式的列表
            if image_path.startswith('[') and image_path.endswith(']'):
                print("  ⚠️  警告：解析为字符串形式的列表，可能不是期望的结果")
            else:
                print("  ✅ 单个文件路径，符合预期")
                
        else:
            print(f"❌ 解析失败，类型: {type(image_path)}")
            print(f"  内容: {image_path}")

def test_pipeline_simulation():
    """模拟pipeline执行"""
    print("\n🧪 模拟pipeline执行")
    print("=" * 50)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 第一步：旋转图片
    print("第一步：旋转图片")
    rotator_result = image_rotator(image_paths, angle=45)
    
    if rotator_result['status'] != 'success':
        print(f"❌ 旋转失败: {rotator_result.get('error', 'Unknown error')}")
        return
    
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
    
    # 第二步：使用占位符解析缩放参数
    print("\n第二步：解析占位符")
    scale_params = {
        "image_path": "$rotate_images_node.output.temp_paths",
        "scale_factor": 2.0
    }
    
    node_outputs = {"rotate_images_node": rotator_output}
    resolved_params = resolver.resolve_placeholders(scale_params, node_outputs)
    
    print(f"原始参数: {scale_params}")
    print(f"解析后的参数: {resolved_params}")
    
    # 第三步：执行缩放
    print("\n第三步：执行缩放")
    image_path = resolved_params.get('image_path')
    
    if isinstance(image_path, list):
        print(f"✅ 成功获取图片路径列表，包含 {len(image_path)} 个路径")
        scaler_result = image_scaler(image_path, scale_factor=2.0)
        
        if scaler_result['status'] == 'success':
            print(f"✅ 缩放成功，处理了 {scaler_result.get('successful_count', 0)} 个图片")
            scaled_paths = scaler_result.get('temp_paths', [])
            print(f"   最终获得 {len(scaled_paths)} 个缩放后的图片")
            
            # 显示所有路径
            for i, path in enumerate(scaled_paths):
                print(f"   图片 {i+1}: {path}")
        else:
            print(f"❌ 缩放失败: {scaler_result.get('error', 'Unknown error')}")
    else:
        print(f"❌ 获取图片路径失败，类型: {type(image_path)}")
        print(f"   内容: {image_path}")

def test_edge_cases():
    """测试边界情况"""
    print("\n🧪 测试边界情况")
    print("=" * 50)
    
    # 创建占位符解析器
    resolver = PlaceholderResolver()
    
    # 测试空输出
    print("测试空输出:")
    empty_output = NodeOutput(
        node_id="empty_node",
        output_type="any",
        output_key="data",
        value={},
        description="空输出"
    )
    
    params = {"data": "$empty_node.output.data"}
    node_outputs = {"empty_node": empty_output}
    resolved = resolver.resolve_placeholders(params, node_outputs)
    print(f"  结果: {resolved}")
    
    # 测试不存在的节点
    print("\n测试不存在的节点:")
    params = {"data": "$nonexistent_node.output.data"}
    resolved = resolver.resolve_placeholders(params, node_outputs)
    print(f"  结果: {resolved}")
    
    # 测试不存在的键
    print("\n测试不存在的键:")
    test_output = NodeOutput(
        node_id="test_node",
        output_type="any",
        output_key="data",
        value={"existing_key": "value"},
        description="测试输出"
    )
    
    params = {"data": "$test_node.output.nonexistent_key"}
    node_outputs = {"test_node": test_output}
    resolved = resolver.resolve_placeholders(params, node_outputs)
    print(f"  结果: {resolved}")

def main():
    """主测试函数"""
    print("🚀 占位符解析修复测试")
    print("=" * 80)
    
    # 运行所有测试
    test_placeholder_resolution_fix()
    test_pipeline_simulation()
    test_edge_cases()
    
    print("\n🎯 所有测试完成！")
    
    # 清理测试文件
    print("\n🧹 清理测试文件...")
    import shutil
    test_dir = "./test_placeholder_fix_images"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"✅ {test_dir} 已清理")

if __name__ == "__main__":
    main() 