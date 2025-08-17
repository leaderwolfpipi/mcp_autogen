#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的SSE流式输出测试
"""

import asyncio
import json
import logging
from core.protocol_adapter import ProtocolAdapter

logging.basicConfig(level=logging.INFO)

async def test_simple_sse():
    """测试简化的SSE流"""
    
    print("🚀 简化SSE流式输出测试\n")
    
    # 初始化协议适配器
    adapter = ProtocolAdapter()
    
    # 简单的测试查询
    request = {
        "mcp_version": "1.0",
        "session_id": "simple_test",
        "request_id": "simple_req",
        "user_query": "你好，今天天气怎么样？",  # 简单的闲聊查询
        "context": {}
    }
    
    print(f"📝 测试查询: {request['user_query']}")
    print("🔄 开始SSE流式处理...\n")
    
    try:
        # 直接使用SSE处理器的流生成器
        stream = adapter.sse_handler.create_sse_stream(request)
        
        print("📡 接收SSE事件:")
        print("-" * 40)
        
        event_count = 0
        heartbeat_count = 0
        status_count = 0
        result_count = 0
        
        async for event_data in stream:
            event_count += 1
            
            try:
                # 解析事件数据
                if isinstance(event_data, str):
                    event = json.loads(event_data)
                else:
                    event = event_data
                
                event_type = event.get('type', 'unknown')
                
                # 统计不同类型的事件
                if event_type == 'heartbeat':
                    heartbeat_count += 1
                    if heartbeat_count <= 3:  # 只显示前3个心跳
                        print(f"💓 [{event_count:2d}] 心跳")
                    elif heartbeat_count == 4:
                        print(f"💓 ... (更多心跳事件)")
                
                elif event_type == 'status':
                    status_count += 1
                    status_data = event.get('data', {})
                    message = status_data.get('message', 'N/A')
                    print(f"📊 [{event_count:2d}] 状态: {message}")
                
                elif event_type == 'result':
                    result_count += 1
                    result_data = event.get('data', {})
                    final_response = result_data.get('final_response', 'N/A')
                    print(f"✅ [{event_count:2d}] 结果: {final_response[:50]}...")
                
                elif event_type == 'error':
                    error_msg = event.get('data', {}).get('error', {}).get('message', 'Unknown error')
                    print(f"❌ [{event_count:2d}] 错误: {error_msg}")
                
                else:
                    print(f"🔍 [{event_count:2d}] 其他: {event_type}")
                
                # 限制总事件数量
                if event_count >= 30:
                    print("... (限制显示前30个事件)")
                    break
                    
            except json.JSONDecodeError:
                print(f"⚠️  [{event_count:2d}] 解析失败: {str(event_data)[:50]}...")
            except Exception as e:
                print(f"❌ [{event_count:2d}] 处理错误: {e}")
        
        print("-" * 40)
        print(f"📊 事件统计:")
        print(f"  总事件数: {event_count}")
        print(f"  心跳事件: {heartbeat_count}")
        print(f"  状态事件: {status_count}")
        print(f"  结果事件: {result_count}")
        
        # 判断是否正常流式输出
        if status_count > 0 or result_count > 0:
            print("\n✅ SSE流式输出正常工作")
        else:
            print("\n❌ SSE流式输出可能有问题")
        
        if heartbeat_count < 50:  # 心跳数量合理
            print("✅ 心跳机制正常")
        else:
            print("⚠️ 心跳过多，可能存在循环问题")
        
    except Exception as e:
        print(f"❌ SSE测试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    await test_simple_sse()

if __name__ == "__main__":
    asyncio.run(main()) 