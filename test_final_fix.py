#!/usr/bin/env python3
"""
最终测试验证修复是否完全解决了原始问题
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
    test_dir = "./test_final_fix_images"
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

def test_original_problem_fix():
    """测试原始问题是否已修复"""
    print("🧪 测试原始问题是否已修复")
    print("=" * 50)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 第一步：执行image_rotator（模拟load_images_node的输出）
    print("第一步：执行image_rotator")
    rotator_result = image_rotator(image_paths, angle=45)
    
    if rotator_result['status'] != 'success':
        print(f"❌ 旋转失败: {rotator_result.get('error', 'Unknown error')}")
        return False
    
    print(f"✅ 旋转成功，处理了 {rotator_result.get('successful_count', 0)} 个图片")
    print(f"   输出结构: {list(rotator_result.keys())}")
    print(f"   temp_paths: {rotator_result.get('temp_paths', [])}")
    
    # 第二步：模拟占位符解析（模拟pipeline中的占位符解析）
    print("\n第二步：模拟占位符解析")
    rotator_output = NodeOutput(
        node_id="rotate_images_node",
        output_type="any",
        output_key="rotated_images",
        value=rotator_result,
        description="旋转后的图片"
    )
    
    resolver = PlaceholderResolver()
    
    # 模拟scale_images_node的参数
    scale_params = {
        "image_path": "$rotate_images_node.output.temp_paths",
        "scale_factor": 3
    }
    
    print(f"原始参数: {scale_params}")
    
    node_outputs = {"rotate_images_node": rotator_output}
    resolved_params = resolver.resolve_placeholders(scale_params, node_outputs)
    
    print(f"解析后的参数: {resolved_params}")
    
    # 验证解析结果
    image_path = resolved_params.get('image_path')
    
    if isinstance(image_path, list):
        print(f"✅ 成功解析为列表类型，包含 {len(image_path)} 个路径")
        
        # 第三步：执行image_scaler
        print("\n第三步：执行image_scaler")
        scaler_result = image_scaler(image_path, scale_factor=3)
        
        if scaler_result['status'] == 'success':
            print(f"✅ 缩放成功，处理了 {scaler_result.get('successful_count', 0)} 个图片")
            print(f"   最终获得 {len(scaler_result.get('temp_paths', []))} 个缩放后的图片")
            return True
        else:
            print(f"❌ 缩放失败: {scaler_result.get('error', 'Unknown error')}")
            return False
    else:
        print(f"❌ 解析失败，期望列表类型，实际: {type(image_path)}")
        print(f"   内容: {image_path}")
        return False

def test_string_list_parsing():
    """测试字符串列表解析（模拟适配器输出）"""
    print("\n🧪 测试字符串列表解析")
    print("=" * 50)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 执行image_rotator
    rotator_result = image_rotator(image_paths, angle=45)
    
    # 获取temp_paths并转换为字符串形式（模拟适配器输出）
    temp_paths = rotator_result.get('temp_paths', [])
    string_paths = str(temp_paths)
    
    print(f"原始路径列表: {temp_paths}")
    print(f"字符串形式: {string_paths}")
    
    # 测试image_scaler是否能正确解析
    print("\n测试image_scaler解析字符串形式列表:")
    scaler_result = image_scaler(string_paths, scale_factor=1.5)
    
    if scaler_result['status'] == 'success':
        print(f"✅ 解析成功，处理了 {scaler_result.get('successful_count', 0)} 个图片")
        return True
    else:
        print(f"❌ 解析失败: {scaler_result.get('error', 'Unknown error')}")
        return False

def test_pipeline_integration():
    """测试完整的pipeline集成"""
    print("\n🧪 测试完整的pipeline集成")
    print("=" * 50)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    print("模拟完整的pipeline执行流程:")
    
    # 1. 加载图片（模拟）
    print("1. 加载图片...")
    loaded_images = image_paths  # 简化，实际应该是PIL Image对象
    
    # 2. 旋转图片
    print("2. 旋转图片...")
    rotator_result = image_rotator(loaded_images, angle=45)
    
    if rotator_result['status'] != 'success':
        print(f"❌ 旋转失败: {rotator_result.get('error', 'Unknown error')}")
        return False
    
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
        return True
    else:
        print(f"❌ 缩放失败: {scaler_result.get('error', 'Unknown error')}")
        return False

def main():
    """主测试函数"""
    print("🚀 最终修复验证测试")
    print("=" * 80)
    
    # 运行所有测试
    test1_passed = test_original_problem_fix()
    test2_passed = test_string_list_parsing()
    test3_passed = test_pipeline_integration()
    
    print("\n🎯 测试结果总结:")
    print("=" * 50)
    print(f"原始问题修复测试: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"字符串列表解析测试: {'✅ 通过' if test2_passed else '❌ 失败'}")
    print(f"完整pipeline集成测试: {'✅ 通过' if test3_passed else '❌ 失败'}")
    
    if test1_passed and test2_passed and test3_passed:
        print("\n🎉 所有测试通过！原始问题已完全修复！")
        print("\n💡 修复总结:")
        print("   1. ✅ 占位符解析器现在能正确处理列表类型数据")
        print("   2. ✅ image_rotator工具支持多种输入格式")
        print("   3. ✅ image_scaler工具支持多种输入格式")
        print("   4. ✅ 字符串形式列表解析正常工作")
        print("   5. ✅ 完整的pipeline集成测试通过")
    else:
        print("\n⚠️  部分测试失败，需要进一步调试")
    
    # 清理测试文件
    print("\n🧹 清理测试文件...")
    import shutil
    test_dir = "./test_final_fix_images"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"✅ {test_dir} 已清理")

if __name__ == "__main__":
    main() 