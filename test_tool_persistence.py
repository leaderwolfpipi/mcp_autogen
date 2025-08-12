#!/usr/bin/env python3
"""
测试工具持久化到数据库
"""

import asyncio
import logging
import os

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_tool_persistence():
    """测试工具持久化"""
    print("🔍 测试工具持久化到数据库")
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
        
        # 测试前检查数据库中的工具
        print("\n📋 测试前数据库中的工具:")
        tools_before = db_registry.list_tools()
        for tool in tools_before:
            print(f"  - {tool['tool_id']} (来源: {tool.get('source', 'unknown')})")
        
        # 测试搜索相关的pipeline（这会触发工具生成）
        test_input = "请搜索李自成生平事迹"
        print(f"\n🚀 执行测试: {test_input}")
        
        result = await engine.execute_from_natural_language(test_input)
        
        print(f"  执行结果: {'成功' if result['success'] else '失败'}")
        print(f"  执行时间: {result['execution_time']:.3f}秒")
        
        if result['success']:
            print(f"  最终输出: {result['final_output']}")
            
            # 显示工具来源信息
            for node_result in result['node_results']:
                tool_source = node_result.get('tool_source', 'unknown')
                print(f"    工具 {node_result['tool_type']}: {tool_source}")
                
                # 如果有错误，显示错误信息
                if 'error' in node_result:
                    print(f"    错误: {node_result['error']}")
        else:
            print(f"  错误信息: {result['errors']}")
        
        # 测试后检查数据库中的工具
        print("\n📋 测试后数据库中的工具:")
        tools_after = db_registry.list_tools()
        for tool in tools_after:
            print(f"  - {tool['tool_id']} (来源: {tool.get('source', 'unknown')})")
        
        # 检查是否有新工具被添加
        tools_before_ids = {tool['tool_id'] for tool in tools_before}
        tools_after_ids = {tool['tool_id'] for tool in tools_after}
        new_tools = tools_after_ids - tools_before_ids
        
        if new_tools:
            print(f"\n✅ 新工具已保存到数据库: {list(new_tools)}")
            
            # 检查新工具的详细信息
            for tool_id in new_tools:
                tool_info = db_registry.get_tool(tool_id)
                if tool_info:
                    print(f"  📝 工具 {tool_id} 详情:")
                    print(f"    描述: {tool_info.get('description', 'N/A')}")
                    print(f"    来源: {tool_info.get('source', 'N/A')}")
                    print(f"    参数: {tool_info.get('params', {})}")
                    print(f"    代码长度: {len(tool_info.get('code', ''))} 字符")
        else:
            print("\n❌ 没有新工具被保存到数据库")
        
        print("\n✅ 工具持久化测试完成")
        
    except Exception as e:
        print(f"❌ 工具持久化测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tool_persistence()) 