#!/usr/bin/env python3
"""
调试StreamingMCPEngine
"""
import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.mcp_standard_api import StreamingMCPEngine
from core.mcp_adapter import MCPAdapter

async def debug_streaming():
    """调试流式引擎"""
    print("🔍 开始调试StreamingMCPEngine")
    
    # 初始化MCP适配器
    mcp_adapter = MCPAdapter(tool_registry=None, max_sessions=1000)
    
    # 初始化流式引擎
    llm_config = {
        "type": "openai",
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": os.getenv("OPENAI_MODEL", "gpt-4-turbo"),
        "base_url": os.getenv("OPENAI_BASE_URL")
    }
    
    streaming_engine = StreamingMCPEngine(llm_config=llm_config, mcp_adapter=mcp_adapter)
    
    print("✅ StreamingMCPEngine初始化完成")
    
    # 测试对话
    user_input = "搜索张良的资料"
    session_id = "debug_session"
    
    print(f"📤 发送测试查询: {user_input}")
    
    message_count = 0
    async for result in streaming_engine.execute_streaming_conversation(user_input, session_id):
        message_count += 1
        print(f"📨 [{message_count}] {result.get('type', 'unknown'):15s} - {result.get('message', '')[:50]}...")
        
        if result.get('type') in ['task_complete', 'error']:
            print(f"✅ 收到最终状态: {result.get('type')}")
            break
    
    print(f"📊 总共收到 {message_count} 条消息")

if __name__ == "__main__":
    asyncio.run(debug_streaming()) 