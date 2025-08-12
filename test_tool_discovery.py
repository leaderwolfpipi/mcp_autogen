#!/usr/bin/env python3
"""
测试工具发现机制
找出为什么search_tool没有被正确发现
"""

import logging
import sys
import os

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_tools_import():
    """测试tools模块导入"""
    logger = logging.getLogger("test_tools_import")
    
    try:
        # 直接导入tools模块
        import tools
        logger.info("✓ 成功导入tools模块")
        
        # 列出tools模块中的所有属性
        logger.info("tools模块中的所有属性:")
        for attr_name in dir(tools):
            if not attr_name.startswith('_'):
                attr = getattr(tools, attr_name)
                if callable(attr):
                    logger.info(f"  - {attr_name}: {type(attr).__name__} (可调用)")
                else:
                    logger.info(f"  - {attr_name}: {type(attr).__name__}")
        
        # 检查search_tool是否存在
        if hasattr(tools, 'search_tool'):
            logger.info("✓ search_tool在tools模块中存在")
            search_tool_func = getattr(tools, 'search_tool')
            logger.info(f"  search_tool类型: {type(search_tool_func)}")
            logger.info(f"  search_tool可调用: {callable(search_tool_func)}")
        else:
            logger.error("✗ search_tool在tools模块中不存在")
        
        # 检查baidu_search_tool是否存在
        if hasattr(tools, 'baidu_search_tool'):
            logger.info("✓ baidu_search_tool在tools模块中存在")
        else:
            logger.error("✗ baidu_search_tool在tools模块中不存在")
        
        # 检查web_searcher是否存在
        if hasattr(tools, 'web_searcher'):
            logger.info("✓ web_searcher在tools模块中存在")
        else:
            logger.error("✗ web_searcher在tools模块中不存在")
        
        return True
        
    except Exception as e:
        logger.error(f"测试tools模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_manager_discovery():
    """测试工具管理器的工具发现"""
    logger = logging.getLogger("test_tool_manager_discovery")
    
    try:
        # 导入工具管理器
        from core.unified_tool_manager import get_unified_tool_manager
        
        # 创建工具管理器实例
        manager = get_unified_tool_manager()
        
        # 获取工具列表
        tool_list = manager.get_tool_list()
        logger.info(f"工具管理器发现的工具数量: {len(tool_list)}")
        
        # 列出所有工具
        logger.info("工具管理器发现的所有工具:")
        for tool in tool_list:
            logger.info(f"  - {tool.get('name')}: {tool.get('description', 'N/A')}")
        
        # 检查特定工具
        search_tools = [tool for tool in tool_list if 'search' in tool.get('name', '').lower()]
        logger.info(f"搜索相关工具数量: {len(search_tools)}")
        for tool in search_tools:
            logger.info(f"  搜索工具: {tool.get('name')} - {tool.get('description', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试工具管理器发现失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_tool_execution():
    """测试直接工具执行"""
    logger = logging.getLogger("test_direct_tool_execution")
    
    try:
        # 直接导入并测试search_tool
        from tools.search_tool import search_tool
        
        logger.info("测试search_tool直接执行...")
        result = search_tool("测试查询", max_results=2)
        
        logger.info(f"search_tool执行结果:")
        logger.info(f"  状态: {result.get('status')}")
        logger.info(f"  消息: {result.get('message')}")
        logger.info(f"  搜索源: {result.get('source')}")
        logger.info(f"  结果数量: {len(result.get('results', []))}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试直接工具执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger = logging.getLogger("main")
    logger.info("开始测试工具发现机制...")
    
    # 测试1: tools模块导入
    success1 = test_tools_import()
    
    # 测试2: 工具管理器发现
    success2 = test_tool_manager_discovery()
    
    # 测试3: 直接工具执行
    success3 = test_direct_tool_execution()
    
    if success1 and success2 and success3:
        logger.info("🎉 所有测试通过！")
        sys.exit(0)
    else:
        logger.error("❌ 部分测试失败！")
        sys.exit(1) 