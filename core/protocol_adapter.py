#!/usr/bin/env python3
"""
MCP协议传输适配器
支持stdio和SSE两种传输协议的统一适配层
"""

import asyncio
import json
import logging
import sys
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator, Callable
from enum import Enum
from dataclasses import dataclass
from fastapi import Request, Response
from sse_starlette.sse import EventSourceResponse
import time

from .mcp_adapter import MCPAdapter


class TransportType(Enum):
    """传输协议类型"""
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"
    WEBSOCKET = "websocket"


# 🎯 新增：心跳配置
@dataclass
class HeartbeatConfig:
    """心跳配置"""
    enabled: bool = True
    interval: float = 5.0  # 心跳间隔（秒）
    max_count: int = 60    # 最大心跳次数
    timeout: float = 1.0   # 等待超时（秒）


@dataclass
class ProtocolContext:
    """协议上下文"""
    transport_type: TransportType
    session_id: str
    request_id: str
    connection_info: Dict[str, Any]


class BaseTransportHandler(ABC):
    """传输协议处理器基类"""
    
    def __init__(self, mcp_adapter: MCPAdapter):
        self.mcp_adapter = mcp_adapter
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def handle_request(self, request: Any, context: ProtocolContext) -> Any:
        """处理请求"""
        pass
    
    @abstractmethod
    async def send_response(self, response: Dict[str, Any], context: ProtocolContext) -> None:
        """发送响应"""
        pass


class StdioTransportHandler(BaseTransportHandler):
    """Stdio传输协议处理器"""
    
    def __init__(self, mcp_adapter: MCPAdapter):
        super().__init__(mcp_adapter)
        self.running = False
        
    async def handle_request(self, request: Dict[str, Any], context: ProtocolContext) -> Dict[str, Any]:
        """处理stdio请求"""
        try:
            # 确保请求格式符合MCP标准
            mcp_request = {
                "mcp_version": request.get("mcp_version", "1.0"),
                "session_id": context.session_id,
                "request_id": context.request_id,
                "user_query": request.get("user_query", ""),
                "context": request.get("context", {})
            }
            
            # 调用MCP适配器处理
            response = await self.mcp_adapter.handle_request(mcp_request)
            return response
            
        except Exception as e:
            self.logger.error(f"Stdio请求处理失败: {e}")
            return {
                "mcp_version": "1.0",
                "session_id": context.session_id,
                "request_id": context.request_id,
                "status": "error",
                "error": {
                    "code": 500,
                    "message": str(e)
                }
            }
    
    async def send_response(self, response: Dict[str, Any], context: ProtocolContext) -> None:
        """发送stdio响应"""
        try:
            # 将响应写入stdout，符合JSON-RPC 2.0格式
            json_response = json.dumps(response, ensure_ascii=False)
            sys.stdout.write(json_response + "\n")
            sys.stdout.flush()
        except Exception as e:
            self.logger.error(f"Stdio响应发送失败: {e}")
    
    async def start_stdio_server(self):
        """启动stdio服务器"""
        self.running = True
        self.logger.info("🚀 Stdio服务器启动，等待输入...")
        
        try:
            while self.running:
                # 从stdin读取一行
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line.strip():
                    continue
                
                try:
                    # 解析JSON请求
                    request = json.loads(line.strip())
                    
                    # 创建协议上下文
                    context = ProtocolContext(
                        transport_type=TransportType.STDIO,
                        session_id=request.get("session_id", str(uuid.uuid4())),
                        request_id=request.get("request_id", str(uuid.uuid4())),
                        connection_info={"source": "stdio"}
                    )
                    
                    # 处理请求
                    response = await self.handle_request(request, context)
                    
                    # 发送响应
                    await self.send_response(response, context)
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON解析失败: {e}")
                    error_response = {
                        "mcp_version": "1.0",
                        "status": "error",
                        "error": {
                            "code": 400,
                            "message": f"Invalid JSON: {str(e)}"
                        }
                    }
                    await self.send_response(error_response, context)
                    
                except Exception as e:
                    self.logger.error(f"请求处理失败: {e}")
                    error_response = {
                        "mcp_version": "1.0",
                        "status": "error",
                        "error": {
                            "code": 500,
                            "message": str(e)
                        }
                    }
                    await self.send_response(error_response, context)
                    
        except KeyboardInterrupt:
            self.logger.info("📋 接收到停止信号，关闭stdio服务器")
        finally:
            self.running = False
    
    def stop(self):
        """停止stdio服务器"""
        self.running = False


