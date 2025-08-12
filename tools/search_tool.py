#!/usr/bin/env python3
"""
通用搜索工具 - 基于多搜索引擎的专业实现
支持多种搜索引擎，自动选择最佳搜索源
"""

import logging
import time
from typing import Any, Dict, List, Union
from tools.base_tool import create_standardized_output

# 导入百度搜索工具
from .baidu_search_tool import baidu_search_tool

def search_tool(query: str, max_results: int = 3) -> Dict[str, Any]:
    """
    通用搜索工具函数。
    支持多种搜索引擎，自动选择最佳搜索源，输出结构标准化。

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
    logger = logging.getLogger("search_tool")
    start_time = time.time()
    
    try:
        # 参数验证
        logger.info(f"开始执行搜索工具")
        logger.info(f"搜索查询: {query}")
        
        if not query or not query.strip():
            return create_standardized_output(
                tool_name="search_tool",
                status="error",
                message="搜索查询不能为空",
                error="搜索查询不能为空",
                start_time=start_time,
                parameters={"query": query, "max_results": max_results}
            )
        
        if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
            max_results = 3
            logger.warning(f"max_results参数无效，使用默认值: {max_results}")
        
        # 执行搜索
        logger.info(f"使用多引擎搜索: {query}")
        result = baidu_search_tool(query, max_results)
        
        # 检查搜索结果
        if result.get('status') != 'success':
            return create_standardized_output(
                tool_name="search_tool",
                status="error",
                message=result.get('message', '搜索失败'),
                error=result.get('message', '搜索失败'),
                start_time=start_time,
                parameters={"query": query, "max_results": max_results}
            )
        
        # 提取搜索结果 - 从标准化输出中正确提取
        search_results = result.get('data', {}).get('primary', [])
        source = result.get('data', {}).get('secondary', {}).get('source', 'unknown')
        
        # 构建标准化输出
        return create_standardized_output(
            tool_name="search_tool",
            status="success",
            primary_data=search_results,
            secondary_data={
                "source": source,
                "query": query,
                "search_metadata": result
            },
            counts={
                "total": len(search_results),
                "requested": max_results,
                "actual": len(search_results)
            },
            paths=[source],  # 搜索源信息
            message=f"搜索成功，找到 {len(search_results)} 个结果，来源: {source}",
            start_time=start_time,
            parameters={"query": query, "max_results": max_results}
        )
            
    except Exception as e:
        logger.error(f"搜索工具执行失败: {e}")
        return create_standardized_output(
            tool_name="search_tool",
            status="error",
            message=f"搜索失败: {str(e)}",
            error=str(e),
            start_time=start_time,
            parameters={"query": query, "max_results": max_results}
        )

# 为了向后兼容，保留原有的函数签名
def legacy_search_tool(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    传统搜索工具函数（向后兼容）
    现在完全基于多引擎搜索
    """
    return search_tool(query, max_results) 