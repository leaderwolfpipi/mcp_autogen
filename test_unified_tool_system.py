#!/usr/bin/env python3
"""
测试统一工具系统
验证整合后的数据库注册表和MCP包装器功能
"""

import asyncio
import logging
import os
from typing import Dict, Any, List

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_unified_tool_manager():
    """测试统一工具管理器"""
    print("🔍 测试统一工具管理器")
    print("=" * 60)
    
    try:
        from core.unified_tool_manager import UnifiedToolManager, ToolSource, MCPTool
        
        print("✅ 导入UnifiedToolManager成功")
        
        # 创建模拟数据库注册表
        class MockDBRegistry:
            def list_tools(self):
                return []
            def register_tool(self, tool_info):
                print(f"  模拟注册工具: {tool_info.get('tool_id')}")
                return True
            def get_tool_code(self, tool_name):
                return None
            def find_tool(self, tool_name):
                return None
        
        mock_db_registry = MockDBRegistry()
        
        # 创建统一工具管理器
        tool_manager = UnifiedToolManager(db_registry=mock_db_registry)
        print("✅ 统一工具管理器初始化成功")
        
        # 测试工具注册
        print("\n📋 测试1: 工具注册")
        
        def test_tool(text: str, count: int = 1) -> str:
            """测试工具函数 - 这是一个用于测试的工具函数"""
            return f"处理结果: {text} x {count}"
        
        tool_def = tool_manager.register_tool(test_tool, "test_tool", "测试工具")
        print(f"  工具注册成功: {tool_def.name}")
        print(f"  工具来源: {tool_def.source.value}")
        print(f"  是否异步: {tool_def.is_async}")
        print(f"  MCP工具: {tool_def.mcp_tool is not None}")
        
        # 测试MCP工具功能
        print("\n📋 测试2: MCP工具功能")
        if tool_def.mcp_tool:
            print(f"  输入Schema: {tool_def.mcp_tool.inputSchema}")
            print(f"  输出Schema: {tool_def.mcp_tool.outputSchema}")
            print(f"  参数数量: {len(tool_def.mcp_tool.parameters)}")
        
        # 测试工具执行
        print("\n📋 测试3: 工具执行")
        result = await tool_manager.execute_tool("test_tool", text="hello", count=3)
        print(f"  执行结果: {result}")
        
        # 测试MCP工具调用
        print("\n📋 测试4: MCP工具调用")
        mcp_result = await tool_manager.call_mcp_tool("test_tool", {"text": "world", "count": 2})
        print(f"  MCP调用结果: {mcp_result}")
        
        # 测试工具列表
        print("\n📋 测试5: 工具列表")
        tool_list = tool_manager.get_tool_list()
        print(f"  工具数量: {len(tool_list)}")
        for tool in tool_list:
            print(f"    {tool['name']}: {tool['source']} (异步: {tool['is_async']})")
        
        # 测试MCP工具列表
        print("\n📋 测试6: MCP工具列表")
        mcp_tool_list = tool_manager.get_mcp_tool_list()
        print(f"  MCP工具数量: {len(mcp_tool_list)}")
        for tool in mcp_tool_list:
            print(f"    {tool['name']}: 输入={bool(tool['inputSchema'])}, 输出={bool(tool['outputSchema'])}")
        
        # 测试工具存在性检查
        print("\n📋 测试7: 工具存在性检查")
        print(f"  test_tool存在: {tool_manager.exists('test_tool')}")
        print(f"  unknown_tool存在: {tool_manager.exists('unknown_tool')}")
        
        # 测试工具来源
        print("\n📋 测试8: 工具来源")
        source = tool_manager.get_source("test_tool")
        print(f"  test_tool来源: {source.value if source else 'unknown'}")
        
        # 测试导出功能
        print("\n📋 测试9: 导出功能")
        manifest = tool_manager.export_tools_manifest()
        print(f"  导出工具数量: {manifest['total_tools']}")
        print(f"  导出MCP工具数量: {manifest['total_mcp_tools']}")
        print(f"  导出时间: {manifest['exported_at']}")
        
        # 测试保存到数据库
        print("\n📋 测试10: 保存到数据库")
        result = await tool_manager.save_tool_to_database("test_tool", test_tool, "测试工具")
        print(f"  保存结果: {'成功' if result else '失败'}")
        
        print("\n✅ 统一工具系统测试完成")
        
    except Exception as e:
        print(f"❌ 统一工具系统测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_smart_pipeline_integration():
    """测试智能Pipeline引擎与统一工具管理器的集成"""
    print("\n🔍 测试智能Pipeline引擎与统一工具管理器的集成")
    print("=" * 60)
    
    try:
        from core.smart_pipeline_engine import SmartPipelineEngine
        
        print("✅ 导入SmartPipelineEngine成功")
        
        # 创建模拟数据库注册表
        class MockDBRegistry:
            def list_tools(self):
                return []
            def register_tool(self, tool_info):
                print(f"  模拟注册工具: {tool_info.get('tool_id')}")
                return True
            def get_tool_code(self, tool_name):
                return None
            def find_tool(self, tool_name):
                return None
        
        mock_db_registry = MockDBRegistry()
        
        # 初始化智能Pipeline引擎
        engine = SmartPipelineEngine(use_llm=False, db_registry=mock_db_registry)
        print("✅ 智能Pipeline引擎初始化成功")
        
        # 测试工具信息获取
        print("\n📋 测试工具信息获取")
        tool_info = engine.get_tool_info("test_tool")
        print(f"  工具信息: {tool_info}")
        
        # 测试工具列表
        print("\n📋 测试工具列表")
        tools = engine.list_all_tools()
        print(f"  工具数量: {len(tools)}")
        
        print("\n✅ 智能Pipeline引擎与统一工具管理器集成测试完成")
        
    except Exception as e:
        print(f"❌ 智能Pipeline引擎与统一工具管理器集成测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_unified_tool_manager())
    asyncio.run(test_smart_pipeline_integration()) 