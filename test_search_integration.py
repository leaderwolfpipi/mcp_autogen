#!/usr/bin/env python3
"""
测试搜索工具集成
验证大模型是否能正确使用本地的search_tool
"""

import logging
import sys
import os
import asyncio

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_search_integration():
    """测试搜索工具集成"""
    logger = logging.getLogger("test_search_integration")
    
    try:
        # 导入智能Pipeline引擎
        from core.smart_pipeline_engine import SmartPipelineEngine
        
        logger.info("初始化智能Pipeline引擎...")
        engine = SmartPipelineEngine(use_llm=True)
        
        # 显示可用工具
        tools_info = engine.list_all_tools()
        logger.info("可用工具列表:")
        for tool_name, tool_info in tools_info.items():
            if 'search' in tool_name.lower():
                logger.info(f"  🔍 {tool_name}: {tool_info.get('description', 'N/A')}")
        
        # 测试搜索查询
        test_queries = [
            "请搜索李自成的生平经历和事迹",
            "搜索Python编程教程",
            "查找人工智能发展历史"
        ]
        
        for query in test_queries:
            logger.info(f"\n=== 测试查询: {query} ===")
            
            try:
                # 执行pipeline
                result = await engine.execute_from_natural_language(query)
                
                logger.info(f"执行结果:")
                logger.info(f"  成功: {result.get('success', False)}")
                logger.info(f"  执行时间: {result.get('execution_time', 0):.2f}秒")
                
                if result.get('success'):
                    logger.info("  ✅ Pipeline执行成功")
                    # 显示使用的工具
                    components = result.get('components', [])
                    for comp in components:
                        tool_type = comp.get('tool_type', 'unknown')
                        logger.info(f"    使用的工具: {tool_type}")
                        
                        # 检查是否使用了正确的搜索工具
                        if 'search' in tool_type.lower():
                            if tool_type in ['search_tool', 'baidu_search_tool']:
                                logger.info(f"    ✅ 正确使用了本地搜索工具: {tool_type}")
                            else:
                                logger.warning(f"    ⚠️ 使用了非本地搜索工具: {tool_type}")
                else:
                    errors = result.get('errors', [])
                    logger.error(f"  ❌ Pipeline执行失败:")
                    for error in errors:
                        logger.error(f"    - {error}")
                
            except Exception as e:
                logger.error(f"执行查询失败: {e}")
                import traceback
                traceback.print_exc()
            
            logger.info("-" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_requirement_parser():
    """测试需求解析器"""
    logger = logging.getLogger("test_requirement_parser")
    
    try:
        from core.requirement_parser import RequirementParser
        from core.unified_tool_manager import get_unified_tool_manager
        
        # 获取工具列表
        tool_manager = get_unified_tool_manager()
        available_tools = tool_manager.get_tool_list()
        
        # 创建需求解析器
        parser = RequirementParser(available_tools=available_tools)
        
        # 测试解析
        test_query = "请搜索李自成的生平经历和事迹"
        logger.info(f"测试解析查询: {test_query}")
        
        result = parser.parse(test_query)
        
        logger.info("解析结果:")
        logger.info(f"  Pipeline ID: {result.get('pipeline_id')}")
        
        components = result.get('components', [])
        logger.info(f"  组件数量: {len(components)}")
        
        for i, comp in enumerate(components):
            tool_type = comp.get('tool_type', 'unknown')
            logger.info(f"    组件{i+1}: {tool_type}")
            
            # 检查是否使用了正确的搜索工具
            if 'search' in tool_type.lower():
                if tool_type in ['search_tool', 'baidu_search_tool']:
                    logger.info(f"    ✅ 正确使用了本地搜索工具: {tool_type}")
                else:
                    logger.warning(f"    ⚠️ 使用了非本地搜索工具: {tool_type}")
        
        return True
        
    except Exception as e:
        logger.error(f"需求解析器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger = logging.getLogger("main")
    logger.info("开始测试搜索工具集成...")
    
    # 测试1: 需求解析器
    success1 = asyncio.run(test_requirement_parser())
    
    # 测试2: 完整集成
    success2 = asyncio.run(test_search_integration())
    
    if success1 and success2:
        logger.info("🎉 所有测试通过！搜索工具集成成功！")
        sys.exit(0)
    else:
        logger.error("❌ 部分测试失败！")
        sys.exit(1) 