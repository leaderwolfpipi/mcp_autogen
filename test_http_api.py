#!/usr/bin/env python3
import requests
import json

def test_http_api():
    """测试HTTP API端点"""
    base_url = "http://localhost:8000"
    
    print("🔍 测试HTTP API端点...")
    
    # 测试根路径
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ 根路径: {response.status_code}")
    except Exception as e:
        print(f"❌ 根路径错误: {e}")
    
    # 测试API文档
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"✅ API文档: {response.status_code}")
    except Exception as e:
        print(f"❌ API文档错误: {e}")
    
    # 测试工具列表
    try:
        response = requests.get(f"{base_url}/tools")
        print(f"✅ 工具列表: {response.status_code}")
        if response.status_code == 200:
            tools = response.json()
            print(f"   发现 {len(tools.get('tools', []))} 个工具")
    except Exception as e:
        print(f"❌ 工具列表错误: {e}")
    
    # 测试任务执行（HTTP版本）
    try:
        payload = {
            "user_input": "请帮我翻译这段文字：Hello, how are you?",
            "input_data": None
        }
        response = requests.post(f"{base_url}/execute_task", json=payload)
        print(f"✅ 任务执行: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   执行结果: {result.get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ 任务执行错误: {e}")

if __name__ == "__main__":
    test_http_api() 