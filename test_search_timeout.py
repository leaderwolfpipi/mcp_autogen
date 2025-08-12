#!/usr/bin/env python3
"""
测试搜索工具超时问题
"""

import logging
import time
import asyncio

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_search_timeout():
    """测试搜索工具超时"""
    logger = logging.getLogger("test_search_timeout")
    
    try:
        from tools.search_tool import search_tool
        
        logger.info("开始测试搜索工具超时...")
        start_time = time.time()
        
        # 测试搜索
        result = search_tool("李自成生平经历", max_results=3)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"搜索完成，耗时: {duration:.2f}秒")
        logger.info(f"状态: {result.get('status')}")
        logger.info(f"结果数量: {len(result.get('results', []))}")
        
        if duration > 10:
            logger.warning(f"⚠️ 搜索耗时较长: {duration:.2f}秒")
        else:
            logger.info(f"✅ 搜索速度正常: {duration:.2f}秒")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_pipeline_timeout():
    """测试Pipeline超时"""
    logger = logging.getLogger("test_pipeline_timeout")
    
    try:
        from core.smart_pipeline_engine import SmartPipelineEngine
        
        logger.info("开始测试Pipeline超时...")
        start_time = time.time()
        
        engine = SmartPipelineEngine(use_llm=False)
        
        # 设置超时
        try:
            result = await asyncio.wait_for(
                engine.execute_from_natural_language("请搜索李自成的生平经历"),
                timeout=30.0  # 30秒超时
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"Pipeline完成，耗时: {duration:.2f}秒")
            logger.info(f"成功: {result.get('success')}")
            
            if duration > 20:
                logger.warning(f"⚠️ Pipeline耗时较长: {duration:.2f}秒")
            else:
                logger.info(f"✅ Pipeline速度正常: {duration:.2f}秒")
            
            return True
            
        except asyncio.TimeoutError:
            logger.error("❌ Pipeline执行超时（30秒）")
            return False
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger = logging.getLogger("main")
    logger.info("开始测试搜索工具超时问题...")
    
    # 测试1: 直接搜索工具超时
    success1 = test_search_timeout()
    
    # 测试2: Pipeline超时
    success2 = asyncio.run(test_pipeline_timeout())
    
    if success1 and success2:
        logger.info("🎉 所有测试通过！没有超时问题")
    else:
        logger.error("❌ 发现超时问题") 