#!/usr/bin/env python3
"""
百度搜索工具 - 基于多搜索引擎的专业实现
优先使用谷歌搜索，超时后回退到百度搜索，输出结构标准化
"""

import logging
import asyncio
import time
from typing import Any, Dict, List, Union
from tools.base_tool import create_standardized_output

from .multi_search_engine import MultiSearchEngine

# 全局多搜索引擎实例
multi_search_engine = MultiSearchEngine(timeout=10)


def baidu_search_tool(query: str, max_results: int = 3) -> Dict[str, Any]:
    """
    百度搜索工具函数。
    基于多搜索引擎实现，优先使用谷歌搜索，超时后回退到百度搜索，输出结构标准化。

    参数：
        query (str): 搜索查询字符串，不能为空。
        max_results (int): 最大结果数量，默认5个，范围1-20。
    返回：
        dict: 标准化输出，字段包括：
            status: 'success' | 'error'
            data.primary: 搜索结果列表
            data.secondary: 搜索元信息
            data.counts: 结果统计
            metadata: 工具元信息
            paths: 搜索源信息
            message: 执行消息
            error: 错误信息（如有）
    """
    logger = logging.getLogger("baidu_search_tool")
    start_time = time.time()
    
    try:
        # 参数验证
        logger.info(f"开始执行百度搜索工具")
        logger.info(f"搜索查询: {query}")
        
        if not query or not query.strip():
            return create_standardized_output(
                tool_name="baidu_search_tool",
                status="error",
                message="搜索查询不能为空",
                error="搜索查询不能为空",
                start_time=start_time,
                parameters={"query": query, "max_results": max_results}
            )
        
        if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
            max_results = 3
            logger.warning(f"max_results参数无效，使用默认值: {max_results}")
        
        # 执行多引擎搜索（优先谷歌，超时后回退百度）
        # 使用同步方式调用异步函数
        try:
            # 检查是否已经在事件循环中
            loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，使用 create_task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(_run_search_sync, query, max_results)
                search_items = future.result()
        except RuntimeError:
            # 如果没有运行的事件循环，直接运行
            search_items = _run_search_sync(query, max_results)
        
        # 检查搜索结果
        if not search_items:
            return create_standardized_output(
                tool_name="baidu_search_tool",
                status="error",
                message="所有搜索引擎都失败了",
                error="所有搜索引擎都失败了",
                start_time=start_time,
                parameters={"query": query, "max_results": max_results}
            )
        
        # 转换为标准化格式
        results = []
        sources = set()
        for item in search_items:
            results.append({
                "title": item.title,
                "link": item.url,
                "snippet": item.description or ""
            })
            sources.add(item.source)
        
        # 确定搜索源
        source = list(sources)[0] if sources else "unknown"
        
        logger.info(f"搜索成功，找到 {len(results)} 个结果，来源: {source}")
        
        # 构建标准化输出
        return create_standardized_output(
            tool_name="baidu_search_tool",
            status="success",
            primary_data=results,
            secondary_data={
                "source": source,
                "query": query,
                "sources_used": list(sources),
                "search_items": search_items
            },
            counts={
                "total": len(results),
                "requested": max_results,
                "actual": len(results)
            },
            paths=list(sources),  # 搜索源信息
            message=f"搜索成功，找到 {len(results)} 个结果，来源: {source}",
            start_time=start_time,
            parameters={"query": query, "max_results": max_results}
        )
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"搜索工具执行失败: {error_msg}")
        
        return create_standardized_output(
            tool_name="baidu_search_tool",
            status="error",
            message=f"搜索失败: {error_msg}",
            error=error_msg,
            start_time=start_time,
            parameters={"query": query, "max_results": max_results}
        )


def _run_search_sync(query: str, max_results: int):
    """同步方式运行搜索"""
    try:
        # 检查是否已经在事件循环中
        try:
            loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，使用create_task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, 
                    multi_search_engine.search(query, max_results)
                )
                return future.result()
        except RuntimeError:
            # 如果没有运行的事件循环，直接运行
            return asyncio.run(multi_search_engine.search(query, max_results))
    except Exception as e:
        logging.error(f"搜索同步执行失败: {e}")
        return []


# 为了向后兼容，保留原有的函数签名
def legacy_baidu_search_tool(query: str, max_results: int = 5) -> Dict[str, Any]:
    """向后兼容的百度搜索工具函数"""
    return baidu_search_tool(query, max_results) 