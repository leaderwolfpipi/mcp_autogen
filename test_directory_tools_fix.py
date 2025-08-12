#!/usr/bin/env python3
"""
测试修复后的目录工具
验证image_rotator_directory和image_scaler_directory的输出结构
"""

import asyncio
import logging
import tempfile
import os
from PIL import Image

from tools.image_rotator import image_rotator_directory
from tools.image_scaler import image_scaler_directory

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_test_directory():
    """创建测试目录和图片"""
    test_dir = "./test_directory_tools"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建几个测试图片
    for i in range(2):
        img = Image.new('RGB', (100 + i*20, 100 + i*20), color=f'rgb({i*80}, {i*60}, {i*40})')
        img_path = os.path.join(test_dir, f"test_image_{i}.png")
        img.save(img_path)
        print(f"创建测试图片: {img_path}")
    
    return test_dir

def test_directory_tools_output_structure():
    """测试目录工具的输出结构"""
    print("🧪 测试目录工具输出结构")
    print("=" * 60)
    
    # 创建测试目录
    test_dir = create_test_directory()
    
    # 测试image_rotator_directory
    print("\n1. 测试image_rotator_directory输出结构:")
    rotator_result = image_rotator_directory(test_dir, angle=45)
    
    print(f"输出键: {list(rotator_result.keys())}")
    print(f"status: {rotator_result.get('status')}")
    print(f"data键: {list(rotator_result.get('data', {}).keys())}")
    print(f"metadata键: {list(rotator_result.get('metadata', {}).keys())}")
    print(f"paths: {rotator_result.get('paths')}")
    print(f"message: {rotator_result.get('message')}")
    
    # 验证输出结构
    assert 'status' in rotator_result, "缺少status字段"
    assert 'data' in rotator_result, "缺少data字段"
    assert 'metadata' in rotator_result, "缺少metadata字段"
    assert 'paths' in rotator_result, "缺少paths字段"
    assert 'message' in rotator_result, "缺少message字段"
    
    data = rotator_result.get('data', {})
    assert 'primary' in data, "data中缺少primary字段"
    assert 'secondary' in data, "data中缺少secondary字段"
    assert 'counts' in data, "data中缺少counts字段"
    
    metadata = rotator_result.get('metadata', {})
    assert metadata['tool_name'] == 'image_rotator_directory', "tool_name应该是image_rotator_directory"
    assert 'parameters' in metadata, "缺少parameters字段"
    assert 'processing_time' in metadata, "缺少processing_time字段"
    
    print("✅ image_rotator_directory输出结构验证通过")
    
    # 测试image_scaler_directory
    print("\n2. 测试image_scaler_directory输出结构:")
    scaler_result = image_scaler_directory(test_dir, scale_factor=2.0)
    
    print(f"输出键: {list(scaler_result.keys())}")
    print(f"status: {scaler_result.get('status')}")
    print(f"data键: {list(scaler_result.get('data', {}).keys())}")
    print(f"metadata键: {list(scaler_result.get('metadata', {}).keys())}")
    print(f"paths: {scaler_result.get('paths')}")
    print(f"message: {scaler_result.get('message')}")
    
    # 验证输出结构
    assert 'status' in scaler_result, "缺少status字段"
    assert 'data' in scaler_result, "缺少data字段"
    assert 'metadata' in scaler_result, "缺少metadata字段"
    assert 'paths' in scaler_result, "缺少paths字段"
    assert 'message' in scaler_result, "缺少message字段"
    
    data = scaler_result.get('data', {})
    assert 'primary' in data, "data中缺少primary字段"
    assert 'secondary' in data, "data中缺少secondary字段"
    assert 'counts' in data, "data中缺少counts字段"
    
    metadata = scaler_result.get('metadata', {})
    assert metadata['tool_name'] == 'image_scaler_directory', "tool_name应该是image_scaler_directory"
    assert 'parameters' in metadata, "缺少parameters字段"
    assert 'processing_time' in metadata, "缺少processing_time字段"
    
    print("✅ image_scaler_directory输出结构验证通过")

def test_primary_data_consistency():
    """测试主要数据一致性"""
    print("\n🧪 测试主要数据一致性")
    print("=" * 60)
    
    # 创建测试目录
    test_dir = create_test_directory()
    
    # 测试image_rotator_directory主要数据
    print("\n1. 测试image_rotator_directory主要数据:")
    rotator_result = image_rotator_directory(test_dir, angle=45)
    
    primary_data = rotator_result.get('data', {}).get('primary', [])
    paths = rotator_result.get('paths', [])
    
    print(f"  data.primary: {primary_data}")
    print(f"  paths: {paths}")
    
    # 验证主要数据一致性
    assert primary_data == paths, "data.primary和paths应该一致"
    assert len(primary_data) == 2, "应该有2个旋转后的图片"
    assert all(isinstance(path, str) for path in primary_data), "所有路径都应该是字符串"
    
    print("✅ image_rotator_directory主要数据一致性验证通过")
    
    # 测试image_scaler_directory主要数据
    print("\n2. 测试image_scaler_directory主要数据:")
    scaler_result = image_scaler_directory(test_dir, scale_factor=2.0)
    
    primary_data = scaler_result.get('data', {}).get('primary', [])
    paths = scaler_result.get('paths', [])
    
    print(f"  data.primary: {primary_data}")
    print(f"  paths: {paths}")
    
    # 验证主要数据一致性
    assert primary_data == paths, "data.primary和paths应该一致"
    assert len(primary_data) == 2, "应该有2个缩放后的图片"
    assert all(isinstance(path, str) for path in primary_data), "所有路径都应该是字符串"
    
    print("✅ image_scaler_directory主要数据一致性验证通过")

