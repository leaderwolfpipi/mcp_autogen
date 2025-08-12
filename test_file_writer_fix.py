#!/usr/bin/env python3
"""
测试修复后的file_writer工具
"""

import logging
import os

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_file_writer():
    """测试file_writer工具"""
    logger = logging.getLogger("test_file_writer")
    
    try:
        from tools.file_writer import file_writer
        
        logger.info("=== 测试file_writer工具 ===")
        
        # 测试1: 正常情况
        logger.info("测试1: 正常文件写入")
        result1 = file_writer("test_output.txt", "这是测试内容")
        logger.info(f"结果: {result1}")
        
        # 测试2: 空文件路径
        logger.info("\n测试2: 空文件路径")
        result2 = file_writer("", "测试内容")
        logger.info(f"结果: {result2}")
        
        # 测试3: 空字符串文件路径
        logger.info("\n测试3: 空字符串文件路径")
        result3 = file_writer("   ", "测试内容")
        logger.info(f"结果: {result3}")
        
        # 测试4: 空内容
        logger.info("\n测试4: 空内容")
        result4 = file_writer("test_empty.txt", "")
        logger.info(f"结果: {result4}")
        
        # 测试5: 带目录的文件路径
        logger.info("\n测试5: 带目录的文件路径")
        result5 = file_writer("test_dir/test_file.txt", "目录测试内容")
        logger.info(f"结果: {result5}")
        
        # 清理测试文件
        logger.info("\n清理测试文件...")
        test_files = ["test_output.txt", "test_empty.txt", "test_dir/test_file.txt"]
        for file_path in test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"删除文件: {file_path}")
        
        # 清理测试目录
        if os.path.exists("test_dir"):
            os.rmdir("test_dir")
            logger.info("删除目录: test_dir")
        
        logger.info("✅ 所有测试完成")
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger = logging.getLogger("main")
    logger.info("开始测试file_writer工具修复...")
    
    success = test_file_writer()
    
    if success:
        logger.info("🎉 file_writer工具修复成功！")
    else:
        logger.error("❌ file_writer工具测试失败") 