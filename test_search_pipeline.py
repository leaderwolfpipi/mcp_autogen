#!/usr/bin/env python3
"""
测试搜索和报告生成pipeline
"""

import asyncio
import json
from core.smart_pipeline_engine import SmartPipelineEngine

async def test_search_pipeline():
    """测试搜索和报告生成pipeline"""
    print("=== 测试搜索和报告生成Pipeline ===")
    
    # 初始化引擎
    engine = SmartPipelineEngine()
    
    # 测试自然语言输入
    user_input = "搜索李自成的信息，生成报告并保存到文件"
    
    print(f"用户输入: {user_input}")
    print("开始执行...")
    
    try:
        result = await engine.execute_from_natural_language(user_input)
        
        print("\n=== 执行结果 ===")
        print(f"成功: {result.get('success')}")
        print(f"执行时间: {result.get('execution_time', 0):.2f}秒")
        
        if result.get('success'):
            print("✅ Pipeline执行成功!")
            
            # 显示节点结果
            node_results = result.get('node_results', [])
            print(f"\n节点数量: {len(node_results)}")
            
            for i, node_result in enumerate(node_results, 1):
                print(f"\n节点 {i}:")
                print(f"  状态: {node_result.get('status', 'unknown')}")
                print(f"  耗时: {node_result.get('execution_time', 0):.2f}秒")
                
                # 显示输出摘要
                output = node_result.get('output', '')
                if isinstance(output, str) and len(output) > 100:
                    print(f"  输出: {output[:100]}...")
                else:
                    print(f"  输出: {output}")
        else:
            print("❌ Pipeline执行失败!")
            errors = result.get('errors', [])
            for error in errors:
                print(f"  错误: {error}")
                
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search_pipeline()) 