#!/usr/bin/env python3
"""
测试简化后的搜索工具
"""

import asyncio
import logging
from tools.ai_enhanced_search_tool import smart_search

# 设置日志
logging.basicConfig(level=logging.INFO)

async def test_simplified_search():
    """测试简化后的搜索工具"""
    print("=== 测试简化后的搜索工具 ===")
    
    try:
        print("🔍 开始执行smart_search...")
        result = await smart_search("李自成生平经历和事迹", max_results=3)
        
        print(f"✅ smart_search执行完成")
        print(f"   状态: {result.get('status')}")
        print(f"   消息: {result.get('message')}")
        print(f"   结果数量: {len(result.get('results', []))}")
        
        if result.get('dependency_issues'):
            print("⚠️ 检测到依赖问题")
            print(f"   建议修复: {result.get('suggested_fix')}")
        
        if result.get('suggested_fix'):
            print(f"🔧 修复建议: {result.get('suggested_fix')}")
        
        # 显示结果
        if result.get('results'):
            print("\n📋 搜索结果:")
            for i, item in enumerate(result['results'][:3], 1):
                print(f"  {i}. {item.get('title', '无标题')}")
                print(f"     链接: {item.get('link', '无链接')}")
                print(f"     摘要: {item.get('snippet', '无摘要')[:100]}...")
                print()
        
    except Exception as e:
        print(f"❌ smart_search执行失败: {e}")
        import traceback
        traceback.print_exc()

async def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    # 模拟依赖错误
    with patch('tools.multi_search_engine.MultiSearchEngine.search') as mock_search:
        # 模拟搜索返回空结果
        mock_search.return_value = []
        
        print("🔍 开始执行smart_search（模拟依赖错误）...")
        result = await smart_search("李自成生平经历和事迹", max_results=3)
        
        print(f"✅ smart_search执行完成")
        print(f"   状态: {result.get('status')}")
        print(f"   消息: {result.get('message')}")
        print(f"   结果数量: {len(result.get('results', []))}")
        
        if result.get('dependency_issues'):
            print("⚠️ 检测到依赖问题")
            print(f"   建议修复: {result.get('suggested_fix')}")
        
        # 检查是否返回了清晰的错误信息
        if result.get('status') == 'error' and '依赖' in result.get('message', ''):
            print("✅ 成功返回清晰的错误信息")
        else:
            print("❌ 错误信息不够清晰")

async def main():
    """主测试函数"""
    print("🧪 测试简化后的搜索工具")
    print("=" * 60)
    
    await test_simplified_search()
    await test_error_handling()
    
    print("✅ 所有测试完成！")

if __name__ == "__main__":
    # 导入patch
    from unittest.mock import patch
    asyncio.run(main()) 