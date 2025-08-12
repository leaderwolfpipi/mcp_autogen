#!/usr/bin/env python3
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from tools.image_rotator import image_rotator

def test_image_rotation():
    """测试图片旋转功能"""
    print("🔍 测试图片旋转功能...")
    
    # 检查当前工作目录
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查test.png是否存在
    test_image_path = "tests/images/test.png"
    if os.path.exists(test_image_path):
        print(f"✅ 找到测试图片: {test_image_path}")
    else:
        print(f"❌ 未找到测试图片: {test_image_path}")
        return
    
    # 使用绝对路径
    abs_test_image_path = os.path.abspath(test_image_path)
    print(f"绝对路径: {abs_test_image_path}")
    
    try:
        # 测试图片旋转
        print("🔄 开始旋转图片...")
        result = image_rotator(abs_test_image_path, angle=45)
        
        print("📊 旋转结果:")
        print(f"状态: {result.get('status')}")
        print(f"消息: {result.get('message')}")
        
        if result.get('status') == 'success':
            print("✅ 图片旋转成功!")
            paths = result.get('paths', [])
            print(f"输出文件: {paths}")
        else:
            print("❌ 图片旋转失败!")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_rotation() 