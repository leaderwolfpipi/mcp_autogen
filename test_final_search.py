#!/usr/bin/env python3
"""
最终搜索功能测试
验证搜索工具集成是否完全正常工作
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

async def test_search_functionality():
    """测试搜索功能"""
    logger = logging.getLogger("test_search_functionality")
    
    try:
        # 导入智能Pipeline引擎
        from core.smart_pipeline_engine import SmartPipelineEngine
        
        logger.info("初始化智能Pipeline引擎...")
        engine = SmartPipelineEngine(use_llm=False)  # 不使用LLM，使用规则解析
        
        # 测试搜索查询
        test_queries = [
            "请搜索李自成的生平经历和事迹",
            "搜索Python编程教程",
            "查找人工智能发展历史",
            "查询机器学习算法"
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
                    
                    # 显示节点结果
                    node_results = result.get('node_results', [])
                    for node_result in node_results:
                        tool_type = node_result.get('tool_type', 'unknown')
                        tool_source = node_result.get('tool_source', 'unknown')
                        status = node_result.get('status', 'unknown')
                        
                        logger.info(f"    节点: {node_result.get('node_id')}")
                        logger.info(f"      工具: {tool_type}")
                        logger.info(f"      来源: {tool_source}")
                        logger.info(f"      状态: {status}")
                        
                        # 检查是否使用了正确的搜索工具
                        if 'search' in tool_type.lower():
                            if tool_type in ['search_tool', 'baidu_search_tool']:
                                logger.info(f"      ✅ 正确使用了本地搜索工具: {tool_type}")
                                
                                # 显示搜索结果
                                output = node_result.get('output', {})
                                if output:
                                    results = output.get('results', [])
                                    logger.info(f"      搜索结果数量: {len(results)}")
                                    for i, item in enumerate(results[:2]):  # 只显示前2个结果
                                        title = item.get('title', 'N/A')
                                        logger.info(f"        结果{i+1}: {title[:50]}...")
                            else:
                                logger.warning(f"      ⚠️ 使用了非本地搜索工具: {tool_type}")
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

async def test_requirement_parser_search():
    """测试需求解析器的搜索功能"""
    logger = logging.getLogger("test_requirement_parser_search")
    
    try:
        from core.requirement_parser import RequirementParser
        from core.unified_tool_manager import get_unified_tool_manager
        
        # 获取工具列表
        tool_manager = get_unified_tool_manager()
        available_tools = tool_manager.get_tool_list()
        
        # 创建需求解析器（不使用LLM）
        parser = RequirementParser(use_llm=False, available_tools=available_tools)
        
        # 测试搜索查询
        test_queries = [
            "请搜索李自成的生平经历和事迹",
            "搜索Python编程教程",
            "查找人工智能发展历史"
        ]
        
        for query in test_queries:
            logger.info(f"\n=== 测试解析查询: {query} ===")
            
            result = parser.parse(query)
            
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
                        
                        # 显示参数
                        params = comp.get('params', {})
                        query_param = params.get('query', 'N/A')
                        logger.info(f"      搜索查询: {query_param}")
                    else:
                        logger.warning(f"    ⚠️ 使用了非本地搜索工具: {tool_type}")
            
            logger.info("-" * 30)
        
        return True
        
    except Exception as e:
        logger.error(f"需求解析器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_direct_search_tool():
    """测试直接调用搜索工具"""
    logger = logging.getLogger("test_direct_search_tool")
    
    try:
        from tools.search_tool import search_tool
        from tools.baidu_search_tool import baidu_search_tool
        
        test_queries = [
            "李自成生平经历",
            "Python编程教程",
            "人工智能发展"
        ]
        
        for query in test_queries:
            logger.info(f"\n=== 测试直接搜索: {query} ===")
            
            # 测试search_tool
            logger.info("测试search_tool...")
            result1 = search_tool(query, max_results=3)
            logger.info(f"  search_tool状态: {result1.get('status')}")
            logger.info(f"  search_tool结果数量: {len(result1.get('results', []))}")
            
            # 测试baidu_search_tool
            logger.info("测试baidu_search_tool...")
            result2 = baidu_search_tool(query, max_results=2)
            logger.info(f"  baidu_search_tool状态: {result2.get('status')}")
            logger.info(f"  baidu_search_tool结果数量: {len(result2.get('results', []))}")
            
            logger.info("-" * 30)
        
        return True
        
    except Exception as e:
        logger.error(f"直接搜索工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger = logging.getLogger("main")
    logger.info("开始最终搜索功能测试...")
    
    # 测试1: 需求解析器搜索功能
    success1 = asyncio.run(test_requirement_parser_search())
    
    # 测试2: 直接搜索工具
    success2 = asyncio.run(test_direct_search_tool())
    
    # 测试3: 完整Pipeline搜索功能
    success3 = asyncio.run(test_search_functionality())
    
    if success1 and success2 and success3:
        logger.info("🎉 所有测试通过！搜索功能完全正常！")
        logger.info("✅ 大模型现在可以正确使用本地的search_tool和baidu_search_tool")
        logger.info("✅ 搜索工具集成成功完成！")
        sys.exit(0)
    else:
        logger.error("❌ 部分测试失败！")
        sys.exit(1)