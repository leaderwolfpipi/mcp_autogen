#!/usr/bin/env python3
"""
测试百度搜索功能
"""

import os
import sys
import requests
from urllib.parse import quote

def test_baidu_search():
    """测试百度搜索功能"""
    print("🧪 测试百度搜索功能")
    print("=" * 50)
    
    # 测试查询
    query = "李自成生平经历和事迹"
    print(f"搜索查询: {query}")
    
    # 检查环境变量
    baidu_api_key = os.environ.get("BAIDU_API_KEY")
    baidu_secret_key = os.environ.get("BAIDU_SECRET_KEY")
    
    print(f"百度API密钥: {'已配置' if baidu_api_key else '未配置'}")
    print(f"百度Secret密钥: {'已配置' if baidu_secret_key else '未配置'}")
    print()
    
    # 测试百度网页搜索
    print("📝 测试百度网页搜索...")
    try:
        results = baidu_web_search(query, 5)
        if results:
            print(f"✅ 百度网页搜索成功，找到 {len(results)} 个结果")
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. {result['title']}")
                print(f"     链接: {result['link']}")
                print(f"     摘要: {result['snippet'][:100]}...")
                print()
        else:
            print("❌ 百度网页搜索未返回结果")
    except Exception as e:
        print(f"❌ 百度网页搜索失败: {e}")
    
    # 测试模拟搜索
    print("📝 测试模拟搜索...")
    try:
        mock_results = mock_search(query)
        print(f"✅ 模拟搜索成功，找到 {len(mock_results)} 个结果")
        for i, result in enumerate(mock_results, 1):
            print(f"  {i}. {result['title']}")
            print(f"     链接: {result['link']}")
            print(f"     摘要: {result['snippet']}")
            print()
    except Exception as e:
        print(f"❌ 模拟搜索失败: {e}")

def baidu_web_search(query: str, max_results: int = 5):
    """百度网页搜索"""
    try:
        # 构造百度搜索URL
        search_url = f"https://www.baidu.com/s?wd={quote(query)}&rn={max_results}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 简单的HTML解析
        content = response.text
        
        results = []
        
        # 提取搜索结果（简化版本）
        import re
        
        # 查找搜索结果链接
        title_pattern = r'<h3[^>]*><a[^>]*>([^<]+)</a></h3>'
        link_pattern = r'<h3[^>]*><a[^>]*href="([^"]+)"[^>]*>'
        snippet_pattern = r'<div[^>]*class="[^"]*c-abstract[^"]*"[^>]*>([^<]+)</div>'
        
        titles = re.findall(title_pattern, content)
        links = re.findall(link_pattern, content)
        snippets = re.findall(snippet_pattern, content)
        
        # 组合结果
        for i in range(min(len(titles), len(links), len(snippets), max_results)):
            results.append({
                "title": titles[i].strip(),
                "link": links[i].strip(),
                "snippet": snippets[i].strip()
            })
        
        return results
        
    except Exception as e:
        print(f"百度网页搜索失败: {e}")
        return []

def mock_search(query: str):
    """模拟搜索"""
    return [
        {
            "title": f"关于 {query} 的搜索结果1",
            "link": f"https://www.baidu.com/s?wd={quote(query)}",
            "snippet": f"这是关于 {query} 的模拟搜索结果1"
        },
        {
            "title": f"关于 {query} 的搜索结果2", 
            "link": f"https://www.baidu.com/s?wd={quote(query)}",
            "snippet": f"这是关于 {query} 的模拟搜索结果2"
        },
        {
            "title": f"关于 {query} 的搜索结果3",
            "link": f"https://www.baidu.com/s?wd={quote(query)}", 
            "snippet": f"这是关于 {query} 的模拟搜索结果3"
        }
    ]

if __name__ == "__main__":
    test_baidu_search() 