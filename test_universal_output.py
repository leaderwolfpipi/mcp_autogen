#!/usr/bin/env python3
"""
测试通用输出结构
验证工具输出的一致性和通用性
"""

import asyncio
import logging
import tempfile
import os
from PIL import Image

from tools.image_rotator import image_rotator
from tools.image_scaler import image_scaler
from tools.base_tool import create_standardized_output

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_test_images():
    """创建测试图片"""
    test_dir = "./test_universal_images"
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

def test_universal_output_structure():
    """测试通用输出结构"""
    print("🧪 测试通用输出结构")
    print("=" * 60)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 测试image_rotator
    print("\n1. 测试image_rotator通用输出结构:")
    rotator_result = image_rotator(image_paths, angle=45)
    
    print(f"输出键: {list(rotator_result.keys())}")
    print(f"status: {rotator_result.get('status')}")
    print(f"data键: {list(rotator_result.get('data', {}).keys())}")
    print(f"metadata键: {list(rotator_result.get('metadata', {}).keys())}")
    print(f"paths: {rotator_result.get('paths')}")
    print(f"message: {rotator_result.get('message')}")
    
    # 验证通用结构
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
    assert 'tool_name' in metadata, "metadata中缺少tool_name字段"
    assert 'version' in metadata, "metadata中缺少version字段"
    assert 'parameters' in metadata, "metadata中缺少parameters字段"
    assert 'processing_time' in metadata, "metadata中缺少processing_time字段"
    
    print("✅ image_rotator通用输出结构验证通过")
    
    # 测试image_scaler
    print("\n2. 测试image_scaler通用输出结构:")
    scaler_result = image_scaler(image_paths, scale_factor=2.0)
    
    print(f"输出键: {list(scaler_result.keys())}")
    print(f"status: {scaler_result.get('status')}")
    print(f"data键: {list(scaler_result.get('data', {}).keys())}")
    print(f"metadata键: {list(scaler_result.get('metadata', {}).keys())}")
    print(f"paths: {scaler_result.get('paths')}")
    print(f"message: {scaler_result.get('message')}")
    
    # 验证通用结构
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
    assert 'tool_name' in metadata, "metadata中缺少tool_name字段"
    assert 'version' in metadata, "metadata中缺少version字段"
    assert 'parameters' in metadata, "metadata中缺少parameters字段"
    assert 'processing_time' in metadata, "metadata中缺少processing_time字段"
    
    print("✅ image_scaler通用输出结构验证通过")

def test_primary_data_consistency():
    """测试主要数据一致性"""
    print("\n🧪 测试主要数据一致性")
    print("=" * 60)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 测试image_rotator主要数据
    print("\n1. 测试image_rotator主要数据:")
    rotator_result = image_rotator(image_paths, angle=45)
    
    primary_data = rotator_result.get('data', {}).get('primary', [])
    paths = rotator_result.get('paths', [])
    
    print(f"  data.primary: {primary_data}")
    print(f"  paths: {paths}")
    
    # 验证主要数据一致性
    assert primary_data == paths, "data.primary和paths应该一致"
    assert len(primary_data) == 2, "应该有2个旋转后的图片"
    assert all(isinstance(path, str) for path in primary_data), "所有路径都应该是字符串"
    
    print("✅ image_rotator主要数据一致性验证通过")
    
    # 测试image_scaler主要数据
    print("\n2. 测试image_scaler主要数据:")
    scaler_result = image_scaler(image_paths, scale_factor=2.0)
    
    primary_data = scaler_result.get('data', {}).get('primary', [])
    paths = scaler_result.get('paths', [])
    
    print(f"  data.primary: {primary_data}")
    print(f"  paths: {paths}")
    
    # 验证主要数据一致性
    assert primary_data == paths, "data.primary和paths应该一致"
    assert len(primary_data) == 2, "应该有2个缩放后的图片"
    assert all(isinstance(path, str) for path in primary_data), "所有路径都应该是字符串"
    
    print("✅ image_scaler主要数据一致性验证通过")

