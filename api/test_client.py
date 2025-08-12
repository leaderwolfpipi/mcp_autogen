#!/usr/bin/env python3
"""
测试客户端 - 演示新的统一接口使用
支持HTTP流式响应和WebSocket两种方式
"""

import asyncio
import json
import requests
import websockets
import time
from typing import Dict, Any

class MCPAutoGenClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws")
    
    def execute_task_http(self, user_input: str, input_data: Any = None) -> None:
        """
        使用HTTP流式响应执行任务
        """
        print(f"🚀 开始执行任务 (HTTP流式): {user_input}")
        print("=" * 60)
        
        url = f"{self.base_url}/execute_task"
        payload = {
            "user_input": user_input,
            "input_data": input_data
        }
        
        try:
            response = requests.post(url, json=payload, stream=True)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8'))
                    self._print_progress(data)
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTP请求失败: {e}")
    
    async def execute_task_websocket(self, user_input: str, input_data: Any = None) -> None:
        """
        使用WebSocket执行任务
        """
        print(f"🚀 开始执行任务 (WebSocket): {user_input}")
        print("=" * 60)
        
        url = f"{self.ws_url}/ws/execute_task"
        payload = {
            "user_input": user_input,
            "input_data": input_data
        }
        
        try:
            async with websockets.connect(url) as websocket:
                # 发送任务请求
                await websocket.send(json.dumps(payload))
                
                # 接收流式响应
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        self._print_progress(data)
                        
                        # 如果任务完成或失败，退出循环
                        if data["status"] in ["success", "error"]:
                            break
                            
                    except websockets.exceptions.ConnectionClosed:
                        print("❌ WebSocket连接已关闭")
                        break
                        
        except Exception as e:
            print(f"❌ WebSocket连接失败: {e}")
    
    def _print_progress(self, data: Dict[str, Any]) -> None:
        """
        打印进度信息
        """
        status = data["status"]
        step = data["step"]
        message = data["message"]
        
        # 状态图标
        status_icons = {
            "progress": "⏳",
            "success": "✅",
            "error": "❌"
        }
        
        icon = status_icons.get(status, "ℹ️")
        
        # 步骤名称映射
        step_names = {
            "import_tools": "导入工具",
            "parse_requirement": "解析需求",
            "requirement_parsed": "需求解析完成",
            "decide_tools": "决策工具",
            "tools_decided": "工具决策完成",
            "generate_tools": "生成工具",
            "generating_tool": "生成工具中",
            "tool_generated": "工具生成完成",
            "tool_registered": "工具注册完成",
            "tools_redecided": "重新决策完成",
            "compose_pipeline": "生成流水线",
            "pipeline_composed": "流水线生成完成",
            "execute_pipeline": "执行流水线",
            "pipeline_executed": "流水线执行完成",
            "validate_result": "验证结果",
            "completed": "任务完成",
            "failed": "任务失败"
        }
        
        step_name = step_names.get(step, step)
        
        # 打印格式化的进度信息
        print(f"{icon} [{step_name}] {message}")
        
        # 如果有数据，显示摘要
        if data.get("data"):
            if isinstance(data["data"], dict):
                if "result" in data["data"]:
                    result = data["data"]["result"]
                    if isinstance(result, dict) and "result" in result:
                        print(f"   📊 结果: {str(result['result'])[:100]}...")
                elif "pipeline" in data["data"]:
                    pipeline = data["data"]["pipeline"]
                    if "pipeline" in pipeline:
                        tools = [step["tool"] for step in pipeline["pipeline"]]
                        print(f"   🔧 流水线: {' -> '.join(tools)}")
        
        print()

def main():
    """主函数 - 演示两种接口的使用"""
    client = MCPAutoGenClient()
    
    # 测试用例
    test_cases = [
        {
            "name": "文本翻译任务",
            "input": "请帮我翻译这段文字：Hello, how are you?",
            "data": None
        },
        {
            "name": "图片处理任务", 
            "input": "请帮我处理这张图片，提取其中的文字并翻译成中文",
            "data": None
        }
    ]
    
    print("🎯 MCP AutoGen 统一接口测试")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试用例 {i}: {test_case['name']}")
        print("-" * 40)
        
        # HTTP流式测试
        print("🌐 HTTP流式响应测试:")
        client.execute_task_http(test_case["input"], test_case["data"])
        
        print("\n" + "="*60 + "\n")
        
        # WebSocket测试
        print("🔌 WebSocket测试:")
        asyncio.run(client.execute_task_websocket(test_case["input"], test_case["data"]))
        
        if i < len(test_cases):
            print("\n" + "="*60)
            time.sleep(2)  # 测试间隔

if __name__ == "__main__":
    main() 