class SSETransportHandler(BaseTransportHandler):
    """SSE传输协议处理器"""
    
    def __init__(self, mcp_adapter: MCPAdapter, heartbeat_config: HeartbeatConfig = None):
        super().__init__(mcp_adapter)
        self.heartbeat_config = heartbeat_config or HeartbeatConfig(
            enabled=True,
            interval=5.0,  # 默认5秒间隔
            max_count=60,
            timeout=1.0
        )
        self.active_connections: Dict[str, Any] = {}
    
    async def handle_request(self, request: Dict[str, Any], context: ProtocolContext) -> AsyncGenerator[Dict[str, Any], None]:
        """处理SSE请求 - 真正的流式响应"""
        try:
            # 规范化请求
            mcp_request = {
                "mcp_version": request.get("mcp_version", "1.0"),
                "session_id": context.session_id,
                "request_id": context.request_id,
                "user_query": request.get("user_query", ""),
                "context": request.get("context", {})
            }

            # 初始状态事件
            yield {
                "type": "status",
                "data": {
                    "session_id": context.session_id,
                    "status": "processing",
                    "message": "开始处理请求..."
                }
            }

            import asyncio
            status_queue: asyncio.Queue = asyncio.Queue()

            async def status_callback(message):
                # 将外部回调送入内部队列，支持 str/dict
                if isinstance(message, dict):
                    await status_queue.put({"type": "status", "data": message})
                else:
                    await status_queue.put({"type": "status", "data": {"message": str(message)}})

            async def process_with_callback():
                try:
                    if hasattr(self.mcp_adapter, "set_status_callback"):
                        self.mcp_adapter.set_status_callback(status_callback)

                    # 后端实际处理
                    response = await self.mcp_adapter.handle_request(mcp_request)

                    # 发送最终结果
                    await status_queue.put({"type": "final_result", "data": response})
                except Exception as e:
                    await status_queue.put({"type": "error", "error": str(e)})
                finally:
                    # 通知主循环结束
                    await status_queue.put({"type": "done"})

            # 启动处理任务
            process_task = asyncio.create_task(process_with_callback())

            heartbeat_counter = 0
            max_heartbeats = self.heartbeat_config.max_count
            heartbeat_interval = self.heartbeat_config.interval
            last_heartbeat_time = time.time()

            while True:
                try:
                    message = await asyncio.wait_for(status_queue.get(), timeout=self.heartbeat_config.timeout)
                except asyncio.TimeoutError:
                    # 🎯 优化：只在启用心跳且需要时发送，降低频率
                    if not self.heartbeat_config.enabled:
                        continue
                        
                    current_time = time.time()
                    time_since_last_heartbeat = current_time - last_heartbeat_time
                    
                    heartbeat_counter += 1
                    # 只有超过心跳间隔时间且未超过最大次数时才发送心跳
                    if heartbeat_counter <= max_heartbeats and time_since_last_heartbeat >= heartbeat_interval:
                        yield {
                            "type": "heartbeat",
                            "data": {
                                "session_id": context.session_id,
                                "timestamp": int(current_time * 1000)
                            }
                        }
                        last_heartbeat_time = current_time
                        print(f"🫀 发送心跳 #{heartbeat_counter}/{max_heartbeats} (间隔: {heartbeat_interval}s)")
                    continue

                msg_type = message.get("type")
                if msg_type == "done":
                    self.logger.info(f"SSE处理完成，会话ID: {context.session_id}")
                    break
                elif msg_type == "final_result":
                    self.logger.info(f"发送最终结果，会话ID: {context.session_id}")
                    yield {
                        "type": "result",
                        "data": message["data"]
                    }
                elif msg_type == "error":
                    yield {
                        "type": "error",
                        "data": {
                            "message": message.get("error", "未知错误")
                        }
                    }
                else:
                    # 透传状态更新，保持原始格式
                    original_data = message.get("data", {})
                    msg_type = message.get("type")
                    
                    # 🎯 关键修复：检查嵌套的事件类型
                    nested_type = original_data.get("type", "")
                    
                    # 如果是status事件且嵌套了chat_streaming或task_streaming，直接透传
                    if msg_type == "status" and nested_type in ["chat_streaming", "task_streaming"]:
                        yield {
                            "type": "status",
                            "data": {
                                "type": nested_type,
                                "partial_content": original_data.get("partial_content", ""),
                                "accumulated_content": original_data.get("accumulated_content", ""),
                                "message": original_data.get("message", "")
                            }
                        }
                    # 如果是直接的chat_streaming或task_streaming事件
                    elif msg_type in ["chat_streaming", "task_streaming"]:
                        yield {
                            "type": "status",
                            "data": {
                                "type": msg_type,
                                "partial_content": original_data.get("partial_content", ""),
                                "accumulated_content": original_data.get("accumulated_content", ""),
                                "message": original_data.get("message", "")
                            }
                        }
                    else:
                        # 其他状态更新保持兼容格式
                        yield {
                            "type": "status",
                            "data": {
                                "session_id": context.session_id,
                                "status": "processing",
                                "message": original_data.get("message", "处理中...")
                            }
                        }

            # 等待处理任务收尾
            try:
                await asyncio.gather(process_task, return_exceptions=True)
            except Exception:
                pass

            # 完成状态
            yield {
                "type": "status",
                "data": {
                    "session_id": context.session_id,
                    "status": "completed",
                    "message": "处理完成"
                }
            }

        except Exception as e:
            self.logger.error(f"SSE请求处理失败: {e}")
            yield {
                "type": "error",
                "data": {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            }
    
    async def send_response(self, response: Dict[str, Any], context: ProtocolContext) -> None:
        """SSE不需要单独的发送响应方法，通过生成器流式发送"""
        pass
    
    async def create_sse_stream(self, request: Dict[str, Any], session_id: str = None) -> AsyncGenerator[str, None]:
        """创建SSE事件流"""
        context = ProtocolContext(
            transport_type=TransportType.SSE,
            session_id=session_id or str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            connection_info={"source": "sse"}
        )
        
        # 添加连接到活跃连接列表
        self.active_connections[context.session_id] = context
        
        try:
            async for event in self.handle_request(request, context):
                # 添加调试日志 - 改为info级别
                self.logger.info(f"SSE事件类型: {type(event)}, 内容前100字符: {repr(str(event)[:100])}")
                
                # 直接yield JSON字符串，让EventSourceResponse处理SSE格式
                if isinstance(event, dict):
                    event_data = json.dumps(event, ensure_ascii=False)
                    yield event_data
                else:
                    # 如果是其他格式，尝试转换
                    self.logger.warning(f"非字典格式的SSE事件: {type(event)}, {repr(event)}")
                    yield str(event)
                
        except Exception as e:
            self.logger.error(f"SSE流生成失败: {e}")
            error_event = {
                "type": "error",
                "data": {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            }
            yield json.dumps(error_event)
        finally:
            # 移除连接
            if context.session_id in self.active_connections:
                del self.active_connections[context.session_id]
    
    def get_active_connections(self) -> Dict[str, Any]:
        """获取活跃连接"""
        return self.active_connections


class ProtocolAdapter:
    """MCP协议适配器 - 支持多种传输协议"""
    
    def __init__(self, mcp_adapter: MCPAdapter = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化MCP适配器
        self.mcp_adapter = mcp_adapter or MCPAdapter()
        
        # 初始化传输处理器
        self.stdio_handler = StdioTransportHandler(self.mcp_adapter)
        self.sse_handler = SSETransportHandler(self.mcp_adapter)
        
        self.logger.info("🔄 协议适配器初始化完成")
    
    def detect_protocol(self, request: Any) -> TransportType:
        """自动检测协议类型"""
        if isinstance(request, Request):
            # 检查是否是SSE请求
            accept_header = request.headers.get("accept", "")
            if "text/event-stream" in accept_header:
                return TransportType.SSE
            else:
                return TransportType.HTTP
        elif isinstance(request, dict):
            # 来自stdin的JSON请求
            return TransportType.STDIO
        else:
            return TransportType.HTTP
    
    async def handle_stdio_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理stdio请求"""
        context = ProtocolContext(
            transport_type=TransportType.STDIO,
            session_id=request.get("session_id", str(uuid.uuid4())),
            request_id=request.get("request_id", str(uuid.uuid4())),
            connection_info={"source": "stdio"}
        )
        
        return await self.stdio_handler.handle_request(request, context)
    
    async def handle_sse_request(self, request: Dict[str, Any], session_id: str = None) -> EventSourceResponse:
        """处理SSE请求"""
        stream = self.sse_handler.create_sse_stream(request, session_id)
        return EventSourceResponse(stream)
    
    async def start_stdio_server(self):
        """启动stdio服务器"""
        await self.stdio_handler.start_stdio_server()
    
    def stop_stdio_server(self):
        """停止stdio服务器"""
        self.stdio_handler.stop()
    
    def get_sse_connections(self) -> Dict[str, Any]:
        """获取SSE活跃连接"""
        return self.sse_handler.get_active_connections()
    
    def get_protocol_stats(self) -> Dict[str, Any]:
        """获取协议统计信息"""
        return {
            "sse_connections": len(self.sse_handler.get_active_connections()),
            "stdio_running": self.stdio_handler.running,
            "supported_protocols": ["stdio", "sse", "http", "websocket"]
        }