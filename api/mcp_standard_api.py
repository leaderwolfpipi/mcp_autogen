#!/usr/bin/env python3
"""
标准MCP协议API接口
实现完全符合MCP 1.0标准的API接口，支持流式问答
"""

import asyncio
import json
import logging
import os
import re
import sys
import time
import uuid
from typing import Dict, Any, Optional, AsyncGenerator
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# 添加项目根目录到Python路径 - 必须在其他导入之前
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mcp_protocol_engine import MCPProtocolEngine
from core.execution_status_manager import (
    global_status_manager, WebSocketStatusCallback, 
    ExecutionStatus, MessageType
)


from core.mcp_adapter import MCPAdapter
from core.database_manager import get_database_manager

# 导入工具（可选）
try:
    from cmd.import_tools import import_tools
except ImportError:
    def import_tools():
        """空的import_tools函数，作为fallback"""
        pass

# 尝试导入LLM客户端用于流式问答
try:
    from core.llm_clients.openai_client import OpenAIClient
    from core.llm_clients.ernie_client import ErnieClient
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# 添加协议适配器导入
from core.protocol_adapter import ProtocolAdapter, TransportType


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 标准MCP请求/响应模型
class MCPStandardRequest(BaseModel):
    """标准MCP请求"""
    mcp_version: str = Field(default="1.0", description="MCP协议版本")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    request_id: Optional[str] = Field(default=None, description="请求ID")
    user_query: str = Field(..., description="用户查询")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")


class MCPStandardResponse(BaseModel):
    """标准MCP响应"""
    mcp_version: str = Field(default="1.0", description="MCP协议版本")
    session_id: str = Field(..., description="会话ID")
    request_id: str = Field(..., description="请求ID")
    status: str = Field(..., description="执行状态: success/partial/error")
    steps: list = Field(default_factory=list, description="执行步骤")
    final_response: str = Field(default="", description="最终响应")
    cost_estimation: Dict[str, Any] = Field(default_factory=dict, description="成本估算")
    execution_time: float = Field(default=0.0, description="执行时间")
    timestamp: str = Field(..., description="时间戳")
    error: Optional[Dict[str, Any]] = Field(default=None, description="错误信息")


