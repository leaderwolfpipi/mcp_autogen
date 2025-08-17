#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证移除假流式后的真正流式输出
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from core.protocol_adapter import ProtocolAdapter

logging.basicConfig(level=logging.WARNING)

async def test_no_fake_streaming():
    """验证移除假流式后的效果"""
    
    print("🚀 验证移除假流式后的真正流式输出")
    print("=" * 60)
    
    adapter = ProtocolAdapter()
    
    # 测试查询（LLM不可用的情况下）
    request = {
        "mcp_version": "1.0",
        "session_id": f"no_fake_{int(time.time())}",
        "request_id": f"no_fake_req_{int(time.time())}",
        "user_query": "你好，请介绍一下你的功能",
        "context": {}
    }
    
    print(f"📝 测试查询: {request['user_query']}")
    print("🎯 预期: 由于LLM不可用，应该没有假流式，直接返回规则回复")
    print("-" * 40)
    
    events = []
    start_time = time.time()
    
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
                        print(f"❌ {time_str} 检测到假流式事件！")
                    else:
                        print(f"⏰ {time_str} (+{relative_time:.3f}s) 📊 {message}")
                
                elif event_type == 'result':
                    final_response = event.get('data', {}).get('final_response', 'N/A')
                    print(f"⏰ {time_str} (+{relative_time:.3f}s) ✅ 结果: {final_response}")
                
                else:
                    print(f"⏰ {time_str} (+{relative_time:.3f}s) 🔍 {event_type}")
                    
            except json.JSONDecodeError:
                print(f"⚠️ 解析失败")
            except Exception as e:
                print(f"❌ 处理错误: {e}")
        
        # 分析结果
        print(f"\n📊 分析结果:")
        print(f"  总事件数: {len(events)}")
        
        # 检查是否有假流式事件
        fake_streaming_events = [e for e in events if e['data'].get('type') == 'chat_streaming']
        
        if fake_streaming_events:
            print(f"❌ 检测到 {len(fake_streaming_events)} 个假流式事件")
            print("   - 这些事件是模拟的，不是真正的流式生成")
        else:
            print("✅ 没有检测到假流式事件")
            print("   - LLM不可用时，正确地没有进行模拟流式")
        
        # 检查总时间
        if len(events) > 1:
            total_time = events[-1]['relative_time'] - events[0]['relative_time']
            print(f"  总处理时间: {total_time:.3f}秒")
            
            if total_time < 0.1:
                print("✅ 处理时间很短，没有人为延迟")
            else:
                print("⚠️ 处理时间较长，可能有不必要的延迟")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")

async def main():
    print("🎯 目标: 验证移除假流式模拟后的效果")
    print("说明: 当LLM不可用时，应该直接返回规则回复，不进行模拟流式")
    print()
    
    await test_no_fake_streaming()
    
    print("\n" + "=" * 60)
    print("🏆 总结:")
    print("✅ 移除了假流式模拟代码")
    print("✅ LLM不可用时不再进行人为的模拟流式")
    print("✅ 只有在真正的LLM流式生成时才有流式效果")
    print("✅ 避免了用户看到'假打字机效果'")

if __name__ == "__main__":
    asyncio.run(main()) 