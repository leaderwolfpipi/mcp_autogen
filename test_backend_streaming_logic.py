#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端SSE流式输出逻辑深度检查
"""

import asyncio
import json
import logging
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from core.protocol_adapter import ProtocolAdapter
from core.task_engine import TaskEngine
from core.tool_registry import ToolRegistry

logging.basicConfig(level=logging.WARNING)

async def test_backend_streaming_logic():
    """深度测试后端流式逻辑"""
    
    print("🔍 后端SSE流式输出逻辑深度检查")
    print("=" * 60)
    
    # 1. 检查环境变量加载
    print("📋 环境变量检查:")
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE")
    model = os.getenv("OPENAI_MODEL")
    
    print(f"  OPENAI_API_KEY: {'✅ 已设置' if api_key else '❌ 未设置'}")
    print(f"  OPENAI_API_BASE: {base_url or '未设置'}")
    print(f"  OPENAI_MODEL: {model or 'gpt-4-turbo'}")
    
    # 2. 检查TaskEngine初始化
    print(f"\n🤖 TaskEngine初始化检查:")
    tool_registry = ToolRegistry("sqlite:///test.db")
    task_engine = TaskEngine(tool_registry)
    
    print(f"  task_engine.llm: {task_engine.llm}")
    print(f"  LLM类型: {type(task_engine.llm).__name__ if task_engine.llm else 'None'}")
    
    if task_engine.llm:
        print(f"  支持generate: {'✅' if hasattr(task_engine.llm, 'generate') else '❌'}")
        print(f"  支持generate_streaming: {'✅' if hasattr(task_engine.llm, 'generate_streaming') else '❌'}")
        
        # 测试LLM连接
        try:
            print("  🧪 测试LLM连接...")
            response = await task_engine.llm.generate("测试", max_tokens=10)
            print(f"  LLM连接: ✅ 成功 (响应: {response[:30]}...)")
        except Exception as e:
            print(f"  LLM连接: ❌ 失败 ({str(e)[:50]}...)")
    
    # 3. 测试流式输出路径
    print(f"\n🎯 流式输出路径测试:")
    
    # 模拟_handle_chat_mode的条件判断
    query = "你好，请介绍一下你的功能"
    
    if task_engine.llm and hasattr(task_engine.llm, 'generate_streaming'):
        print("✅ 将执行真正的LLM流式生成")
        
        # 测试流式生成
        try:
            print("  🧪 测试LLM流式生成...")
            messages = [{"role": "user", "content": "简单介绍一下AI"}]
            
            chunk_count = 0
            content_buffer = ""
            
            async for chunk in task_engine.llm.generate_streaming(messages, max_tokens=50):
                chunk_count += 1
                if chunk.get('type') == 'content':
                    content = chunk.get('content', '')
                    content_buffer += content
                    print(f"    Chunk {chunk_count}: '{content}' (累计: {len(content_buffer)}字符)")
                if chunk_count >= 5:  # 限制显示
                    break
            
            print(f"  流式生成: ✅ 成功 ({chunk_count}个chunks)")
            
        except Exception as e:
            print(f"  流式生成: ❌ 失败 ({str(e)[:50]}...)")
            
    elif task_engine.llm and hasattr(task_engine.llm, 'generate'):
        print("⚠️ 将执行普通LLM生成（非流式）")
    else:
        print("❌ 将执行规则回复（无LLM）")
    
    # 4. 测试完整的SSE流
    print(f"\n🌊 完整SSE流测试:")
    
    adapter = ProtocolAdapter()
    request = {
        "mcp_version": "1.0",
        "session_id": f"backend_test_{int(time.time())}",
        "request_id": f"backend_req_{int(time.time())}",
        "user_query": query,
        "context": {}
    }
    
    print(f"📝 测试查询: {query}")
    print("-" * 40)
    
    events = []
    start_time = time.time()
    streaming_events = 0
    
    try:
        stream = adapter.sse_handler.create_sse_stream(request)
        
        async for event_data in stream:
            current_time = time.time()
            relative_time = current_time - start_time
            
            try:
                if isinstance(event_data, str):
                    event = json.loads(event_data)
                else:
                    event = event_data
                
                event_type = event.get('type', 'unknown')
                events.append({
                    'type': event_type,
                    'relative_time': relative_time,
                    'data': event.get('data', {})
                })
                
                time_str = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                
                if event_type == 'status':
                    message = event.get('data', {}).get('message', 'N/A')
                    status_type = event.get('data', {}).get('type', 'unknown')
                    
                    if status_type == 'chat_streaming':
                        streaming_events += 1
                        partial = event.get('data', {}).get('partial_content', '')
                        accumulated = event.get('data', {}).get('accumulated_content', '')
                        print(f"🌊 {time_str} (+{relative_time:.3f}s) 流式事件 #{streaming_events}: '{partial}' (累计: {len(accumulated)}字符)")
                    else:
                        print(f"📊 {time_str} (+{relative_time:.3f}s) 状态: {message}")
                
                elif event_type == 'result':
                    final_response = event.get('data', {}).get('final_response', 'N/A')
                    print(f"✅ {time_str} (+{relative_time:.3f}s) 最终结果: {final_response[:50]}...")
                
                else:
                    print(f"🔍 {time_str} (+{relative_time:.3f}s) {event_type}")
                
                # 限制事件数量
                if len(events) >= 20:
                    print("... (限制显示前20个事件)")
                    break
                    
            except json.JSONDecodeError:
                print(f"⚠️ JSON解析失败")
            except Exception as e:
                print(f"❌ 事件处理错误: {e}")
        
        # 5. 分析结果
        print(f"\n📊 流式输出分析:")
        print(f"  总事件数: {len(events)}")
        print(f"  流式事件数: {streaming_events}")
        
        if len(events) > 1:
            total_time = events[-1]['relative_time'] - events[0]['relative_time']
            print(f"  总持续时间: {total_time:.3f}秒")
            
            # 检查时间间隔
            intervals = []
            for i in range(1, len(events)):
                interval = events[i]['relative_time'] - events[i-1]['relative_time']
                intervals.append(interval)
            
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                max_interval = max(intervals)
                min_interval = min(intervals)
                
                print(f"  事件间隔:")
                print(f"    最小: {min_interval:.3f}s")
                print(f"    最大: {max_interval:.3f}s") 
                print(f"    平均: {avg_interval:.3f}s")
        
        # 6. 流式质量判断
        print(f"\n🎯 流式输出质量判断:")
        
        if streaming_events > 0:
            print(f"✅ 检测到 {streaming_events} 个真正的流式事件")
            print("   - 内容是逐步生成的")
        else:
            print("❌ 没有检测到流式事件")
            print("   - 内容是一次性返回的")
            
        # 7. 问题诊断
        print(f"\n🔧 问题诊断:")
        
        if not task_engine.llm:
            print("❌ LLM客户端未初始化")
            print("   - 检查环境变量是否正确加载")
            print("   - 检查API Key是否有效")
        elif not hasattr(task_engine.llm, 'generate_streaming'):
            print("❌ LLM客户端不支持流式生成")
            print("   - 检查LLM客户端实现")
        elif streaming_events == 0:
            print("❌ 流式生成未被触发")
            print("   - 检查_handle_chat_mode逻辑")
            print("   - 检查模式检测结果")
        else:
            print("✅ 流式输出工作正常")
    
    except Exception as e:
        print(f"❌ SSE流测试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("🎯 目标: 深度检查后端SSE流式输出逻辑")
    print("说明: 逐步检查每个环节，找出流式输出问题的根本原因")
    print()
    
    await test_backend_streaming_logic()
    
    print("\n" + "=" * 60)
    print("🏆 检查完成")

if __name__ == "__main__":
    asyncio.run(main()) 