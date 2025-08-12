#!/usr/bin/env python3
"""
简化的统一工具系统测试
"""

import asyncio
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_simple_unified():
    """简化的统一工具管理器测试"""
    print("🔍 简化的统一工具管理器测试")
    print("=" * 60)
    
    try:
        from core.unified_tool_manager import UnifiedToolManager, ToolSource
        
        print("✅ 导入UnifiedToolManager成功")
        
        # 创建统一工具管理器
        tool_manager = UnifiedToolManager()
        print("✅ 统一工具管理器初始化成功")
        
        # 测试工具注册
        print("\n📋 测试工具注册")
        
        def test_tool(text: str, count: int = 1) -> str:
            """测试工具函数"""
            return f"处理结果: {text} x {count}"
        
        tool_def = tool_manager.register_tool(test_tool, "test_tool", "测试工具")
        print(f"  工具注册成功: {tool_def.name}")
        print(f"  工具来源: {tool_def.source.value}")
        print(f"  MCP工具: {tool_def.mcp_tool is not None}")
        
        # 测试工具执行
        print("\n📋 测试工具执行")
        result = await tool_manager.execute_tool("test_tool", text="hello", count=3)
        print(f"  执行结果: {result}")
        
        # 测试工具列表
        print("\n📋 测试工具列表")
        tool_list = tool_manager.get_tool_list()
        print(f"  工具数量: {len(tool_list)}")
        
        # 测试MCP工具列表
        print("\n📋 测试MCP工具列表")
        mcp_tool_list = tool_manager.get_mcp_tool_list()
        print(f"  MCP工具数量: {len(mcp_tool_list)}")
        
        print("\n✅ 简化的统一工具管理器测试完成")
        
    except Exception as e:
        print(f"❌ 简化的统一工具管理器测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_unified()) 