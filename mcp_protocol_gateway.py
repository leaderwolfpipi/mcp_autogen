#!/usr/bin/env python3
"""
MCP协议转换网关
支持stdio和SSE协议之间的双向转换
类似于Supergateway的功能，但专门针对MCP协议
"""

import asyncio
import json
import logging
import os
import sys
import argparse
import aiohttp
import subprocess
from typing import Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from contextlib import asynccontextmanager
import uvicorn

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.protocol_adapter import ProtocolAdapter, TransportType


@dataclass
class GatewayConfig:
    """网关配置"""
    stdio_command: Optional[str] = None  # stdio服务器命令
    sse_url: Optional[str] = None        # SSE服务器URL
    port: int = 8000                     # 网关端口
    host: str = "localhost"              # 网关主机
    log_level: str = "INFO"              # 日志级别


class StdioToSSEGateway:
    """Stdio到SSE的协议转换网关"""
    
    def __init__(self, stdio_command: str):
        self.stdio_command = stdio_command
        self.logger = logging.getLogger(self.__class__.__name__)
        self.process: Optional[subprocess.Popen] = None
        
    async def start_stdio_process(self):
        """启动stdio进程"""
        try:
            self.process = subprocess.Popen(
                self.stdio_command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0  # 无缓冲
            )
            self.logger.info(f"✅ Stdio进程启动成功: {self.stdio_command}")
        except Exception as e:
            self.logger.error(f"❌ Stdio进程启动失败: {e}")
            raise
    
    async def send_to_stdio(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """发送请求到stdio进程并获取响应"""
        if not self.process:
            raise RuntimeError("Stdio进程未启动")
        
        try:
            # 发送请求
            request_json = json.dumps(request, ensure_ascii=False) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()
            
            # 读取响应
            response_line = self.process.stdout.readline()
            if not response_line:
                raise RuntimeError("从stdio进程读取响应失败")
            
            response = json.loads(response_line.strip())
            return response
            
        except Exception as e:
            self.logger.error(f"Stdio通信失败: {e}")
            raise
    
    async def create_sse_stream(self, request: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """创建SSE流，将stdio响应转换为SSE格式"""
        try:
            # 发送初始状态
            yield f"data: {json.dumps({'type': 'status', 'data': {'message': '正在处理请求...'}})}\n\n"
            
            # 调用stdio服务
            response = await self.send_to_stdio(request)
            
            # 发送结果
            yield f"data: {json.dumps({'type': 'result', 'data': response})}\n\n"
            
            # 发送完成状态
            yield f"data: {json.dumps({'type': 'status', 'data': {'message': '请求处理完成'}})}\n\n"
            
        except Exception as e:
            # 发送错误
            error_data = {
                'type': 'error',
                'data': {
                    'error': {
                        'code': 500,
                        'message': str(e)
                    }
                }
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    def stop(self):
        """停止stdio进程"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.logger.info("📋 Stdio进程已停止")


class SSEToStdioGateway:
    """SSE到Stdio的协议转换网关"""
    
    def __init__(self, sse_url: str):
        self.sse_url = sse_url
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def forward_to_sse(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """将请求转发到SSE服务器"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.sse_url,
                    json=request,
                    headers={
                        'Content-Type': 'application/json',
                        'Accept': 'text/event-stream'
                    }
                ) as response:
                    if response.status != 200:
                        raise RuntimeError(f"SSE服务器返回错误: {response.status}")
                    
                    # 读取SSE流并转换为单个响应
                    result_data = None
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            try:
                                event_data = json.loads(line_str[6:])
                                if event_data.get('type') == 'result':
                                    result_data = event_data.get('data')
                                    break
                            except json.JSONDecodeError:
                                continue
                    
                    if result_data is None:
                        raise RuntimeError("未从SSE服务器获取到有效结果")
                    
                    return result_data
                    
        except Exception as e:
            self.logger.error(f"SSE转发失败: {e}")
            raise
    
    async def process_stdio_requests(self):
        """处理stdin输入并转发到SSE服务器"""
        self.logger.info("🚀 开始处理stdio输入...")
        
        try:
            while True:
                # 从stdin读取请求
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line.strip():
                    continue
                
                try:
                    # 解析JSON请求
                    request = json.loads(line.strip())
                    
                    # 转发到SSE服务器
                    response = await self.forward_to_sse(request)
                    
                    # 输出响应到stdout
                    sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                    sys.stdout.flush()
                    
                except json.JSONDecodeError as e:
                    error_response = {
                        "status": "error",
                        "error": {
                            "code": 400,
                            "message": f"Invalid JSON: {str(e)}"
                        }
                    }
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()
                    
                except Exception as e:
                    error_response = {
                        "status": "error", 
                        "error": {
                            "code": 500,
                            "message": str(e)
                        }
                    }
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()
                    
        except KeyboardInterrupt:
            self.logger.info("📋 接收到停止信号")


class MCPProtocolGateway:
    """MCP协议转换网关主类"""
    
    def __init__(self, config: GatewayConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化转换器
        self.stdio_to_sse = None
        self.sse_to_stdio = None
        
        if config.stdio_command:
            self.stdio_to_sse = StdioToSSEGateway(config.stdio_command)
        
        if config.sse_url:
            self.sse_to_stdio = SSEToStdioGateway(config.sse_url)
    
    async def create_fastapi_app(self) -> FastAPI:
        """创建FastAPI应用（用于stdio到SSE转换）"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # 启动时初始化
            if self.stdio_to_sse:
                await self.stdio_to_sse.start_stdio_process()
                self.logger.info("🔄 Stdio到SSE网关已启动")
            
            yield
            
            # 关闭时清理
            if self.stdio_to_sse:
                self.stdio_to_sse.stop()
                self.logger.info("🛑 Stdio到SSE网关已关闭")
        
        app = FastAPI(
            title="MCP协议转换网关",
            description="支持stdio和SSE协议之间的双向转换",
            version="1.0.0",
            lifespan=lifespan
        )
        
        @app.get("/")
        async def gateway_info():
            """网关信息"""
            return {
                "service": "MCP协议转换网关",
                "version": "1.0.0",
                "config": {
                    "stdio_command": self.config.stdio_command,
                    "sse_url": self.config.sse_url,
                    "port": self.config.port,
                    "host": self.config.host
                },
                "endpoints": {
                    "sse": "/sse" if self.stdio_to_sse else None,
                    "stdio_mode": "Available via CLI" if self.sse_to_stdio else None
                },
                "status": "running"
            }
        
        @app.post("/sse")
        async def stdio_to_sse_endpoint(request: Request) -> EventSourceResponse:
            """将stdio服务转换为SSE端点"""
            if not self.stdio_to_sse:
                raise HTTPException(status_code=404, detail="Stdio到SSE转换未配置")
            
            try:
                # 解析请求
                request_data = await request.json()
                
                # 创建SSE流
                stream = self.stdio_to_sse.create_sse_stream(request_data)
                return EventSourceResponse(stream)
                
            except Exception as e:
                self.logger.error(f"SSE端点处理失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/health")
        async def health_check():
            """健康检查"""
            stdio_status = "running" if self.stdio_to_sse and self.stdio_to_sse.process else "not_configured"
            sse_status = "configured" if self.sse_to_stdio else "not_configured"
            
            return {
                "status": "healthy",
                "stdio_gateway": stdio_status,
                "sse_gateway": sse_status
            }
        
        return app
    
    async def run_stdio_mode(self):
        """运行stdio模式（SSE到stdio转换）"""
        if not self.sse_to_stdio:
            raise RuntimeError("SSE到stdio转换未配置")
        
        self.logger.info("🚀 启动SSE到stdio转换模式")
        await self.sse_to_stdio.process_stdio_requests()
    
    async def run_sse_mode(self):
        """运行SSE模式（stdio到SSE转换）"""
        if not self.stdio_to_sse:
            raise RuntimeError("Stdio到SSE转换未配置")
        
        app = await self.create_fastapi_app()
        
        config = uvicorn.Config(
            app,
            host=self.config.host,
            port=self.config.port,
            log_level=self.config.log_level.lower()
        )
        
        server = uvicorn.Server(config)
        self.logger.info(f"🌐 SSE网关启动在 http://{self.config.host}:{self.config.port}")
        await server.serve()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MCP协议转换网关")
    parser.add_argument("--stdio", type=str, help="Stdio服务器命令")
    parser.add_argument("--sse", type=str, help="SSE服务器URL")
    parser.add_argument("--port", type=int, default=8000, help="网关端口")
    parser.add_argument("--host", type=str, default="localhost", help="网关主机")
    parser.add_argument("--log-level", type=str, default="INFO", help="日志级别")
    parser.add_argument("--mode", type=str, choices=["sse", "stdio"], 
                       help="运行模式: sse(将stdio转为SSE) 或 stdio(将SSE转为stdio)")
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建配置
    config = GatewayConfig(
        stdio_command=args.stdio,
        sse_url=args.sse,
        port=args.port,
        host=args.host,
        log_level=args.log_level
    )
    
    # 创建网关
    gateway = MCPProtocolGateway(config)
    
    try:
        if args.mode == "stdio" or (not args.mode and args.sse):
            # stdio模式：将SSE转换为stdio
            asyncio.run(gateway.run_stdio_mode())
        elif args.mode == "sse" or (not args.mode and args.stdio):
            # SSE模式：将stdio转换为SSE
            asyncio.run(gateway.run_sse_mode())
        else:
            print("❌ 请指定--stdio或--sse参数，以及相应的运行模式")
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n📋 网关已停止")
    except Exception as e:
        print(f"❌ 网关运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 