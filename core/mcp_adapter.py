#!/usr/bin/env python3
"""
标准MCP协议适配层
实现符合MCP 1.0标准的协议适配器
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import OrderedDict

from .task_engine import TaskEngine
from .unified_tool_manager import get_unified_tool_manager


class SimpleLRUCache:
    """简单的LRU缓存实现"""
    
    def __init__(self, maxsize: int = 1000):
        self.maxsize = maxsize
        self.cache = OrderedDict()
    
    def __getitem__(self, key):
        if key not in self.cache:
            raise KeyError(key)
        # 移动到末尾（最近使用）
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def __setitem__(self, key, value):
        if key in self.cache:
            # 更新现有键
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.maxsize:
            # 删除最久未使用的项
            self.cache.popitem(last=False)
        self.cache[key] = value
    
    def __contains__(self, key):
        return key in self.cache
    
    def __len__(self):
        return len(self.cache)
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
    
    def pop(self, key, default=None):
        if key in self.cache:
            return self.cache.pop(key)
        return default
    
    def clear(self):
        self.cache.clear()


class MCPAdapter:
    """MCP协议适配器"""
    
    def __init__(self, tool_registry=None, max_sessions=1000):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.sessions = SimpleLRUCache(maxsize=max_sessions)
        
        # 获取工具注册表
        if tool_registry is None:
            self.tool_registry = get_unified_tool_manager()
        else:
            self.tool_registry = tool_registry
        
        # MCP版本
        self.mcp_version = "1.0"
    
    async def handle_request(self, request: dict) -> dict:
        """
        处理MCP标准请求
        
        Args:
            request: 符合MCP标准的请求字典
            
        Returns:
            符合MCP标准的响应字典
        """
        start_time = time.time()
        
        # 协议验证
        if not self._validate_request(request):
            return self._error_response("Invalid MCP format", 400)
        
        # 提取请求信息
        session_id = request.get('session_id', str(uuid.uuid4()))
        request_id = request.get('request_id', str(uuid.uuid4()))
        user_query = request.get('user_query', '')
        context = request.get('context', {})
        
        # 会话管理
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'context': context,
                'history': [],
                'created_at': datetime.now()
            }
        
        # 更新会话上下文
        self.sessions[session_id]['context'].update(context)
        
        try:
            # 任务处理
            engine = TaskEngine(self.tool_registry, max_depth=5)
            result = await engine.execute(
                user_query,
                self.sessions[session_id]['context']
            )
            
            # 更新会话历史
            self.sessions[session_id]['history'].append({
                'timestamp': datetime.now(),
                'request_id': request_id,
                'query': user_query,
                'response': result
            })
            
            # 构造标准MCP响应
            response = self._format_response(
                result, 
                session_id=session_id,
                request_id=request_id,
                execution_time=time.time() - start_time
            )
            
            self.logger.info(f"MCP请求处理完成: {request_id}, 用时: {time.time() - start_time:.2f}秒")
            return response
            
        except Exception as e:
            self.logger.error(f"MCP请求处理失败: {e}")
            return self._error_response(
                message=str(e),
                code=500,
                session_id=session_id,
                request_id=request_id
            )
    
    def _validate_request(self, request: dict) -> bool:
        """验证MCP请求格式"""
        required_fields = ['mcp_version', 'user_query']
        
        # 检查必需字段
        for field in required_fields:
            if field not in request:
                self.logger.warning(f"Missing required field: {field}")
                return False
        
        # 检查MCP版本
        if request.get('mcp_version') != self.mcp_version:
            self.logger.warning(f"Unsupported MCP version: {request.get('mcp_version')}")
            return False
        
        # 检查用户查询
        if not request.get('user_query', '').strip():
            self.logger.warning("Empty user query")
            return False
        
        return True
    
    def _format_response(self, result: dict, session_id: str, request_id: str, execution_time: float) -> dict:
        """格式化为标准MCP响应"""
        
        # 提取执行步骤
        steps = []
        if 'execution_steps' in result:
            for step in result['execution_steps']:
                steps.append({
                    "tool_name": step.get('tool_name', ''),
                    "input_params": step.get('input_params', {}),
                    "output": step.get('output', {}),
                    "execution_time": step.get('execution_time', 0),
                    "status": step.get('status', 'unknown')
                })
        
        # 计算成本估算
        cost_estimation = self._calculate_cost(result, steps)
        
        # 确定状态
        status = "success"
        if result.get('error'):
            status = "error"
        elif not result.get('success', True):
            status = "partial"
        
        # 构造响应
        response = {
            "mcp_version": self.mcp_version,
            "session_id": session_id,
            "request_id": request_id,
            "status": status,
            "steps": steps,
            "final_response": result.get('final_output', result.get('message', '')),
            "cost_estimation": cost_estimation,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
        # 添加错误信息（如果有）
        if result.get('error'):
            response['error'] = {
                "code": result.get('error_code', 'EXECUTION_ERROR'),
                "message": str(result['error']),
                "details": result.get('error_details', {})
            }
        
        return response
    
    def _calculate_cost(self, result: dict, steps: List[dict]) -> dict:
        """计算成本估算"""
        # 基本成本计算
        token_usage = 0
        tool_calls = len(steps)
        
        # 估算token使用量（简单估算）
        if 'final_output' in result:
            token_usage += len(str(result['final_output']).split()) * 1.3  # 粗略估算
        
        for step in steps:
            # 输入输出token估算
            input_tokens = len(str(step.get('input_params', '')).split()) * 1.3
            output_tokens = len(str(step.get('output', '')).split()) * 1.3
            token_usage += input_tokens + output_tokens
        
        return {
            "token_usage": int(token_usage),
            "tool_calls": tool_calls,
            "estimated_cost": token_usage * 0.00001,  # 假设每token成本
            "currency": "USD"
        }
    
    def _error_response(self, message: str, code: int, session_id: str = None, request_id: str = None) -> dict:
        """生成错误响应"""
        return {
            "mcp_version": self.mcp_version,
            "session_id": session_id or str(uuid.uuid4()),
            "request_id": request_id or str(uuid.uuid4()),
            "status": "error",
            "steps": [],
            "final_response": "",
            "error": {
                "code": f"MCP_ERROR_{code}",
                "message": message,
                "details": {}
            },
            "cost_estimation": {
                "token_usage": 0,
                "tool_calls": 0,
                "estimated_cost": 0.0,
                "currency": "USD"
            },
            "execution_time": 0.0,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_session_info(self, session_id: str) -> Optional[dict]:
        """获取会话信息"""
        return self.sessions.get(session_id)
    
    def clear_session(self, session_id: str) -> bool:
        """清除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_sessions_count(self) -> int:
        """获取活跃会话数量"""
        return len(self.sessions)
    
    def get_mcp_info(self) -> dict:
        """获取MCP适配器信息"""
        return {
            "mcp_version": self.mcp_version,
            "adapter_version": "1.0.0",
            "supported_features": [
                "standard_requests",
                "session_management", 
                "cost_estimation",
                "error_handling",
                "tool_execution"
            ],
            "active_sessions": len(self.sessions),
            "max_sessions": self.sessions.maxsize
        } 