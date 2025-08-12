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
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from core.mcp_protocol_engine import MCPProtocolEngine
from core.execution_status_manager import (
    global_status_manager, WebSocketStatusCallback, 
    ExecutionStatus, MessageType
)


# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        if self.llm_client and len(user_input.strip()) > 10:
            try:
                prompt = f"""
你是一个智能助手，需要判断用户查询是否需要使用工具执行。

用户查询: "{user_input}"

判断标准:
1. 如果是简单问候、寒暄、感谢等闲聊内容 → 返回 "chat"
2. 如果需要搜索信息、处理文件、执行具体任务 → 返回 "task"
3. 如果是询问助手功能、求助等 → 返回 "task"
4. 如果是查询历史人物、知识问题、专有名词解释 → 返回 "task"
5. 如果是简短的人名、地名、术语查询（如"李斯"、"秦始皇"） → 返回 "task"

特别注意：
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
        
        # 6. 默认：较长的查询当作任务处理，短查询当作闲聊
        return "task" if len(user_input.strip()) > 10 else "chat"
    
    async def _handle_chat_mode_streaming(self, user_input: str, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """处理闲聊模式 - 流式输出"""
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
                    
                    # 调用LLM
                    response = await self.llm_client.generate_from_messages(messages)
                    
                    # 更新会话历史
                    session['messages'].extend([
                        {"role": "user", "content": user_input, "timestamp": time.time()},
                        {"role": "assistant", "content": response, "timestamp": time.time()}
                    ])
                    
                    yield {
                        "type": "chat_response",
                        "session_id": session_id,
                        "message": response,
                        "mode": "chat",
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
                "type": "chat_response",
                "session_id": session_id,
                "message": fallback_response,
                "mode": "chat",
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"闲聊模式处理失败: {e}")
            # 最后的兜底回复
            yield {
                "type": "chat_response",
                "session_id": session_id,
                "message": "你好！很高兴见到你，有什么可以帮助你的吗？",
                "mode": "chat",
                "timestamp": time.time()
            }
    
    async def _handle_task_mode_streaming(self, user_input: str, session_id: str, start_time: float) -> AsyncGenerator[Dict[str, Any], None]:
        """处理任务模式 - 通过MCP适配器"""
        try:
            # 构建MCP标准请求
            mcp_request = {
                "mcp_version": "1.0",
                "session_id": session_id,
                "request_id": str(uuid.uuid4()),
                "user_query": user_input,
                "context": self.sessions[session_id]['context']
            }
            
            # 发送任务开始信号
            yield {
                "type": "task_start",
                "session_id": session_id,
                "message": "开始任务执行",
                "timestamp": time.time()
            }
            
            # 调用MCP适配器处理
            response = await self.mcp_adapter.handle_request(mcp_request)
            
            # 更新会话上下文
            if 'context' in response:
                self.sessions[session_id]['context'].update(response['context'])
            
            # 发送任务完成信号
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


# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
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
        "base_url": os.getenv("OPENAI_BASE_URL")
    }
    
    streaming_engine = StreamingMCPEngine(llm_config=llm_config, mcp_adapter=mcp_adapter)
    app.state.streaming_engine = streaming_engine
    
    logger.info("🎉 标准MCP协议API服务启动完成（支持流式问答）")
    
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
            "streaming_chat": "/ws/mcp/chat",  # 新增流式聊天接口
            "health": "/health",
            "info": "/mcp/info",
            "tools": "/mcp/tools",
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
            "工具调用"
        ]
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
                
                # 检查是否是任务模式
                task_keywords = [
                    "搜索", "查找", "下载", "上传", "生成", "创建", "执行", "运行", 
                    "分析", "处理", "转换", "计算", "统计", "图表", "报告", "工具"
                ]
                
                is_task_mode = any(keyword in user_input for keyword in task_keywords)
                
                if is_task_mode:
                    # 任务模式：使用状态管理器
                    await handle_task_mode_with_status(user_input, session_id, streaming_engine)
                else:
                    # 闲聊模式：直接执行对话
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


async def handle_task_mode_with_status(user_input: str, session_id: str, streaming_engine):
    """处理任务模式，集成状态管理器"""
    try:
        # 1. 发送任务规划开始
        await global_status_manager.update_planning("正在分析任务并制定执行计划...")
        
        # 2. 模拟生成执行计划（简化版）
        # 这里应该调用实际的规划引擎，这里只是演示
        import re
        steps_data = []
        
        # 简单的工具检测逻辑
        if "搜索" in user_input or "查找" in user_input:
            steps_data.append({
                "tool_name": "smart_search",
                "description": f"搜索相关信息：{user_input}",
                "input_params": {"query": user_input, "max_results": 5}
            })
        
        if "分析" in user_input:
            steps_data.append({
                "tool_name": "data_analyzer",
                "description": "分析数据",
                "input_params": {"data": user_input}
            })
        
        # 如果没有检测到具体工具，添加默认步骤
        if not steps_data:
            steps_data.append({
                "tool_name": "smart_search",
                "description": f"智能处理：{user_input}",
                "input_params": {"query": user_input}
            })
        
        # 3. 启动执行计划
        execution_plan = await global_status_manager.start_task(user_input, steps_data)
        
        # 4. 模拟执行步骤
        final_results = []
        for step in execution_plan.steps:
            # 开始工具执行
            await global_status_manager.start_tool(
                step.id, step.tool_name, step.input_params
            )
            
            # 模拟工具执行（这里应该调用实际的工具）
            import asyncio
            await asyncio.sleep(1)  # 模拟执行时间
            
            # 模拟执行结果
            mock_result = {
                "tool_name": step.tool_name,
                "status": "success",
                "result": f"模拟执行结果：{step.description}",
                "execution_time": 1.0
            }
            
            # 完成工具执行
            await global_status_manager.complete_tool(
                step.id, step.tool_name, mock_result, ExecutionStatus.SUCCESS
            )
            
            final_results.append(mock_result)
        
        # 5. 生成最终摘要
        final_summary = f"任务执行完成。根据您的请求「{user_input}」，我执行了以下操作：\n\n"
        for i, result in enumerate(final_results, 1):
            final_summary += f"{i}. {result['result']}\n"
        
        final_summary += f"\n总共执行了 {len(final_results)} 个步骤。"
        
        # 6. 完成任务
        await global_status_manager.complete_task(final_summary)
        
    except Exception as e:
        logger.error(f"任务执行失败: {e}")
        await global_status_manager.report_error(f"任务执行失败: {str(e)}")


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
                    
                case 'task_start':
                    addModeMessage('task', '🔧 任务执行模式');
                    addMessage('system', data.message);
                    break;
                    
                case 'task_complete':
                    typingIndicator.classList.remove('show');
                    addMessage('assistant', data.message);
                    if (data.steps && data.steps.length > 0) {
                        addMessage('system', `✅ 任务完成，执行了 ${data.steps.length} 个步骤，用时 ${data.execution_time.toFixed(2)} 秒`);
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


if __name__ == "__main__":
    import uvicorn
    
    # 获取端口
    port = int(os.getenv("PORT", 8002))
    
    # 启动服务
    uvicorn.run(
        "mcp_standard_api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    ) 