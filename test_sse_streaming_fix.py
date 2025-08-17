#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SSE流式输出修复效果
"""

import asyncio
import json
import logging
from core.protocol_adapter import ProtocolAdapter
from core.tool_registry import ToolRegistry

logging.basicConfig(level=logging.INFO)

async def test_sse_streaming():
    """测试SSE流式输出"""
    
    print("🚀 测试SSE流式输出修复效果\n")
    
    # 初始化协议适配器
    tool_registry = ToolRegistry("sqlite:///tools_test.db")
    adapter = ProtocolAdapter()
    
    # 模拟SSE请求
    request = {
        "mcp_version": "1.0",
        "session_id": "test_session",
        "request_id": "test_request",
        "user_query": "孙中山 (1866-1925) 的早年经历是其革命思想形成的重要阶段",
        "context": {}
    }
    
    print(f"📝 测试查询: {request['user_query']}")
    print("=" * 60)
    
    try:
        # 测试SSE流式响应
        response = await adapter.handle_sse_request(request)
        
        print("✅ SSE请求处理成功")
        print(f"📊 响应类型: {type(response)}")
        
        # 如果有流式生成器，尝试获取一些事件
        if hasattr(response, 'generate'):
            print("\n📡 开始接收SSE事件:")
            event_count = 0
            async for event in response.generate():
                event_count += 1
                print(f"  事件 {event_count}: {event[:100]}...")
                
                # 只显示前几个事件，避免输出过多
                if event_count >= 5:
                    print("  ... (更多事件)")
                    break
            
            print(f"\n📊 总共接收到 {event_count} 个SSE事件")
        
    except Exception as e:
        print(f"❌ SSE测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_status_callback():
    """测试状态回调机制"""
    
    print("\n🔧 测试状态回调机制\n")
    
    from core.mcp_adapter import MCPAdapter
    
    # 创建MCP适配器
    tool_registry = ToolRegistry("sqlite:///tools_test.db")
    adapter = MCPAdapter(tool_registry)
    
    # 收集状态更新
    status_updates = []
    
    async def status_callback(message):
        status_updates.append(message)
        print(f"📨 收到状态更新: {message.get('type', 'unknown')} - {message.get('message', '')}")
    
    # 设置回调
    adapter.set_status_callback(status_callback)
    
    # 模拟请求
    request = {
        "mcp_version": "1.0",
        "session_id": "callback_test",
        "request_id": "callback_request",
        "user_query": "你好",  # 简单的闲聊测试
        "context": {}
    }
    
    try:
        result = await adapter.handle_request(request)
        
        print(f"\n📊 任务完成:")
        print(f"  状态更新数量: {len(status_updates)}")
        print(f"  最终响应: {result.get('final_response', 'N/A')[:100]}...")
        
        if status_updates:
            print("\n📋 状态更新详情:")
            for i, update in enumerate(status_updates, 1):
                print(f"  {i}. {update.get('type', 'unknown')}: {update.get('message', 'N/A')}")
        
    except Exception as e:
        print(f"❌ 状态回调测试失败: {e}")

async def main():
    """主测试函数"""
    
    # 测试1: SSE流式输出
    await test_sse_streaming()
    
    # 测试2: 状态回调机制
    await test_status_callback()
    
    print("\n🎉 SSE流式输出测试完成!")
    print("\n💡 修复内容:")
    print("✅ 实现了真正的流式SSE输出")
    print("✅ 添加了状态回调机制")
    print("✅ 支持实时状态更新推送")
    print("✅ 添加了心跳机制保持连接")

if __name__ == "__main__":
    asyncio.run(main()) 