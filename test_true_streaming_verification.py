#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真正的流式输出验证测试
验证修复后的后端是否实现了真正的流式输出
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from core.protocol_adapter import ProtocolAdapter

logging.basicConfig(level=logging.WARNING)  # 减少日志噪音

async def test_true_streaming():
    """验证真正的流式输出"""
    
    print("🚀 真正的流式输出验证测试")
    print("=" * 60)
    
    # 初始化协议适配器
    adapter = ProtocolAdapter()
    
    # 测试闲聊查询（应该有流式效果）
    request = {
        "mcp_version": "1.0",
        "session_id": f"true_test_{int(time.time())}",
        "request_id": f"true_req_{int(time.time())}",
        "user_query": "你好，今天天气怎么样？请详细介绍一下你的功能",
        "context": {}
    }
    
    print(f"📝 测试查询: {request['user_query']}")
    print("-" * 40)
    
    # 记录详细的时间戳
    events = []
    start_time = time.time()
    
    try:
        stream = adapter.sse_handler.create_sse_stream(request)
        
        print(f"⏰ 开始时间: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        
        async for event_data in stream:
            current_time = time.time()
            relative_time = current_time - start_time
            
            try:
                if isinstance(event_data, str):
                    event = json.loads(event_data)
                else:
                    event = event_data
                
                event_type = event.get('type', 'unknown')
                event_info = {
                    'type': event_type,
                    'timestamp': current_time,
                    'relative_time': relative_time,
                    'data': event.get('data', {})
                }
                events.append(event_info)
                
                # 显示事件
                time_str = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                
                if event_type == 'status':
                    message = event.get('data', {}).get('message', 'N/A')
                    status_type = event.get('data', {}).get('type', 'unknown')
                    
                    if status_type == 'chat_streaming':
                        # 流式聊天内容
                        partial = event.get('data', {}).get('partial_content', '')
                        accumulated = event.get('data', {}).get('accumulated_content', '')
                        print(f"⏰ {time_str} (+{relative_time:.3f}s) 🌊 流式: '{partial}' (累计: {len(accumulated)}字符)")
                    else:
                        print(f"⏰ {time_str} (+{relative_time:.3f}s) 📊 状态: {message}")
                
                elif event_type == 'result':
                    final_response = event.get('data', {}).get('final_response', 'N/A')
                    print(f"⏰ {time_str} (+{relative_time:.3f}s) ✅ 结果: {final_response[:40]}...")
                
                else:
                    print(f"⏰ {time_str} (+{relative_time:.3f}s) 🔍 {event_type}")
                
                # 限制事件数量
                if len(events) >= 30:
                    print("... (限制显示前30个事件)")
                    break
                    
            except json.JSONDecodeError:
                print(f"⚠️ 解析失败: {str(event_data)[:50]}...")
            except Exception as e:
                print(f"❌ 处理错误: {e}")
        
        # 分析流式特征
        print(f"\n📊 流式输出分析:")
        print(f"  总事件数: {len(events)}")
        
        if len(events) > 1:
            total_duration = events[-1]['relative_time'] - events[0]['relative_time']
            print(f"  总持续时间: {total_duration:.3f}秒")
            
            # 计算事件间隔
            intervals = []
            for i in range(1, len(events)):
                interval = events[i]['relative_time'] - events[i-1]['relative_time']
                intervals.append(interval)
            
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                max_interval = max(intervals)
                min_interval = min(intervals)
                
                print(f"  事件间隔分析:")
                print(f"    最小间隔: {min_interval:.3f}秒")
                print(f"    最大间隔: {max_interval:.3f}秒")
                print(f"    平均间隔: {avg_interval:.3f}秒")
                print(f"    间隔标准差: {(sum((x - avg_interval)**2 for x in intervals) / len(intervals))**0.5:.3f}秒")
                
                # 检查流式聊天事件
                streaming_events = [e for e in events if e['data'].get('type') == 'chat_streaming']
                print(f"  流式聊天事件: {len(streaming_events)}个")
                
                # 判断流式质量
                print(f"\n🎯 流式输出质量判断:")
                
                # 检查是否有真正的流式内容
                has_streaming_content = len(streaming_events) > 0
                has_varied_intervals = max_interval - min_interval > 0.01  # 间隔变化超过10ms
                has_reasonable_duration = total_duration > 0.05  # 总时间超过50ms
                
                if has_streaming_content:
                    print("✅ 检测到流式聊天内容")
                    print(f"   - 流式事件数量: {len(streaming_events)}")
                else:
                    print("❌ 未检测到流式聊天内容")
                
                if has_varied_intervals:
                    print("✅ 事件间隔有自然变化")
                    print(f"   - 间隔变化范围: {min_interval:.3f}s ~ {max_interval:.3f}s")
                else:
                    print("❌ 事件间隔过于规律（可能是人为延迟）")
                    print(f"   - 间隔变化范围: {min_interval:.3f}s ~ {max_interval:.3f}s")
                
                if has_reasonable_duration:
                    print("✅ 总持续时间合理")
                else:
                    print("❌ 总持续时间过短")
                
                # 综合判断
                is_truly_streaming = has_streaming_content or (has_varied_intervals and has_reasonable_duration)
                
                print(f"\n🏆 最终判断:")
                if is_truly_streaming:
                    print("✅ 实现了真正的流式输出")
                    if has_streaming_content:
                        print("   - 有真正的流式聊天内容生成")
                    if has_varied_intervals:
                        print("   - 事件时间分布自然")
                else:
                    print("❌ 未实现真正的流式输出")
                    print("   - 仍然是批量返回或人为延迟")
            
        else:
            print("⚠️ 事件数量不足，无法分析")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主测试函数"""
    await test_true_streaming()

if __name__ == "__main__":
    asyncio.run(main()) 