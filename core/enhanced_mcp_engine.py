"""
增强版MCP协议引擎
集成执行状态管理器，支持实时状态推送和前端同步
"""

import time
import uuid
import logging
import json
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable
from core.execution_status_manager import (
    ExecutionStatusManager, WebSocketStatusCallback, 
    ExecutionStatus, MessageType, ExecutionStep, ExecutionPlan
)
from core.mcp_protocol_engine import MCPProtocolEngine  # 继承原有引擎
from core.task_engine import TaskEngine


class EnhancedMCPEngine(MCPProtocolEngine):
    """增强版MCP协议引擎"""
    
    def __init__(self, llm_config: Dict[str, Any] = None, db_registry=None, 
                 tool_registry=None, max_iterations: int = 10):
        super().__init__(llm_config, db_registry)
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化任务执行引擎
        self.task_engine = TaskEngine(tool_registry) if tool_registry else None
        
        # 初始化状态管理器
        self.status_manager = ExecutionStatusManager()
        
        # WebSocket回调函数
        self.websocket_callback: Optional[WebSocketStatusCallback] = None
    
    def setup_websocket_callback(self, websocket_send_func: Callable) -> None:
        """设置WebSocket回调"""
        self.websocket_callback = WebSocketStatusCallback(websocket_send_func)
        self.status_manager.add_callback(self.websocket_callback)
        self.logger.info("WebSocket状态回调已设置")
    
    async def execute_conversation_with_status(self, user_input: str, 
                                             session_id: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行MCP对话流程 - 增强版，支持实时状态推送
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        start_time = time.time()
        
        try:
            # 1. 模式检测
            available_tools = await self._get_available_tools()
            mode = await self._determine_mode(user_input, available_tools)
            
            # 发送模式检测结果
            yield {
                "type": "mode_detection",
                "mode": mode,
                "session_id": session_id,
                "message": f"检测到{'任务执行' if mode == 'task' else '闲聊对话'}模式"
            }
            
            if mode == "chat":
                # 闲聊模式 - 直接调用LLM
                async for chunk in self._handle_chat_mode(session_id):
                    yield chunk
                return
            
            # 2. 任务模式 - 使用增强的执行流程
            await self._execute_task_mode_enhanced(user_input, session_id)
            
        except Exception as e:
            self.logger.error(f"执行对话失败: {e}")
            await self.status_manager.report_error(f"执行失败: {str(e)}")
    
    async def _execute_task_mode_enhanced(self, user_input: str, session_id: str) -> None:
        """执行任务模式 - 增强版"""
        try:
            # 1. 发送任务规划开始消息
            await self.status_manager.update_planning("正在分析任务并制定执行计划...")
            
            # 2. 生成执行计划
            if self.task_engine:
                # 使用TaskEngine生成计划
                plan_result = await self._generate_plan_with_task_engine(user_input)
                plan_data = plan_result.get("execution_plan", [])
            else:
                # 使用LLM生成计划
                plan_data = await self._generate_plan_with_llm(user_input)
            
            if not plan_data:
                await self.status_manager.report_error("无法生成有效的执行计划")
                return
            
            # 3. 创建并启动执行计划
            steps_data = []
            for i, step in enumerate(plan_data):
                steps_data.append({
                    "tool_name": step.get("tool", step.get("tool_name", f"tool_{i}")),
                    "description": step.get("description", f"执行步骤 {i+1}"),
                    "input_params": step.get("params", step.get("input_params", {}))
                })
            
            execution_plan = await self.status_manager.start_task(user_input, steps_data)
            
            # 4. 执行计划中的每个步骤
            final_result = await self._execute_plan_steps(execution_plan)
            
            # 5. 完成任务
            await self.status_manager.complete_task(final_result)
            
        except Exception as e:
            self.logger.error(f"任务执行失败: {e}")
            await self.status_manager.report_error(f"任务执行失败: {str(e)}")
    
    async def _generate_plan_with_task_engine(self, user_input: str) -> Dict[str, Any]:
        """使用TaskEngine生成执行计划"""
        try:
            result = await self.task_engine.execute(user_input, {})
            return result
        except Exception as e:
            self.logger.error(f"TaskEngine执行失败: {e}")
            return {}
    
    async def _generate_plan_with_llm(self, user_input: str) -> List[Dict[str, Any]]:
        """使用LLM生成执行计划"""
        try:
            # 获取可用工具
            available_tools = await self._get_available_tools()
            
            # 构造规划提示
            tools_desc = "\n".join([
                f"- {tool['name']}: {tool.get('description', '无描述')}"
                for tool in available_tools
            ])
            
            planning_prompt = f"""
请为以下用户请求制定详细的执行计划：

用户请求：{user_input}

可用工具：
{tools_desc}

请返回JSON格式的执行计划，包含以下字段：
- tool: 工具名称
- description: 步骤描述  
- params: 工具参数

示例：
[
  {{"tool": "web_search", "description": "搜索相关信息", "params": {{"query": "搜索关键词"}}}},
  {{"tool": "file_writer", "description": "保存结果", "params": {{"content": "结果内容"}}}}
]
"""
            
            # 调用LLM生成计划
            response = await self.llm_client.generate(
                messages=[{"role": "user", "content": planning_prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            # 解析LLM响应
            content = response.get("content", "")
            if content:
                # 尝试提取JSON
                import re
                json_match = re.search(r'\[.*?\]', content, re.DOTALL)
                if json_match:
                    plan_json = json_match.group()
                    plan = json.loads(plan_json)
                    return plan
            
            return []
            
        except Exception as e:
            self.logger.error(f"LLM规划失败: {e}")
            return []
    
    async def _execute_plan_steps(self, execution_plan: ExecutionPlan) -> str:
        """执行计划中的各个步骤"""
        results = []
        
        for step in execution_plan.steps:
            try:
                # 开始执行步骤
                await self.status_manager.start_tool(
                    step.id, step.tool_name, step.input_params or {}
                )
                
                # 执行工具
                tool_result = await self._execute_single_tool(
                    step.tool_name, step.input_params or {}
                )
                
                # 完成步骤
                if tool_result.get("success", False):
                    await self.status_manager.complete_tool(
                        step.id, step.tool_name, tool_result, ExecutionStatus.SUCCESS
                    )
                    results.append(tool_result)
                else:
                    error_msg = tool_result.get("error", "工具执行失败")
                    await self.status_manager.complete_tool(
                        step.id, step.tool_name, tool_result, ExecutionStatus.ERROR, error_msg
                    )
                
            except Exception as e:
                error_msg = f"步骤执行异常: {str(e)}"
                self.logger.error(error_msg)
                await self.status_manager.complete_tool(
                    step.id, step.tool_name, {"error": error_msg}, 
                    ExecutionStatus.ERROR, error_msg
                )
        
        # 生成最终结果摘要
        if results:
            # 使用LLM生成结果摘要
            final_result = await self._generate_final_summary(
                execution_plan.query, results
            )
        else:
            final_result = "任务执行过程中遇到错误，未能获得有效结果。"
        
        return final_result
    
    async def _execute_single_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个工具"""
        try:
            if not self.tool_registry:
                return {"success": False, "error": "工具注册表未初始化"}
            
            # 获取工具函数
            tool_func = self.tool_registry.get_tool(tool_name)
            if not tool_func:
                return {"success": False, "error": f"未找到工具: {tool_name}"}
            
            # 执行工具
            start_time = time.time()
            result = await tool_func(**params) if hasattr(tool_func, '__call__') else tool_func(**params)
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "tool_name": tool_name,
                "input_params": params
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "input_params": params
            }
    
    async def _generate_final_summary(self, query: str, results: List[Dict[str, Any]]) -> str:
        """生成最终结果摘要"""
        try:
            results_text = "\n".join([
                f"工具: {r.get('tool_name', '未知')}\n结果: {str(r.get('result', '无结果'))[:200]}..."
                for r in results
            ])
            
            summary_prompt = f"""
请根据以下执行结果，为用户查询生成简洁明了的回答：

用户查询：{query}

执行结果：
{results_text}

请提供一个综合性的回答，重点突出用户关心的信息。
"""
            
            response = await self.llm_client.generate(
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.get("content", "执行完成，但无法生成摘要。")
            
        except Exception as e:
            self.logger.error(f"生成摘要失败: {e}")
            return f"任务执行完成，共获得 {len(results)} 个结果。"
    
    async def _get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        try:
            if not self.tool_registry:
                return []
            
            tools = []
            for tool_name in self.tool_registry.list_tools():
                tool_info = self.tool_registry.get_tool_info(tool_name)
                if tool_info:
                    tools.append({
                        "name": tool_name,
                        "description": tool_info.get("description", ""),
                        "parameters": tool_info.get("parameters", {})
                    })
            
            return tools
            
        except Exception as e:
            self.logger.error(f"获取工具列表失败: {e}")
            return []
    
    async def _determine_mode(self, user_input: str, available_tools: List[Dict[str, Any]]) -> str:
        """确定对话模式"""
        # 简化的模式检测逻辑
        task_keywords = [
            "搜索", "查找", "下载", "上传", "生成", "创建", "执行", "运行", 
            "分析", "处理", "转换", "计算", "统计", "图表", "报告"
        ]
        
        for keyword in task_keywords:
            if keyword in user_input:
                return "task"
        
        return "chat"
    
    async def _handle_chat_mode(self, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """处理闲聊模式"""
        # 获取会话消息
        messages = self.sessions.get(session_id, [])
        
        try:
            # 调用LLM生成回复
            response = await self.llm_client.generate(
                messages=[{"role": msg.role.value, "content": msg.content} for msg in messages[-10:]],
                max_tokens=1000,
                temperature=0.8
            )
            
            content = response.get("content", "抱歉，我现在无法回答您的问题。")
            
            # 添加助手消息到会话
            from core.types import Message, MessageRole
            assistant_message = Message(role=MessageRole.ASSISTANT, content=content)
            self.sessions[session_id].append(assistant_message)
            
            # 返回聊天响应
            yield {
                "type": "chat_response",
                "session_id": session_id,
                "message": content
            }
            
        except Exception as e:
            self.logger.error(f"闲聊模式处理失败: {e}")
            yield {
                "type": "error",
                "message": f"处理失败: {str(e)}"
            } 