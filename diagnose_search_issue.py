#!/usr/bin/env python3
"""
诊断搜索问题
帮助分析搜索工具执行中的问题
"""

import logging
import time
import asyncio
import threading

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def diagnose_search_tool():
    """诊断搜索工具"""
    logger = logging.getLogger("diagnose_search_tool")
    
    try:
        from tools.search_tool import search_tool
        from tools.baidu_search_tool import baidu_search_tool
        
        logger.info("=== 诊断搜索工具 ===")
        
        # 测试1: 直接调用search_tool
        logger.info("测试1: 直接调用search_tool")
        start_time = time.time()
        
        try:
            result = search_tool("测试查询", max_results=2)
            duration = time.time() - start_time
            
            logger.info(f"✅ search_tool执行成功，耗时: {duration:.2f}秒")
            logger.info(f"  状态: {result.get('status')}")
            logger.info(f"  结果数量: {len(result.get('results', []))}")
            
        except Exception as e:
            logger.error(f"❌ search_tool执行失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试2: 直接调用baidu_search_tool
        logger.info("\n测试2: 直接调用baidu_search_tool")
        start_time = time.time()
        
        try:
            result = baidu_search_tool("测试查询", max_results=2)
            duration = time.time() - start_time
            
            logger.info(f"✅ baidu_search_tool执行成功，耗时: {duration:.2f}秒")
            logger.info(f"  状态: {result.get('status')}")
            logger.info(f"  结果数量: {len(result.get('results', []))}")
            
        except Exception as e:
            logger.error(f"❌ baidu_search_tool执行失败: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        logger.error(f"诊断失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def diagnose_pipeline():
    """诊断Pipeline执行"""
    logger = logging.getLogger("diagnose_pipeline")
    
    try:
        from core.smart_pipeline_engine import SmartPipelineEngine
        
        logger.info("\n=== 诊断Pipeline执行 ===")
        
        # 测试1: 简单搜索Pipeline
        logger.info("测试1: 简单搜索Pipeline")
        start_time = time.time()
        
        try:
            engine = SmartPipelineEngine(use_llm=False)
            
            result = await asyncio.wait_for(
                engine.execute_from_natural_language("请搜索李自成的生平经历"),
                timeout=10.0  # 10秒超时
            )
            
            duration = time.time() - start_time
            
            logger.info(f"✅ Pipeline执行成功，耗时: {duration:.2f}秒")
            logger.info(f"  成功: {result.get('success')}")
            
            if result.get('success'):
                node_results = result.get('node_results', [])
                for node_result in node_results:
                    tool_type = node_result.get('tool_type', 'unknown')
                    status = node_result.get('status', 'unknown')
                    logger.info(f"  节点: {tool_type} - {status}")
            
        except asyncio.TimeoutError:
            logger.error("❌ Pipeline执行超时（10秒）")
        except Exception as e:
            logger.error(f"❌ Pipeline执行失败: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        logger.error(f"Pipeline诊断失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def diagnose_network():
    """诊断网络连接"""
    logger = logging.getLogger("diagnose_network")
    
    try:
        import requests
        
        logger.info("\n=== 诊断网络连接 ===")
        
        # 测试1: 百度首页
        logger.info("测试1: 访问百度首页")
        start_time = time.time()
        
        try:
            response = requests.get("https://www.baidu.com", timeout=5)
            duration = time.time() - start_time
            
            logger.info(f"✅ 百度首页访问成功，耗时: {duration:.2f}秒")
            logger.info(f"  状态码: {response.status_code}")
            
        except Exception as e:
            logger.error(f"❌ 百度首页访问失败: {e}")
        
        # 测试2: 百度搜索
        logger.info("\n测试2: 访问百度搜索")
        start_time = time.time()
        
        try:
            response = requests.get("https://www.baidu.com/s?wd=测试", timeout=5)
            duration = time.time() - start_time
            
            logger.info(f"✅ 百度搜索访问成功，耗时: {duration:.2f}秒")
            logger.info(f"  状态码: {response.status_code}")
            
        except Exception as e:
            logger.error(f"❌ 百度搜索访问失败: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"网络诊断失败: {e}")
        return False

if __name__ == "__main__":
    logger = logging.getLogger("main")
    logger.info("开始诊断搜索问题...")
    
    # 诊断1: 搜索工具
    success1 = diagnose_search_tool()
    
    # 诊断2: Pipeline执行
    success2 = asyncio.run(diagnose_pipeline())
    
    # 诊断3: 网络连接
    success3 = diagnose_network()
    
    logger.info("\n=== 诊断总结 ===")
    if success1 and success2 and success3:
        logger.info("✅ 所有诊断通过，搜索功能正常")
    else:
        logger.info("❌ 发现一些问题，请检查上述日志")
    
    logger.info("\n建议:")
    logger.info("1. 如果网络诊断失败，可能是网络连接问题")
    logger.info("2. 如果搜索工具诊断失败，可能是工具配置问题")
    logger.info("3. 如果Pipeline诊断失败，可能是系统集成问题")
    logger.info("4. 如果所有诊断都通过但实际使用中仍有问题，可能是并发或环境问题") 