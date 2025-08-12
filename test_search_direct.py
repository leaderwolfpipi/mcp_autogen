#!/usr/bin/env python3
"""
直接测试搜索工具
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_search_tool():
    """直接测试搜索工具"""
    print("🔍 直接测试搜索工具")
    print("=" * 60)
    
    try:
        # 直接导入搜索工具
        from tools.search_tool import search_tool
        
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
        
    except Exception as e:
        print(f"❌ 搜索工具测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search_tool() 