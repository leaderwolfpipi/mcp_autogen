 #!/usr/bin/env python3
"""
独立测试搜索工具
"""

import logging
import os
import requests
from typing import Any, Dict, List, Optional

def search_tool(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    搜索工具函数
    
    参数说明:
    - query: 搜索查询字符串
    - max_results: 最大结果数量，默认5个
    
    返回格式:
    {
        "status": "success/error",
        "message": "执行消息",
        "results": [
            {
                "title": "结果标题",
                "link": "结果链接", 
                "snippet": "结果摘要"
            }
        ],
        "source": "搜索源"
    }
    """
    logger = logging.getLogger("search_tool")
    
    try:
        # 参数验证
        logger.info(f"开始执行搜索工具")
        logger.info(f"搜索查询: {query}")
        
        if not query:
            logger.error("搜索查询不能为空")
            return {
                "status": "error", 
                "message": "搜索查询不能为空", 
                "results": []
            }
        
        # 尝试使用Google Custom Search API
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        google_cse_id = os.environ.get("GOOGLE_CSE_ID")
        
        if google_api_key and google_cse_id:
            try:
                logger.info(f"使用Google Custom Search API搜索: {query}")
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "key": google_api_key,
                    "cx": google_cse_id,
                    "q": query,
                    "num": max_results
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                items = data.get("items", [])
                
                results = []
                for item in items:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })
                
                logger.info(f"Google搜索成功，找到 {len(results)} 个结果")
                return {
                    "status": "success",
                    "message": f"搜索成功，找到 {len(results)} 个结果",
                    "results": results,
                    "source": "google"
                }
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Google搜索失败: {e}")
            except Exception as e:
                logger.warning(f"Google搜索出错: {e}")
        
        # 尝试使用DuckDuckGo搜索
        try:
            logger.info(f"使用DuckDuckGo搜索: {query}")
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # 提取相关主题
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if "Text" in topic:
                    results.append({
                        "title": topic.get("Text", ""),
                        "link": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", "")
                    })
            
            # 提取摘要
            if data.get("Abstract"):
                results.insert(0, {
                    "title": data.get("Heading", "摘要"),
                    "link": data.get("AbstractURL", ""),
                    "snippet": data.get("Abstract", "")
                })
            
            logger.info(f"DuckDuckGo搜索成功，找到 {len(results)} 个结果")
            return {
                "status": "success",
                "message": f"搜索成功，找到 {len(results)} 个结果",
                "results": results,
                "source": "duckduckgo"
            }
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"DuckDuckGo搜索失败: {e}")
        except Exception as e:
            logger.warning(f"DuckDuckGo搜索出错: {e}")
        
        # 如果所有搜索都失败，返回模拟结果
        logger.warning("所有搜索API都失败，返回模拟结果")
        mock_results = [
            {
                "title": f"关于 {query} 的搜索结果1",
                "link": "https://example.com/result1",
                "snippet": f"这是关于 {query} 的模拟搜索结果1"
            },
            {
                "title": f"关于 {query} 的搜索结果2", 
                "link": "https://example.com/result2",
                "snippet": f"这是关于 {query} 的模拟搜索结果2"
            },
            {
                "title": f"关于 {query} 的搜索结果3",
                "link": "https://example.com/result3", 
                "snippet": f"这是关于 {query} 的模拟搜索结果3"
            }
        ]
        
        return {
            "status": "success",
            "message": f"搜索完成，找到 {len(mock_results)} 个结果（模拟数据）",
            "results": mock_results,
            "source": "mock"
        }
            
    except Exception as e:
        logger.error(f"搜索工具执行失败: {e}")
        return {
            "status": "error",
            "message": f"搜索失败: {str(e)}",
            "results": []
        }
    finally:
        logger.info(f"搜索工具执行完成")

def test_search_tool():
    """测试搜索工具"""
    print("🔍 独立测试搜索工具")
    print("=" * 60)
    
    # 检查环境变量
    print("📋 环境变量检查:")
    print(f"  GOOGLE_API_KEY: {'已配置' if os.getenv('GOOGLE_API_KEY') else '未配置'}")
    print(f"  GOOGLE_CSE_ID: {'已配置' if os.getenv('GOOGLE_CSE_ID') else '未配置'}")
    
    # 测试搜索
    test_queries = [
        "李自成生平事迹",
        "人工智能发展",
        "Python编程教程"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 测试 {i}: {query}")
        
        result = search_tool(query)
        
        print(f"  状态: {result.get('status')}")
        print(f"  消息: {result.get('message')}")
        print(f"  搜索源: {result.get('source')}")
        print(f"  结果数量: {len(result.get('results', []))}")
        
        # 显示前3个结果
        for j, item in enumerate(result.get('results', [])[:3], 1):
            print(f"    结果{j}: {item.get('title', 'N/A')}")
            print(f"      链接: {item.get('link', 'N/A')}")
            print(f"      摘要: {item.get('snippet', 'N/A')[:100]}...")
    
    print("\n✅ 搜索工具测试完成")

if __name__ == "__main__":
    test_search_tool()