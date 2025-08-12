#!/usr/bin/env python3
"""
测试标准化输出结构
验证工具输出的一致性和清晰性
"""

import asyncio
import logging
import tempfile
import os
from PIL import Image

from tools.image_rotator import image_rotator
from tools.image_scaler import image_scaler

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_test_images():
    """创建测试图片"""
    test_dir = "./test_standardized_images"
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

def test_standardized_output_structure():
    """测试标准化输出结构"""
    print("🧪 测试标准化输出结构")
    print("=" * 60)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 测试image_rotator
    print("\n1. 测试image_rotator输出结构:")
    rotator_result = image_rotator(image_paths, angle=45)
    
    print(f"输出键: {list(rotator_result.keys())}")
    print(f"status: {rotator_result.get('status')}")
    print(f"data键: {list(rotator_result.get('data', {}).keys())}")
    print(f"metadata键: {list(rotator_result.get('metadata', {}).keys())}")
    print(f"paths: {rotator_result.get('paths')}")
    print(f"message: {rotator_result.get('message')}")
    
    # 验证标准化结构
    assert 'status' in rotator_result, "缺少status字段"
    assert 'data' in rotator_result, "缺少data字段"
    assert 'metadata' in rotator_result, "缺少metadata字段"
    assert 'paths' in rotator_result, "缺少paths字段"
    assert 'message' in rotator_result, "缺少message字段"
    
    data = rotator_result.get('data', {})
    assert 'rotated_images' in data, "data中缺少rotated_images字段"
    assert 'total_count' in data, "data中缺少total_count字段"
    assert 'successful_count' in data, "data中缺少successful_count字段"
    
    metadata = rotator_result.get('metadata', {})
    assert 'angle' in metadata, "metadata中缺少angle字段"
    assert 'processing_time' in metadata, "metadata中缺少processing_time字段"
    
    print("✅ image_rotator输出结构验证通过")
    
    # 测试image_scaler
    print("\n2. 测试image_scaler输出结构:")
    scaler_result = image_scaler(image_paths, scale_factor=2.0)
    
    print(f"输出键: {list(scaler_result.keys())}")
    print(f"status: {scaler_result.get('status')}")
    print(f"data键: {list(scaler_result.get('data', {}).keys())}")
    print(f"metadata键: {list(scaler_result.get('metadata', {}).keys())}")
    print(f"paths: {scaler_result.get('paths')}")
    print(f"message: {scaler_result.get('message')}")
    
    # 验证标准化结构
    assert 'status' in scaler_result, "缺少status字段"
    assert 'data' in scaler_result, "缺少data字段"
    assert 'metadata' in scaler_result, "缺少metadata字段"
    assert 'paths' in scaler_result, "缺少paths字段"
    assert 'message' in scaler_result, "缺少message字段"
    
    data = scaler_result.get('data', {})
    assert 'scaled_images' in data, "data中缺少scaled_images字段"
    assert 'total_count' in data, "data中缺少total_count字段"
    assert 'successful_count' in data, "data中缺少successful_count字段"
    
    metadata = scaler_result.get('metadata', {})
    assert 'scale_factor' in metadata, "metadata中缺少scale_factor字段"
    assert 'processing_time' in metadata, "metadata中缺少processing_time字段"
    
    print("✅ image_scaler输出结构验证通过")

def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n🧪 测试向后兼容性")
    print("=" * 60)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 测试image_rotator向后兼容性
    print("\n1. 测试image_rotator向后兼容性:")
    rotator_result = image_rotator(image_paths, angle=45)
    
    # 检查旧字段是否仍然存在
    old_fields = ['total_images', 'successful_count', 'failed_count', 'angle', 'results', 'temp_paths', 'temp_path']
    for field in old_fields:
        assert field in rotator_result, f"缺少向后兼容字段: {field}"
        print(f"  ✅ {field}: {rotator_result[field]}")
    
    print("✅ image_rotator向后兼容性验证通过")
    
    # 测试image_scaler向后兼容性
    print("\n2. 测试image_scaler向后兼容性:")
    scaler_result = image_scaler(image_paths, scale_factor=2.0)
    
    # 检查旧字段是否仍然存在
    old_fields = ['total_images', 'successful_count', 'failed_count', 'scale_factor', 'results', 'temp_paths', 'temp_path', 'scaled_image_path']
    for field in old_fields:
        assert field in scaler_result, f"缺少向后兼容字段: {field}"
        print(f"  ✅ {field}: {scaler_result[field]}")
    
    print("✅ image_scaler向后兼容性验证通过")

