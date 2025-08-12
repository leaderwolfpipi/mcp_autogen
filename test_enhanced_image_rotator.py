#!/usr/bin/env python3
"""
测试增强版image_rotator工具
验证其处理多种输入格式的能力
"""

import asyncio
import logging
import tempfile
import os
import json
from PIL import Image

from tools.image_rotator import image_rotator, _normalize_input

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_test_images():
    """创建测试图片"""
    test_dir = "./test_rotator_images"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建几个测试图片
    image_paths = []
    for i in range(3):
        img = Image.new('RGB', (100 + i*20, 100 + i*20), color=f'rgb({i*80}, {i*60}, {i*40})')
        img_path = os.path.join(test_dir, f"test_image_{i}.png")
        img.save(img_path)
        image_paths.append(img_path)
        print(f"创建测试图片: {img_path}")
    
    return image_paths

def test_single_file_path():
    """测试单个文件路径"""
    print("🧪 测试单个文件路径")
    print("=" * 40)
    
    # 创建测试图片
    image_paths = create_test_images()
    single_path = image_paths[0]
    
    # 测试旋转
    result = image_rotator(single_path, angle=45)
    
    print(f"输入: {single_path}")
    print(f"输出状态: {result['status']}")
    if result['status'] == 'success':
        print(f"原始尺寸: {result['original_size']}")
        print(f"旋转后尺寸: {result['rotated_size']}")
        print(f"临时路径: {result['temp_path']}")
        print(f"消息: {result['message']}")
    else:
        print(f"错误: {result.get('error', 'Unknown error')}")

def test_file_path_list():
    """测试文件路径列表"""
    print("\n🧪 测试文件路径列表")
    print("=" * 40)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 测试旋转
    result = image_rotator(image_paths, angle=90)
    
    print(f"输入: {len(image_paths)} 个文件路径")
    print(f"输出状态: {result['status']}")
    if result['status'] == 'success':
        print(f"总图片数: {result['total_images']}")
        print(f"成功处理: {result['successful_count']}")
        print(f"失败数量: {result['failed_count']}")
        print(f"临时路径: {result['temp_paths']}")
        print(f"消息: {result['message']}")
    else:
        print(f"错误: {result.get('error', 'Unknown error')}")

def test_pil_image_objects():
    """测试PIL Image对象"""
    print("\n🧪 测试PIL Image对象")
    print("=" * 40)
    
    # 创建PIL Image对象
    images = []
    for i in range(2):
        img = Image.new('RGB', (80 + i*10, 80 + i*10), color=f'rgb({i*100}, {i*50}, {i*25})')
        images.append(img)
    
    # 测试单个PIL Image
    print("单个PIL Image:")
    result = image_rotator(images[0], angle=30)
    print(f"输出状态: {result['status']}")
    if result['status'] == 'success':
        print(f"原始尺寸: {result['original_size']}")
        print(f"旋转后尺寸: {result['rotated_size']}")
    
    # 测试PIL Image列表
    print("\nPIL Image列表:")
    result = image_rotator(images, angle=60)
    print(f"输出状态: {result['status']}")
    if result['status'] == 'success':
        print(f"总图片数: {result['total_images']}")
        print(f"成功处理: {result['successful_count']}")

def test_json_string():
    """测试JSON字符串输入"""
    print("\n🧪 测试JSON字符串输入")
    print("=" * 40)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 创建JSON字符串
    json_input = json.dumps(image_paths)
    
    # 测试旋转
    result = image_rotator(json_input, angle=180)
    
    print(f"输入: JSON字符串 (包含 {len(image_paths)} 个路径)")
    print(f"输出状态: {result['status']}")
    if result['status'] == 'success':
        print(f"总图片数: {result['total_images']}")
        print(f"成功处理: {result['successful_count']}")
        print(f"消息: {result['message']}")
    else:
        print(f"错误: {result.get('error', 'Unknown error')}")

