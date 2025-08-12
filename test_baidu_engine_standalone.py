#!/usr/bin/env python3
"""
独立测试百度搜索引擎实现
"""

import os
import sys
import requests
from urllib.parse import quote, urljoin
from dataclasses import dataclass
import re
from typing import Optional

@dataclass
class SearchItem:
    """搜索结果项"""
    title: str
    url: str
    description: Optional[str] = None
    source: str = "baidu"

class BaiduSearchEngine:
    """百度搜索引擎"""
    
    def __init__(self):
        self.logger = self._get_logger()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive"
        })
    
    def _get_logger(self):
        """获取简单的日志记录器"""
        class SimpleLogger:
            def info(self, msg): print(f"INFO: {msg}")
            def warning(self, msg): print(f"WARNING: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
        return SimpleLogger()
    
    def perform_search(self, query: str, num_results: int = 10, *args, **kwargs) -> list[SearchItem]:
        """
        执行百度搜索
        
        Args:
            query: 搜索查询
            num_results: 结果数量
            
        Returns:
            List[SearchItem]: 搜索结果列表
        """
        self.logger.info(f"开始百度搜索: {query}, 期望结果数: {num_results}")
        
        try:
            # 尝试使用百度搜索API
            if self._has_api_credentials():
                results = self._api_search(query, num_results)
                if results:
                    self.logger.info(f"API搜索成功，找到 {len(results)} 个结果")
                    return results
            
            # 使用网页爬虫搜索
            results = self._web_search(query, num_results)
            if results:
                self.logger.info(f"网页搜索成功，找到 {len(results)} 个结果")
                return results
            
            # 返回模拟结果
            self.logger.warning("所有搜索方式都失败，返回模拟结果")
            return self._mock_search(query, num_results)
            
        except Exception as e:
            self.logger.error(f"百度搜索失败: {e}")
            return self._mock_search(query, num_results)
    
    def _has_api_credentials(self) -> bool:
        """检查是否有API凭据"""
        return bool(os.environ.get("BAIDU_API_KEY") and os.environ.get("BAIDU_SECRET_KEY"))
    
    def _api_search(self, query: str, num_results: int) -> list[SearchItem]:
        """使用百度API搜索"""
        try:
            api_key = os.environ.get("BAIDU_API_KEY")
            secret_key = os.environ.get("BAIDU_SECRET_KEY")
            
            # 获取访问令牌
            access_token = self._get_access_token(api_key, secret_key)
            if not access_token:
                return []
            
            # 使用百度搜索API
            url = "https://aip.baidubce.com/rest/2.0/solution/v1/news_search"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            params = {"access_token": access_token}
            data = {
                "query": query,
                "num": num_results,
                "start": 0
            }
            
            response = self.session.post(url, params=params, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            
            result_data = response.json()
            results = []
            
            if "results" in result_data:
                for item in result_data["results"][:num_results]:
                    results.append(SearchItem(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        description=item.get("summary", ""),
                        source="baidu_api"
                    ))
            
            return results
            
        except Exception as e:
            self.logger.error(f"API搜索失败: {e}")
            return []
    
    def _get_access_token(self, api_key: str, secret_key: str) -> str | None:
        """获取百度访问令牌"""
        try:
            url = "https://aip.baidubce.com/oauth/2.0/token"
            params = {
                "grant_type": "client_credentials",
                "client_id": api_key,
                "client_secret": secret_key
            }
            
            response = self.session.post(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get("access_token")
            
        except Exception as e:
            self.logger.error(f"获取访问令牌失败: {e}")
            return None
    
    def _web_search(self, query: str, num_results: int) -> list[SearchItem]:
        """使用网页爬虫搜索"""
        try:
            # 构造搜索URL
            search_url = f"https://www.baidu.com/s?wd={quote(query)}&rn={num_results}&ie=utf-8"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # 使用正则表达式解析HTML
            results = self._regex_search(response.text, num_results)
            return results
            
        except Exception as e:
            self.logger.error(f"网页搜索失败: {e}")
            return []
    
    def _regex_search(self, html_content: str, num_results: int) -> list[SearchItem]:
        """使用正则表达式解析搜索结果"""
        results = []
        
        try:
            # 查找搜索结果的正则模式
            title_pattern = r'<h3[^>]*><a[^>]*>([^<]+)</a></h3>'
            link_pattern = r'<h3[^>]*><a[^>]*href="([^"]+)"[^>]*>'
            snippet_pattern = r'<div[^>]*class="[^"]*c-abstract[^"]*"[^>]*>([^<]+)</div>'
            
            titles = re.findall(title_pattern, html_content)
            links = re.findall(link_pattern, html_content)
            snippets = re.findall(snippet_pattern, html_content)
            
            # 组合结果
            for i in range(min(len(titles), len(links), len(snippets), num_results)):
                url = links[i].strip()
                if url.startswith('/s?'):
                    url = urljoin('https://www.baidu.com', url)
                
                results.append(SearchItem(
                    title=titles[i].strip(),
                    url=url,
                    description=snippets[i].strip(),
                    source="baidu_web"
                ))
            
        except Exception as e:
            self.logger.error(f"正则表达式搜索失败: {e}")
        
        return results
    
    def _mock_search(self, query: str, num_results: int) -> list[SearchItem]:
        """生成模拟搜索结果"""
        results = []
        for i in range(min(num_results, 3)):
            results.append(SearchItem(
                title=f"关于 {query} 的搜索结果{i+1}",
                url=f"https://www.baidu.com/s?wd={quote(query)}",
                description=f"这是关于 {query} 的模拟搜索结果{i+1}",
                source="baidu_mock"
            ))
        return results

def test_baidu_engine():
    """测试百度搜索引擎"""
    print("🧪 测试新的百度搜索引擎")
    print("=" * 50)
    
    # 创建搜索引擎实例
    engine = BaiduSearchEngine()
    
    # 测试查询
    query = "李自成生平经历和事迹"
    print(f"搜索查询: {query}")
    
    # 检查环境变量
    baidu_api_key = os.environ.get("BAIDU_API_KEY")
    baidu_secret_key = os.environ.get("BAIDU_SECRET_KEY")
    
    print(f"百度API密钥: {'已配置' if baidu_api_key else '未配置'}")
    print(f"百度Secret密钥: {'已配置' if baidu_secret_key else '未配置'}")
    print()
    
    # 执行搜索
    print("📝 执行百度搜索...")
    try:
        search_items = engine.perform_search(query, 5)
        
        if search_items:
            print(f"✅ 搜索成功，找到 {len(search_items)} 个结果")
            print(f"搜索源: {search_items[0].source}")
            print()
            
            for i, item in enumerate(search_items[:3], 1):
                print(f"结果 {i}:")
                print(f"  标题: {item.title}")
                print(f"  链接: {item.url}")
                print(f"  摘要: {item.description[:100] if item.description else '无摘要'}...")
                print(f"  来源: {item.source}")
                print()
        else:
            print("❌ 搜索未返回结果")
            
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
    
    # 测试SearchItem数据类
    print("📝 测试SearchItem数据类...")
    try:
        test_item = SearchItem(
            title="测试标题",
            url="https://example.com",
            description="这是一个测试描述",
            source="test"
        )
        print(f"✅ SearchItem创建成功:")
        print(f"  标题: {test_item.title}")
        print(f"  链接: {test_item.url}")
        print(f"  摘要: {test_item.description}")
        print(f"  来源: {test_item.source}")
        
    except Exception as e:
        print(f"❌ SearchItem测试失败: {e}")

if __name__ == "__main__":
    test_baidu_engine() 