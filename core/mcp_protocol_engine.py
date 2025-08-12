#!/usr/bin/env python3
"""
MCP协议执行引擎
实现标准的MCP（Model Context Protocol）协议，支持大模型持续控制的工具调用流程
"""

import asyncio
import json
import logging
import re
import time
import uuid
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import copy

from .llm_clients.openai_client import OpenAIClient
from .llm_clients.ernie_client import ErnieClient
from .unified_tool_manager import get_unified_tool_manager


class MessageRole(Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant" 
    TOOL = "tool"


@dataclass
class ToolCall:
    """工具调用"""
    id: str
    type: str = "function"
    function: Dict[str, Any] = None


@dataclass
class Message:
    """MCP消息"""
    role: MessageRole
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None  # 工具名称（当role为tool时）


@dataclass
class MCPRequest:
    """MCP请求"""
    session_id: str
    messages: List[Message]
    tools: Optional[List[Dict[str, Any]]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    model: Optional[str] = None


@dataclass
class MCPResponse:
    """MCP响应"""
    session_id: str
    message: Message
    usage: Optional[Dict[str, Any]] = None
    finish_reason: str = "stop"


@dataclass
class ExecutionStep:
    """执行步骤"""
    step_id: str
    tool_name: str
    input_params: Dict[str, Any]
    output: Any
    execution_time: float
    status: str = "success"
    error: Optional[str] = None


class MCPProtocolEngine:
    """MCP协议执行引擎"""
    
    def __init__(self, llm_config: Dict[str, Any] = None, db_registry=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化LLM客户端
        self.llm_config = llm_config or {}
        self.llm_client = self._init_llm_client()
        
        # 初始化工具系统
        self.tool_system = get_unified_tool_manager(db_registry)
        
        # 会话管理
        self.sessions: Dict[str, List[Message]] = {}
        
        # 执行配置
        self.max_iterations = 10  # 最大迭代次数
        self.execution_timeout = 300  # 执行超时时间（秒）
        
        # 流程图生成器
        self.mermaid_generator = MermaidGenerator()
    
    def _init_llm_client(self):
        """初始化LLM客户端"""
        llm_type = self.llm_config.get("type", "openai")
        
        if llm_type == "openai":
            return OpenAIClient(
                api_key=self.llm_config.get("api_key"),
                model=self.llm_config.get("model", "gpt-4-turbo"),
                base_url=self.llm_config.get("base_url")
            )
        elif llm_type == "ernie":
            return ErnieClient(
                api_key=self.llm_config.get("api_key"),
                secret_key=self.llm_config.get("secret_key")
            )
        else:
            raise ValueError(f"不支持的LLM类型: {llm_type}")
    
    async def execute_conversation(self, user_input: str, session_id: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行MCP对话流程 - 流式输出
        这是核心方法，实现标准MCP协议的对话流程
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # 初始化会话
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        # 添加用户消息
        user_message = Message(role=MessageRole.USER, content=user_input)
        self.sessions[session_id].append(user_message)
        
        # 获取可用工具列表
        available_tools = await self._get_available_tools()
        
        # 执行状态跟踪
        execution_steps = []
        iteration_count = 0
        start_time = time.time()
        
        # 判断模式（聊天 vs 任务）
        mode = await self._determine_mode(user_input, available_tools)
        
        # 发送模式识别结果
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
        
        # 任务模式 - 进入MCP协议循环
        yield {
            "type": "task_start",
            "session_id": session_id,
            "message": "开始任务执行",
            "mermaid_diagram": ""  # 初始为空，后续更新
        }
        
        # MCP协议主循环
        while iteration_count < self.max_iterations:
            iteration_count += 1
            
            try:
                # 调用LLM
                self.logger.info(f"MCP迭代 {iteration_count}: 调用LLM")
                llm_response = await self._call_llm_with_tools(
                    self.sessions[session_id], 
                    available_tools
                )
                
                # 添加LLM响应到会话历史
                assistant_message = Message(
                    role=MessageRole.ASSISTANT,
                    content=llm_response.get("content"),
                    tool_calls=llm_response.get("tool_calls")
                )
                self.sessions[session_id].append(assistant_message)
                
                # 检查是否有工具调用
                if not assistant_message.tool_calls:
                    # 没有工具调用，对话结束
                    self.logger.info("LLM返回最终答案，对话结束")
                    
                    # 生成最终的Mermaid图
                    final_mermaid = self.mermaid_generator.generate_final_diagram(execution_steps)
                    
                    yield {
                        "type": "task_complete",
                        "session_id": session_id,
                        "message": assistant_message.content,
                        "execution_time": time.time() - start_time,
                        "mermaid_diagram": final_mermaid,
                        "steps": execution_steps
                    }
                    break
                
                # 执行工具调用
                for tool_call in assistant_message.tool_calls:
                    step_start_time = time.time()
                    
                    try:
                        # 解析工具调用
                        function_name = tool_call.function["name"]
                        function_args = json.loads(tool_call.function["arguments"])
                        
                        self.logger.info(f"执行工具: {function_name}")
                        
                        # 执行工具
                        tool_result = await self.tool_system.execute_tool(
                            function_name, **function_args
                        )
                        
                        # 记录执行步骤
                        step = ExecutionStep(
                            step_id=tool_call.id,
                            tool_name=function_name,
                            input_params=function_args,
                            output=tool_result,
                            execution_time=time.time() - step_start_time,
                            status="success"
                        )
                        execution_steps.append(step)
                        
                        # 将工具结果添加到会话历史
                        tool_message = Message(
                            role=MessageRole.TOOL,
                            content=json.dumps(tool_result, ensure_ascii=False),
                            tool_call_id=tool_call.id,
                            name=function_name
                        )
                        self.sessions[session_id].append(tool_message)
                        
                        # 发送步骤结果
                        yield {
                            "type": "tool_result",
                            "session_id": session_id,
                            "step": asdict(step),
                            "mermaid_diagram": self.mermaid_generator.generate_progress_diagram(execution_steps)
                        }
                        
                    except Exception as e:
                        self.logger.error(f"工具执行失败: {function_name}, 错误: {e}")
                        
                        # 记录失败步骤
                        step = ExecutionStep(
                            step_id=tool_call.id,
                            tool_name=function_name,
                            input_params=function_args,
                            output=None,
                            execution_time=time.time() - step_start_time,
                            status="error",
                            error=str(e)
                        )
                        execution_steps.append(step)
                        
                        # 将错误信息添加到会话历史
                        tool_message = Message(
                            role=MessageRole.TOOL,
                            content=f"工具执行失败: {str(e)}",
                            tool_call_id=tool_call.id,
                            name=function_name
                        )
                        self.sessions[session_id].append(tool_message)
                        
                        # 发送错误结果
                        yield {
                            "type": "tool_error",
                            "session_id": session_id,
                            "step": asdict(step),
                            "error": str(e)
                        }
                
            except Exception as e:
                self.logger.error(f"MCP迭代失败: {e}")
                yield {
                    "type": "error",
                    "session_id": session_id,
                    "message": f"执行失败: {str(e)}",
                    "iteration": iteration_count
                }
                break
        
        # 检查是否达到最大迭代次数
        if iteration_count >= self.max_iterations:
            yield {
                "type": "max_iterations_reached",
                "session_id": session_id,
                "message": f"达到最大迭代次数({self.max_iterations})，强制结束",
                "steps": execution_steps
            }
    
    async def _determine_mode(self, user_input: str, available_tools: List[Dict]) -> str:
        """判断对话模式"""
        # 1. 闲聊模式检测 - 简单问候和日常对话
        chat_patterns = [
            r'^(你好|hi|hello|早上好|晚上好|下午好)[\s！!。.]*$',
            r'^(谢谢|感谢|辛苦了|thanks)[\s！!。.]*$',
            r'^(再见|拜拜|bye|goodbye)[\s！!。.]*$',
            r'^(好的|ok|是的|不行|嗯|哦)[\s！!。.]*$',
            r'^(你是谁|你会什么|现在几点|今天怎么样)[\s？?。.]*$'
        ]
        
        for pattern in chat_patterns:
            if re.search(pattern, user_input.strip(), re.IGNORECASE):
                return "chat"
        
        # 2. 任务模式检测 - 扩展的关键词列表
        task_keywords = [
            # 搜索相关
            "搜索", "查询", "查找", "查", "查一下", "查看", "找", "找一下", 
            "搜", "搜一下", "百度", "google", "检索",
            # 分析处理
            "分析", "生成", "处理", "计算", "统计", "总结", "整理",
            # 操作相关  
            "下载", "上传", "创建", "删除", "制作", "转换", "修改", "编辑",
            # 请求相关
            "帮我", "请", "求助", "告诉我", "给我", "我想知道", "我需要",
            # 工具相关
            "报告", "图表", "文档", "翻译", "解释", "说明"
        ]
        
        if any(keyword in user_input for keyword in task_keywords):
            return "task"
        
        # 3. 增强的历史人物和知识查询检测
        knowledge_patterns = [
            r'(.*)(是谁|干什么|做什么|怎么样|历史|生平|介绍)',  # XX是谁，XX怎么样
            r'^(谁是|什么是)(.*)',  # 谁是XX，什么是XX
            r'(.*)(的|关于)(.*)(信息|资料|介绍|历史|故事)',  # 关于XX的信息
        ]
        
        for pattern in knowledge_patterns:
            if re.search(pattern, user_input.strip(), re.IGNORECASE):
                # 排除明显的闲聊内容
                if not any(chat_word in user_input for chat_word in ['你好', '谢谢', '再见', '辛苦', '早上好', '晚上好']):
                    return "task"
        
        # 4. 检测可能的人名或专有名词查询（2-8个字符且非闲聊）
        if 2 <= len(user_input.strip()) <= 8:
            # 检查是否可能是人名、地名、专有名词等
            # 排除明显的闲聊词汇
            chat_exclusions = ['你好', '谢谢', '再见', '辛苦', '好的', 'ok', '是的', '不行', '嗯', '哦']
            if not any(exclusion in user_input.lower() for exclusion in chat_exclusions):
                # 检查是否包含中文字符（可能是中文人名或术语）
                if re.search(r'[\u4e00-\u9fff]', user_input):
                    return "task"
        
        # 5. 检查是否很短的查询（通常是闲聊）
        if len(user_input.strip()) < 3:
            return "chat"
        
        # 6. 检查是否包含疑问句或复杂句式
        question_patterns = [
            r'[\?\？]',  # 包含问号
            r'(什么|怎么|为什么|哪里|如何|多少|几)',  # 疑问词
            r'(谁|when|where|what|why|how)',
            r'(告诉我|给我|帮我找|我想知道|我需要)'
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return "task"
        
        # 7. 使用LLM进行更精确的判断
        if len(user_input.strip()) > 10:
            try:
                prompt = f"""
你是一个智能助手，需要判断用户查询是否需要使用工具执行。

用户查询: "{user_input}"

可用工具类型:
- 搜索工具 (smart_search, google_search)
- 文件处理工具 (minio_uploader, image_scaler) 
- 其他专用工具

判断标准:
1. 如果是简单问候、寒暄、感谢等闲聊内容 → 返回 "chat"
2. 如果需要搜索信息、处理文件、执行具体任务 → 返回 "task"
3. 如果是询问助手功能、求助等 → 返回 "task"

只返回 "chat" 或 "task"，不要其他内容。
"""
                
                response = await self.llm_client.generate(prompt, max_tokens=10, temperature=0.1)
                mode = response.strip().lower()
                
                return "task" if mode == "task" else "chat"
                
            except Exception as e:
                self.logger.warning(f"模式判断失败，使用规则判断: {e}")
        
        # 8. 默认：较长的查询当作任务处理，短查询当作闲聊
        return "task" if len(user_input.strip()) > 10 else "chat"
    
    async def _handle_chat_mode(self, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """处理闲聊模式"""
        try:
            # 直接调用LLM，不使用工具
            messages = [{"role": msg.role.value, "content": msg.content} 
                       for msg in self.sessions[session_id]]
            
            response = await self.llm_client.generate_from_messages(messages)
            
            # 添加响应到会话历史
            assistant_message = Message(role=MessageRole.ASSISTANT, content=response)
            self.sessions[session_id].append(assistant_message)
            
            yield {
                "type": "chat_response",
                "session_id": session_id,
                "message": response,
                "mode": "chat"
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "session_id": session_id,
                "message": f"聊天模式执行失败: {str(e)}"
            }
    
    async def _call_llm_with_tools(self, messages: List[Message], tools: List[Dict]) -> Dict[str, Any]:
        """调用LLM，支持工具调用"""
        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            formatted_msg = {"role": msg.role.value}
            
            if msg.content:
                formatted_msg["content"] = msg.content
            
            if msg.tool_calls:
                formatted_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": tc.function
                    }
                    for tc in msg.tool_calls
                ]
            
            if msg.tool_call_id:
                formatted_msg["tool_call_id"] = msg.tool_call_id
            
            if msg.name:
                formatted_msg["name"] = msg.name
            
            formatted_messages.append(formatted_msg)
        
        # 调用LLM
        return await self.llm_client.generate_with_tools(formatted_messages, tools)
    
    async def _get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        tools = []
        tool_list = self.tool_system.get_tool_list()
        
        # 处理工具列表，支持列表和字典两种格式
        if isinstance(tool_list, list):
            # 如果是列表格式
            for tool_info in tool_list:
                tool_name = tool_info.get("name", "unknown_tool")
                description = tool_info.get("description", "")
                # 尝试从inputSchema获取参数信息
                parameters = tool_info.get("inputSchema", tool_info.get("parameters", {
                    "type": "object",
                    "properties": {},
                    "required": []
                }))
                
                tool_def = {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": description,
                        "parameters": parameters
                    }
                }
                tools.append(tool_def)
        else:
            # 如果是字典格式（向后兼容）
            for tool_name, tool_info in tool_list.items():
                tool_def = {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": tool_info.get("description", ""),
                        "parameters": tool_info.get("parameters", {
                            "type": "object",
                            "properties": {},
                            "required": []
                        })
                    }
                }
                tools.append(tool_def)
        
        return tools
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史"""
        if session_id not in self.sessions:
            return []
        
        return [
            {
                "role": msg.role.value,
                "content": msg.content,
                "tool_calls": [asdict(tc) for tc in msg.tool_calls] if msg.tool_calls else None,
                "tool_call_id": msg.tool_call_id,
                "name": msg.name
            }
            for msg in self.sessions[session_id]
        ]
    
    def clear_session(self, session_id: str):
        """清除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]


class MermaidGenerator:
    """Mermaid流程图生成器"""
    
    def generate_progress_diagram(self, steps: List[ExecutionStep]) -> str:
        """生成进度流程图"""
        if not steps:
            return """
graph LR
    Start[开始] --> End[等待中...]
    
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef pending fill:#fff3cd,stroke:#856404,stroke-width:1px,color:#856404;
    class End pending;
"""
        
        mermaid_lines = ["graph LR"]
        mermaid_lines.append("    Start[开始]")
        
        # 添加节点
        for i, step in enumerate(steps):
            node_id = f"Step{i+1}"
            status_icon = "✅" if step.status == "success" else "❌"
            mermaid_lines.append(f'    {node_id}["{status_icon} {step.tool_name}"]')
        
        mermaid_lines.append("    End[完成]")
        
        # 添加连接
        if steps:
            mermaid_lines.append("    Start --> Step1")
            for i in range(len(steps) - 1):
                mermaid_lines.append(f"    Step{i+1} --> Step{i+2}")
            mermaid_lines.append(f"    Step{len(steps)} --> End")
        else:
            mermaid_lines.append("    Start --> End")
        
        # 添加样式
        mermaid_lines.extend([
            "",
            "    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;",
            "    classDef success fill:#d4edda,stroke:#155724,stroke-width:1px,color:#155724;",
            "    classDef error fill:#f8d7da,stroke:#721c24,stroke-width:1px,color:#721c24;",
            "    classDef endpoint fill:#e0e7ff,stroke:#4f46e5,stroke-width:1px,color:#4f46e5;",
            "",
            "    class Start,End endpoint;"
        ])
        
        # 应用状态样式
        for i, step in enumerate(steps):
            node_id = f"Step{i+1}"
            status_class = "success" if step.status == "success" else "error"
            mermaid_lines.append(f"    class {node_id} {status_class};")
        
        return "\n".join(mermaid_lines)
    
    def generate_final_diagram(self, steps: List[ExecutionStep]) -> str:
        """生成最终完整流程图"""
        return self.generate_progress_diagram(steps)


# 全局实例
_mcp_engine = None

def get_mcp_engine(llm_config: Dict[str, Any] = None, db_registry=None) -> MCPProtocolEngine:
    """获取MCP引擎单例"""
    global _mcp_engine
    if _mcp_engine is None:
        _mcp_engine = MCPProtocolEngine(llm_config, db_registry)
    return _mcp_engine 