#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
严谨的流式输出验证测试
验证后端是否真正实现了流式输出，而不是一次性全部返回
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from core.protocol_adapter import ProtocolAdapter

logging.basicConfig(level=logging.INFO)

async def test_streaming_verification():
    """严谨验证流式输出"""
    
    print("🔍 严谨的流式输出验证测试")
    print("=" * 60)
    
    # 初始化协议适配器
    adapter = ProtocolAdapter()
    
    # 测试不同类型的查询
    test_cases = [
        {
            "name": "闲聊查询",
            "query": "你好，今天天气怎么样？",
            "expected_streaming": False  # 当前闲聊模式不是流式的
        },
        {
            "name": "任务查询",
            "query": "孙中山 (1866-1925) 的早年经历是其革命思想形成的重要阶段",
            "expected_streaming": True   # 任务模式应该是流式的
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 测试案例: {test_case['name']}")
        print(f"📝 查询: {test_case['query']}")
        print(f"🎯 期望流式: {'是' if test_case['expected_streaming'] else '否'}")
        print("-" * 40)
        
        # 构建请求
        request = {
            "mcp_version": "1.0",
            "session_id": f"test_{int(time.time())}",
            "request_id": f"req_{int(time.time())}",
            "user_query": test_case['query'],
            "context": {}
        }
        
        # 记录时间戳验证流式输出
        event_timestamps = []
        event_count = 0
        first_event_time = None
        last_event_time = None
        
        try:
            # 直接使用SSE处理器的流生成器
            stream = adapter.sse_handler.create_sse_stream(request)
            
            start_time = time.time()
            print(f"⏰ 开始时间: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
            
            async for event_data in stream:
                current_time = time.time()
                event_count += 1
                
                if first_event_time is None:
                    first_event_time = current_time
                last_event_time = current_time
                
                # 记录事件时间戳
                event_timestamps.append({
                    'index': event_count,
                    'timestamp': current_time,
                    'relative_time': current_time - start_time,
                    'event_data': event_data
                })
                
                try:
                    # 解析事件
                    if isinstance(event_data, str):
                        event = json.loads(event_data)
                    else:
                        event = event_data
                    
                    event_type = event.get('type', 'unknown')
                    current_time_str = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    
                    # 显示事件信息
                    if event_type == 'status':
                        message = event.get('data', {}).get('message', 'N/A')
                        print(f"⏰ {current_time_str} [{event_count:2d}] 📊 状态: {message}")
                    elif event_type == 'result':
                        final_response = event.get('data', {}).get('final_response', 'N/A')
                        print(f"⏰ {current_time_str} [{event_count:2d}] ✅ 结果: {final_response[:30]}...")
                    elif event_type == 'heartbeat':
                        print(f"⏰ {current_time_str} [{event_count:2d}] 💓 心跳")
                    else:
                        print(f"⏰ {current_time_str} [{event_count:2d}] 🔍 {event_type}")
                    
                    # 限制事件数量
                    if event_count >= 20:
                        print("... (限制显示前20个事件)")
                        break
                        
                except json.JSONDecodeError:
                    print(f"⚠️  [{event_count:2d}] 解析失败")
                except Exception as e:
                    print(f"❌ [{event_count:2d}] 处理错误: {e}")
            
            # 分析流式输出特征
            total_duration = last_event_time - first_event_time if first_event_time and last_event_time else 0
            print(f"\n📊 流式输出分析:")
            print(f"  总事件数: {event_count}")
            print(f"  总持续时间: {total_duration:.3f}秒")
            print(f"  平均事件间隔: {total_duration/max(event_count-1, 1):.3f}秒")
            
            # 分析时间间隔
            if len(event_timestamps) > 1:
                intervals = []
                for i in range(1, len(event_timestamps)):
                    interval = event_timestamps[i]['relative_time'] - event_timestamps[i-1]['relative_time']
                    intervals.append(interval)
                
                avg_interval = sum(intervals) / len(intervals)
                max_interval = max(intervals)
                min_interval = min(intervals)
                
                print(f"  事件间隔分析:")
                print(f"    最小间隔: {min_interval:.3f}秒")
                print(f"    最大间隔: {max_interval:.3f}秒")
                print(f"    平均间隔: {avg_interval:.3f}秒")
                
                # 判断是否真正流式
                is_truly_streaming = (
                    total_duration > 0.1 and  # 总时间超过100ms
                    event_count > 2 and       # 至少3个事件
                    max_interval > 0.05       # 最大间隔超过50ms
                )
                
                print(f"\n🎯 流式输出判断:")
                if is_truly_streaming:
                    print("✅ 检测到真正的流式输出")
                    print(f"   - 事件分布在 {total_duration:.3f}秒 时间内")
                    print(f"   - 事件间有明显的时间间隔")
                else:
                    print("❌ 未检测到真正的流式输出")
                    print("   - 事件可能是一次性批量返回的")
                    if total_duration < 0.1:
                        print(f"   - 总时间过短: {total_duration:.3f}秒")
                    if max_interval < 0.05:
                        print(f"   - 事件间隔过小: {max_interval:.3f}秒")
                
                # 验证预期
                if test_case['expected_streaming'] == is_truly_streaming:
                    print("✅ 符合预期")
                else:
                    print("❌ 不符合预期")
                    if test_case['expected_streaming']:
                        print("   期望流式输出，但实际不是")
                    else:
                        print("   期望非流式输出，但实际是流式的")
            else:
                print("⚠️ 事件数量不足，无法分析")
        
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()

async def test_llm_streaming_capability():
    """测试LLM流式生成能力"""
    
    print(f"\n🧪 测试LLM流式生成能力")
    print("-" * 40)
    
    try:
        from core.llm_clients.openai_client import OpenAIClient
        import os
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ 未设置OPENAI_API_KEY，跳过LLM流式测试")
            return
        
        client = OpenAIClient(api_key=api_key)
        messages = [{"role": "user", "content": "请简单介绍一下人工智能的发展历史"}]
        
        print("🔄 开始LLM流式生成测试...")
        start_time = time.time()
        
        chunk_count = 0
        content_buffer = ""
        
        async for chunk in client.generate_streaming(messages):
            chunk_count += 1
            current_time = time.time()
            
            if chunk.get('type') == 'content':
                content = chunk.get('content', '')
                content_buffer += content
                
                print(f"⏰ {datetime.now().strftime('%H:%M:%S.%f')[:-3]} [{chunk_count:2d}] 📝 '{content}'")
            
            # 限制显示的chunk数量
            if chunk_count >= 10:
                print("... (限制显示前10个chunks)")
                break
        
        total_time = time.time() - start_time
        print(f"\n📊 LLM流式生成分析:")
        print(f"  总chunks: {chunk_count}")
        print(f"  总时间: {total_time:.3f}秒")
        print(f"  内容长度: {len(content_buffer)}字符")
        
        if chunk_count > 1 and total_time > 0.1:
            print("✅ LLM支持真正的流式生成")
        else:
            print("❌ LLM流式生成可能有问题")
    
    except Exception as e:
        print(f"❌ LLM流式测试失败: {e}")

async def main():
    """主测试函数"""
    
    print("🚀 严谨的SSE流式输出验证")
    print("目标: 验证后端是否真正实现了流式输出")
    print("方法: 通过时间戳分析事件分布特征")
    print("=" * 60)
    
    # 测试1: 验证SSE流式输出
    await test_streaming_verification()
    
    # 测试2: 验证LLM流式能力
    await test_llm_streaming_capability()
    
    print("\n" + "=" * 60)
    print("🎯 结论:")
    print("如果闲聊模式显示'未检测到真正的流式输出'，")
    print("说明TaskEngine的_handle_chat_mode需要改为流式实现。")
    print("如果任务模式也不是流式的，说明整个流程都需要优化。")

if __name__ == "__main__":
    asyncio.run(main()) 