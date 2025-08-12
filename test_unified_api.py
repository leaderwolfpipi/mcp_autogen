#!/usr/bin/env python3
"""
测试新的统一接口
"""

import requests
import json
import time

def test_http_streaming():
    """测试HTTP流式接口"""
    print("🌐 测试HTTP流式接口")
    print("=" * 50)
    
    url = "http://localhost:8000/execute_task"
    payload = {
        "user_input": "请帮我翻译这段文字：Hello, how are you?",
        "input_data": None
    }
    
    try:
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode('utf-8'))
                print(f"[{data['status']}] {data['step']}: {data['message']}")
                
                if data['status'] in ['success', 'error']:
                    break
                    
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_websocket():
    """测试WebSocket接口"""
    print("\n🔌 测试WebSocket接口")
    print("=" * 50)
    
    try:
        import websockets
        import asyncio
        
        async def ws_test():
            uri = "ws://localhost:8000/ws/execute_task"
            async with websockets.connect(uri) as websocket:
                payload = {
                    "user_input": "请帮我翻译这段文字：Hello, how are you?",
                    "input_data": None
                }
                
                await websocket.send(json.dumps(payload))
                print("✅ WebSocket连接成功，任务已发送")
                
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"[{data['status']}] {data['step']}: {data['message']}")
                    
                    if data['status'] in ['success', 'error']:
                        break
        
        asyncio.run(ws_test())
        
    except ImportError:
        print("❌ 需要安装websockets库: pip install websockets")
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")

def test_demo_page():
    """测试演示页面"""
    print("\n🌍 测试演示页面")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ 演示页面访问成功")
            print("📝 页面内容长度:", len(response.text))
        else:
            print(f"❌ 演示页面访问失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 演示页面测试失败: {e}")

def main():
    """主测试函数"""
    print("🎯 MCP AutoGen 统一接口测试")
    print("=" * 60)
    
    # 等待服务启动
    print("⏳ 等待服务启动...")
    time.sleep(2)
    
    # 测试HTTP流式接口
    test_http_streaming()
    
    # 测试WebSocket接口
    test_websocket()
    
    # 测试演示页面
    test_demo_page()
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    main() 