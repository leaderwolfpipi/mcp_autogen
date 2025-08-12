#!/usr/bin/env python3
"""
搜索基础类和搜索引擎接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SearchItem:
    """搜索结果项"""
    title: str
    url: str
    description: Optional[str] = None
    source: str = "unknown"


class WebSearchEngine(ABC):
    """搜索引擎基类"""
    
    @abstractmethod
    def perform_search(
        self, query: str, num_results: int = 10, *args, **kwargs
    ) -> List[SearchItem]:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            num_results: 结果数量
            
        Returns:
            List[SearchItem]: 搜索结果列表
        """
        pass 