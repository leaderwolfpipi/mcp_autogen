"""
执行状态管理器
统一管理任务执行过程中的状态变化，支持实时回调和WebSocket推送
"""

import time
import uuid
import logging
import json
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from enum import Enum
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod


class ExecutionStatus(Enum):
    """执行状态枚举"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 正在执行
    SUCCESS = "success"       # 执行成功
    ERROR = "error"          # 执行失败
    CANCELLED = "cancelled"   # 已取消


class MessageType(Enum):
    """消息类型枚举"""
    TASK_START = "task_start"           # 任务开始
    TASK_PLANNING = "task_planning"     # 任务规划
    TASK_COMPLETE = "task_complete"     # 任务完成
    TOOL_START = "tool_start"           # 工具开始执行
    TOOL_RESULT = "tool_result"         # 工具执行结果
    PLAN_UPDATE = "plan_update"         # 执行计划更新
    STATUS_UPDATE = "status_update"     # 状态更新
    ERROR = "error"                     # 错误信息


@dataclass
class ExecutionStep:
    """执行步骤"""
    id: str
    tool_name: str
    description: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    execution_time: Optional[float] = None
    input_params: Optional[Dict[str, Any]] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "description": self.description,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "execution_time": self.execution_time,
            "input_params": self.input_params,
            "output": self.output,
            "error": self.error
        }


@dataclass
class ExecutionPlan:
    """执行计划"""
    id: str
    query: str
    steps: List[ExecutionStep]
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    execution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "query": self.query,
            "steps": [step.to_dict() for step in self.steps],
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "execution_time": self.execution_time
        }


class StatusCallback(ABC):
    """状态回调接口"""
    
    @abstractmethod
    async def on_task_start(self, plan: ExecutionPlan) -> None:
        """任务开始回调"""
        pass
    
    @abstractmethod
    async def on_task_planning(self, message: str, plan: Optional[ExecutionPlan] = None) -> None:
        """任务规划回调"""
        pass
    
    @abstractmethod
    async def on_tool_start(self, step: ExecutionStep) -> None:
        """工具开始执行回调"""
        pass
    
    @abstractmethod
    async def on_tool_result(self, step: ExecutionStep) -> None:
        """工具执行结果回调"""
        pass
    
    @abstractmethod
    async def on_task_complete(self, plan: ExecutionPlan, final_result: Any) -> None:
        """任务完成回调"""
        pass
    
    @abstractmethod
    async def on_error(self, error_msg: str, context: Optional[Dict[str, Any]] = None) -> None:
        """错误回调"""
        pass


class WebSocketStatusCallback(StatusCallback):
    """WebSocket状态回调实现"""
    
    def __init__(self, websocket_send_func: Callable):
        self.send = websocket_send_func
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def on_task_start(self, plan: ExecutionPlan) -> None:
        """发送任务开始消息"""
        message = {
            "type": MessageType.TASK_START.value,
            "session_id": plan.id,
            "message": f"开始执行任务：{plan.query}",
            "plan": plan.to_dict(),
            "timestamp": time.time()
        }
        await self._send_message(message)
    
    async def on_task_planning(self, message: str, plan: Optional[ExecutionPlan] = None) -> None:
        """发送任务规划消息"""
        msg = {
            "type": MessageType.TASK_PLANNING.value,
            "message": message,
            "timestamp": time.time()
        }
        if plan:
            msg["plan"] = plan.to_dict()
        await self._send_message(msg)
    
    async def on_tool_start(self, step: ExecutionStep) -> None:
        """发送工具开始执行消息"""
        message = {
            "type": MessageType.TOOL_START.value,
            "message": f"正在执行：{step.description}",
            "tool_name": step.tool_name,
            "step_id": step.id,
            "input_params": step.input_params,
            "timestamp": time.time()
        }
        await self._send_message(message)
    
    async def on_tool_result(self, step: ExecutionStep) -> None:
        """发送工具执行结果消息"""
        message = {
            "type": MessageType.TOOL_RESULT.value,
            "step_data": step.to_dict(),
            "timestamp": time.time()
        }
        await self._send_message(message)
    
    async def on_task_complete(self, plan: ExecutionPlan, final_result: Any) -> None:
        """发送任务完成消息"""
        message = {
            "type": MessageType.TASK_COMPLETE.value,
            "session_id": plan.id,
            "message": final_result,
            "execution_time": plan.execution_time,
            "steps": [step.to_dict() for step in plan.steps],
            "timestamp": time.time()
        }
        await self._send_message(message)
    
    async def on_error(self, error_msg: str, context: Optional[Dict[str, Any]] = None) -> None:
        """发送错误消息"""
        message = {
            "type": MessageType.ERROR.value,
            "message": error_msg,
            "context": context,
            "timestamp": time.time()
        }
        await self._send_message(message)
    
    async def _send_message(self, message: Dict[str, Any]) -> None:
        """发送消息到WebSocket"""
        try:
            await self.send(message)
        except Exception as e:
            self.logger.error(f"WebSocket消息发送失败: {e}")


class ExecutionStatusManager:
    """执行状态管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_plan: Optional[ExecutionPlan] = None
        self.callbacks: List[StatusCallback] = []
        self.sessions: Dict[str, ExecutionPlan] = {}
    
    def add_callback(self, callback: StatusCallback) -> None:
        """添加状态回调"""
        self.callbacks.append(callback)
        self.logger.info("添加状态回调")
    
    def remove_callback(self, callback: StatusCallback) -> None:
        """移除状态回调"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            self.logger.info("移除状态回调")
    
    async def start_task(self, query: str, steps_data: List[Dict[str, Any]]) -> ExecutionPlan:
        """开始任务执行"""
        plan_id = str(uuid.uuid4())
        
        # 创建执行步骤
        steps = []
        for i, step_data in enumerate(steps_data):
            step = ExecutionStep(
                id=f"step_{i}",
                tool_name=step_data.get("tool_name", f"tool_{i}"),
                description=step_data.get("description", f"执行步骤 {i+1}"),
                input_params=step_data.get("input_params", {})
            )
            steps.append(step)
        
        # 创建执行计划
        plan = ExecutionPlan(
            id=plan_id,
            query=query,
            steps=steps,
            start_time=time.time()
        )
        
        self.current_plan = plan
        self.sessions[plan_id] = plan
        
        # 通知所有回调
        for callback in self.callbacks:
            try:
                await callback.on_task_start(plan)
            except Exception as e:
                self.logger.error(f"回调执行失败: {e}")
        
        self.logger.info(f"任务开始: {query}, 计划ID: {plan_id}")
        return plan
    
    async def update_planning(self, message: str, plan_data: Optional[Dict[str, Any]] = None) -> None:
        """更新任务规划状态"""
        plan = None
        if plan_data and self.current_plan:
            # 更新当前计划
            if "steps" in plan_data:
                self.current_plan.steps = []
                for i, step_data in enumerate(plan_data["steps"]):
                    step = ExecutionStep(
                        id=f"step_{i}",
                        tool_name=step_data.get("tool_name", f"tool_{i}"),
                        description=step_data.get("description", f"执行步骤 {i+1}"),
                        input_params=step_data.get("input_params", {})
                    )
                    self.current_plan.steps.append(step)
            plan = self.current_plan
        
        # 通知所有回调
        for callback in self.callbacks:
            try:
                await callback.on_task_planning(message, plan)
            except Exception as e:
                self.logger.error(f"回调执行失败: {e}")
    
    async def start_tool(self, step_id: str, tool_name: str, input_params: Dict[str, Any]) -> None:
        """开始工具执行"""
        if not self.current_plan:
            return
        
        # 找到对应的步骤
        step = None
        for s in self.current_plan.steps:
            if s.id == step_id or s.tool_name == tool_name:
                step = s
                break
        
        if not step:
            # 创建新步骤
            step = ExecutionStep(
                id=step_id,
                tool_name=tool_name,
                description=f"执行工具: {tool_name}",
                input_params=input_params
            )
            self.current_plan.steps.append(step)
        
        # 更新步骤状态
        step.status = ExecutionStatus.RUNNING
        step.start_time = time.time()
        step.input_params = input_params
        
        # 通知所有回调
        for callback in self.callbacks:
            try:
                await callback.on_tool_start(step)
            except Exception as e:
                self.logger.error(f"回调执行失败: {e}")
        
        self.logger.info(f"工具开始执行: {tool_name}")
    
    async def complete_tool(self, step_id: str, tool_name: str, output: Any, 
                          status: ExecutionStatus = ExecutionStatus.SUCCESS, 
                          error: Optional[str] = None) -> None:
        """完成工具执行"""
        if not self.current_plan:
            return
        
        # 找到对应的步骤
        step = None
        for s in self.current_plan.steps:
            if s.id == step_id or s.tool_name == tool_name:
                step = s
                break
        
        if not step:
            self.logger.warning(f"未找到步骤: {step_id} / {tool_name}")
            return
        
        # 更新步骤状态
        step.status = status
        step.end_time = time.time()
        step.execution_time = step.end_time - (step.start_time or step.end_time)
        step.output = output
        step.error = error
        
        # 通知所有回调
        for callback in self.callbacks:
            try:
                await callback.on_tool_result(step)
            except Exception as e:
                self.logger.error(f"回调执行失败: {e}")
        
        self.logger.info(f"工具执行完成: {tool_name}, 状态: {status.value}")
    
    async def complete_task(self, final_result: Any, status: ExecutionStatus = ExecutionStatus.SUCCESS) -> None:
        """完成任务执行"""
        if not self.current_plan:
            return
        
        # 更新计划状态
        self.current_plan.status = status
        self.current_plan.end_time = time.time()
        self.current_plan.execution_time = self.current_plan.end_time - (self.current_plan.start_time or self.current_plan.end_time)
        
        # 通知所有回调
        for callback in self.callbacks:
            try:
                await callback.on_task_complete(self.current_plan, final_result)
            except Exception as e:
                self.logger.error(f"回调执行失败: {e}")
        
        self.logger.info(f"任务执行完成, 状态: {status.value}")
    
    async def report_error(self, error_msg: str, context: Optional[Dict[str, Any]] = None) -> None:
        """报告错误"""
        # 通知所有回调
        for callback in self.callbacks:
            try:
                await callback.on_error(error_msg, context)
            except Exception as e:
                self.logger.error(f"回调执行失败: {e}")
        
        self.logger.error(f"执行错误: {error_msg}")
    
    def get_current_plan(self) -> Optional[ExecutionPlan]:
        """获取当前执行计划"""
        return self.current_plan
    
    def get_plan_by_id(self, plan_id: str) -> Optional[ExecutionPlan]:
        """根据ID获取执行计划"""
        return self.sessions.get(plan_id)


# 全局状态管理器实例
global_status_manager = ExecutionStatusManager() 