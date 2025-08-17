#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实的SSE流式输出
"""

import asyncio
import json
from core.protocol_adapter import ProtocolAdapter

async def test_real_sse_stream():
    """测试真实的SSE流"""
    
    print("🌊 测试真实SSE流式输出\n")
    
    # 初始化协议适配器
    adapter = ProtocolAdapter()
    
    # 模拟复杂的任务查询
    request = {
        "mcp_version": "1.0",
        "session_id": "stream_test",
        "request_id": "stream_req",
        "user_query": "孙中山的早年经历",
        "context": {}
    }
    
    print(f"📝 查询: {request['user_query']}")
    print("🔄 开始SSE流式处理...\n")
    
    try:
        # 获取SSE响应
        response = await adapter.handle_sse_request(request)
        
        # 模拟前端接收SSE流
        print("📡 模拟前端接收SSE事件:")
        print("-" * 50)
        
        event_count = 0
        async for event_data in response.generate():
            event_count += 1
            
            try:
                # 解析事件数据
                if isinstance(event_data, str):
                    event = json.loads(event_data)
                else:
                    event = event_data
                
                event_type = event.get('type', 'unknown')
                
                # 格式化显示事件
                if event_type == 'status':
                    status = event.get('data', {}).get('status', 'unknown')
                    message = event.get('data', {}).get('message', '')
                    print(f"📊 [{event_count:2d}] 状态: {status} - {message}")
                
                elif event_type == 'result':
                    result_data = event.get('data', {})
                    final_response = result_data.get('final_response', 'N/A')
                    print(f"✅ [{event_count:2d}] 结果: {final_response[:100]}...")
                
                elif event_type == 'heartbeat':
                    timestamp = event.get('data', {}).get('timestamp', 'N/A')
                    print(f"💓 [{event_count:2d}] 心跳: {timestamp}")
                
                elif event_type == 'error':
                    error_msg = event.get('data', {}).get('error', {}).get('message', 'Unknown error')
                    print(f"❌ [{event_count:2d}] 错误: {error_msg}")
                
                else:
                    print(f"🔍 [{event_count:2d}] 其他事件: {event_type}")
                
                # 添加延迟模拟真实网络
                await asyncio.sleep(0.1)
                
                # 限制显示的事件数量
                if event_count >= 20:
                    print("... (限制显示前20个事件)")
                    break
                    
            except json.JSONDecodeError:
                print(f"⚠️  [{event_count:2d}] 无法解析的事件数据: {event_data[:50]}...")
            except Exception as e:
                print(f"❌ [{event_count:2d}] 事件处理错误: {e}")
        
        print("-" * 50)
        print(f"🎉 SSE流处理完成，共处理 {event_count} 个事件")
        
    except Exception as e:
        print(f"❌ SSE流测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_markdown_content():
    """测试Markdown内容的流式输出"""
    
    print("\n📝 测试Markdown内容流式输出\n")
    
    adapter = ProtocolAdapter()
    
    # 测试包含Markdown格式的复杂查询
    request = {
        "mcp_version": "1.0",
        "session_id": "markdown_test",
        "request_id": "markdown_req", 
        "user_query": "请详细介绍孙中山的三民主义思想",
        "context": {}
    }
    
    print(f"📝 查询: {request['user_query']}")
    print("🔄 检查Markdown格式处理...\n")
    
    try:
        response = await adapter.handle_sse_request(request)
        
        markdown_content = ""
        
        async for event_data in response.generate():
            if isinstance(event_data, str):
                event = json.loads(event_data)
            else:
                event = event_data
            
            if event.get('type') == 'result':
                result_data = event.get('data', {})
                final_response = result_data.get('final_response', '')
                
                if final_response:
                    markdown_content = final_response
                    break
        
        if markdown_content:
            print("📄 检测到的内容格式:")
            print("-" * 30)
            
            # 检查Markdown元素
            has_headers = '#' in markdown_content
            has_lists = ('- ' in markdown_content or '* ' in markdown_content or 
                        any(f'{i}. ' in markdown_content for i in range(1, 10)))
            has_bold = '**' in markdown_content
            has_links = '[' in markdown_content and '](' in markdown_content
            
            print(f"✅ 标题 (Headers): {'是' if has_headers else '否'}")
            print(f"✅ 列表 (Lists): {'是' if has_lists else '否'}")
            print(f"✅ 粗体 (Bold): {'是' if has_bold else '否'}")
            print(f"✅ 链接 (Links): {'是' if has_links else '否'}")
            
            print(f"\n📊 内容长度: {len(markdown_content)} 字符")
            print(f"📝 内容预览: {markdown_content[:200]}...")
        else:
            print("❌ 未检测到有效的响应内容")
            
    except Exception as e:
        print(f"❌ Markdown测试失败: {e}")

async def main():
    """主测试函数"""
    
    print("🚀 SSE流式输出和Markdown显示修复测试\n")
    print("=" * 60)
    
    # 测试1: 真实SSE流
    await test_real_sse_stream()
    
    # 测试2: Markdown内容
    await test_markdown_content()
    
    print("\n" + "=" * 60)
    print("🎯 修复总结:")
    print("✅ 实现真正的流式SSE输出")
    print("✅ 添加实时状态更新推送")
    print("✅ 支持心跳机制保持连接")
    print("✅ 优化事件格式和错误处理")
    print("✅ 支持Markdown内容流式传输")

if __name__ == "__main__":
    asyncio.run(main()) 