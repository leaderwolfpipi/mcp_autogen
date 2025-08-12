#!/usr/bin/env python3
"""
智能模式检测演示
展示新的任务引擎如何智能区分闲聊模式和任务模式
"""

import asyncio
import os
from core.task_engine import TaskEngine

# 模拟工具注册表
class MockToolRegistry:
    def get_tool_list(self):
        return [
            {
                "name": "smart_search",
                "description": "智能搜索工具",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索查询"}
                    },
                    "required": ["query"]
                }
            }
        ]

async def demo_mode_detection():
    """演示模式检测功能"""
    
    # 如果没有设置API key，我们只能演示规则检测部分
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  未设置OPENAI_API_KEY，将演示规则检测部分")
        print("=" * 60)
        
        # 手动测试规则检测逻辑
        tool_registry = MockToolRegistry()
        engine = TaskEngine(tool_registry)
        
        test_queries = [
            # 闲聊模式测试
            ("你好", "应该是闲聊模式"),
            ("谢谢你", "应该是闲聊模式"),
            ("早上好", "应该是闲聊模式"),
            ("ok", "应该是闲聊模式"),
            ("再见", "应该是闲聊模式"),
            
            # 任务模式测试
            ("搜索刘邦的历史", "应该是任务模式"),
            ("帮我查找关于AI的信息", "应该是任务模式"),
            ("请生成一份报告", "应该是任务模式"),
            ("什么是机器学习？", "应该是任务模式"),
            ("告诉我今天天气如何", "应该是任务模式"),
            ("我需要上传一个文件", "应该是任务模式"),
            ("翻译这段文字", "应该是任务模式"),
        ]
        
        print("模式检测测试结果：")
        print("-" * 60)
        
        for query, expected in test_queries:
            is_task = await engine._detect_task_mode(query)
            mode = "任务模式" if is_task else "闲聊模式"
            print(f"查询: \"{query}\"")
            print(f"检测结果: {mode} ({expected})")
            print()
    
    else:
        print("🚀 完整功能演示（包含LLM调用）")
        print("=" * 60)
        
        tool_registry = MockToolRegistry()
        engine = TaskEngine(tool_registry)
        
        # 演示完整的执行流程
        demo_queries = [
            "你好！",
            "谢谢你的帮助",
            "搜索刘邦的信息",
            "什么是人工智能？"
        ]
        
        for query in demo_queries:
            print(f"\n🔍 处理查询: \"{query}\"")
            print("-" * 40)
            
            try:
                # 这里会调用完整的execute方法，包括模式检测和相应处理
                result = await engine.execute(query, {})
                
                mode = result.get('mode', 'unknown')
                final_output = result.get('final_output', '')
                execution_time = result.get('execution_time', 0)
                
                print(f"检测模式: {mode}")
                print(f"执行时间: {execution_time:.3f}秒")
                print(f"回复内容: {final_output}")
                
                if mode == 'task':
                    step_count = result.get('step_count', 0)
                    print(f"执行步骤: {step_count}个")
                
            except Exception as e:
                print(f"处理失败: {e}")

def main():
    """主函数"""
    print("🤖 智能模式检测演示")
    print("=" * 60)
    print("这个演示展示了任务引擎如何智能区分:")
    print("• 闲聊模式：简单问候、感谢等，直接用LLM回复")
    print("• 任务模式：需要搜索、处理等，生成执行计划")
    print()
    
    asyncio.run(demo_mode_detection())
    
    print("\n✨ 演示完成！")
    print("\n💡 特性说明:")
    print("1. 多层次检测：规则检测 + LLM精确判断")
    print("2. 通用设计：适用于各种场景，无硬编码")
    print("3. 高效处理：闲聊模式快速响应，任务模式智能规划")
    print("4. 友好体验：自然的对话交互")

if __name__ == "__main__":
    main() 