def test_secondary_data_structure():
    """测试次要数据结构"""
    print("\n🧪 测试次要数据结构")
    print("=" * 60)
    
    # 创建测试目录
    test_dir = create_test_directory()
    
    # 测试image_rotator_directory次要数据
    print("\n1. 测试image_rotator_directory次要数据:")
    rotator_result = image_rotator_directory(test_dir, angle=45)
    
    secondary_data = rotator_result.get('data', {}).get('secondary', {})
    print(f"  secondary_data键: {list(secondary_data.keys())}")
    
    # 验证次要数据结构
    assert 'results' in secondary_data, "secondary_data中缺少results字段"
    assert 'original_sizes' in secondary_data, "secondary_data中缺少original_sizes字段"
    assert 'rotated_sizes' in secondary_data, "secondary_data中缺少rotated_sizes字段"
    assert 'angle' in secondary_data, "secondary_data中缺少angle字段"
    assert 'directory' in secondary_data, "secondary_data中缺少directory字段"
    
    print("✅ image_rotator_directory次要数据结构验证通过")
    
    # 测试image_scaler_directory次要数据
    print("\n2. 测试image_scaler_directory次要数据:")
    scaler_result = image_scaler_directory(test_dir, scale_factor=2.0)
    
    secondary_data = scaler_result.get('data', {}).get('secondary', {})
    print(f"  secondary_data键: {list(secondary_data.keys())}")
    
    # 验证次要数据结构
    assert 'results' in secondary_data, "secondary_data中缺少results字段"
    assert 'original_sizes' in secondary_data, "secondary_data中缺少original_sizes字段"
    assert 'scaled_sizes' in secondary_data, "secondary_data中缺少scaled_sizes字段"
    assert 'scale_factor' in secondary_data, "secondary_data中缺少scale_factor字段"
    assert 'directory' in secondary_data, "secondary_data中缺少directory字段"
    
    print("✅ image_scaler_directory次要数据结构验证通过")

def test_error_handling():
    """测试错误处理"""
    print("\n🧪 测试错误处理")
    print("=" * 60)
    
    # 测试不存在的目录
    print("\n1. 测试不存在的目录:")
    rotator_result = image_rotator_directory("nonexistent_directory", angle=45)
    
    print(f"错误状态: {rotator_result.get('status')}")
    print(f"错误消息: {rotator_result.get('message')}")
    print(f"错误数据: {rotator_result.get('data')}")
    print(f"错误路径: {rotator_result.get('paths')}")
    
    # 验证错误输出结构
    assert rotator_result.get('status') == 'error', "错误状态应该是'error'"
    assert 'error' in rotator_result, "应该包含error字段"
    assert rotator_result.get('paths') == [], "错误时paths应该是空列表"
    assert rotator_result.get('data', {}).get('primary') is None, "错误时primary应该是None"
    
    print("✅ 错误处理验证通过")
    
    # 测试无效缩放因子
    print("\n2. 测试无效缩放因子:")
    scaler_result = image_scaler_directory("test_directory", scale_factor=0)
    
    print(f"错误状态: {scaler_result.get('status')}")
    print(f"错误消息: {scaler_result.get('message')}")
    print(f"错误数据: {scaler_result.get('data')}")
    print(f"错误路径: {scaler_result.get('paths')}")
    
    # 验证错误输出结构
    assert scaler_result.get('status') == 'error', "错误状态应该是'error'"
    assert 'error' in scaler_result, "应该包含error字段"
    assert scaler_result.get('paths') == [], "错误时paths应该是空列表"
    assert scaler_result.get('data', {}).get('primary') is None, "错误时primary应该是None"
    
    print("✅ 错误处理验证通过")

def main():
    """主测试函数"""
    print("🚀 目录工具修复测试")
    print("=" * 80)
    
    # 运行所有测试
    test_directory_tools_output_structure()
    test_primary_data_consistency()
    test_secondary_data_structure()
    test_error_handling()
    
    print("\n🎯 所有测试完成！")
    print("\n💡 目录工具修复总结:")
    print("   1. ✅ image_rotator_directory输出结构标准化")
    print("   2. ✅ image_scaler_directory输出结构标准化")
    print("   3. ✅ 主要输出数据通过data.primary字段提供")
    print("   4. ✅ 次要输出数据通过data.secondary字段提供")
    print("   5. ✅ 统计信息通过data.counts字段提供")
    print("   6. ✅ 元数据通过metadata字段提供")
    print("   7. ✅ 文件路径通过paths字段提供")
    print("   8. ✅ 错误处理标准化")
    print("   9. ✅ 文档清晰，便于大模型理解")
    print("   10. ✅ 完全符合通用性设计原则")
    
    # 清理测试文件
    print("\n🧹 清理测试文件...")
    import shutil
    test_dir = "./test_directory_tools"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"✅ {test_dir} 已清理")

if __name__ == "__main__":
    main() 