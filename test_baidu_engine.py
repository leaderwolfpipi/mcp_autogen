#!/usr/bin/env python3
"""
测试新的百度搜索引擎实现
"""

import os
import sys
from tools.baidu_search_tool import BaiduSearchEngine, SearchItem

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

def test_search_tool_integration():
    """测试搜索工具集成"""
    print("\n🧪 测试搜索工具集成")
    print("=" * 50)
    
    try:
        from tools.search_tool import search_tool
        
        query = "Python编程教程"
        print(f"搜索查询: {query}")
        
        result = search_tool(query, 3)
        
        print(f"搜索状态: {result['status']}")
        print(f"搜索消息: {result['message']}")
        print(f"搜索源: {result['source']}")
        print(f"结果数量: {len(result['results'])}")
        
        if result['results']:
            print("\n搜索结果:")
            for i, item in enumerate(result['results'][:2], 1):
                print(f"  {i}. {item['title']}")
                print(f"     链接: {item['link']}")
                print(f"     摘要: {item['snippet'][:100] if item['snippet'] else '无摘要'}...")
                print()
        
    except Exception as e:
        print(f"❌ 搜索工具集成测试失败: {e}")

if __name__ == "__main__":
    test_baidu_engine()
    test_search_tool_integration() 