class StreamingMCPEngine:
    """流式MCP引擎"""
    
    def __init__(self, llm_config: Dict[str, Any] = None, mcp_adapter=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.llm_config = llm_config or {}
        self.mcp_adapter = mcp_adapter
        
        # 初始化LLM客户端（用于闲聊模式）
        self.llm_client = None
        if LLM_AVAILABLE:
            try:
                # 检查是否有基本配置
                api_key = self.llm_config.get("api_key")
                llm_type = self.llm_config.get("type", "openai")
                
                if api_key and api_key.strip():
                    self.llm_client = self._init_llm_client()
                    self.logger.info(f"✅ LLM客户端初始化成功 (类型: {llm_type})")
                else:
                    self.logger.info("⚠️ 未配置LLM API Key，将使用智能回退机制")
            except Exception as e:
                self.logger.warning(f"⚠️ LLM客户端初始化失败，将使用智能回退机制: {e}")
        else:
            self.logger.info("⚠️ LLM模块不可用，将使用智能回退机制")
        
        # 会话管理
        self.sessions = {}
    
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
    
    async def execute_streaming_conversation(self, user_input: str, session_id: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行流式对话 - 支持闲聊和任务两种模式
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # 初始化会话
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'messages': [],
                'context': {},
                'created_at': time.time()
            }
        
        start_time = time.time()
        
        # 判断模式（聊天 vs 任务）
        mode = await self._determine_mode(user_input)
        
        # 发送模式识别结果
        yield {
            "type": "mode_detection",
            "mode": mode,
            "session_id": session_id,
            "message": f"检测到{'任务执行' if mode == 'task' else '闲聊对话'}模式",
            "timestamp": time.time()
        }
        
        if mode == "chat":
            # 闲聊模式 - 直接调用LLM
            async for chunk in self._handle_chat_mode_streaming(user_input, session_id):
                yield chunk
        else:
            # 任务模式 - 使用MCP适配器
            async for chunk in self._handle_task_mode_streaming(user_input, session_id, start_time):
                yield chunk
    
    async def _determine_mode(self, user_input: str) -> str:
        """判断对话模式 - 使用改进的检测逻辑"""
        user_input_clean = user_input.strip()
        
        # 1. 闲聊模式检测 - 扩展的中文日常问候和寒暄
        chat_patterns = [
            # 基本问候
            r'^(你好|hi|hello|早上好|晚上好|下午好|早|晚好)[\s！!。.]*$',
            # 感谢道别
            r'^(谢谢|感谢|辛苦了|thanks|再见|拜拜|bye|goodbye)[\s！!。.]*$',
            # 确认否定
            r'^(好的|ok|是的|不是|不行|嗯|哦|行|可以|不可以)[\s！!。.]*$',
            # 典型中文日常问候（重点添加）
            r'^(吃了吗|吃饭了吗|吃了没|吃过了吗)[\s？?！!。.]*$',
            r'^(忙吗|忙不忙|在忙吗|最近忙吗)[\s？?！!。.]*$',
            r'^(在干嘛|在做什么|干嘛呢|做什么呢)[\s？?！!。.]*$',
            r'^(睡了吗|睡觉了吗|休息了吗)[\s？?！!。.]*$',
            r'^(回来了吗|到家了吗|下班了吗|上班了吗)[\s？?！!。.]*$',
            r'^(还好吗|怎么样|最近怎样|近来如何)[\s？?！!。.]*$',
            r'^(累吗|累不累|辛苦吗)[\s？?！!。.]*$',
            # 关心问候
            r'^(身体怎么样|身体好吗|健康吗)[\s？?！!。.]*$',
            r'^(工作怎么样|学习怎么样|生活怎么样)[\s？?！!。.]*$',
            # 简单状态询问
            r'^(你是谁|你会什么|现在几点|今天怎么样)[\s？?。.]*$'
        ]
        
        for pattern in chat_patterns:
            if re.search(pattern, user_input_clean, re.IGNORECASE):
                return "chat"
        
        # 2. 明确的闲聊词汇检测（关键词方式）
        chat_keywords = [
            "吃了吗", "吃饭了吗", "吃过了吗", "吃了没",
            "忙吗", "忙不忙", "在忙吗", "最近忙吗",
            "在干嘛", "在做什么", "干嘛呢", "做什么呢",
            "睡了吗", "睡觉了吗", "休息了吗",
            "回来了吗", "到家了吗", "下班了吗", "上班了吗",
            "还好吗", "怎么样", "最近怎样", "近来如何",
            "累吗", "累不累", "辛苦吗",
            "身体怎么样", "身体好吗", "健康吗",
            "工作怎么样", "学习怎么样", "生活怎么样"
        ]
        
        for keyword in chat_keywords:
            if keyword in user_input_clean:
                return "chat"
        
        # 3. 任务模式检测 - 扩展的关键词列表
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
        
        # 4. 增强的历史人物和知识查询检测
        knowledge_patterns = [
            r'(.*)(是谁|干什么|做什么|怎么样|历史|生平|介绍)',  # XX是谁，XX怎么样
            r'^(谁是|什么是)(.*)',  # 谁是XX，什么是XX
            r'(.*)(的|关于)(.*)(信息|资料|介绍|历史|故事)',  # 关于XX的信息
        ]
        
        for pattern in knowledge_patterns:
            if re.search(pattern, user_input_clean, re.IGNORECASE):
                # 排除明显的闲聊内容（扩展排除列表）
                chat_exclusions = [
                    '你好', '谢谢', '再见', '辛苦', '早上好', '晚上好',
                    '吃了吗', '忙吗', '在干嘛', '睡了吗', '累吗', '还好吗'
                ]
                if not any(chat_word in user_input for chat_word in chat_exclusions):
                    return "task"
        
        # 5. 检测可能的人名或专有名词查询（2-8个字符且非闲聊）
        if 2 <= len(user_input_clean) <= 8:
            # 检查是否可能是人名、地名、专有名词等
            # 排除明显的闲聊词汇（扩展排除列表）
            chat_exclusions = [
                '你好', '谢谢', '再见', '辛苦', '好的', 'ok', '是的', '不行', '嗯', '哦',
                '吃了吗', '忙吗', '在干嘛', '睡了吗', '累吗', '还好吗', '怎么样'
            ]
            if not any(exclusion in user_input.lower() for exclusion in chat_exclusions):
                # 检查是否包含中文字符（可能是中文人名或术语）
                if re.search(r'[\u4e00-\u9fff]', user_input):
                    return "task"
        
        # 6. 检查是否很短的查询（通常是闲聊）
        if len(user_input_clean) < 3:
            return "chat"
        
        # 7. 改进的疑问句检测 - 先排除闲聊疑问句
        # 明确的闲聊疑问句（已经在上面处理过，这里再次确认）
        chat_question_keywords = [
            "吃了吗", "忙吗", "在干嘛", "睡了吗", "累吗", "还好吗", "怎么样",
            "身体好吗", "工作怎么样", "学习怎么样", "回来了吗", "到家了吗"
        ]
        
        is_chat_question = any(keyword in user_input_clean for keyword in chat_question_keywords)
        
        if not is_chat_question:
            # 只有在非闲聊疑问句的情况下，才进行任务疑问句检测
            question_patterns = [
                r'[\?\？]',  # 包含问号
                r'(什么|怎么|为什么|哪里|如何|多少|几)',  # 疑问词
                r'(谁|when|where|what|why|how)',
                r'(告诉我|给我|帮我找|我想知道|我需要)'
            ]
            
            for pattern in question_patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return "task"
        
        # 8. 使用LLM进行更精确的判断
        if self.llm_client and len(user_input_clean) > 10:
            try:
                prompt = f"""
你是一个智能助手，需要判断用户查询是否需要使用工具执行。

用户查询: "{user_input}"

判断标准:
1. 如果是简单问候、寒暄、感谢、日常闲聊（如"吃了吗"、"忙吗"、"在干嘛"等） → 返回 "chat"
2. 如果需要搜索信息、处理文件、执行具体任务 → 返回 "task"
3. 如果是询问助手功能、求助等 → 返回 "task"
4. 如果是查询历史人物、知识问题、专有名词解释 → 返回 "task"
5. 如果是简短的人名、地名、术语查询（如"李斯"、"秦始皇"） → 返回 "task"

特别注意：
- 中文日常问候如"吃了吗"、"忙吗"、"在干嘛"、"睡了吗"、"累吗"等都是闲聊
- "查一下XX"、"XX是谁"、"XX怎么样" 等都是任务查询
- 历史人物、科学概念、地理名词等专有名词查询都是任务
- 纯粹的问候和社交对话才是闲聊

只返回 "chat" 或 "task"，不要其他内容。
"""
                
                response = await self.llm_client.generate(prompt, max_tokens=10, temperature=0.1)
                mode = response.strip().lower()
                
                return "task" if mode == "task" else "chat"
                
            except Exception as e:
                self.logger.warning(f"模式判断失败，使用规则判断: {e}")
        
        # 9. 默认：较长的查询当作任务处理，短查询当作闲聊
        return "task" if len(user_input_clean) > 10 else "chat"
    
    async def _handle_chat_mode_streaming(self, user_input: str, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """处理闲聊模式 - 流式输出"""
        start_time = time.time()  # 记录开始时间
        try:
            # 尝试使用LLM客户端
            if self.llm_client:
                try:
                    # 构建对话历史
                    messages = []
                    session = self.sessions[session_id]
                    
                    # 添加历史消息（最近10条）
                    for msg in session['messages'][-10:]:
                        messages.append({"role": msg["role"], "content": msg["content"]})
                    
                    # 添加当前用户消息
                    messages.append({"role": "user", "content": user_input})
                    
                    # 检查是否支持流式生成
                    if hasattr(self.llm_client, 'generate_streaming'):
                        print(f"🔍 LLM客户端支持流式生成，开始流式处理...")
                        # 流式生成回复
                        content_buffer = ""
                        try:
                            async for chunk in self.llm_client.generate_streaming(messages, max_tokens=300, temperature=0.7):
                                print(f"🔍 收到LLM流式块: {chunk}")
                                if chunk.get('type') == 'content':
                                    content = chunk.get('content', '')
                                    content_buffer += content
                                    
                                    # 🎯 关键修复：发送正确的chat_streaming格式
                                    streaming_event = {
                                        "type": "status",
                                        "data": {
                                            "type": "chat_streaming",
                                            "message": f"生成中: {content_buffer}",
                                            "partial_content": content,
                                            "accumulated_content": content_buffer
                                        },
                                        "session_id": session_id,
                                        "timestamp": time.time()
                                    }
                                    
                                    # 🔍 调试：打印实际发送的事件
                                    print(f"🔍 LLM流式事件: {streaming_event}")
                                    
                                    yield streaming_event
                        except Exception as stream_error:
                            print(f"❌ LLM流式生成异常: {stream_error}")
                            raise stream_error
                        
                        # 发送最终完整响应（流式生成完成后）
                        if content_buffer.strip():
                            final_response = content_buffer.strip()
                        else:
                            final_response = "你好！有什么可以帮助您的吗？"
                        
                        print(f"🔍 LLM流式生成完成，最终响应: {final_response}")
                    else:
                        print(f"🔍 LLM客户端不支持流式生成，使用模拟流式输出...")
                        
                        # 降级到同步生成，但仍然以流式方式返回
                        response = await self.llm_client.generate_from_messages(messages)
                        final_response = response
                        
                        # 模拟流式输出效果
                        import asyncio
                        words = final_response.split()
                        content_buffer = ""
                        for i, word in enumerate(words):
                            content_buffer += (word + " " if i < len(words) - 1 else word)
                            
                            streaming_event = {
                                "type": "status",
                                "data": {
                                    "type": "chat_streaming",
                                    "message": f"生成中: {content_buffer}",
                                    "partial_content": word + (" " if i < len(words) - 1 else ""),
                                    "accumulated_content": content_buffer
                                },
                                "session_id": session_id,
                                "timestamp": time.time()
                            }
                            
                            # 🔍 调试：打印模拟流式事件
                            print(f"🔍 模拟流式事件: {streaming_event}")
                            
                            yield streaming_event
                            # 小延迟增加流式效果
                            await asyncio.sleep(0.05)
                        
                        final_response = content_buffer
                    
                    # 更新会话历史
                    session['messages'].extend([
                        {"role": "user", "content": user_input, "timestamp": time.time()},
                        {"role": "assistant", "content": final_response, "timestamp": time.time()}
                    ])
                    
                    yield {
                        "type": "result",
                        "data": {
                            "final_response": final_response,
                            "mode": "chat",
                            "execution_time": time.time() - start_time
                        },
                        "session_id": session_id,
                        "timestamp": time.time()
                    }
                    return
                    
                except Exception as e:
                    self.logger.warning(f"LLM闲聊回复失败，使用智能回退: {e}")
            
            # LLM不可用或失败时，使用智能回退机制
            fallback_response = self._generate_fallback_chat_response(user_input)
            
            # 更新会话历史（如果会话存在）
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session['messages'].extend([
                    {"role": "user", "content": user_input, "timestamp": time.time()},
                    {"role": "assistant", "content": fallback_response, "timestamp": time.time()}
                ])
            
            yield {
                "type": "result",
                "data": {
                    "final_response": "你好！很高兴见到你，有什么可以帮助你的吗？",
                    "mode": "chat",
                    "execution_time": 0.1
                },
                "session_id": session_id,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"闲聊模式处理失败: {e}")
            # 最后的兜底回复
            yield {
                "type": "result",
                "data": {
                    "final_response": "你好！很高兴见到你，有什么可以帮助你的吗？",
                    "mode": "chat",
                    "execution_time": 0.1
                },
                "session_id": session_id,
                "timestamp": time.time()
            }
    
    async def _handle_task_mode_streaming(self, user_input: str, session_id: str, start_time: float) -> AsyncGenerator[Dict[str, Any], None]:
        """处理任务模式 - 通过MCP适配器，带实时状态推送"""
        try:
            # 构建MCP标准请求
            mcp_request = {
                "mcp_version": "1.0",
                "session_id": session_id,
                "request_id": str(uuid.uuid4()),
                "user_query": user_input,
                "context": self.sessions[session_id]['context']
            }
            
            # 1. 发送任务规划开始
            yield {
                "type": "task_planning",
                "session_id": session_id,
                "message": "正在分析任务并制定执行计划...",
                "timestamp": time.time()
            }
            
            # 2. 发送任务开始信号
            yield {
                "type": "task_start",
                "session_id": session_id,
                "message": "开始任务执行",
                "timestamp": time.time()
            }
            
            # 3. 发送工具开始信号
            tool_name = "smart_search" if any(keyword in user_input for keyword in ["搜索", "查找", "搜", "查"]) else "general_tool"
            step_id = f"step_{tool_name}_{int(time.time())}"  # 生成唯一的step_id
            
            tool_start_message = {
                "type": "tool_start",
                "session_id": session_id,
                "message": f"正在执行工具: {tool_name}",
                "tool_name": tool_name,
                "step_id": step_id,  # 添加step_id字段
                "step_index": 1,
                "total_steps": 1,
                "timestamp": time.time()
            }
            
            # 调试日志：确认消息格式
            self.logger.info(f"🔧 发送tool_start消息: tool_name={tool_name}, step_id={step_id}")
            yield tool_start_message
            
            # 添加延迟模拟真实执行过程
            await asyncio.sleep(0.5)  # 模拟工具启动时间
            
            # 4. 设置MCP适配器的状态回调（关键修复！实时推送而非收集）
            async def task_status_callback(message):
                """任务状态回调函数 - 实时推送TaskEngine消息"""
                try:
                    self.logger.info(f"📤 TaskEngine状态更新: {message.get('type')} - {message.get('message', '')}")
                    
                    # 转换TaskEngine消息格式为前端期望的格式
                    converted_message = None
                    msg_type = message.get('type')
                    
                    if msg_type == 'task_start':
                        # 任务开始消息保持原样
                        converted_message = {
                            "type": "task_start",
                            "session_id": session_id,
                            "message": message.get('message', '开始任务执行'),
                            "timestamp": time.time()
                        }
                    
                    elif msg_type == 'tool_start':
                        # 工具开始消息 - 转换为前端期望的格式
                        converted_message = {
                            "type": "tool_start",
                            "session_id": session_id,
                            "message": message.get('message', '工具开始执行'),
                            "tool_name": message.get('tool_name', 'unknown_tool'),
                            "step_id": message.get('step_id', f"task_step_{int(time.time())}"),
                            "step_index": message.get('step_index', 0),
                            "total_steps": message.get('total_steps', 1),
                            "timestamp": time.time()
                        }
                    
                    elif msg_type == 'tool_result':
                        # 工具结果消息 - 转换为前端期望的格式
                        converted_message = {
                            "type": "tool_result",
                            "session_id": session_id,
                            "message": message.get('message', '工具执行完成'),
                            "step_data": {
                                "id": message.get('step_id', f"task_step_{int(time.time())}"),
                                "tool_name": message.get('tool_name', 'unknown_tool'),
                                "status": message.get('status', 'success'),
                                "result": message.get('result', ''),
                                "execution_time": message.get('execution_time', 0)
                            },
                            "status": message.get('status', 'success'),
                            "timestamp": time.time()
                        }
                    
                    elif msg_type == 'task_complete':
                        # 任务完成消息保持原样
                        converted_message = {
                            "type": "task_complete",
                            "session_id": session_id,
                            "message": message.get('message', '任务执行完成'),
                            "execution_time": message.get('execution_time', 0),
                            "timestamp": time.time()
                        }
                    
                    # 立即通过生成器推送消息，而不是收集到数组
                    if converted_message:
                        self.logger.info(f"✅ 实时推送TaskEngine消息: {msg_type} -> 前端")
                        # 这里我们无法直接yield，需要通过其他方式实时推送
                        # 暂时记录到实例变量中，让主流程处理
                        if not hasattr(self, '_pending_status_messages'):
                            self._pending_status_messages = []
                        self._pending_status_messages.append(converted_message)
                    
                except Exception as e:
                    self.logger.error(f"TaskEngine状态回调失败: {e}")
            
            # 设置MCP适配器的状态回调
            self.mcp_adapter.set_status_callback(task_status_callback)
            
            # 初始化待推送消息列表
            self._pending_status_messages = []
            
            # 5. 调用MCP适配器处理（异步处理，同时检查待推送消息）
            # 创建MCP处理任务
            mcp_task = asyncio.create_task(self.mcp_adapter.handle_request(mcp_request))
            
            # 定期检查并推送待处理的状态消息
            while not mcp_task.done():
                # 推送所有待处理的状态消息
                if hasattr(self, '_pending_status_messages') and self._pending_status_messages:
                    for status_msg in self._pending_status_messages:
                        yield status_msg
                    self._pending_status_messages.clear()
                
                # 短暂等待，避免占用太多CPU
                await asyncio.sleep(0.1)
            
            # 获取MCP处理结果
            response = await mcp_task
            
            # 推送剩余的状态消息
            if hasattr(self, '_pending_status_messages') and self._pending_status_messages:
                for status_msg in self._pending_status_messages:
                    yield status_msg
                self._pending_status_messages.clear()
            
            # 添加延迟模拟处理时间
            await asyncio.sleep(1.0)  # 模拟工具执行时间
            
            # 6. 发送工具完成信号
            tool_result_message = {
                "type": "tool_result",
                "session_id": session_id,
                "message": f"工具 {tool_name} 执行完成",
                "step_data": {
                    "id": step_id,  # 使用相同的step_id
                    "tool_name": tool_name,
                    "status": "success" if response.get("status") == "success" else "error",
                    "result": response.get("final_response", ""),
                    "execution_time": 1.5  # 添加执行时间
                },
                "status": "success" if response.get("status") == "success" else "error",
                "timestamp": time.time()
            }
            
            # 调试日志：确认消息格式
            self.logger.info(f"✅ 发送tool_result消息: step_id={step_id}, status={tool_result_message['status']}")
            yield tool_result_message
            
            # 更新会话上下文
            if 'context' in response:
                self.sessions[session_id]['context'].update(response['context'])
            
            # 7. 发送任务完成信号
            yield {
                "type": "task_complete",
                "session_id": session_id,
                "message": response.get("final_response", "任务执行完成"),
                "execution_time": time.time() - start_time,
                "steps": response.get("steps", []),
                "mcp_response": response,  # 包含完整的MCP响应
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"任务模式处理失败: {e}")
            yield {
                "type": "error",
                "session_id": session_id,
                "message": f"任务执行失败: {str(e)}",
                "timestamp": time.time()
            }
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        return self.sessions.get(session_id)
    
    def clear_session(self, session_id: str) -> bool:
        """清除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    async def _handle_chat_mode(self, query: str) -> str:
        """处理闲聊模式"""
        try:
            # 如果有可用的LLM客户端，使用它
            if self.llm_client:
                try:
                    response = await self.llm_client.generate(
                        f"你是一个友好的AI助手。用户说: \"{query}\"\n请给出自然、友好的回应，保持简洁。",
                        max_tokens=100,
                        temperature=0.7
                    )
                    if response and response.strip():
                        return response.strip()
                except Exception as e:
                    self.logger.warning(f"LLM闲聊回复失败: {e}")
            
            # LLM不可用时的智能回退机制
            return self._generate_fallback_chat_response(query)
            
        except Exception as e:
            self.logger.error(f"闲聊模式处理失败: {e}")
            return self._generate_fallback_chat_response(query)
    
    def _generate_fallback_chat_response(self, query: str) -> str:
        """生成回退的聊天回复（不依赖LLM）"""
        query_lower = query.lower().strip()
        
        # 问候回复
        greetings = {
            '你好': '你好！很高兴见到你，有什么可以帮助你的吗？',
            'hi': 'Hi! 很高兴见到你，有什么可以帮助你的吗？',
            'hello': 'Hello! 很高兴见到你，有什么可以帮助你的吗？',
            '早上好': '早上好！新的一天开始了，有什么需要帮助的吗？',
            '下午好': '下午好！希望你今天过得愉快，有什么可以帮助你的吗？',
            '晚上好': '晚上好！希望你今天过得充实，有什么需要帮助的吗？',
        }
        
        # 感谢回复
        thanks = {
            '谢谢': '不客气！很高兴能帮到你。',
            'thanks': 'You\'re welcome! 很高兴能帮到你。',
            '感谢': '不用谢！这是我应该做的。',
        }
        
        # 告别回复
        goodbyes = {
            '再见': '再见！希望下次还能为你提供帮助。',
            'bye': 'Bye! 希望下次还能为你提供帮助。',
            '拜拜': '拜拜！有需要随时找我哦。',
            'goodbye': 'Goodbye! 希望下次还能为你提供帮助。',
        }
        
        # 状态询问回复
        status_queries = {
            '怎么样': '我很好，谢谢关心！作为AI助手，我随时准备为你提供帮助。',
            '还好吗': '我很好！随时准备为你服务。有什么需要帮助的吗？',
            '忙不忙': '我不会感到忙碌，随时都可以为你提供帮助！',
        }
        
        # 能力询问回复
        capability_queries = {
            '你是谁': '我是一个AI助手，可以帮你搜索信息、处理文件、回答问题等。有什么需要帮助的吗？',
            '你会什么': '我可以帮你搜索网络信息、处理各种文件、回答问题、进行数据分析等。有什么具体需要帮助的吗？',
            '你能做什么': '我可以为你提供信息搜索、文件处理、问题解答等服务。告诉我你需要什么帮助吧！',
        }
        
        # 尝试匹配具体的回复
        for pattern, response in greetings.items():
            if pattern in query_lower:
                return response
        
        for pattern, response in thanks.items():
            if pattern in query_lower:
                return response
        
        for pattern, response in goodbyes.items():
            if pattern in query_lower:
                return response
        
        for pattern, response in status_queries.items():
            if pattern in query_lower:
                return response
        
        for pattern, response in capability_queries.items():
            if pattern in query_lower:
                return response
        
        # 确认类回复
        confirmations = ['好的', 'ok', '是的', '对的', '嗯', '行']
        if any(conf in query_lower for conf in confirmations):
            return '好的！有什么其他需要帮助的吗？'
        
        # 否定类回复
        negations = ['不是', '不对', '不行', 'no']
        if any(neg in query_lower for neg in negations):
            return '好的，我明白了。有什么其他可以帮助你的吗？'
        
        # 默认友好回复
        default_responses = [
            '我明白了。作为AI助手，我可以帮你搜索信息、处理文件等。有什么具体需要帮助的吗？',
            '很高兴和你聊天！我可以为你提供各种帮助，比如搜索信息、回答问题等。',
            '感谢你的交流！我随时准备为你提供帮助，有什么需要的尽管说。',
        ]
        
        # 根据查询长度选择不同的回复
        if len(query) <= 5:
            return default_responses[0]
        elif len(query) <= 15:
            return default_responses[1]
        else:
            return default_responses[2]


# 全局变量声明（在文件开头）
engine: Optional[StreamingMCPEngine] = None
mcp_adapter: Optional[MCPAdapter] = None
protocol_adapter: Optional[ProtocolAdapter] = None

# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global engine, mcp_adapter, protocol_adapter  # 添加全局变量声明
    
    logger.info("🚀 启动标准MCP协议API服务（支持流式问答）")
    
    # 初始化数据库
    db_manager = get_database_manager()
    
    # 导入工具
    try:
        import_tools()
        logger.info("✅ 工具导入完成")
    except Exception as e:
        logger.warning(f"⚠️ 工具导入失败: {e}")
    
    # 初始化MCP适配器
    mcp_adapter = MCPAdapter(tool_registry=None, max_sessions=1000)
    app.state.mcp_adapter = mcp_adapter
    
    # 初始化流式引擎
    llm_config = {
        "type": "openai",  # 或 "ernie"
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": os.getenv("OPENAI_MODEL", "gpt-4-turbo"),
        "base_url": os.getenv("OPENAI_API_BASE")  # 修复：使用正确的环境变量名
    }
    
    engine = StreamingMCPEngine(llm_config=llm_config, mcp_adapter=mcp_adapter)
    app.state.streaming_engine = engine
    
    logger.info("🎉 MCP协议API服务启动完成（纯MCP工具系统）")
    
    # 初始化协议适配器
    protocol_adapter = ProtocolAdapter(mcp_adapter)
    app.state.protocol_adapter = protocol_adapter
    logger.info("🔄 协议适配器初始化完成")
    
    yield
    
    logger.info("🛑 标准MCP协议API服务关闭")


# 创建FastAPI应用
app = FastAPI(
    title="MCP AutoGen Standard API",
    description="符合MCP 1.0标准的智能工具调用系统，支持流式问答",
    version="2.1.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径 - API信息"""
    return {
        "name": "MCP AutoGen Standard API",
        "version": "2.1.0",
        "protocol": "MCP 1.0",
        "description": "符合MCP标准的智能工具调用系统，支持流式问答",
        "endpoints": {
            "mcp_request": "/mcp/request",
            "mcp_websocket": "/ws/mcp/standard",
            "streaming_chat": "/ws/mcp/chat",
            "health": "/health",
            "info": "/mcp/info",
            "tools": "/mcp/tools",
            "system_status": "/mcp/system/status",
            "sessions": "/mcp/sessions"
        },
        "demos": {
            "standard_mcp": "/demo/standard",
            "streaming_chat": "/demo/streaming"
        },
        "features": [
            "标准MCP协议支持",
            "流式问答",
            "智能模式检测",
            "会话管理",
            "MCP工具调用",
            "实时状态推送",
            "动态执行流程展示"
        ],
        "system_info": {
            "llm_available": LLM_AVAILABLE,
            "status_manager_active": True
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "2.1.0",
        "protocol": "MCP 1.0",
        "features": {
            "streaming": True,
            "llm_available": LLM_AVAILABLE,
            "mcp_standard": True
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/mcp/info")
async def mcp_info():
    """获取MCP适配器信息"""
    try:
        mcp_adapter = app.state.mcp_adapter
        info = mcp_adapter.get_mcp_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取MCP信息失败: {str(e)}")


@app.get("/mcp/tools")
async def list_mcp_tools():
    """获取可用工具列表"""
    try:
        mcp_adapter = app.state.mcp_adapter
        tool_list = mcp_adapter.tool_registry.get_tool_list()
        
        # 如果tool_list是列表，直接使用
        if isinstance(tool_list, list):
            tools = tool_list
        else:
            # 如果是字典，转换为列表
            tools = []
            for tool_name, tool_info in tool_list.items():
                tools.append({
                    "name": tool_name,
                    "description": tool_info.get("description", ""),
                    "parameters": tool_info.get("parameters", {}),
                    "source": tool_info.get("source", "unknown")
                })
        
        return {
            "mcp_version": "1.0",
            "tools": tools,
            "tool_count": len(tools),
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {str(e)}")



@app.get("/mcp/system/status")
async def get_system_status():
    """获取系统状态信息"""
    try:
        # 基础状态
        status = {
            "mcp_version": "1.0",
            "api_version": "2.1.0", 
            "llm_available": LLM_AVAILABLE,
            "timestamp": time.time()
        }
        
        # MCP工具系统状态
        mcp_adapter = app.state.mcp_adapter
        if mcp_adapter:
            try:
                mcp_tools = mcp_adapter.tool_registry.get_tool_list()
                mcp_tool_count = len(mcp_tools) if isinstance(mcp_tools, list) else len(mcp_tools.keys())
                status["mcp_tools"] = {
                    "enabled": True,
                    "tool_count": mcp_tool_count
                }
            except Exception as e:
                status["mcp_tools"] = {
                    "enabled": False,
                    "error": str(e)
                }
        
        # 状态管理器状态
        current_plan = global_status_manager.get_current_plan()
        status["status_manager"] = {
            "active": True,
            "current_plan": current_plan.to_dict() if current_plan else None,
            "callback_count": len(global_status_manager.callbacks)
        }
        
        return status
        
    except Exception as e:
        return {
            "success": False,
            "error": f"获取系统状态失败: {e}",
            "timestamp": time.time()
        }


@app.post("/mcp/request", response_model=MCPStandardResponse)
async def mcp_standard_request(request: MCPStandardRequest):
    """
    标准MCP协议请求处理
    完全符合MCP 1.0标准的同步请求处理
    """
    try:
        mcp_adapter = app.state.mcp_adapter
        
        # 转换为字典格式
        request_dict = request.dict()
        
        # 处理请求
        response_dict = await mcp_adapter.handle_request(request_dict)
        
        # 返回标准响应
        return MCPStandardResponse(**response_dict)
        
    except Exception as e:
        logger.error(f"❌ MCP标准请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"请求处理失败: {str(e)}")


@app.websocket("/ws/mcp/chat")
async def mcp_streaming_chat(websocket: WebSocket):
    """
    流式MCP聊天接口 - 增强版
    支持智能模式检测、实时流式输出和状态推送
    """
    await websocket.accept()
    logger.info("🌊 增强版流式MCP聊天连接已建立")
    
    # 状态管理器回调函数
    websocket_callback = None
    
    try:
        streaming_engine = app.state.streaming_engine
        
        while True:
            try:
                # 接收客户端消息
                data = await websocket.receive_text()
                request_data = json.loads(data)
                
                user_input = request_data.get("user_input", "")
                session_id = request_data.get("session_id")
                
                if not user_input.strip():
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "用户输入不能为空"
                    }, ensure_ascii=False))
                    continue

                logger.info(f"📝 收到增强版聊天请求: {user_input[:50]}...")
                
                # 设置WebSocket状态回调
                async def websocket_send_func(message):
                    """WebSocket发送函数"""
                    try:
                        await websocket.send_text(json.dumps(message, ensure_ascii=False))
                    except Exception as e:
                        logger.error(f"状态消息发送失败: {e}")
                
                # 创建并注册WebSocket回调
                if websocket_callback:
                    global_status_manager.remove_callback(websocket_callback)
                
                websocket_callback = WebSocketStatusCallback(websocket_send_func)
                global_status_manager.add_callback(websocket_callback)
                
                # 直接使用StreamingMCPEngine处理所有请求（包含智能模式检测）
                streaming_engine = app.state.streaming_engine
                async for result in streaming_engine.execute_streaming_conversation(user_input, session_id):
                    await websocket.send_text(json.dumps(result, ensure_ascii=False))
                
                logger.info("✅ 增强版聊天请求处理完成")
                
            except json.JSONDecodeError as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"JSON解析错误: {str(e)}"
                }, ensure_ascii=False))
                
            except Exception as e:
                logger.error(f"❌ 增强版聊天处理失败: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"处理失败: {str(e)}"
                }, ensure_ascii=False))
                
    except WebSocketDisconnect:
        logger.info("🔌 增强版MCP聊天连接断开")
        if websocket_callback:
            global_status_manager.remove_callback(websocket_callback)
    except Exception as e:
        logger.error(f"❌ 增强版MCP聊天错误: {e}")
        if websocket_callback:
            global_status_manager.remove_callback(websocket_callback)


