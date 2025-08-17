#!/usr/bin/env python3
"""
MCP双协议功能测试脚本
测试stdio和SSE协议的基本功能
"""

import asyncio
import json
import subprocess
import time
import sys
import os
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import aiohttp
    from core.protocol_adapter import ProtocolAdapter
    from core.mcp_adapter import MCPAdapter
    print("✅ 导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请先安装依赖: pip install -r requirements_mcp_protocols.txt")
    sys.exit(1)


class MCPProtocolTester:
    """MCP协议测试器"""
    
    def __init__(self):
        self.test_request = {
            "mcp_version": "1.0",
            "session_id": "test_session",
            "request_id": "test_001",
            "user_query": "这是一个测试请求",
            "context": {}
        }
    
    async def test_protocol_adapter(self):
        """测试协议适配器基本功能"""
        print("🔄 测试协议适配器...")
        
        try:
            # 创建MCP适配器
            mcp_adapter = MCPAdapter()
            
            # 创建协议适配器
            protocol_adapter = ProtocolAdapter(mcp_adapter)
            
            # 测试stdio请求处理
            response = await protocol_adapter.handle_stdio_request(self.test_request)
            print(f"✅ Stdio请求处理成功: {response.get('status', '未知状态')}")
            
            # 获取协议统计
            stats = protocol_adapter.get_protocol_stats()
            print(f"📊 协议统计: {stats}")
            
            return True
            
        except Exception as e:
            print(f"❌ 协议适配器测试失败: {e}")
            return False
    
    def test_stdio_server_import(self):
        """测试stdio服务器导入"""
        print("🔄 测试stdio服务器导入...")
        
        try:
            # 测试导入stdio服务器模块
            import mcp_stdio_server
            print("✅ Stdio服务器模块导入成功")
            return True
            
        except ImportError as e:
            print(f"❌ Stdio服务器模块导入失败: {e}")
            return False
    
    def test_stdio_server_version(self):
        """测试stdio服务器版本信息"""
        print("🔄 测试stdio服务器版本...")
        
        try:
            # 运行版本命令
            result = subprocess.run(
                [sys.executable, "mcp_stdio_server.py", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✅ Stdio服务器版本: {result.stdout.strip()}")
                return True
            else:
                print(f"❌ Stdio服务器版本获取失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Stdio服务器版本获取超时")
            return False
        except Exception as e:
            print(f"❌ Stdio服务器版本测试失败: {e}")
            return False
    
    async def test_stdio_request_response(self):
        """测试stdio请求响应"""
        print("🔄 测试stdio请求响应...")
        
        try:
            # 启动stdio服务器进程
            process = subprocess.Popen(
                [sys.executable, "mcp_stdio_server.py", "--log-level", "ERROR"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 发送测试请求
            request_json = json.dumps(self.test_request)
            process.stdin.write(request_json + "\n")
            process.stdin.flush()
            
            # 等待响应（最多5秒）
            try:
                stdout, stderr = process.communicate(timeout=5)
                
                if stdout.strip():
                    response = json.loads(stdout.strip())
                    print(f"✅ Stdio响应: {response.get('status', '未知状态')}")
                    return True
                else:
                    print(f"❌ Stdio无响应，错误: {stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                process.kill()
                print("❌ Stdio请求超时")
                return False
                
        except Exception as e:
            print(f"❌ Stdio请求响应测试失败: {e}")
            return False
    
    async def test_sse_api_import(self):
        """测试SSE API导入"""
        print("🔄 测试SSE API导入...")
        
        try:
            # 测试导入API模块
            from api import mcp_standard_api
            print("✅ SSE API模块导入成功")
            return True
            
        except ImportError as e:
            print(f"❌ SSE API模块导入失败: {e}")
            return False
    
    async def test_gateway_import(self):
        """测试网关导入"""
        print("🔄 测试协议网关导入...")
        
        try:
            import mcp_protocol_gateway
            print("✅ 协议网关模块导入成功")
            return True
            
        except ImportError as e:
            print(f"❌ 协议网关模块导入失败: {e}")
            return False
    
    def test_dependencies(self):
        """测试依赖包"""
        print("🔄 测试依赖包...")
        
        dependencies = [
            "fastapi",
            "uvicorn", 
            "sse_starlette",
            "aiohttp",
            "pydantic"
        ]
        
        missing_deps = []
        
        for dep in dependencies:
            try:
                __import__(dep)
                print(f"✅ {dep} 已安装")
            except ImportError:
                print(f"❌ {dep} 未安装")
                missing_deps.append(dep)
        
        if missing_deps:
            print(f"🔧 缺少依赖: {', '.join(missing_deps)}")
            print("请运行: pip install -r requirements_mcp_protocols.txt")
            return False
        
        return True
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始MCP双协议功能测试")
        print("=" * 50)
        
        tests = [
            ("依赖包检查", self.test_dependencies),
            ("协议适配器", self.test_protocol_adapter),
            ("Stdio服务器导入", self.test_stdio_server_import),
            ("Stdio服务器版本", self.test_stdio_server_version),
            ("Stdio请求响应", self.test_stdio_request_response),
            ("SSE API导入", self.test_sse_api_import),
            ("协议网关导入", self.test_gateway_import)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n📋 运行测试: {test_name}")
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ 测试 {test_name} 异常: {e}")
                results.append((test_name, False))
        
        # 输出测试结果摘要
        print("\n" + "=" * 50)
        print("📊 测试结果摘要:")
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n🎯 总计: {passed}/{total} 个测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！MCP双协议功能可用。")
            return True
        else:
            print("⚠️  部分测试失败，请检查配置和依赖。")
            return False


def create_demo_config():
    """创建演示配置文件"""
    config = {
        "llm": {
            "type": "openai",
            "model": "gpt-4-turbo", 
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "base_url": "https://api.openai.com/v1"
        },
        "tool_registry": {
            "auto_discover": True,
            "tool_paths": ["./tools"]
        },
        "server": {
            "max_sessions": 100,
            "execution_timeout": 300,
            "max_iterations": 10
        }
    }
    
    config_file = "demo_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"📄 演示配置文件已创建: {config_file}")
    return config_file


async def main():
    """主函数"""
    print("🎯 MCP双协议功能测试")
    print("本测试将验证stdio和SSE协议的基本功能")
    
    # 创建演示配置
    create_demo_config()
    
    # 运行测试
    tester = MCPProtocolTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🚀 快速开始指南:")
        print("1. 启动stdio服务器:")
        print("   python mcp_stdio_server.py --config demo_config.json")
        print()
        print("2. 启动SSE服务器:")
        print("   python -m uvicorn api.mcp_standard_api:app --port 8000")
        print()
        print("3. 测试网关:")
        print("   python mcp_protocol_gateway.py --stdio 'python mcp_stdio_server.py' --port 8001")
        print()
        print("4. 访问演示页面:")
        print("   http://localhost:8000/mcp/sse/demo")
    
    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n📋 测试被中断")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        sys.exit(1) 