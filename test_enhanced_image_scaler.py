#!/usr/bin/env python3
"""
测试增强版image_scaler工具
验证其处理多种输入格式的能力
"""

import asyncio
import logging
import tempfile
import os
import json
from PIL import Image

from tools.image_scaler import image_scaler, image_scaler_directory, _normalize_input

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_test_images():
    """创建测试图片"""
    test_dir = "./test_scaler_images"
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
    
    # 测试缩放
    result = image_scaler(single_path, scale_factor=2.0)
    
    print(f"输入: {single_path}")
    print(f"输出状态: {result['status']}")
    if result['status'] == 'success':
        print(f"原始尺寸: {result['original_size']}")
        print(f"缩放后尺寸: {result['scaled_size']}")
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
    
    # 测试缩放
    result = image_scaler(image_paths, scale_factor=1.5)
    
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
    result = image_scaler(images[0], scale_factor=0.5)
    print(f"输出状态: {result['status']}")
    if result['status'] == 'success':
        print(f"原始尺寸: {result['original_size']}")
        print(f"缩放后尺寸: {result['scaled_size']}")
    
    # 测试PIL Image列表
    print("\nPIL Image列表:")
    result = image_scaler(images, scale_factor=2.0)
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
    
    # 测试缩放
    result = image_scaler(json_input, scale_factor=0.8)
    
    print(f"输入: JSON字符串 (包含 {len(image_paths)} 个路径)")
    print(f"输出状态: {result['status']}")
    if result['status'] == 'success':
        print(f"总图片数: {result['total_images']}")
        print(f"成功处理: {result['successful_count']}")
        print(f"消息: {result['message']}")
    else:
        print(f"错误: {result.get('error', 'Unknown error')}")

def test_string_list_parsing():
    """测试字符串形式列表的解析"""
    print("\n🧪 测试字符串形式列表的解析")
    print("=" * 40)
    
    # 创建测试图片
    image_paths = create_test_images()
    
    # 创建字符串形式的列表（模拟适配器输出）
    string_list = str(image_paths)
    
    # 测试缩放
    result = image_scaler(string_list, scale_factor=1.2)
    
    print(f"输入: 字符串形式列表")
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
    
    # 测试缩放
    result = image_scaler(mixed_input, scale_factor=1.5)
    
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
    result = image_scaler("nonexistent_file.png", scale_factor=2.0)
    print(f"输出状态: {result['status']}")
    print(f"错误: {result.get('error', 'No error')}")
    
    # 测试无效的缩放因子
    print("\n无效的缩放因子:")
    result = image_scaler("test.png", scale_factor=0)
    print(f"输出状态: {result['status']}")
    print(f"错误: {result.get('error', 'No error')}")
    
    # 测试空输入
    print("\n空输入:")
    result = image_scaler([], scale_factor=2.0)
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
        ("字符串形式列表", "['test1.png', 'test2.png']"),
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
            
            # 直接传递给image_scaler
            result = image_scaler(load_result, scale_factor=2.0)
            
            print(f"image_scaler输出状态: {result['status']}")
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

def test_directory_scaling():
    """测试目录缩放功能"""
    print("\n🧪 测试目录缩放功能")
    print("=" * 40)
    
    # 创建测试目录
    test_dir = "./test_scaler_directory"
    os.makedirs(test_dir, exist_ok=True)
    
    # 在目录中创建测试图片
    for i in range(2):
        img = Image.new('RGB', (100 + i*20, 100 + i*20), color=f'rgb({i*80}, {i*60}, {i*40})')
        img_path = os.path.join(test_dir, f"dir_image_{i}.png")
        img.save(img_path)
        print(f"创建目录图片: {img_path}")
    
    # 测试目录缩放
    result = image_scaler_directory(test_dir, scale_factor=1.5)
    
    print(f"输入目录: {test_dir}")
    print(f"输出状态: {result['status']}")
    if result['status'] == 'success':
        print(f"总目录数: {result['total_directories']}")
        print(f"成功处理: {result['successful_count']}")
        print(f"消息: {result['message']}")
        
        # 显示处理结果
        for res in result['results']:
            if res['status'] == 'success':
                print(f"  目录 {res['directory']}: 处理了 {res['total_files']} 个文件")
    else:
        print(f"错误: {result.get('error', 'Unknown error')}")

def main():
    """主测试函数"""
    print("🚀 增强版image_scaler工具测试")
    print("=" * 80)
    
    # 运行所有测试
    test_single_file_path()
    test_file_path_list()
    test_pil_image_objects()
    test_json_string()
    test_string_list_parsing()
    test_mixed_input()
    test_error_handling()
    test_normalize_input()
    test_pipeline_integration()
    test_directory_scaling()
    
    print("\n🎯 所有测试完成！")
    
    # 清理测试文件
    print("\n🧹 清理测试文件...")
    import shutil
    for test_dir in ["./test_scaler_images", "./test_scaler_directory"]:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"✅ {test_dir} 已清理")

if __name__ == "__main__":
    main() 