#!/usr/bin/env python3
"""
测试大模型工具选择
验证大模型是否会优先选择AI增强搜索工具
"""

import asyncio
import logging
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.requirement_parser import RequirementParser
from core.unified_tool_manager import get_unified_tool_manager


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


async def test_llm_tool_selection():
    """测试大模型工具选择"""
    print("\n" + "="*60)
    print("🧠 测试大模型工具选择")
    print("="*60)
    
    # 获取统一工具管理器
    tool_manager = get_unified_tool_manager()
    
    # 创建需求解析器
    available_tools = tool_manager.get_tool_list()
    parser = RequirementParser(
        use_llm=True,
        available_tools=available_tools
    )
    
    # 测试搜索相关的查询
    test_queries = [
        "搜索李自成生平经历和事迹",
        "查找Python编程教程",
        "查询人工智能发展历史",
        "帮我搜索最新的科技新闻",
        "搜索机器学习算法介绍"
    ]
    
    print("🔍 测试搜索查询的工具选择...")
    print("-" * 40)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. 查询: {query}")
        print("-" * 30)
        
        try:
            # 解析用户需求
            result = parser.parse(query)
            
            # 检查选择的工具
            components = result.get("components", [])
            
            if components:
                for j, component in enumerate(components, 1):
                    tool_type = component.get("tool_type", "unknown")
                    tool_id = component.get("id", "unknown")
                    
                    print(f"   组件 {j}: {tool_id}")
                    print(f"   工具类型: {tool_type}")
                    
                    # 判断是否是AI增强工具
                    if any(keyword in tool_type.lower() for keyword in ['smart', 'ai_enhanced', 'enhanced']):
                        print(f"   ✅ 选择了AI增强工具: {tool_type}")
                    elif 'search' in tool_type.lower():
                        print(f"   ⚠️ 选择了基础搜索工具: {tool_type}")
                        print(f"   💡 建议使用 smart_search 或 ai_enhanced_search_tool_function")
                    else:
                        print(f"   📋 选择了其他工具: {tool_type}")
                    
                    # 显示参数
                    params = component.get("params", {})
                    if params:
                        print(f"   参数: {params}")
                    
                    print()
            else:
                print("   ❌ 没有解析出任何组件")
                
        except Exception as e:
            print(f"   ❌ 解析失败: {e}")
    
    print("\n" + "="*60)
    print("📊 工具选择统计")
    print("="*60)
    
    # 统计工具选择情况
    ai_enhanced_count = 0
    basic_search_count = 0
    other_count = 0
    
    for query in test_queries:
        try:
            result = parser.parse(query)
            components = result.get("components", [])
            
            for component in components:
                tool_type = component.get("tool_type", "unknown")
                
                if any(keyword in tool_type.lower() for keyword in ['smart', 'ai_enhanced', 'enhanced']):
                    ai_enhanced_count += 1
                elif 'search' in tool_type.lower():
                    basic_search_count += 1
                else:
                    other_count += 1
                    
        except Exception as e:
            print(f"解析失败: {e}")
    
    print(f"🤖 AI增强工具选择次数: {ai_enhanced_count}")
    print(f"🔍 基础搜索工具选择次数: {basic_search_count}")
    print(f"📋 其他工具选择次数: {other_count}")
    
    if ai_enhanced_count > basic_search_count:
        print("✅ 大模型成功优先选择AI增强工具！")
    elif ai_enhanced_count == basic_search_count:
        print("⚠️ AI增强工具和基础工具选择次数相等")
    else:
        print("❌ 大模型仍然倾向于选择基础工具")


async def test_tool_description_impact():
    """测试工具描述对选择的影响"""
    print("\n" + "="*60)
    print("📝 测试工具描述对选择的影响")
    print("="*60)
    
    # 获取工具管理器
    tool_manager = get_unified_tool_manager()
    
    # 检查搜索相关工具的描述
    search_tools = []
    for tool in tool_manager.get_tool_list():
        name = tool.get("name", "")
        description = tool.get("description", "")
        if "search" in name.lower():
            search_tools.append((name, description))
    
    print("🔍 搜索相关工具描述对比:")
    print("-" * 40)
    
    for name, description in search_tools:
        print(f"\n工具: {name}")
        print(f"描述: {description}")
        
        # 分析描述质量
        if "AI" in description or "智能" in description or "增强" in description:
            print("   ✅ 描述突出了AI/智能特性")
        elif "推荐" in description or "强烈" in description:
            print("   ✅ 描述包含推荐词汇")
        else:
            print("   ⚠️ 描述较为基础")
    
    print("\n💡 建议:")
    print("- AI增强工具的描述应该突出其智能依赖管理功能")
    print("- 使用'推荐'、'强烈推荐'等词汇提高优先级")
    print("- 明确说明相比基础工具的优势")


async def test_available_tools_text():
    """测试可用工具列表文本的构建"""
    print("\n" + "="*60)
    print("📋 测试可用工具列表文本构建")
    print("="*60)
    
    # 获取工具管理器
    tool_manager = get_unified_tool_manager()
    
    # 创建需求解析器
    available_tools = tool_manager.get_tool_list()
    parser = RequirementParser(
        use_llm=True,
        available_tools=available_tools
    )
    
    # 获取构建的工具列表文本
    tools_text = parser._build_available_tools_text()
    
    print("📋 构建的可用工具列表:")
    print("-" * 40)
    print(tools_text)
    
    # 分析文本结构
    if "【🤖 AI增强工具 - 强烈推荐】" in tools_text:
        print("\n✅ 成功识别并优先展示AI增强工具")
    else:
        print("\n❌ 未找到AI增强工具优先展示")
    
    if "【💡 工具选择建议】" in tools_text:
        print("✅ 包含工具选择建议")
    else:
        print("❌ 缺少工具选择建议")


async def main():
    """主测试函数"""
    print("🧠 大模型工具选择测试")
    print("="*60)
    print("本测试将验证大模型是否会优先选择AI增强搜索工具")
    print("="*60)
    
    # 运行各项测试
    await test_available_tools_text()
    await test_tool_description_impact()
    await test_llm_tool_selection()
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)
    print("💡 总结:")
    print("   - 检查可用工具列表的构建")
    print("   - 分析工具描述对选择的影响")
    print("   - 验证大模型工具选择偏好")
    print("   - 评估AI增强工具的推荐效果")


if __name__ == "__main__":
    asyncio.run(main()) 