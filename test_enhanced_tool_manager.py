#!/usr/bin/env python3
"""
测试增强的工具管理器功能
"""

import asyncio
import logging
import os

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_enhanced_tool_manager():
    """测试增强的工具管理器"""
    print("🔧 测试增强的工具管理器")
    print("=" * 60)
    
    try:
        from core.unified_tool_manager import get_unified_tool_manager, ToolSource
        from core.tool_registry import ToolRegistry
        
        # 数据库连接配置
        PG_HOST = os.environ.get("PG_HOST", "106.14.24.138")
        PG_PORT = os.environ.get("PG_PORT", "5432")
        PG_USER = os.environ.get("PG_USER", "postgres")
        PG_PASSWORD = os.environ.get("PG_PASSWORD", "mypass123_lh007")
        PG_DB = os.environ.get("PG_DB", "mcp")
        db_url = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
        
        # 初始化数据库工具注册表
        try:
            db_registry = ToolRegistry(db_url)
            print("✅ 数据库工具注册表初始化成功")
        except Exception as e:
            print(f"❌ 数据库工具注册表初始化失败: {e}")
            db_registry = None
        
        # 初始化统一工具管理器
        tool_manager = get_unified_tool_manager(db_registry)
        
        # 1. 测试工具发现
        print("\n📋 工具发现测试:")
        tools_info = tool_manager.list_tools()
        for tool_name, tool_info in tools_info.items():
            source = tool_info.get("source", "unknown")
            print(f"  - {tool_name} (来源: {source})")
        
        print(f"📊 总共发现 {len(tools_info)} 个工具")
        
        # 2. 测试工具注册和保存
        print("\n📝 测试工具注册和保存:")
        
        def test_user_tool(param1: str, param2: int = 10) -> str:
            """测试用户上传的工具"""
            return f"User tool result: {param1}, {param2}"
        
        def test_auto_tool(input_data: str, config: dict = None) -> dict:
            """测试自动生成的工具"""
            return {
                "status": "success",
                "input": input_data,
                "config": config or {},
                "processed": True
            }
        
        # 注册用户上传的工具
        tool_manager.register_tool("test_user_tool", test_user_tool, ToolSource.USER_UPLOADED)
        print("✅ 注册用户工具成功")
        
        # 注册自动生成的工具
        tool_manager.register_tool("test_auto_tool", test_auto_tool, ToolSource.AUTO_GENERATED)
        print("✅ 注册自动生成工具成功")
        
        # 保存工具到数据库
        if db_registry:
            await tool_manager.save_tool_to_database(
                "test_user_tool", 
                test_user_tool, 
                "用户上传的测试工具",
                "user_uploaded"
            )
            print("✅ 用户工具保存到数据库成功")
            
            await tool_manager.save_tool_to_database(
                "test_auto_tool", 
                test_auto_tool, 
                "自动生成的测试工具",
                "auto_generated"
            )
            print("✅ 自动生成工具保存到数据库成功")
        
        # 3. 测试工具来源
        print("\n🔍 测试工具来源:")
        test_tools = ["test_user_tool", "test_auto_tool"]
        
        for tool_name in test_tools:
            exists = tool_manager.exists(tool_name)
            source = tool_manager.get_source(tool_name)
            print(f"  {tool_name}: 存在={exists}, 来源={source.value if source else 'unknown'}")
        
        # 4. 测试工具执行
        print("\n🚀 测试工具执行:")
        
        for tool_name in test_tools:
            try:
                if tool_name == "test_user_tool":
                    result = await tool_manager.execute_tool(tool_name, param1="test", param2=20)
                elif tool_name == "test_auto_tool":
                    result = await tool_manager.execute_tool(tool_name, input_data="test data", config={"key": "value"})
                else:
                    result = await tool_manager.execute_tool(tool_name, test_param="test")
                
                print(f"  {tool_name}: {result}")
            except Exception as e:
                print(f"  {tool_name}: 执行失败 - {e}")
        
        # 5. 测试数据库工具加载
        if db_registry:
            print("\n💾 测试数据库工具加载:")
            
            # 从数据库重新加载工具
            tool_func = await tool_manager.get_tool("test_user_tool")
            if tool_func:
                try:
                    result = tool_func("reloaded", 30)
                    print(f"  重新加载的test_user_tool: {result}")
                except Exception as e:
                    print(f"  重新加载的test_user_tool执行失败: {e}")
        
        print("\n✅ 增强工具管理器测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_pipeline_integration():
    """测试Pipeline集成"""
    print("\n🚀 测试Pipeline与增强工具管理器集成")
    print("=" * 60)
    
    try:
        from core.smart_pipeline_engine import SmartPipelineEngine
        from core.tool_registry import ToolRegistry
        
        # 数据库连接配置
        PG_HOST = os.environ.get("PG_HOST", "106.14.24.138")
        PG_PORT = os.environ.get("PG_PORT", "5432")
        PG_USER = os.environ.get("PG_USER", "postgres")
        PG_PASSWORD = os.environ.get("PG_PASSWORD", "mypass123_lh007")
        PG_DB = os.environ.get("PG_DB", "mcp")
        db_url = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
        
        db_registry = ToolRegistry(db_url)
        engine = SmartPipelineEngine(use_llm=False, db_registry=db_registry)
        
        # 测试Pipeline执行
        test_inputs = [
            "请将图片放大3倍",
            "请将文件上传到云存储",
            "请处理图片然后上传"
        ]
        
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\n📝 测试 {i}: {user_input}")
            
            result = await engine.execute_from_natural_language(user_input)
            
            print(f"  执行结果: {'成功' if result['success'] else '失败'}")
            print(f"  执行时间: {result['execution_time']:.3f}秒")
            
            if result['success']:
                print(f"  最终输出: {result['final_output']}")
                
                # 显示工具来源信息
                for node_result in result['node_results']:
                    tool_source = node_result.get('tool_source', 'unknown')
                    print(f"    工具 {node_result['tool_type']}: {tool_source}")
            else:
                print(f"  错误信息: {result['errors']}")
        
        print("\n✅ Pipeline集成测试完成")
        
    except Exception as e:
        print(f"❌ Pipeline集成测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_enhanced_tool_manager())
    asyncio.run(test_pipeline_integration()) 