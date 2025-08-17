#!/usr/bin/env python3
"""
详细的流式输出调试脚本
追踪从API到前端的完整执行路径
"""

import asyncio
import json
import aiohttp
import time
import sys
from datetime import datetime

async def test_streaming_detailed():
    """详细测试流式输出的每个环节"""
    
    print("🔍 详细流式输出调试开始...")
    print("=" * 60)
    
    # 测试数据
    test_request = {
        "mcp_version": "1.0",
        "session_id": f"debug_session_{int(time.time())}",
        "request_id": f"debug_req_{int(time.time())}",
        "user_query": "你好，请简单介绍一下你自己",
        "context": {}
    }
    
    url = "http://localhost:8000/mcp/sse"
    
    print(f"📤 发送请求到: {url}")
    print(f"📋 请求数据: {json.dumps(test_request, ensure_ascii=False, indent=2)}")
    print("\n" + "=" * 60)
    print("📨 开始接收SSE响应...")
    print("=" * 60)
    
    event_count = 0
    chat_streaming_count = 0
    total_partial_content = ""
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=test_request) as response:
                print(f"🌐 HTTP状态码: {response.status}")
                print(f"📄 响应头: {dict(response.headers)}")
                print("\n" + "-" * 40)
                
                if response.status != 200:
                    print(f"❌ HTTP错误: {response.status}")
                    text = await response.text()
                    print(f"错误响应: {text}")
                    return
                
                # 解析SSE流
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    
                    if not line_str:
                        continue
                        
                    print(f"📦 原始SSE行: {repr(line_str)}")
                    
                    if line_str.startswith('data: '):
                        event_count += 1
                        data_str = line_str[6:]  # 移除 'data: ' 前缀
                        
                        try:
                            event_data = json.loads(data_str)
                            event_type = event_data.get('type', 'unknown')
                            
                            print(f"\n🎯 事件 #{event_count}: {event_type}")
                            print(f"   完整数据: {json.dumps(event_data, ensure_ascii=False, indent=4)}")
                            
                            # 特别关注status事件
                            if event_type == 'status':
                                status_data = event_data.get('data', {})
                                status_type = status_data.get('type', '')
                                
                                print(f"   📊 状态类型: {status_type}")
                                
                                if status_type == 'chat_streaming':
                                    chat_streaming_count += 1
                                    partial = status_data.get('partial_content', '')
                                    accumulated = status_data.get('accumulated_content', '')
                                    total_partial_content += partial
                                    
                                    print(f"   💬 流式内容 #{chat_streaming_count}:")
                                    print(f"      部分内容: {repr(partial)}")
                                    print(f"      累积内容: {repr(accumulated)}")
                                    print(f"      总累积: {repr(total_partial_content)}")
                            
                            # 关注result事件
                            elif event_type == 'result':
                                result_data = event_data.get('data', {})
                                final_response = result_data.get('final_response', '')
                                mode = result_data.get('mode', '')
                                
                                print(f"   🏁 最终结果:")
                                print(f"      模式: {mode}")
                                print(f"      响应: {repr(final_response)}")
                                
                        except json.JSONDecodeError as e:
                            print(f"   ❌ JSON解析失败: {e}")
                            print(f"   原始数据: {repr(data_str)}")
                    
                    elif line_str.startswith('event: '):
                        event_name = line_str[7:]
                        print(f"📌 事件名称: {event_name}")
                    
                    elif line_str == 'id: ' or line_str.startswith('id: '):
                        print(f"🆔 事件ID: {line_str}")
                    
                    # 检查是否超时
                    if event_count > 50:  # 防止无限循环
                        print("⚠️ 事件数量过多，停止接收")
                        break
                        
    except asyncio.TimeoutError:
        print("⏰ 请求超时")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("📊 调试统计:")
    print(f"   总事件数: {event_count}")
    print(f"   chat_streaming事件数: {chat_streaming_count}")
    print(f"   总部分内容长度: {len(total_partial_content)}")
    print(f"   是否检测到流式输出: {'是' if chat_streaming_count > 0 else '否'}")
    print("=" * 60)

async def main():
    await test_streaming_detailed()

if __name__ == "__main__":
    asyncio.run(main()) 