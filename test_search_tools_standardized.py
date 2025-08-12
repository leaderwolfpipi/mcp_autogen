#!/usr/bin/env python3
"""
测试搜索工具的标准化输出格式
"""

import logging
from tools.search_tool import search_tool
from tools.smart_search import smart_search

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_search_tools_standardized():
    """测试搜索工具的标准化输出"""
    print("🧪 测试搜索工具的标准化输出格式")
    print("=" * 60)
    
    test_query = "Python编程"
    
    # 测试通用搜索工具
    print("\n1. 测试通用搜索工具 (search_tool)")
    print("-" * 40)
    result = search_tool(test_query, 3)
    print(f"状态: {result.get('status')}")
    print(f"消息: {result.get('message')}")
    print(f"主要数据: {len(result.get('data', {}).get('primary', []))} 个结果")
    print(f"统计信息: {result.get('data', {}).get('counts', {})}")
    print(f"元数据: {result.get('metadata', {}).get('tool_name')}")
    
    # 测试智能搜索工具
    print("\n2. 测试智能搜索工具 (smart_search)")
    print("-" * 40)
    result2 = smart_search(test_query, 2)
    print(f"状态: {result2.get('status')}")
    print(f"消息: {result2.get('message')}")
    print(f"主要数据: {len(result2.get('data', {}).get('primary', []))} 个结果")
    print(f"统计信息: {result2.get('data', {}).get('counts', {})}")
    print(f"元数据: {result2.get('metadata', {}).get('tool_name')}")
    
    # 验证标准化结构
    print("\n3. 验证标准化结构")
    print("-" * 40)
    tools_results = [result, result2]
    tool_names = ["search_tool", "smart_search"]
    
    for i, (tool_result, tool_name) in enumerate(zip(tools_results, tool_names)):
        print(f"\n工具 {i+1}: {tool_name}")
        
        # 检查必需字段
        required_fields = ['status', 'data', 'metadata', 'message']
        missing_fields = [field for field in required_fields if field not in tool_result]
        
        if missing_fields:
            print(f"  ❌ 缺少必需字段: {missing_fields}")
        else:
            print(f"  ✅ 包含所有必需字段")
        
        # 检查data子字段
        data = tool_result.get('data', {})
        data_fields = ['primary', 'secondary', 'counts']
        missing_data_fields = [field for field in data_fields if field not in data]
        
        if missing_data_fields:
            print(f"  ❌ data缺少字段: {missing_data_fields}")
        else:
            print(f"  ✅ data包含所有必需字段")
        
        # 检查metadata子字段
        metadata = tool_result.get('metadata', {})
        metadata_fields = ['tool_name', 'version', 'parameters', 'processing_time']
        missing_metadata_fields = [field for field in metadata_fields if field not in metadata]
        
        if missing_metadata_fields:
            print(f"  ❌ metadata缺少字段: {missing_metadata_fields}")
        else:
            print(f"  ✅ metadata包含所有必需字段")
    
    print("\n🎯 测试完成！")

if __name__ == "__main__":
    test_search_tools_standardized() 