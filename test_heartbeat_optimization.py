#!/usr/bin/env python3
"""
心跳优化测试脚本
测试修复后的心跳频率是否合理
"""

import asyncio
import json
import aiohttp
import time
from datetime import datetime

async def test_heartbeat_frequency():
    """测试心跳频率"""
    
    print("🫀 心跳优化测试开始...")
    print("=" * 60)
    
    # 测试数据
    test_request = {
        "mcp_version": "1.0",
        "session_id": f"heartbeat_test_{int(time.time())}",
        "request_id": f"heartbeat_req_{int(time.time())}",
        "user_query": "你好，请简单介绍一下你自己",
        "context": {}
    }
    
    url = "http://localhost:8000/mcp/sse"
    
    print(f"📤 发送请求到: {url}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%H:%M:%S')}")
    print("\n" + "=" * 60)
    print("📊 心跳事件监控（预期间隔：5秒）...")
    print("=" * 60)
    
    event_count = 0
    heartbeat_count = 0
    chat_streaming_count = 0
    start_time = time.time()
    heartbeat_timestamps = []
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=test_request) as response:
                print(f"🌐 HTTP状态码: {response.status}")
                
                if response.status != 200:
                    print(f"❌ HTTP错误: {response.status}")
                    return
                
                # 解析SSE流
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    
                    if not line_str:
                        continue
                    
                    if line_str.startswith('data: '):
                        event_count += 1
                        data_str = line_str[6:]
                        
                        try:
                            event_data = json.loads(data_str)
                            event_type = event_data.get('type', 'unknown')
                            current_time = time.time()
                            elapsed = current_time - start_time
                            
                            if event_type == 'heartbeat':
                                heartbeat_count += 1
                                heartbeat_timestamps.append(current_time)
                                
                                # 计算与上次心跳的间隔
                                interval = ""
                                if len(heartbeat_timestamps) > 1:
                                    interval = f" (间隔: {current_time - heartbeat_timestamps[-2]:.1f}s)"
                                
                                print(f"💓 心跳 #{heartbeat_count} @ {elapsed:.1f}s{interval}")
                            
                            elif event_type == 'status':
                                status_data = event_data.get('data', {})
                                status_type = status_data.get('type', '')
                                
                                if status_type == 'chat_streaming':
                                    chat_streaming_count += 1
                                    accumulated = status_data.get('accumulated_content', '')
                                    print(f"💬 流式内容 #{chat_streaming_count} @ {elapsed:.1f}s: {repr(accumulated[:20])}...")
                                else:
                                    print(f"📊 状态事件 @ {elapsed:.1f}s: {status_data.get('message', 'unknown')[:30]}...")
                            
                            elif event_type == 'result':
                                print(f"🏁 任务完成 @ {elapsed:.1f}s")
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"   ❌ JSON解析失败: {e}")
                    
                    # 限制测试时间，避免无限等待
                    if time.time() - start_time > 30:  # 30秒超时
                        print("⏰ 测试超时，停止监控")
                        break
                        
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    print("\n" + "=" * 60)
    print("📊 心跳统计分析:")
    print(f"   总事件数: {event_count}")
    print(f"   心跳事件数: {heartbeat_count}")
    print(f"   流式内容数: {chat_streaming_count}")
    print(f"   测试时长: {time.time() - start_time:.1f}秒")
    
    # 分析心跳间隔
    if len(heartbeat_timestamps) > 1:
        intervals = []
        for i in range(1, len(heartbeat_timestamps)):
            interval = heartbeat_timestamps[i] - heartbeat_timestamps[i-1]
            intervals.append(interval)
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            min_interval = min(intervals)
            max_interval = max(intervals)
            
            print(f"   平均心跳间隔: {avg_interval:.1f}秒")
            print(f"   最小心跳间隔: {min_interval:.1f}秒")
            print(f"   最大心跳间隔: {max_interval:.1f}秒")
            
            # 评估优化效果
            if avg_interval >= 4.5:  # 接近5秒目标
                print("   ✅ 心跳频率优化成功 - 间隔合理")
            elif avg_interval >= 2.0:
                print("   ⚠️ 心跳频率有所改善 - 仍可进一步优化")
            else:
                print("   ❌ 心跳频率仍然过高 - 需要进一步调整")
    
    print("=" * 60)

async def main():
    await test_heartbeat_frequency()

if __name__ == "__main__":
    asyncio.run(main()) 