def test_secondary_data_structure():
    """测试次要数据结构"""
    print("\n🧪 测试次要数据结构")
    print("=" * 60)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 测试image_rotator次要数据
    print("\n1. 测试image_rotator次要数据:")
    rotator_result = image_rotator(image_paths, angle=45)
    
    secondary_data = rotator_result.get('data', {}).get('secondary', {})
    print(f"  secondary_data键: {list(secondary_data.keys())}")
    
    # 验证次要数据结构
    assert 'results' in secondary_data, "secondary_data中缺少results字段"
    assert 'original_sizes' in secondary_data, "secondary_data中缺少original_sizes字段"
    assert 'rotated_sizes' in secondary_data, "secondary_data中缺少rotated_sizes字段"
    assert 'angle' in secondary_data, "secondary_data中缺少angle字段"
    
    print("✅ image_rotator次要数据结构验证通过")
    
    # 测试image_scaler次要数据
    print("\n2. 测试image_scaler次要数据:")
    scaler_result = image_scaler(image_paths, scale_factor=2.0)
    
    secondary_data = scaler_result.get('data', {}).get('secondary', {})
    print(f"  secondary_data键: {list(secondary_data.keys())}")
    
    # 验证次要数据结构
    assert 'results' in secondary_data, "secondary_data中缺少results字段"
    assert 'original_sizes' in secondary_data, "secondary_data中缺少original_sizes字段"
    assert 'scaled_sizes' in secondary_data, "secondary_data中缺少scaled_sizes字段"
    assert 'scale_factor' in secondary_data, "secondary_data中缺少scale_factor字段"
    
    print("✅ image_scaler次要数据结构验证通过")

def test_counts_data_structure():
    """测试统计数据"""
    print("\n🧪 测试统计数据")
    print("=" * 60)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 测试image_rotator统计数据
    print("\n1. 测试image_rotator统计数据:")
    rotator_result = image_rotator(image_paths, angle=45)
    
    counts = rotator_result.get('data', {}).get('counts', {})
    print(f"  counts: {counts}")
    
    # 验证统计数据
    assert 'total' in counts, "counts中缺少total字段"
    assert 'successful' in counts, "counts中缺少successful字段"
    assert 'failed' in counts, "counts中缺少failed字段"
    assert counts['total'] == 2, "total应该是2"
    assert counts['successful'] == 2, "successful应该是2"
    assert counts['failed'] == 0, "failed应该是0"
    
    print("✅ image_rotator统计数据验证通过")
    
    # 测试image_scaler统计数据
    print("\n2. 测试image_scaler统计数据:")
    scaler_result = image_scaler(image_paths, scale_factor=2.0)
    
    counts = scaler_result.get('data', {}).get('counts', {})
    print(f"  counts: {counts}")
    
    # 验证统计数据
    assert 'total' in counts, "counts中缺少total字段"
    assert 'successful' in counts, "counts中缺少successful字段"
    assert 'failed' in counts, "counts中缺少failed字段"
    assert counts['total'] == 2, "total应该是2"
    assert counts['successful'] == 2, "successful应该是2"
    assert counts['failed'] == 0, "failed应该是0"
    
    print("✅ image_scaler统计数据验证通过")

