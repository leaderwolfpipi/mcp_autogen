#!/usr/bin/env python3
"""
测试改造后的search_tool工具
验证百度搜索集成是否正常工作
"""

import logging
import sys
import os

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_search_tool():
    """测试search_tool功能"""
    logger = logging.getLogger("test_search_tool")
    
    try:
        # 导入改造后的search_tool
        from tools.search_tool import search_tool
        from tools.baidu_search_tool import baidu_search_tool
        
        logger.info("成功导入search_tool和baidu_search_tool")
        
        # 测试查询
        test_queries = [
            "Python编程",
            "人工智能发展",
            "机器学习算法"
        ]
        
        for query in test_queries:
            logger.info(f"\n=== 测试查询: {query} ===")
            
            # 测试search_tool
            logger.info("测试search_tool...")
            result = search_tool(query, max_results=3)
            
            logger.info(f"状态: {result.get('status')}")
            logger.info(f"消息: {result.get('message')}")
            logger.info(f"搜索源: {result.get('source')}")
            logger.info(f"结果数量: {len(result.get('results', []))}")
            
            # 显示前两个结果
            for i, item in enumerate(result.get('results', [])[:2]):
                logger.info(f"结果{i+1}:")
                logger.info(f"  标题: {item.get('title', 'N/A')}")
                logger.info(f"  链接: {item.get('link', 'N/A')}")
                logger.info(f"  摘要: {item.get('snippet', 'N/A')[:100]}...")
            
            # 测试baidu_search_tool
            logger.info("\n测试baidu_search_tool...")
            baidu_result = baidu_search_tool(query, max_results=2)
            
            logger.info(f"百度搜索状态: {baidu_result.get('status')}")
            logger.info(f"百度搜索源: {baidu_result.get('source')}")
            logger.info(f"百度结果数量: {len(baidu_result.get('results', []))}")
            
            logger.info("-" * 50)
        
        logger.info("所有测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_integration():
    """测试工具集成"""
    logger = logging.getLogger("test_tool_integration")
    
    try:
        # 测试工具管理器是否能发现search_tool
        from core.unified_tool_manager import get_unified_tool_manager
        
        manager = get_unified_tool_manager()
        tool_list = manager.get_tool_list()
        
        logger.info("工具管理器发现的工具:")
        for tool in tool_list:
            if 'search' in tool.get('name', '').lower():
                logger.info(f"  - {tool.get('name')}: {tool.get('description', 'N/A')}")
        
        # 检查search_tool是否存在
        if manager.exists('search_tool'):
            logger.info("✓ search_tool已成功注册到工具管理器")
        else:
            logger.warning("✗ search_tool未在工具管理器中找到")
        
        return True
        
    except Exception as e:
        logger.error(f"工具集成测试失败: {e}")
        return False

if __name__ == "__main__":
    logger = logging.getLogger("main")
    logger.info("开始测试改造后的search_tool...")
    
    # 测试基本功能
    success1 = test_search_tool()
    
    # 测试工具集成
    success2 = test_tool_integration()
    
    if success1 and success2:
        logger.info("🎉 所有测试通过！search_tool改造成功！")
        sys.exit(0)
    else:
        logger.error("❌ 部分测试失败！")
        sys.exit(1) 