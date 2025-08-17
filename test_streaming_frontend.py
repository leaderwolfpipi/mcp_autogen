#!/usr/bin/env python3
"""
前端流式输出测试脚本
测试修复后的SSE流式输出是否正常工作
"""

import asyncio
import json
import aiohttp
import time
from datetime import datetime

async def test_streaming_output():
    """测试流式输出"""
    
    print("🚀 开始测试流式输出...")
    
    # 测试数据
    test_request = {
        "mcp_version": "1.0",
        "session_id": f"test_session_{int(time.time())}",
        "request_id": f"test_req_{int(time.time())}",
        "user_query": "你好，请简单介绍一下你自己",
        "context": {}
    }
    
    url = "http://localhost:8000/mcp/sse"
    
    print(f"📤 发送请求到: {url}")
    print(f"📋 请求数据: {json.dumps(test_request, ensure_ascii=False, indent=2)}")
    print("\n" + "="*50)
    print("📨 开始接收流式响应:")
    print("="*50)
    
    async with aiohttp.ClientSession() as session:
        try:
            start_time = time.time()
            event_count = 0
            content_updates = []
            
            async with session.post(
                url,
                json=test_request,
                headers={
                    'Accept': 'text/event-stream',
                    'Cache-Control': 'no-cache'
                }
            ) as response:
                
                if response.status != 200:
                    print(f"❌ 请求失败: {response.status} {response.reason}")
                    return
                
                print(f"✅ 连接成功，开始接收数据流...")
                
                # 读取SSE流
                buffer = ""
                async for chunk in response.content.iter_any():
                    chunk_text = chunk.decode('utf-8')
                    buffer += chunk_text
                    
                    # 按行处理
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line.startswith('data:'):
                            data_text = line[5:].strip()
                            if data_text:
                                try:
                                    event_data = json.loads(data_text)
                                    event_count += 1
                                    
                                    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                                    elapsed = time.time() - start_time
                                    
                                    print(f"[{timestamp}] (+{elapsed:.3f}s) Event #{event_count}: {event_data.get('type', 'unknown')}")
                                    
                                    # 处理不同类型的事件
                                    if event_data.get('type') == 'mode_detection':
                                        print(f"  🎯 模式: {event_data.get('mode')} - {event_data.get('message')}")
                                    
                                    elif event_data.get('type') == 'status':
                                        status_data = event_data.get('data', {})
                                        status_type = status_data.get('type')
                                        
                                        # 详细打印status事件
                                        print(f"  📊 状态事件详情: {json.dumps(status_data, ensure_ascii=False)[:200]}...")
                                        
                                        if status_type == 'chat_streaming':
                                            partial = status_data.get('partial_content', '')
                                            accumulated = status_data.get('accumulated_content', '')
                                            
                                            content_updates.append({
                                                'time': elapsed,
                                                'partial': partial,
                                                'accumulated_length': len(accumulated)
                                            })
                                            
                                            print(f"  🌊 流式内容: +'{partial}' (总长度: {len(accumulated)})")
                                        else:
                                            print(f"  ⚠️  未识别的状态类型: {status_type}")
                                    
                                    elif event_data.get('type') == 'result':
                                        result_data = event_data.get('data', {})
                                        final_response = result_data.get('final_response', '')
                                        execution_time = result_data.get('execution_time', 0)
                                        
                                        print(f"  ✅ 最终结果: {final_response[:50]}...")
                                        print(f"  ⏱️  执行时间: {execution_time:.3f}秒")
                                    
                                    else:
                                        print(f"  📋 其他事件: {json.dumps(event_data, ensure_ascii=False)[:100]}...")
                                    
                                except json.JSONDecodeError as e:
                                    print(f"  ❌ JSON解析失败: {e}")
                                    print(f"  📝 原始数据: {data_text[:100]}...")
                        
                        elif line.startswith('event:'):
                            event_type = line[6:].strip()
                            print(f"  📡 事件类型: {event_type}")
                        
                        elif line == '':
                            # 空行，事件结束
                            pass
        
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return
    
    # 分析结果
    total_time = time.time() - start_time
    print("\n" + "="*50)
    print("📊 测试结果分析:")
    print("="*50)
    print(f"总事件数: {event_count}")
    print(f"总耗时: {total_time:.3f}秒")
    print(f"流式内容更新次数: {len(content_updates)}")
    
    if content_updates:
        print("\n🌊 流式内容分析:")
        for i, update in enumerate(content_updates):
            print(f"  更新 #{i+1}: {update['time']:.3f}s, +'{update['partial']}', 总长度: {update['accumulated_length']}")
        
        # 检查是否真正流式
        if len(content_updates) > 1:
            time_intervals = [content_updates[i]['time'] - content_updates[i-1]['time'] 
                            for i in range(1, len(content_updates))]
            avg_interval = sum(time_intervals) / len(time_intervals) if time_intervals else 0
            
            print(f"\n⏱️  平均更新间隔: {avg_interval:.3f}秒")
            
            if avg_interval < 0.5:  # 如果更新间隔小于0.5秒，认为是真正的流式
                print("✅ 检测到真正的流式输出!")
            else:
                print("⚠️  更新间隔较大，可能不是真正的流式输出")
        else:
            print("❌ 只有一次内容更新，不是流式输出")
    else:
        print("❌ 没有检测到流式内容更新")

async def main():
    """主函数"""
    print("🔧 MCP SSE 流式输出测试")
    print("="*50)
    
    try:
        await test_streaming_output()
    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
    except Exception as e:
        print(f"❌ 测试异常: {e}")
    
    print("\n🏁 测试完成")

if __name__ == "__main__":
    asyncio.run(main()) 