def test_mixed_input():
    """测试混合输入"""
    print("\n🧪 测试混合输入")
    print("=" * 40)
    
    # 创建混合输入：文件路径 + PIL Image对象
    image_paths = create_test_images()
    pil_image = Image.new('RGB', (120, 120), color='blue')
    
    mixed_input = [image_paths[0], pil_image, image_paths[1]]
    
    # 测试旋转
    result = image_rotator(mixed_input, angle=45)
    
    print(f"输入: 混合类型 (文件路径 + PIL Image)")
    print(f"输出状态: {result['status']}")
    if result['status'] == 'success':
        print(f"总图片数: {result['total_images']}")
        print(f"成功处理: {result['successful_count']}")
        print(f"失败数量: {result['failed_count']}")
        print(f"消息: {result['message']}")
    else:
        print(f"错误: {result.get('error', 'Unknown error')}")

def test_error_handling():
    """测试错误处理"""
    print("\n🧪 测试错误处理")
    print("=" * 40)
    
    # 测试不存在的文件
    print("不存在的文件:")
    result = image_rotator("nonexistent_file.png", angle=45)
    print(f"输出状态: {result['status']}")
    print(f"错误: {result.get('error', 'No error')}")
    
    # 测试空输入
    print("\n空输入:")
    result = image_rotator([], angle=45)
    print(f"输出状态: {result['status']}")
    print(f"错误: {result.get('error', 'No error')}")
    
    # 测试None输入
    print("\nNone输入:")
    result = image_rotator(None, angle=45)
    print(f"输出状态: {result['status']}")
    print(f"错误: {result.get('error', 'No error')}")

def test_normalize_input():
    """测试输入标准化函数"""
    print("\n🧪 测试输入标准化函数")
    print("=" * 40)
    
    # 测试各种输入格式
    test_cases = [
        ("单个字符串", "test.png"),
        ("字符串列表", ["test1.png", "test2.png"]),
        ("嵌套列表", [["test1.png"], ["test2.png"]]),
        ("JSON字符串", '["test1.png", "test2.png"]'),
        ("空列表", []),
        ("None", None),
    ]
    
    for name, test_input in test_cases:
        normalized = _normalize_input(test_input)
        print(f"{name}: {type(test_input)} -> {len(normalized)} 项")

def test_pipeline_integration():
    """测试与pipeline的集成"""
    print("\n🧪 测试与pipeline的集成")
    print("=" * 40)
    
    # 模拟从image_loader获取的输出
    from tools.image_loader import image_loader
    
    try:
        # 使用现有的测试图片目录
        test_dir = "tests/images"
        if os.path.exists(test_dir):
            load_result = image_loader(test_dir)
            
            print(f"image_loader输出: {len(load_result)} 个PIL Image对象")
            
            # 直接传递给image_rotator
            result = image_rotator(load_result, angle=45)
            
            print(f"image_rotator输出状态: {result['status']}")
            if result['status'] == 'success':
                print(f"处理图片数: {result['total_images']}")
                print(f"成功数量: {result['successful_count']}")
                print(f"临时路径: {result['temp_paths']}")
                print(f"消息: {result['message']}")
            else:
                print(f"错误: {result.get('error', 'Unknown error')}")
        else:
            print(f"测试目录不存在: {test_dir}")
            
    except Exception as e:
        print(f"集成测试失败: {e}")

def main():
    """主测试函数"""
    print("🚀 增强版image_rotator工具测试")
    print("=" * 80)
    
    # 运行所有测试
    test_single_file_path()
    test_file_path_list()
    test_pil_image_objects()
    test_json_string()
    test_mixed_input()
    test_error_handling()
    test_normalize_input()
    test_pipeline_integration()
    
    print("\n🎯 所有测试完成！")
    
    # 清理测试文件
    print("\n🧹 清理测试文件...")
    import shutil
    if os.path.exists("./test_rotator_images"):
        shutil.rmtree("./test_rotator_images")
        print("✅ 测试目录已清理")

if __name__ == "__main__":
    main() 