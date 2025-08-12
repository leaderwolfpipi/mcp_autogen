#!/usr/bin/env python3
"""
多搜索引擎管理器
支持超时和回退机制
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional

from .search_base import SearchItem, WebSearchEngine
from .baidu_search_engine import BaiduSearchEngine
from .google_search_engine import GoogleSearchEngine


class MultiSearchEngine:
    """多搜索引擎管理器"""
    
    def __init__(self, timeout: int = 10):
        self.logger = logging.getLogger("MultiSearchEngine")
        self.timeout = timeout
        
        # 初始化搜索引擎
        self.search_engines: Dict[str, WebSearchEngine] = {
            "google": GoogleSearchEngine(),
            "baidu": BaiduSearchEngine(),
        }
        
        self.logger.info(f"多搜索引擎初始化完成，超时时间: {timeout}秒")
    
    async def search(
        self, 
        query: str, 
        num_results: int = 5,
        preferred_engine: str = "google"
    ) -> List[SearchItem]:
        """
        执行多引擎搜索
        
        Args:
            query: 搜索查询
            num_results: 结果数量
            preferred_engine: 首选搜索引擎
            
        Returns:
            List[SearchItem]: 搜索结果列表
        """
        self.logger.info(f"开始多引擎搜索: {query}")
        
        # 确定搜索引擎顺序
        engine_order = self._get_engine_order(preferred_engine)
        
        for engine_name in engine_order:
            if engine_name not in self.search_engines:
                self.logger.warning(f"搜索引擎 {engine_name} 不可用，跳过")
                continue
            
            engine = self.search_engines[engine_name]
            self.logger.info(f"尝试使用 {engine_name} 搜索引擎...")
            
            try:
                # 使用超时机制
                results = await asyncio.wait_for(
                    self._perform_search(engine, query, num_results),
                    timeout=self.timeout
                )
                
                if results:
                    self.logger.info(f"✅ {engine_name} 搜索成功，找到 {len(results)} 个结果")
                    return results
                else:
                    self.logger.warning(f"⚠️ {engine_name} 搜索未返回结果")
                    
            except asyncio.TimeoutError:
                self.logger.warning(f"⏰ {engine_name} 搜索超时 ({self.timeout}秒)")
            except Exception as e:
                self.logger.error(f"❌ {engine_name} 搜索失败: {e}")
        
        # 所有搜索引擎都失败了，返回空结果
        self.logger.error("所有搜索引擎都失败了")
        return []
    
    def _get_engine_order(self, preferred_engine: str) -> List[str]:
        """获取搜索引擎执行顺序"""
        if preferred_engine in self.search_engines:
            # 首选引擎 + 其他引擎
            other_engines = [name for name in self.search_engines.keys() if name != preferred_engine]
            return [preferred_engine] + other_engines
        else:
            # 如果首选引擎不可用，使用默认顺序
            return list(self.search_engines.keys())
    
    async def _perform_search(
        self, 
        engine: WebSearchEngine, 
        query: str, 
        num_results: int
    ) -> List[SearchItem]:
        """在线程池中执行搜索"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: engine.perform_search(query, num_results)
        ) 