def test_primary_output_fields():
    """测试主要输出字段"""
    print("\n🧪 测试主要输出字段")
    print("=" * 60)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 测试image_rotator主要输出
    print("\n1. 测试image_rotator主要输出:")
    rotator_result = image_rotator(image_paths, angle=45)
    
    # 检查主要输出字段
    data = rotator_result.get('data', {})
    rotated_images = data.get('rotated_images', [])
    paths = rotator_result.get('paths', [])
    
    print(f"  data.rotated_images: {rotated_images}")
    print(f"  paths: {paths}")
    
    # 验证主要输出字段的一致性
    assert rotated_images == paths, "data.rotated_images和paths应该一致"
    assert len(rotated_images) == 2, "应该有2个旋转后的图片"
    assert all(isinstance(path, str) for path in rotated_images), "所有路径都应该是字符串"
    
    print("✅ image_rotator主要输出验证通过")
    
    # 测试image_scaler主要输出
    print("\n2. 测试image_scaler主要输出:")
    scaler_result = image_scaler(image_paths, scale_factor=2.0)
    
    # 检查主要输出字段
    data = scaler_result.get('data', {})
    scaled_images = data.get('scaled_images', [])
    paths = scaler_result.get('paths', [])
    
    print(f"  data.scaled_images: {scaled_images}")
    print(f"  paths: {paths}")
    
    # 验证主要输出字段的一致性
    assert scaled_images == paths, "data.scaled_images和paths应该一致"
    assert len(scaled_images) == 2, "应该有2个缩放后的图片"
    assert all(isinstance(path, str) for path in scaled_images), "所有路径都应该是字符串"
    
    print("✅ image_scaler主要输出验证通过")

def test_error_handling():
    """测试错误处理"""
    print("\n🧪 测试错误处理")
    print("=" * 60)
    
    # 测试无效输入
    print("\n1. 测试无效输入:")
    rotator_result = image_rotator("nonexistent_file.png", angle=45)
    
    print(f"错误状态: {rotator_result.get('status')}")
    print(f"错误消息: {rotator_result.get('message')}")
    print(f"错误数据: {rotator_result.get('data')}")
    print(f"错误路径: {rotator_result.get('paths')}")
    
    # 验证错误输出结构
    assert rotator_result.get('status') == 'error', "错误状态应该是'error'"
    assert 'error' in rotator_result, "应该包含error字段"
    assert rotator_result.get('paths') == [], "错误时paths应该是空列表"
    
    print("✅ 错误处理验证通过")
    
    # 测试无效缩放因子
    print("\n2. 测试无效缩放因子:")
    scaler_result = image_scaler("test.png", scale_factor=0)
    
    print(f"错误状态: {scaler_result.get('status')}")
    print(f"错误消息: {scaler_result.get('message')}")
    print(f"错误数据: {scaler_result.get('data')}")
    print(f"错误路径: {scaler_result.get('paths')}")
    
    # 验证错误输出结构
    assert scaler_result.get('status') == 'error', "错误状态应该是'error'"
    assert 'error' in scaler_result, "应该包含error字段"
    assert scaler_result.get('paths') == [], "错误时paths应该是空列表"
    
    print("✅ 错误处理验证通过")

def main():
    """主测试函数"""
    print("🚀 标准化输出结构测试")
    print("=" * 80)
    
    # 运行所有测试
    test_standardized_output_structure()
    test_backward_compatibility()
    test_primary_output_fields()
    test_error_handling()
    
    print("\n🎯 所有测试完成！")
    print("\n💡 标准化输出结构总结:")
    print("   1. ✅ 所有工具都有统一的输出结构")
    print("   2. ✅ 主要输出字段清晰明确")
    print("   3. ✅ 向后兼容性得到保证")
    print("   4. ✅ 错误处理标准化")
    print("   5. ✅ 文档清晰，便于大模型理解")
    
    # 清理测试文件
    print("\n🧹 清理测试文件...")
    import shutil
    test_dir = "./test_standardized_images"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"✅ {test_dir} 已清理")

if __name__ == "__main__":
    main() 