def test_metadata_structure():
    """测试元数据结构"""
    print("\n🧪 测试元数据结构")
    print("=" * 60)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 测试image_rotator元数据
    print("\n1. 测试image_rotator元数据:")
    rotator_result = image_rotator(image_paths, angle=45)
    
    metadata = rotator_result.get('metadata', {})
    print(f"  metadata: {metadata}")
    
    # 验证元数据
    assert metadata['tool_name'] == 'image_rotator', "tool_name应该是image_rotator"
    assert metadata['version'] == '1.0.0', "version应该是1.0.0"
    assert 'parameters' in metadata, "缺少parameters字段"
    assert 'processing_time' in metadata, "缺少processing_time字段"
    assert metadata['parameters']['angle'] == 45, "angle参数应该是45"
    
    print("✅ image_rotator元数据验证通过")
    
    # 测试image_scaler元数据
    print("\n2. 测试image_scaler元数据:")
    scaler_result = image_scaler(image_paths, scale_factor=2.0)
    
    metadata = scaler_result.get('metadata', {})
    print(f"  metadata: {metadata}")
    
    # 验证元数据
    assert metadata['tool_name'] == 'image_scaler', "tool_name应该是image_scaler"
    assert metadata['version'] == '1.0.0', "version应该是1.0.0"
    assert 'parameters' in metadata, "缺少parameters字段"
    assert 'processing_time' in metadata, "缺少processing_time字段"
    assert metadata['parameters']['scale_factor'] == 2.0, "scale_factor参数应该是2.0"
    
    print("✅ image_scaler元数据验证通过")

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
    assert rotator_result.get('data', {}).get('primary') is None, "错误时primary应该是None"
    
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
    assert scaler_result.get('data', {}).get('primary') is None, "错误时primary应该是None"
    
    print("✅ 错误处理验证通过")

def test_base_tool_function():
    """测试基础工具函数"""
    print("\n🧪 测试基础工具函数")
    print("=" * 60)
    
    # 测试成功输出
    print("\n1. 测试成功输出:")
    success_output = create_standardized_output(
        tool_name="test_tool",
        status="success",
        primary_data=["path1", "path2"],
        secondary_data={"key": "value"},
        counts={"total": 2},
        paths=["path1", "path2"],
        message="Test successful",
        parameters={"param1": "value1"},
        version="1.0.0"
    )
    
    print(f"成功输出: {success_output}")
    
    # 验证成功输出结构
    assert success_output['status'] == 'success', "状态应该是success"
    assert success_output['data']['primary'] == ["path1", "path2"], "primary数据不正确"
    assert success_output['data']['secondary']['key'] == "value", "secondary数据不正确"
    assert success_output['data']['counts']['total'] == 2, "counts数据不正确"
    assert success_output['paths'] == ["path1", "path2"], "paths不正确"
    assert success_output['metadata']['tool_name'] == "test_tool", "tool_name不正确"
    
    print("✅ 成功输出验证通过")
    
    # 测试错误输出
    print("\n2. 测试错误输出:")
    error_output = create_standardized_output(
        tool_name="test_tool",
        status="error",
        error="Test error",
        parameters={"param1": "value1"},
        version="1.0.0"
    )
    
    print(f"错误输出: {error_output}")
    
    # 验证错误输出结构
    assert error_output['status'] == 'error', "状态应该是error"
    assert error_output['error'] == "Test error", "error信息不正确"
    assert error_output['data']['primary'] is None, "错误时primary应该是None"
    assert error_output['paths'] == [], "错误时paths应该是空列表"
    
    print("✅ 错误输出验证通过")

def main():
    """主测试函数"""
    print("🚀 通用输出结构测试")
    print("=" * 80)
    
    # 运行所有测试
    test_universal_output_structure()
    test_primary_data_consistency()
    test_secondary_data_structure()
    test_counts_data_structure()
    test_metadata_structure()
    test_error_handling()
    test_base_tool_function()
    
    print("\n🎯 所有测试完成！")
    print("\n💡 通用输出结构总结:")
    print("   1. ✅ 所有工具都遵循统一的输出结构")
    print("   2. ✅ 主要输出数据通过data.primary字段提供")
    print("   3. ✅ 次要输出数据通过data.secondary字段提供")
    print("   4. ✅ 统计信息通过data.counts字段提供")
    print("   5. ✅ 元数据通过metadata字段提供")
    print("   6. ✅ 文件路径通过paths字段提供")
    print("   7. ✅ 错误处理标准化")
    print("   8. ✅ 没有特定工具的硬编码字段")
    print("   9. ✅ 完全符合通用性设计原则")
    
    # 清理测试文件
    print("\n🧹 清理测试文件...")
    import shutil
    test_dir = "./test_universal_images"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"✅ {test_dir} 已清理")

if __name__ == "__main__":
    main() 