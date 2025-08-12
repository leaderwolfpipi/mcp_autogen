#!/usr/bin/env python3
"""
谷歌搜索引擎实现 - 标准化输出格式
"""

import logging
import time
from typing import List, Dict, Any
from tools.base_tool import create_standardized_output

try:
    from googlesearch import search
    GOOGLESEARCH_AVAILABLE = True
except ImportError:
    GOOGLESEARCH_AVAILABLE = False
    logging.warning("googlesearch-python库未安装，谷歌搜索功能将不可用")

from .search_base import SearchItem, WebSearchEngine


class GoogleSearchEngine(WebSearchEngine):
    """谷歌搜索引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger("GoogleSearchEngine")
        if not GOOGLESEARCH_AVAILABLE:
            self.logger.error("googlesearch-python库未安装，谷歌搜索功能不可用")
            
    
    def perform_search(
        self, query: str, num_results: int = 10, *args, **kwargs
    ) -> List[SearchItem]:
        """
        谷歌搜索引擎
        
        Returns results formatted according to SearchItem model.
        """
        if not GOOGLESEARCH_AVAILABLE:
            self.logger.error("googlesearch-python库未安装，无法执行谷歌搜索")
            return []
        
        try:
            self.logger.info(f"开始谷歌搜索: {query}, 期望结果数: {num_results}")
            raw_results = search(query, num_results=num_results, advanced=True)
            
            results = []
            for i, item in enumerate(raw_results):
                if isinstance(item, str):
                    # If it's just a URL
                    results.append(
                        SearchItem(
                            title=f"Google Result {i+1}", 
                            url=item, 
                            description="",
                            source="google"
                        )
                    )
                else:
                    # If it's an object with attributes
                    results.append(
                        SearchItem(
                            title=getattr(item, "title", f"Google Result {i+1}"), 
                            url=getattr(item, "url", ""), 
                            description=getattr(item, "description", ""),
                            source="google"
                        )
                    )
            
            self.logger.info(f"谷歌搜索成功，找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            self.logger.error(f"谷歌搜索失败: {e}")
            return []


def google_search_tool(query: str, max_results: int = 3) -> Dict[str, Any]:
    """
    ⚠️ 谷歌搜索工具（有依赖限制）
    
    注意：此工具依赖 googlesearch-python 库，可能因缺少依赖而失败。
    推荐使用 smart_search 工具，它提供更好的稳定性和多引擎支持。
    
    依赖要求：
    - 需要安装 googlesearch-python 库
    - 网络连接要求高
    - 可能受到谷歌搜索限制影响

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
    logger = logging.getLogger("google_search_tool")
    start_time = time.time()
    
    try:
        # 参数验证
        if not query or not query.strip():
            return create_standardized_output(
                tool_name="google_search_tool",
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
        search_engine = GoogleSearchEngine()
        
        # 执行搜索
        logger.info(f"开始谷歌搜索: {query}")
        search_items = search_engine.perform_search(query, max_results)
        
        if not search_items:
            return create_standardized_output(
                tool_name="google_search_tool",
                status="error",
                message="谷歌搜索未返回结果",
                error="谷歌搜索未返回结果",
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
        
        logger.info(f"谷歌搜索成功，找到 {len(results)} 个结果")
        
        # 构建标准化输出
        return create_standardized_output(
            tool_name="google_search_tool",
            status="success",
            primary_data=results,
            secondary_data={
                "source": "google",
                "query": query,
                "search_items": search_items
            },
            counts={
                "total": len(results),
                "requested": max_results,
                "actual": len(results)
            },
            paths=["google"],
            message=f"谷歌搜索成功，找到 {len(results)} 个结果",
            start_time=start_time,
            parameters={"query": query, "max_results": max_results}
        )
        
    except Exception as e:
        logger.error(f"谷歌搜索工具执行失败: {e}")
        return create_standardized_output(
            tool_name="google_search_tool",
            status="error",
            message=f"谷歌搜索失败: {str(e)}",
            error=str(e),
            start_time=start_time,
            parameters={"query": query, "max_results": max_results}
        ) 