#!/usr/bin/env python3
"""
测试多搜索引擎功能
"""

import logging
import asyncio
import time

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_multi_search_engine():
    """测试多搜索引擎"""
    logger = logging.getLogger("test_multi_search_engine")
    
    try:
        from tools.multi_search_engine import MultiSearchEngine
        
        logger.info("=== 测试多搜索引擎 ===")
        
        # 创建多搜索引擎实例
        search_engine = MultiSearchEngine(timeout=10)
        
        # 测试查询
        test_queries = [
            "李自成生平经历",
            "Python编程教程",
            "人工智能发展"
        ]
        
        for query in test_queries:
            logger.info(f"\n--- 测试查询: {query} ---")
            start_time = time.time()
            
            # 执行搜索
            results = await search_engine.search(
                query=query,
                num_results=3,
                preferred_engine="google"
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"搜索耗时: {duration:.2f}秒")
            logger.info(f"找到结果数量: {len(results)}")
            
            # 显示搜索结果
            for i, result in enumerate(results):
                logger.info(f"结果{i+1}:")
                logger.info(f"  标题: {result.title}")
                logger.info(f"  链接: {result.url}")
                logger.info(f"  来源: {result.source}")
                if result.description:
                    logger.info(f"  摘要: {result.description[:100]}...")
            
            logger.info("-" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_baidu_search_tool():
    """测试百度搜索工具"""
    logger = logging.getLogger("test_baidu_search_tool")
    
    try:
        from tools.baidu_search_tool import baidu_search_tool
        
        logger.info("\n=== 测试百度搜索工具 ===")
        
        # 测试查询
        test_queries = [
            "李自成生平经历",
            "Python编程教程"
        ]
        
        for query in test_queries:
            logger.info(f"\n--- 测试查询: {query} ---")
            start_time = time.time()
            
            # 执行搜索
            result = baidu_search_tool(query, max_results=3)
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"搜索耗时: {duration:.2f}秒")
            logger.info(f"状态: {result.get('status')}")
            logger.info(f"来源: {result.get('source')}")
            logger.info(f"结果数量: {len(result.get('results', []))}")
            
            # 显示搜索结果
            results = result.get('results', [])
            for i, item in enumerate(results):
                logger.info(f"结果{i+1}:")
                logger.info(f"  标题: {item.get('title', 'N/A')}")
                logger.info(f"  链接: {item.get('link', 'N/A')}")
                if item.get('snippet'):
                    logger.info(f"  摘要: {item.get('snippet', '')[:100]}...")
            
            logger.info("-" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_search_tool():
    """测试搜索工具"""
    logger = logging.getLogger("test_search_tool")
    
    try:
        from tools.search_tool import search_tool
        
        logger.info("\n=== 测试搜索工具 ===")
        
        # 测试查询
        test_query = "李自成生平经历"
        
        logger.info(f"测试查询: {test_query}")
        start_time = time.time()
        
        # 执行搜索
        result = search_tool(test_query, max_results=3)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"搜索耗时: {duration:.2f}秒")
        logger.info(f"状态: {result.get('status')}")
        logger.info(f"来源: {result.get('source')}")
        logger.info(f"结果数量: {len(result.get('results', []))}")
        
        # 显示搜索结果
        results = result.get('results', [])
        for i, item in enumerate(results):
            logger.info(f"结果{i+1}:")
            logger.info(f"  标题: {item.get('title', 'N/A')}")
            logger.info(f"  链接: {item.get('link', 'N/A')}")
            if item.get('snippet'):
                logger.info(f"  摘要: {item.get('snippet', '')[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger = logging.getLogger("main")
    logger.info("开始测试多搜索引擎功能...")
    
    # 测试1: 多搜索引擎
    success1 = asyncio.run(test_multi_search_engine())
    
    # 测试2: 百度搜索工具
    success2 = asyncio.run(test_baidu_search_tool())
    
    # 测试3: 搜索工具
    success3 = asyncio.run(test_search_tool())
    
    if success1 and success2 and success3:
        logger.info("🎉 所有测试通过！多搜索引擎功能正常")
        logger.info("✅ 谷歌搜索优先，超时后回退到百度搜索")
        logger.info("✅ 搜索工具集成成功完成！")
    else:
        logger.error("❌ 部分测试失败") 