#!/usr/bin/env python3
"""
测试搜索工具问题
"""

import asyncio
import logging
import os

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_search_tool():
    """测试搜索工具问题"""
    print("🔍 测试搜索工具问题")
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
        
        # 测试搜索相关的pipeline
        test_inputs = [
            "请搜索李自成生平事迹",
            "搜索关于人工智能的信息",
            "查找Python编程教程"
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
                    
                    # 如果有错误，显示错误信息
                    if 'error' in node_result:
                        print(f"    错误: {node_result['error']}")
            else:
                print(f"  错误信息: {result['errors']}")
        
        print("\n✅ 搜索工具测试完成")
        
    except Exception as e:
        print(f"❌ 搜索工具测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search_tool()) 