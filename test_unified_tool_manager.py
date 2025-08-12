#!/usr/bin/env python3
"""
测试统一工具管理器
"""

import asyncio
import logging
import os
from core.unified_tool_manager import get_unified_tool_manager
from core.tool_registry import ToolRegistry

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_unified_tool_manager():
    """测试统一工具管理器"""
    print("🔧 测试统一工具管理器")
    print("=" * 60)
    
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
    
    # 2. 测试工具获取
    print("\n🔍 工具获取测试:")
    test_tools = ["image_scaler", "file_uploader", "text_translator"]
    
    for tool_name in test_tools:
        print(f"\n测试工具: {tool_name}")
        
        # 检查工具是否存在
        exists = tool_manager.exists(tool_name)
        print(f"  存在: {exists}")
        
        if exists:
            # 获取工具来源
            source = tool_manager.get_source(tool_name)
            print(f"  来源: {source.value if source else 'unknown'}")
            
            # 获取工具函数
            tool_func = await tool_manager.get_tool(tool_name)
            if tool_func:
                print(f"  获取成功: {type(tool_func).__name__}")
                
                # 测试工具执行（使用模拟参数）
                try:
                    if tool_name == "image_scaler":
                        result = await tool_manager.execute_tool(tool_name, image_path="test.jpg", scale_factor=2.0)
                    elif tool_name == "file_uploader":
                        result = await tool_manager.execute_tool(tool_name, file_path="test.txt", destination="local")
                    elif tool_name == "text_translator":
                        result = await tool_manager.execute_tool(tool_name, text="Hello", target_lang="zh")
                    else:
                        result = await tool_manager.execute_tool(tool_name, test_param="test_value")
                    
                    print(f"  执行结果: {result}")
                except Exception as e:
                    print(f"  执行失败: {e}")
            else:
                print("  获取失败")
        else:
            print("  工具不存在")
    
    # 3. 测试工具注册
    print("\n📝 工具注册测试:")
    
    def test_generated_tool(param1: str, param2: int = 10) -> str:
        """测试生成的工具"""
        return f"Generated tool result: {param1}, {param2}"
    
    tool_manager.register_tool("test_generated_tool", test_generated_tool)
    print("✅ 注册测试工具成功")
    
    # 验证注册
    exists = tool_manager.exists("test_generated_tool")
    source = tool_manager.get_source("test_generated_tool")
    print(f"  存在: {exists}, 来源: {source.value if source else 'unknown'}")
    
    # 测试执行
    try:
        result = await tool_manager.execute_tool("test_generated_tool", param1="test", param2=20)
        print(f"  执行结果: {result}")
    except Exception as e:
        print(f"  执行失败: {e}")

async def test_pipeline_with_unified_tools():
    """测试使用统一工具管理器的Pipeline"""
    print("\n🚀 测试Pipeline与统一工具管理器集成")
    print("=" * 60)
    
    from core.smart_pipeline_engine import SmartPipelineEngine
    
    # 数据库连接配置
    PG_HOST = os.environ.get("PG_HOST", "106.14.24.138")
    PG_PORT = os.environ.get("PG_PORT", "5432")
    PG_USER = os.environ.get("PG_USER", "postgres")
    PG_PASSWORD = os.environ.get("PG_PASSWORD", "mypass123_lh007")
    PG_DB = os.environ.get("PG_DB", "mcp")
    db_url = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    
    try:
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
                
    except Exception as e:
        print(f"❌ Pipeline测试失败: {e}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_unified_tool_manager())
    asyncio.run(test_pipeline_with_unified_tools()) 