#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务模式流式输出修复验证测试
测试任务模式是否实现了真正的流式输出
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from core.protocol_adapter import ProtocolAdapter

logging.basicConfig(level=logging.WARNING)

async def test_task_streaming_fix():
    """测试任务模式流式输出修复效果"""
    
    print("🔧 任务模式流式输出修复验证测试")
    print("=" * 60)
    
    print("🎯 测试目标:")
    print("1. 验证任务模式发送task_streaming事件")
    print("2. 检查任务流式事件格式是否符合前端预期")
    print("3. 确认任务模式也有逐字符的打字机效果")
    print()
    
    adapter = ProtocolAdapter()
    
    # 测试任务查询（应该触发任务模式流式输出）
    request = {
        "mcp_version": "1.0",
        "session_id": f"task_test_{int(time.time())}",
        "request_id": f"task_req_{int(time.time())}",
        "user_query": "请搜索一下孙中山的生平事迹，并详细总结他的主要贡献",
        "context": {}
    }
    
    print(f"📝 测试查询: {request['user_query']}")
    print("🎯 预期: 任务模式应该有工具执行 + 流式总结生成")
    print("-" * 40)
    
    events = []
    chat_streaming_events = []
    task_streaming_events = []
    start_time = time.time()
    
    # 模拟前端状态
    current_task_content = ""
    task_streaming_active = False
    
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
                event_data_content = event.get('data', {})
                
                events.append({
                    'type': event_type,
                    'relative_time': relative_time,
                    'data': event_data_content
                })
                
                time_str = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                
                if event_type == 'status':
                    status_type = event_data_content.get('type', event_data_content.get('status', 'unknown'))
                    message = event_data_content.get('message', 'N/A')
                    
                    if status_type == 'chat_streaming':
                        # 闲聊模式流式事件
                        partial_content = event_data_content.get('partial_content', '')
                        accumulated_content = event_data_content.get('accumulated_content', '')
                        
                        chat_streaming_events.append({
                            'partial': partial_content,
                            'accumulated': accumulated_content,
                            'time': relative_time
                        })
                        
                        print(f"💬 {time_str} (+{relative_time:.3f}s) 闲聊流式: '{partial_content}' → '{accumulated_content}'")
                        
                    elif status_type == 'task_streaming':
                        # 🎯 任务模式流式事件
                        partial_content = event_data_content.get('partial_content', '')
                        accumulated_content = event_data_content.get('accumulated_content', '')
                        
                        task_streaming_events.append({
                            'partial': partial_content,
                            'accumulated': accumulated_content,
                            'time': relative_time
                        })
                        
                        # 模拟前端更新UI
                        current_task_content = accumulated_content
                        task_streaming_active = True
                        
                        print(f"🔧 {time_str} (+{relative_time:.3f}s) 任务流式: '{partial_content}' → 总内容: '{accumulated_content}'")
                    else:
                        print(f"📊 {time_str} (+{relative_time:.3f}s) 状态: {status_type} - {message}")
                
                elif event_type == 'result':
                    final_response = event_data_content.get('final_response', 'N/A')
                    
                    # 模拟前端完成流式更新
                    if task_streaming_active:
                        print(f"✅ {time_str} (+{relative_time:.3f}s) 任务流式完成，最终内容: {final_response}")
                        task_streaming_active = False
                    else:
                        print(f"✅ {time_str} (+{relative_time:.3f}s) 最终结果: {final_response[:50]}...")
                
                else:
                    print(f"🔍 {time_str} (+{relative_time:.3f}s) {event_type}")
                
                # 限制事件数量
                if len(events) >= 30:
                    print("... (限制显示前30个事件)")
                    break
                    
            except json.JSONDecodeError:
                print(f"⚠️ JSON解析失败")
            except Exception as e:
                print(f"❌ 事件处理错误: {e}")
        
        # 分析结果
        print(f"\n📊 流式输出分析:")
        print(f"  总事件数: {len(events)}")
        print(f"  闲聊流式事件数: {len(chat_streaming_events)}")
        print(f"  任务流式事件数: {len(task_streaming_events)}")
        
        if len(events) > 1:
            total_time = events[-1]['relative_time'] - events[0]['relative_time']
            print(f"  总持续时间: {total_time:.3f}秒")
        
        # 任务流式事件详细分析
        if task_streaming_events:
            print(f"\n🔧 任务流式事件详细分析:")
            print(f"  任务流式事件数量: {len(task_streaming_events)}")
            
            # 显示内容增长过程
            print("  任务内容增长过程:")
            for i, event in enumerate(task_streaming_events[:10], 1):  # 只显示前10个
                print(f"    {i:2d}. (+{event['time']:.3f}s) +'{event['partial']}' → '{event['accumulated']}'")
            
            if len(task_streaming_events) > 10:
                print(f"    ... 还有 {len(task_streaming_events) - 10} 个任务流式事件")
            
            # 检查内容是否逐步增长
            content_lengths = [len(event['accumulated']) for event in task_streaming_events]
            is_progressive = all(content_lengths[i] >= content_lengths[i-1] for i in range(1, len(content_lengths)))
            
            print(f"  内容逐步增长: {'✅ 是' if is_progressive else '❌ 否'}")
            print(f"  最终内容长度: {content_lengths[-1] if content_lengths else 0} 字符")
        
        # 前端兼容性检查
        print(f"\n🎨 前端兼容性检查:")
        
        # 检查事件格式是否符合前端预期
        task_streaming_status_events = [e for e in events if e['type'] == 'status' and e['data'].get('type') == 'task_streaming']
        
        if task_streaming_status_events:
            print("✅ 检测到符合前端预期的task_streaming事件")
            
            # 检查必要字段
            sample_event = task_streaming_status_events[0]['data']
            has_partial = 'partial_content' in sample_event
            has_accumulated = 'accumulated_content' in sample_event
            has_type = sample_event.get('type') == 'task_streaming'
            
            print(f"  必要字段检查:")
            print(f"    type='task_streaming': {'✅' if has_type else '❌'}")
            print(f"    partial_content: {'✅' if has_partial else '❌'}")
            print(f"    accumulated_content: {'✅' if has_accumulated else '❌'}")
            
            if has_type and has_partial and has_accumulated:
                print("✅ 任务流式事件格式完全符合前端预期")
                print("✅ 任务模式前端修复应该生效")
            else:
                print("❌ 任务流式事件格式不完整")
        else:
            print("❌ 未检测到task_streaming事件")
        
        # 模拟前端处理效果
        print(f"\n🎭 模拟前端处理效果:")
        if task_streaming_events:
            print("✅ 前端应该看到任务模式的逐字符打字机效果")
            print(f"   - 任务总结会从 '{task_streaming_events[0]['accumulated']}' 开始")
            print(f"   - 逐步增长到 '{task_streaming_events[-1]['accumulated']}'")
            print(f"   - 总共 {len(task_streaming_events)} 次任务UI更新")
        else:
            print("❌ 前端仍会看到任务结果一次性显示")
            print("   - 任务总结会在最后一次性出现")
        
        # 对比分析
        print(f"\n🔄 对比分析:")
        if chat_streaming_events and task_streaming_events:
            print("✅ 闲聊模式和任务模式都实现了流式输出")
        elif chat_streaming_events and not task_streaming_events:
            print("⚠️ 只有闲聊模式实现了流式输出，任务模式仍是一次性输出")
        elif not chat_streaming_events and task_streaming_events:
            print("⚠️ 只有任务模式实现了流式输出，闲聊模式仍是一次性输出")
        else:
            print("❌ 闲聊模式和任务模式都没有实现流式输出")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("🎯 目标: 验证任务模式流式输出修复效果")
    print("说明: 测试任务模式是否发送task_streaming事件并实现真正的流式输出")
    print()
    
    await test_task_streaming_fix()
    
    print("\n" + "=" * 60)
    print("🏆 测试完成")
    print()
    print("💡 如果看到'任务模式前端修复应该生效'，说明:")
    print("   1. 后端正确发送了任务流式事件")
    print("   2. 事件格式符合前端预期")
    print("   3. 前端修复代码应该能正确处理")
    print("   4. 用户将看到任务模式的真正打字机效果")

if __name__ == "__main__":
    asyncio.run(main()) 