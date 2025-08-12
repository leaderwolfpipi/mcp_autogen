#!/usr/bin/env python3
"""
测试destination解析修复
"""

import logging
import os

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_destination_parsing():
    """测试destination解析修复"""
    print("🔍 测试destination解析修复")
    print("=" * 60)
    
    try:
        # 测试file_uploader
        print("\n📋 测试1: file_uploader destination解析")
        from tools.file_uploader import file_uploader
        
        # 创建测试文件
        test_file = "test_upload.txt"
        with open(test_file, "w") as f:
            f.write("test content")
        
        # 测试不同的destination格式
        test_cases = [
            ("minio", "minio格式"),
            ("minio/kb-dev", "minio/bucket格式"),
            ("minio/test-bucket", "minio/自定义bucket格式"),
            ("s3", "不支持的格式")
        ]
        
        for destination, description in test_cases:
            print(f"\n  测试: {description} - {destination}")
            try:
                result = file_uploader(destination, test_file)
                print(f"    结果: {'成功' if result else '失败'}")
            except Exception as e:
                print(f"    错误: {e}")
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
        
        # 测试image_uploader
        print("\n📋 测试2: image_uploader destination解析")
        from tools.image_uploader import image_uploader
        
        # 创建测试图片文件
        test_image = "test_image.png"
        try:
            from PIL import Image
            # 创建一个简单的测试图片
            img = Image.new('RGB', (100, 100), color='red')
            img.save(test_image)
            
            # 测试不同的destination格式
            for destination, description in test_cases:
                print(f"\n  测试: {description} - {destination}")
                try:
                    result = image_uploader(destination, test_image)
                    print(f"    结果: {'成功' if result else '失败'}")
                except Exception as e:
                    print(f"    错误: {e}")
            
            # 清理测试文件
            if os.path.exists(test_image):
                os.remove(test_image)
                
        except ImportError:
            print("  PIL未安装，跳过图片测试")
        
        print("\n✅ destination解析修复测试完成")
        
    except Exception as e:
        print(f"❌ destination解析修复测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_destination_parsing() 