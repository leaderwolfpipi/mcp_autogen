#!/usr/bin/env python3
"""
测试MCP工具的输出schema功能
"""

import asyncio
import logging
from typing import Dict, Any, List

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_mcp_output_schema():
    """测试MCP工具的输出schema功能"""
    print("🔍 测试MCP工具的输出schema功能")
    print("=" * 60)
    
    try:
        from core.mcp_wrapper import MCPWrapper, MCPTool
        
        print("✅ 导入MCPWrapper成功")
        
        # 创建MCP包装器
        mcp_wrapper = MCPWrapper()
        
        # 测试不同类型的工具函数
        print("\n📋 测试1: 字符串返回类型")
        
        def string_tool(text: str) -> str:
            """返回字符串的工具"""
            return f"处理结果: {text}"
        
        mcp_tool = mcp_wrapper.register_tool(string_tool, "string_tool", "字符串处理工具")
        print(f"  工具名称: {mcp_tool.name}")
        print(f"  输入Schema: {mcp_tool.inputSchema}")
        print(f"  输出Schema: {mcp_tool.outputSchema}")
        
        print("\n📋 测试2: 布尔返回类型")
        
        def boolean_tool(value: bool) -> bool:
            """返回布尔值的工具"""
            return not value
        
        mcp_tool2 = mcp_wrapper.register_tool(boolean_tool, "boolean_tool", "布尔处理工具")
        print(f"  工具名称: {mcp_tool2.name}")
        print(f"  输入Schema: {mcp_tool2.inputSchema}")
        print(f"  输出Schema: {mcp_tool2.outputSchema}")
        
        print("\n📋 测试3: 数字返回类型")
        
        def number_tool(a: int, b: float) -> float:
            """返回数字的工具"""
            return a + b
        
        mcp_tool3 = mcp_wrapper.register_tool(number_tool, "number_tool", "数字计算工具")
        print(f"  工具名称: {mcp_tool3.name}")
        print(f"  输入Schema: {mcp_tool3.inputSchema}")
        print(f"  输出Schema: {mcp_tool3.outputSchema}")
        
        print("\n📋 测试4: 列表返回类型")
        
        def list_tool(items: List[str]) -> List[str]:
            """返回列表的工具"""
            return [item.upper() for item in items]
        
        mcp_tool4 = mcp_wrapper.register_tool(list_tool, "list_tool", "列表处理工具")
        print(f"  工具名称: {mcp_tool4.name}")
        print(f"  输入Schema: {mcp_tool4.inputSchema}")
        print(f"  输出Schema: {mcp_tool4.outputSchema}")
        
        print("\n📋 测试5: 字典返回类型")
        
        def dict_tool(data: Dict[str, Any]) -> Dict[str, Any]:
            """返回字典的工具"""
            return {"processed": True, "data": data}
        
        mcp_tool5 = mcp_wrapper.register_tool(dict_tool, "dict_tool", "字典处理工具")
        print(f"  工具名称: {mcp_tool5.name}")
        print(f"  输入Schema: {mcp_tool5.inputSchema}")
        print(f"  输出Schema: {mcp_tool5.outputSchema}")
        
        print("\n📋 测试6: 无类型注解的工具")
        
        def no_type_tool(param):
            """无类型注解的工具"""
            return f"处理了: {param}"
        
        mcp_tool6 = mcp_wrapper.register_tool(no_type_tool, "no_type_tool", "无类型注解工具")
        print(f"  工具名称: {mcp_tool6.name}")
        print(f"  输入Schema: {mcp_tool6.inputSchema}")
        print(f"  输出Schema: {mcp_tool6.outputSchema}")
        
        # 测试工具列表
        print("\n📋 测试7: 获取工具列表")
        tool_list = mcp_wrapper.get_tool_list()
        print(f"  工具数量: {len(tool_list)}")
        for tool in tool_list:
            print(f"    {tool['name']}: 输入={bool(tool['inputSchema'])}, 输出={bool(tool['outputSchema'])}")
        
        # 测试MCP Schema生成
        print("\n📋 测试8: 生成MCP Schema")
        schema = mcp_wrapper.generate_mcp_schema()
        print(f"  Schema包含输出Schema: {'outputSchema' in str(schema)}")
        
        print("\n✅ MCP工具的输出schema功能测试完成")
        
    except Exception as e:
        print(f"❌ MCP工具的输出schema功能测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mcp_output_schema() 