#!/usr/bin/env python3
"""
百度搜索引擎实现 - 标准化输出格式
"""

import logging
import time
from typing import List, Dict, Any
from tools.base_tool import create_standardized_output

try:
    from baidusearch.baidusearch import search
    BAIDUSEARCH_AVAILABLE = True
except ImportError:
    BAIDUSEARCH_AVAILABLE = False
    logging.warning("baidusearch库未安装，百度搜索功能将不可用")

from .search_base import SearchItem, WebSearchEngine


class BaiduSearchEngine(WebSearchEngine):
    """百度搜索引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger("BaiduSearchEngine")
        
        if not BAIDUSEARCH_AVAILABLE:
            self.logger.error("baidusearch库未安装，百度搜索功能不可用")
    
    def perform_search(
        self, query: str, num_results: int = 10, *args, **kwargs
    ) -> List[SearchItem]:
        """
        百度搜索引擎
        
        Returns results formatted according to SearchItem model.
        """
        if not BAIDUSEARCH_AVAILABLE:
            self.logger.error("baidusearch库未安装，无法执行百度搜索")
            return []
        
        try:
            self.logger.info(f"开始百度搜索: {query}, 期望结果数: {num_results}")
            raw_results = search(query, num_results=num_results)
            
            # Convert raw results to SearchItem format
            results = []
            for i, item in enumerate(raw_results):
                if isinstance(item, str):
                    # If it's just a URL
                    results.append(
                        SearchItem(
                            title=f"Baidu Result {i+1}", 
                            url=item, 
                            description=None,
                            source="baidu"
                        )
                    )
                elif isinstance(item, dict):
                    # If it's a dictionary with details
                    results.append(
                        SearchItem(
                            title=item.get("title", f"Baidu Result {i+1}"),
                            url=item.get("url", ""),
                            description=item.get("abstract", None),
                            source="baidu"
                        )
                    )
                else:
                    # Try to get attributes directly
                    try:
                        results.append(
                            SearchItem(
                                title=getattr(item, "title", f"Baidu Result {i+1}"),
                                url=getattr(item, "url", ""),
                                description=getattr(item, "abstract", None),
                                source="baidu"
                            )
                        )
                    except Exception:
                        # Fallback to a basic result
                        results.append(
                            SearchItem(
                                title=f"Baidu Result {i+1}", 
                                url=str(item), 
                                description=None,
                                source="baidu"
                            )
                        )
            
            self.logger.info(f"百度搜索成功，找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            self.logger.error(f"百度搜索失败: {e}")
            return []


def baidu_search_engine_tool(query: str, max_results: int = 3) -> Dict[str, Any]:
    """
    百度搜索工具函数。
    使用百度搜索引擎获取搜索结果，输出结构标准化。

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
    logger = logging.getLogger("baidu_search_engine_tool")
    start_time = time.time()
    
    try:
        # 参数验证
        if not query or not query.strip():
            return create_standardized_output(
                tool_name="baidu_search_engine_tool",
                status="error",
                message="搜索查询不能为空",
                error="搜索查询不能为空",
                start_time=start_time,
                parameters={"query": query, "max_results": max_results}
            )
        
        if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
            max_results = 3
            logger.warning(f"max_results参数无效，使用默认值: {max_results}")
        
        # 创建搜索引擎实例
        search_engine = BaiduSearchEngine()
        
        # 执行搜索
        logger.info(f"开始百度搜索: {query}")
        search_items = search_engine.perform_search(query, max_results)
        
        if not search_items:
            return create_standardized_output(
                tool_name="baidu_search_engine_tool",
                status="error",
                message="百度搜索未返回结果",
                error="百度搜索未返回结果",
                start_time=start_time,
                parameters={"query": query, "max_results": max_results}
            )
        
        # 转换为标准化格式
        results = []
        for item in search_items:
            results.append({
                "title": item.title,
                "link": item.url,
                "snippet": item.description or ""
            })
        
        logger.info(f"百度搜索成功，找到 {len(results)} 个结果")
        
        # 构建标准化输出
        return create_standardized_output(
            tool_name="baidu_search_engine_tool",
            status="success",
            primary_data=results,
            secondary_data={
                "source": "baidu",
                "query": query,
                "search_items": search_items
            },
            counts={
                "total": len(results),
                "requested": max_results,
                "actual": len(results)
            },
            paths=["baidu"],
            message=f"百度搜索成功，找到 {len(results)} 个结果",
            start_time=start_time,
            parameters={"query": query, "max_results": max_results}
        )
        
    except Exception as e:
        logger.error(f"百度搜索工具执行失败: {e}")
        return create_standardized_output(
            tool_name="baidu_search_engine_tool",
            status="error",
            message=f"百度搜索失败: {str(e)}",
            error=str(e),
            start_time=start_time,
            parameters={"query": query, "max_results": max_results}
        ) 