@app.get("/mcp/sessions/{session_id}")
async def get_session_info(session_id: str):
    """获取会话信息"""
    try:
        # 尝试从流式引擎获取会话信息
        streaming_engine = app.state.streaming_engine
        session_info = streaming_engine.get_session_info(session_id)
        
        if session_info is None:
            # 尝试从MCP适配器获取
                mcp_adapter = app.state.mcp_adapter
                session_info = mcp_adapter.get_session_info(session_id)
        
        if session_info is None:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {
            "mcp_version": "1.0",
            "session_id": session_id,
            "session_info": session_info,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话信息失败: {str(e)}")


@app.delete("/mcp/sessions/{session_id}")
async def clear_session(session_id: str):
    """清除会话"""
    try:
        # 从两个引擎中都清除会话
        streaming_engine = app.state.streaming_engine
        mcp_adapter = app.state.mcp_adapter
        
        success1 = streaming_engine.clear_session(session_id)
        success2 = mcp_adapter.clear_session(session_id)
        
        if not (success1 or success2):
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {
            "mcp_version": "1.0",
            "message": f"会话 {session_id} 已清除",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除会话失败: {str(e)}")


@app.get("/mcp/sessions")
async def list_sessions():
    """列出所有会话"""
    try:
        mcp_adapter = app.state.mcp_adapter
        streaming_engine = app.state.streaming_engine
        
        mcp_session_count = mcp_adapter.get_sessions_count()
        streaming_session_count = len(streaming_engine.sessions)
        
        return {
            "mcp_version": "1.0",
            "active_sessions": {
                "mcp_adapter": mcp_session_count,
                "streaming_engine": streaming_session_count,
                "total": mcp_session_count + streaming_session_count
            },
            "max_sessions": mcp_adapter.sessions.maxsize,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@app.websocket("/ws/mcp/standard")
async def mcp_standard_websocket(websocket: WebSocket):
    """
    标准MCP协议WebSocket接口
    支持流式和批量处理
    """
    await websocket.accept()
    logger.info("🔗 标准MCP WebSocket连接已建立")
    
    try:
        mcp_adapter = app.state.mcp_adapter
        
        while True:
            try:
                # 接收客户端消息
                data = await websocket.receive_text()
                request_data = json.loads(data)
                
                # 验证请求格式
                try:
                    request = MCPStandardRequest(**request_data)
                except Exception as e:
                    await websocket.send_text(json.dumps({
                        "mcp_version": "1.0",
                        "status": "error",
                        "error": {
                            "code": "INVALID_REQUEST_FORMAT",
                            "message": f"请求格式错误: {str(e)}"
                        }
                    }, ensure_ascii=False))
                    continue
                
                logger.info(f"📝 收到标准MCP请求: {request.user_query[:50]}...")
                
                # 处理请求
                response_dict = await mcp_adapter.handle_request(request.dict())
                
                # 发送响应
                await websocket.send_text(json.dumps(response_dict, ensure_ascii=False))
                
                logger.info("✅ 标准MCP请求处理完成")
                
            except json.JSONDecodeError as e:
                await websocket.send_text(json.dumps({
                    "mcp_version": "1.0",
                    "status": "error",
                    "error": {
                        "code": "JSON_DECODE_ERROR",
                        "message": f"JSON解析错误: {str(e)}"
                    }
                }, ensure_ascii=False))
                
            except Exception as e:
                logger.error(f"❌ 标准MCP WebSocket处理失败: {e}")
                await websocket.send_text(json.dumps({
                    "mcp_version": "1.0",
                    "status": "error",
                    "error": {
                        "code": "WEBSOCKET_ERROR",
                        "message": f"WebSocket处理失败: {str(e)}"
                    }
                }, ensure_ascii=False))
                
    except WebSocketDisconnect:
        logger.info("🔌 标准MCP WebSocket连接断开")
    except Exception as e:
        logger.error(f"❌ 标准MCP WebSocket错误: {e}")


# 演示页面
@app.get("/demo/standard")
async def demo_standard_page():
    """标准MCP协议演示页面"""
    demo_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>标准MCP协议演示</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
            background-color: #f8f9fa;
        }
        .header {
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .container { 
            background: white;
            border: 1px solid #e9ecef; 
            border-radius: 12px; 
            padding: 25px; 
            margin: 20px 0; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .container h3 {
            margin-top: 0;
            color: #495057;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
        }
        .input-container { 
            display: flex; 
            gap: 12px; 
            margin: 15px 0; 
            align-items: center;
        }
        .input-container input { 
            flex: 1; 
            padding: 12px 16px; 
            border: 2px solid #e9ecef; 
            border-radius: 8px; 
            font-size: 16px;
            transition: border-color 0.3s;
        }
        .input-container input:focus {
            outline: none;
            border-color: #007bff;
        }
        .input-container button { 
            padding: 12px 20px; 
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); 
            color: white; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-weight: 600;
            transition: all 0.3s;
        }
        .input-container button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
        }
        .json-display { 
            background: #f8f9fa; 
            padding: 16px; 
            border-radius: 8px; 
            font-family: 'Consolas', 'Monaco', monospace; 
            white-space: pre-wrap; 
            border: 1px solid #e9ecef;
            max-height: 400px;
            overflow-y: auto;
            font-size: 14px;
        }
        .status { 
            padding: 8px 16px; 
            border-radius: 6px; 
            font-size: 14px; 
            margin: 10px 0;
            font-weight: 600;
        }
        .status.success { 
            background-color: #d4edda; 
            color: #155724; 
            border: 1px solid #c3e6cb;
        }
        .status.error { 
            background-color: #f8d7da; 
            color: #721c24; 
            border: 1px solid #f5c6cb;
        }
        .status.info { 
            background-color: #d1ecf1; 
            color: #0c5460; 
            border: 1px solid #bee5eb;
        }
        .final-response-preview {
            background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
            border: 2px solid #2196f3;
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
            min-height: 100px;
        }
        .final-response-preview h4 {
            margin: 0 0 15px 0;
            color: #1976d2;
            font-size: 1.2em;
        }
        .final-response-content {
            background: white;
            padding: 15px;
            border-radius: 8px;
            line-height: 1.6;
            white-space: pre-wrap;
            border: 1px solid #e3f2fd;
        }
        .response-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #f8f9fa;
            padding: 12px 16px;
            border-radius: 8px;
            margin: 10px 0;
            font-size: 0.9em;
            color: #6c757d;
        }
        .steps-summary {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
        .steps-summary h5 {
            margin: 0 0 10px 0;
            color: #856404;
        }
        .step-item {
            padding: 8px 12px;
            margin: 5px 0;
            background: white;
            border-radius: 6px;
            border-left: 4px solid #ffc107;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="header">
    <h1>🚀 标准MCP协议演示</h1>
        <p>完全符合MCP 1.0标准的智能工具调用系统 - 支持同步和WebSocket调用</p>
    </div>
    
    <div class="container">
        <h3>📤 MCP请求</h3>
        <div class="input-container">
            <input type="text" id="userQuery" placeholder="输入您的查询..." value="帮我搜索北京的天气">
            <input type="text" id="sessionId" placeholder="会话ID (可选)" style="max-width: 200px;">
            <button onclick="sendMCPRequest()">🚀 发送MCP请求</button>
            <button onclick="sendWebSocketRequest()">🔌 WebSocket请求</button>
        </div>
        <div id="requestDisplay" class="json-display">等待发送请求...</div>
        <div id="status" class="status info">🟢 准备就绪</div>
    </div>
    
    <div class="container">
        <h3>📥 MCP响应</h3>
        
        <!-- 最终响应预览 -->
        <div id="finalResponsePreview" class="final-response-preview" style="display: none;">
            <h4>💬 最终响应 (final_response)</h4>
            <div id="finalResponseContent" class="final-response-content"></div>
        </div>
        
        <!-- 响应元数据 -->
        <div id="responseMeta" class="response-meta" style="display: none;">
            <span id="responseStatus"></span>
            <span id="responseTime"></span>
            <span id="responseCost"></span>
        </div>
        
        <!-- 执行步骤摘要 -->
        <div id="stepsSummary" class="steps-summary" style="display: none;">
            <h5>🔧 执行步骤摘要</h5>
            <div id="stepsContent"></div>
        </div>
        
        <!-- 原始JSON响应 -->
        <details>
            <summary style="cursor: pointer; padding: 10px; background: #f8f9fa; border-radius: 8px; margin: 10px 0;">
                <strong>📋 原始JSON响应 (点击查看详细)</strong>
            </summary>
        <div id="responseDisplay" class="json-display">等待响应...</div>
        </details>
    </div>
    
    <div class="container">
        <h3>🔧 系统信息</h3>
        <div id="systemInfo" class="json-display">加载中...</div>
    </div>

    <script>
        let ws = null;
        
        async function sendMCPRequest() {
            const userQuery = document.getElementById('userQuery').value;
            const sessionId = document.getElementById('sessionId').value;
            
            if (!userQuery.trim()) {
                updateStatus('请输入查询内容', 'error');
                return;
            }
            
            const request = {
                mcp_version: "1.0",
                session_id: sessionId || null,
                request_id: generateUUID(),
                user_query: userQuery,
                context: {
                    user_profile: {},
                    conversation_history: []
                }
            };
            
            document.getElementById('requestDisplay').textContent = JSON.stringify(request, null, 2);
            updateStatus('🚀 发送HTTP请求中...', 'info');
            hideResponseSections();
            
            try {
                const response = await fetch('/mcp/request', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(request)
                });
                
                const result = await response.json();
                
                // 显示原始JSON
                document.getElementById('responseDisplay').textContent = JSON.stringify(result, null, 2);
                
                // 显示格式化的响应
                displayFormattedResponse(result);
                
                if (response.ok) {
                    updateStatus('✅ 请求成功完成', 'success');
                } else {
                    updateStatus('❌ 请求失败', 'error');
                }
                
            } catch (error) {
                updateStatus(`❌ 请求失败: ${error.message}`, 'error');
                document.getElementById('responseDisplay').textContent = `错误: ${error.message}`;
            }
        }
        
        function sendWebSocketRequest() {
            const userQuery = document.getElementById('userQuery').value;
            const sessionId = document.getElementById('sessionId').value;
            
            if (!userQuery.trim()) {
                updateStatus('请输入查询内容', 'error');
                return;
            }
            
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws/mcp/standard`);
            
            ws.onopen = function() {
                updateStatus('🔌 WebSocket连接已建立', 'success');
                
                const request = {
                    mcp_version: "1.0",
                    session_id: sessionId || null,
                    request_id: generateUUID(),
                    user_query: userQuery,
                    context: {
                        user_profile: {},
                        conversation_history: []
                    }
                };
                
                document.getElementById('requestDisplay').textContent = JSON.stringify(request, null, 2);
                ws.send(JSON.stringify(request));
                updateStatus('📤 WebSocket请求已发送', 'info');
                hideResponseSections();
            };
            
            ws.onmessage = function(event) {
                const response = JSON.parse(event.data);
                
                // 显示原始JSON
                document.getElementById('responseDisplay').textContent = JSON.stringify(response, null, 2);
                
                // 显示格式化的响应
                displayFormattedResponse(response);
                
                updateStatus('📥 WebSocket响应已接收', 'success');
            };
            
            ws.onclose = function() {
                updateStatus('🔌 WebSocket连接已关闭', 'info');
            };
            
            ws.onerror = function(error) {
                updateStatus('❌ WebSocket连接错误', 'error');
            };
        }
        
        function displayFormattedResponse(response) {
            // 显示最终响应
            if (response.final_response) {
                document.getElementById('finalResponsePreview').style.display = 'block';
                document.getElementById('finalResponseContent').textContent = response.final_response;
            }
            
            // 显示响应元数据
            if (response.status || response.execution_time !== undefined) {
                document.getElementById('responseMeta').style.display = 'flex';
                
                const statusText = response.status === 'success' ? '✅ 成功' : 
                                 response.status === 'error' ? '❌ 错误' : 
                                 response.status === 'partial' ? '⚠️ 部分成功' : response.status;
                document.getElementById('responseStatus').textContent = `状态: ${statusText}`;
                
                document.getElementById('responseTime').textContent = 
                    `⏱️ 执行时间: ${(response.execution_time || 0).toFixed(2)}秒`;
                
                if (response.cost_estimation) {
                    const cost = response.cost_estimation;
                    document.getElementById('responseCost').textContent = 
                        `💰 成本: ${cost.tool_calls || 0} 次调用, ${cost.token_usage || 0} tokens`;
                }
            }
            
            // 显示执行步骤
            if (response.steps && response.steps.length > 0) {
                document.getElementById('stepsSummary').style.display = 'block';
                const stepsHtml = response.steps.map((step, index) => {
                    let stepDescription = `<strong>步骤 ${index + 1}:</strong> ${step.tool_name || 'Unknown'} 
                        <span style="color: #6c757d;">- ${step.status || 'unknown'}</span>`;
                    
                    return `<div class="step-item">${stepDescription}</div>`;
                }).join('');
                document.getElementById('stepsContent').innerHTML = stepsHtml;
            }
        }
        
        function hideResponseSections() {
            document.getElementById('finalResponsePreview').style.display = 'none';
            document.getElementById('responseMeta').style.display = 'none';
            document.getElementById('stepsSummary').style.display = 'none';
        }
        
        function updateStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = `status ${type}`;
        }
        
        function generateUUID() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0;
                const v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }
        
        // 加载系统信息
        async function loadSystemInfo() {
            try {
                const [infoResponse, toolsResponse] = await Promise.all([
                    fetch('/mcp/info'),
                    fetch('/mcp/tools')
                ]);
                
                const info = await infoResponse.json();
                const tools = await toolsResponse.json();
                
                const systemInfo = {
                    mcp_info: info,
                    available_tools: tools.tools.length,
                    tools_sample: tools.tools.slice(0, 3).map(t => ({
                        name: t.name,
                        description: t.description
                    }))
                };
                
                document.getElementById('systemInfo').textContent = JSON.stringify(systemInfo, null, 2);
            } catch (error) {
                document.getElementById('systemInfo').textContent = `加载失败: ${error.message}`;
            }
        }
        
        // 页面加载完成后执行
        document.addEventListener('DOMContentLoaded', function() {
            loadSystemInfo();
        });
    </script>
</body>
</html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=demo_html)


@app.get("/demo/streaming")
async def demo_streaming_page():
    """流式聊天演示页面"""
    demo_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>流式MCP聊天演示</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
            background-color: #f8f9fa;
        }
        .header {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .chat-container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            height: 600px;
            display: flex;
            flex-direction: column;
        }
        .chat-header {
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #e9ecef;
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .message {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 18px;
            line-height: 1.4;
            word-wrap: break-word;
        }
        .message.user {
            align-self: flex-end;
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
        }
        .message.assistant {
            align-self: flex-start;
            background: #e9ecef;
            color: #333;
        }
        .message.system {
            align-self: center;
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
            font-size: 0.9em;
            text-align: center;
        }
        .message.error {
            align-self: center;
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .chat-input {
            border-top: 1px solid #e9ecef;
            padding: 20px;
            display: flex;
            gap: 12px;
            align-items: center;
        }
        .chat-input input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e9ecef;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        .chat-input input:focus {
            border-color: #28a745;
        }
        .chat-input button {
            padding: 12px 24px;
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        .chat-input button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4);
        }
        .chat-input button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .status {
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .status.connected {
            background-color: #d4edda;
            color: #155724;
        }
        .status.disconnected {
            background-color: #f8d7da;
            color: #721c24;
        }
        .status.processing {
            background-color: #d1ecf1;
            color: #0c5460;
        }
        .mode-indicator {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
            margin-left: 10px;
        }
        .mode-indicator.chat {
            background-color: #e3f2fd;
            color: #1976d2;
        }
        .mode-indicator.task {
            background-color: #fff3e0;
            color: #f57c00;
        }
        .typing-indicator {
            display: none;
            align-self: flex-start;
            padding: 12px 16px;
            background: #e9ecef;
            border-radius: 18px;
            color: #666;
            font-style: italic;
        }
        .typing-indicator.show {
            display: block;
        }
        .mode-banner {
            align-self: stretch;
            padding: 8px 16px;
            margin: 10px 0;
            border-radius: 8px;
            font-size: 0.9em;
            font-weight: 600;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .mode-banner.chat {
            background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
            color: #1976d2;
            border: 1px solid #bbdefb;
        }
        .mode-banner.task {
            background: linear-gradient(135deg, #fff3e0 0%, #e8f5e8 100%);
            color: #f57c00;
            border: 1px solid #ffcc02;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>💬 流式MCP聊天演示</h1>
        <p>智能模式检测 + 实时流式对话 - 支持闲聊和任务执行</p>
    </div>
    
    <div class="chat-container">
        <div class="chat-header">
            <div>
                <strong>🤖 智能助手</strong>
                <span id="modeIndicator" class="mode-indicator chat">闲聊模式</span>
            </div>
            <div id="connectionStatus" class="status disconnected">未连接</div>
        </div>
        
        <div id="chatMessages" class="chat-messages">
            <div class="message system">
                👋 欢迎使用流式MCP聊天！我可以进行日常对话，也可以帮您执行各种任务。
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            正在思考中...
        </div>
        
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="输入您的消息..." onkeypress="handleKeyPress(event)">
            <button id="sendButton" onclick="sendMessage()" disabled>发送</button>
        </div>
    </div>

    <script>
        let ws = null;
        let currentSessionId = null;
        let isProcessing = false;
        
        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws/mcp/chat`);
            
            ws.onopen = function() {
                updateConnectionStatus('connected', '已连接');
                document.getElementById('sendButton').disabled = false;
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };
            
            ws.onclose = function() {
                updateConnectionStatus('disconnected', '连接断开');
                document.getElementById('sendButton').disabled = true;
                setTimeout(initWebSocket, 3000); // 3秒后重连
            };
            
            ws.onerror = function(error) {
                updateConnectionStatus('disconnected', '连接错误');
                console.error('WebSocket error:', error);
            };
        }
        
        function handleWebSocketMessage(data) {
            const messagesContainer = document.getElementById('chatMessages');
            const typingIndicator = document.getElementById('typingIndicator');
            
            console.log('收到WebSocket消息:', data); // 调试日志
            
            switch(data.type) {
                case 'mode_detection':
                    currentSessionId = data.session_id;
                    updateModeIndicator(data.mode);
                    // 模式检测完成，等待后续的具体响应来显示模式横幅
                    break;
                    
                case 'chat_response':
                    typingIndicator.classList.remove('show');
                    // 为闲聊模式添加模式标识区域
                    addModeMessage('chat', '💬 闲聊模式');
                    addMessage('assistant', data.message);
                    setProcessing(false);
                    break;
                
                // === 新增：状态管理器消息处理 ===
                case 'task_planning':
                    addMessage('system', '🧠 ' + data.message);
                    break;
                    
                case 'task_start':
                    addModeMessage('task', '🔧 任务执行模式');
                    addMessage('system', '🚀 ' + data.message);
                    
                    // 显示初始执行计划
                    if (data.plan && data.plan.steps) {
                        displayExecutionPlan(data.plan);
                    }
                    break;
                    
                case 'tool_start':
                    addMessage('system', '⚙️ ' + data.message);
                    updateExecutionStep(data.step_id, 'running', data.tool_name);
                    break;
                    
                case 'tool_result':
                    const stepData = data.step_data;
                    const status = stepData.status === 'success' ? '✅' : '❌';
                    const statusText = stepData.status === 'success' ? '成功' : '失败';
                    addMessage('system', `${status} ${stepData.tool_name} - ${statusText}`);
                    updateExecutionStep(stepData.id, stepData.status, stepData.tool_name);
                    break;
                    
                case 'task_complete':
                    typingIndicator.classList.remove('show');
                    addMessage('assistant', data.message);
                    
                    // 显示最终的执行统计
                    if (data.plan) {
                        const successSteps = data.plan.steps.filter(s => s.status === 'success').length;
                        const totalSteps = data.plan.steps.length;
                        addMessage('system', `🎯 任务完成！成功执行 ${successSteps}/${totalSteps} 个步骤`);
                    }
                    
                    setProcessing(false);
                    break;
                    
                case 'error':
                    typingIndicator.classList.remove('show');
                    addMessage('error', '❌ ' + data.message);
                    setProcessing(false);
                    break;
                    
            }
        }
        
        // 新增：显示执行计划的ASCII图表
        function displayExecutionPlan(plan) {
            const messagesContainer = document.getElementById('chatMessages');
            const planDiv = document.createElement('div');
            planDiv.className = 'execution-plan';
            planDiv.id = `plan_${plan.id}`;
            
            let asciiPlan = `
📋 执行计划：
┌─ 👤 用户输入
│
├─ 🧠 LLM分析
│`;
            
            plan.steps.forEach((step, index) => {
                const isLast = index === plan.steps.length - 1;
                const connector = isLast ? '└─' : '├─';
                asciiPlan += `
${connector} ⏳ ${step.tool_name} (待执行)`;
            });
            
            asciiPlan += `
│
└─ ⏱️ 准备输出`;
            
            planDiv.innerHTML = `<pre style="background: #f8f9fa; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 12px; line-height: 1.4; border-left: 4px solid #28a745;">${asciiPlan}</pre>`;
            messagesContainer.appendChild(planDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        // 新增：更新执行步骤状态
        function updateExecutionStep(stepId, status, toolName) {
            const planElement = document.querySelector('.execution-plan');
            if (!planElement) return;
            
            const preElement = planElement.querySelector('pre');
            if (!preElement) return;
            
            let content = preElement.textContent;
            
            // 根据状态更新图标和文字
            const statusIcon = status === 'success' ? '✅' : status === 'error' ? '❌' : '🔄';
            const statusText = status === 'success' ? '已完成' : status === 'error' ? '失败' : '执行中';
            
            // 更新对应工具的状态
            content = content.replace(
                new RegExp(`⏳ ${toolName} \\(待执行\\)`, 'g'),
                `${statusIcon} ${toolName} (${statusText})`
            );
            
            // 如果是执行中，添加动态效果
            if (status === 'running') {
                content = content.replace(
                    new RegExp(`🔄 ${toolName} \\(执行中\\)`, 'g'),
                    `🔄 ${toolName} (执行中...)`
                );
            }
            
            preElement.textContent = content;
            
            // 更新边框颜色
            if (status === 'success') {
                preElement.style.borderLeftColor = '#28a745';
            } else if (status === 'error') {
                preElement.style.borderLeftColor = '#dc3545';
            } else {
                preElement.style.borderLeftColor = '#ffc107';
            }
        }
        
        function addMessage(type, content) {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.textContent = content;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function addModeMessage(type, content) {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `mode-banner ${type}`;
            messageDiv.innerHTML = content;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function updateConnectionStatus(status, text) {
            const statusDiv = document.getElementById('connectionStatus');
            statusDiv.className = `status ${status}`;
            statusDiv.textContent = text;
        }
        
        function updateModeIndicator(mode) {
            const indicator = document.getElementById('modeIndicator');
            indicator.className = `mode-indicator ${mode}`;
            indicator.textContent = mode === 'chat' ? '闲聊模式' : '任务模式';
        }
        
        function setProcessing(processing) {
            isProcessing = processing;
            const sendButton = document.getElementById('sendButton');
            const typingIndicator = document.getElementById('typingIndicator');
            
            if (processing) {
                sendButton.disabled = true;
                sendButton.textContent = '处理中...';
                typingIndicator.classList.add('show');
                updateConnectionStatus('processing', '处理中');
            } else {
                sendButton.disabled = false;
                sendButton.textContent = '发送';
                typingIndicator.classList.remove('show');
                updateConnectionStatus('connected', '已连接');
            }
        }
        
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || !ws || ws.readyState !== WebSocket.OPEN || isProcessing) {
                return;
            }
            
            // 显示用户消息
            addMessage('user', message);
            
            // 发送消息
            ws.send(JSON.stringify({
                user_input: message,
                session_id: currentSessionId
            }));
            
            input.value = '';
            setProcessing(true);
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter' && !isProcessing) {
                sendMessage();
            }
        }
        
        // 初始化
        document.addEventListener('DOMContentLoaded', function() {
            initWebSocket();
        });
    </script>
</body>
</html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=demo_html)


# 添加SSE端点
@app.post("/mcp/sse")
async def mcp_sse_endpoint(request: MCPStandardRequest) -> EventSourceResponse:
    """
    MCP SSE (Server-Sent Events) 端点
    支持流式响应的实时通信
    """
    global protocol_adapter
    
    if not protocol_adapter:
        raise HTTPException(status_code=500, detail="协议适配器未初始化")
    
    try:
        # 转换为字典格式
        request_dict = {
            "mcp_version": request.mcp_version,
            "session_id": request.session_id,
            "request_id": request.request_id,
            "user_query": request.user_query,
            "context": request.context
        }
        
        # 处理SSE请求
        return await protocol_adapter.handle_sse_request(
            request_dict, 
            request.session_id
        )
        
    except Exception as e:
        logger.error(f"SSE端点处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"SSE请求处理失败: {str(e)}")


@app.get("/test/sse")
async def test_sse_endpoint():
    """简单的SSE测试端点"""
    async def generate():
        import json
        yield json.dumps({'message': 'Hello', 'timestamp': '2024-01-01'})
        await asyncio.sleep(1)
        yield json.dumps({'message': 'World', 'timestamp': '2024-01-02'})
        await asyncio.sleep(1) 
        yield json.dumps({'message': 'Done', 'timestamp': '2024-01-03'})
    
    return EventSourceResponse(generate())


@app.get("/protocol/stats")
async def get_protocol_stats():
    """
    获取协议统计信息
    """
    global protocol_adapter
    
    if not protocol_adapter:
        raise HTTPException(status_code=500, detail="协议适配器未初始化")
    
    try:
        stats = protocol_adapter.get_protocol_stats()
        return JSONResponse(content={
            "status": "success",
            "data": stats,
            "timestamp": time.time()
        })
    except Exception as e:
        logger.error(f"获取协议统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@app.get("/protocol/connections")
async def get_active_connections():
    """
    获取活跃连接信息
    """
    global protocol_adapter
    
    if not protocol_adapter:
        raise HTTPException(status_code=500, detail="协议适配器未初始化")
    
    try:
        connections = protocol_adapter.get_sse_connections()
        return JSONResponse(content={
            "status": "success", 
            "data": {
                "sse_connections": list(connections.keys()),
                "total_connections": len(connections)
            },
            "timestamp": time.time()
        })
    except Exception as e:
        logger.error(f"获取连接信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取连接信息失败: {str(e)}")


# 修改根路径以显示新的协议支持信息
@app.get("/")
async def get_api_info():
    """获取API信息和支持的协议"""
    return {
        "service": "MCP AutoGen 2.0 标准API",
        "version": "2.0.0",
        "mcp_version": "1.0",
        "supported_protocols": [
            {
                "name": "HTTP POST",
                "endpoint": "/mcp/chat",
                "description": "标准HTTP POST请求"
            },
            {
                "name": "WebSocket", 
                "endpoint": "/mcp/ws",
                "description": "WebSocket实时双向通信"
            },
            {
                "name": "SSE",
                "endpoint": "/mcp/sse", 
                "description": "Server-Sent Events流式响应"
            },
            {
                "name": "Stdio",
                "endpoint": "mcp_stdio_server.py",
                "description": "标准输入输出通信"
            }
        ],
        "demo_pages": [
            {
                "name": "WebSocket Demo",
                "url": "/demo"
            },
            {
                "name": "SSE Demo", 
                "url": "/mcp/sse/demo"
            }
        ],
        "management": [
            {
                "name": "Protocol Stats",
                "url": "/protocol/stats"
            },
            {
                "name": "Active Connections",
                "url": "/protocol/connections"
            }
        ],
        "tools_count": len(mcp_adapter.tool_registry.list_tools()) if mcp_adapter else 0,
        "status": "running",
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    
    # 获取端口
    port = int(os.getenv("PORT", 8000))
    
    # 启动服务
    uvicorn.run(
        "mcp_standard_api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    ) 