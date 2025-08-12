#!/usr/bin/env python3
"""
文心一言客户端 - 支持MCP协议的工具调用
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, List, Optional, AsyncGenerator
import httpx


class ErnieClient:
    """文心一言客户端"""
    
    def __init__(self, api_key: str, secret_key: str, model: str = "ernie-4.0-turbo"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.api_key = api_key
        self.secret_key = secret_key
        self.model = model
        self.access_token = None
        self.token_expires_at = 0
        
        # API端点
        self.token_url = "https://aip.baidubce.com/oauth/2.0/token"
        self.chat_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-4.0-turbo"
    
    async def _get_access_token(self) -> str:
        """获取访问令牌"""
        import time
        
        # 检查token是否过期
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    params={
                        "grant_type": "client_credentials",
                        "client_id": self.api_key,
                        "client_secret": self.secret_key
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                self.access_token = data["access_token"]
                self.token_expires_at = time.time() + data.get("expires_in", 3600) - 60  # 提前1分钟过期
                
                return self.access_token
                
        except Exception as e:
            self.logger.error(f"获取文心一言访问令牌失败: {e}")
            raise
    
    async def generate(self, prompt: str, max_tokens: int = None, temperature: float = 0.7) -> str:
        """简单文本生成"""
        try:
            access_token = await self._get_access_token()
            
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature
            }
            
            if max_tokens:
                payload["max_output_tokens"] = max_tokens
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.chat_url}?access_token={access_token}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                data = response.json()
                return data["result"]
                
        except Exception as e:
            self.logger.error(f"文心一言生成失败: {e}")
            raise
    
    async def generate_from_messages(self, messages: List[Dict[str, Any]], 
                                   max_tokens: int = None, 
                                   temperature: float = 0.7) -> str:
        """从消息列表生成响应"""
        try:
            access_token = await self._get_access_token()
            
            # 过滤掉工具相关的消息，文心一言可能不支持
            filtered_messages = []
            for msg in messages:
                if msg.get("role") in ["user", "assistant"] and msg.get("content"):
                    filtered_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            payload = {
                "messages": filtered_messages,
                "temperature": temperature
            }
            
            if max_tokens:
                payload["max_output_tokens"] = max_tokens
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.chat_url}?access_token={access_token}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                data = response.json()
                return data["result"]
                
        except Exception as e:
            self.logger.error(f"文心一言消息生成失败: {e}")
            raise
    
    async def generate_with_tools(self, messages: List[Dict[str, Any]], 
                                tools: List[Dict[str, Any]],
                                max_tokens: int = None,
                                temperature: float = 0.7) -> Dict[str, Any]:
        """支持工具调用的生成"""
        # 注意：文心一言可能不直接支持OpenAI格式的工具调用
        # 这里我们使用提示工程的方式来模拟工具调用
        
        try:
            access_token = await self._get_access_token()
            
            # 构建工具描述
            tools_description = self._format_tools_for_prompt(tools)
            
            # 构建增强的消息
            enhanced_messages = self._enhance_messages_with_tools(messages, tools_description)
            
            payload = {
                "messages": enhanced_messages,
                "temperature": temperature
            }
            
            if max_tokens:
                payload["max_output_tokens"] = max_tokens
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.chat_url}?access_token={access_token}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                data = response.json()
                result_text = data["result"]
                
                # 解析响应，检查是否包含工具调用
                return self._parse_tool_response(result_text)
                
        except Exception as e:
            self.logger.error(f"文心一言工具调用生成失败: {e}")
            raise
    
    def _format_tools_for_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """将工具格式化为提示文本"""
        if not tools:
            return ""
        
        tools_text = "可用工具列表：\n"
        for tool in tools:
            func = tool.get("function", {})
            name = func.get("name", "")
            description = func.get("description", "")
            parameters = func.get("parameters", {})
            
            tools_text += f"- {name}: {description}\n"
            
            if parameters.get("properties"):
                tools_text += "  参数:\n"
                for param_name, param_info in parameters["properties"].items():
                    param_desc = param_info.get("description", "")
                    param_type = param_info.get("type", "")
                    tools_text += f"    - {param_name} ({param_type}): {param_desc}\n"
        
        tools_text += "\n如果需要使用工具，请按以下JSON格式回复：\n"
        tools_text += '{"tool_calls": [{"name": "工具名", "arguments": {"参数名": "参数值"}}]}\n'
        tools_text += "如果不需要使用工具，直接回复答案。\n\n"
        
        return tools_text
    
    def _enhance_messages_with_tools(self, messages: List[Dict[str, Any]], tools_description: str) -> List[Dict[str, Any]]:
        """在消息中添加工具描述"""
        enhanced_messages = []
        
        # 添加系统消息（如果没有的话）
        if not messages or messages[0].get("role") != "system":
            enhanced_messages.append({
                "role": "user",
                "content": f"系统提示：{tools_description}"
            })
        
        # 添加原始消息
        for msg in messages:
            if msg.get("role") in ["user", "assistant"] and msg.get("content"):
                enhanced_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            elif msg.get("role") == "tool":
                # 将工具结果转换为用户消息
                tool_name = msg.get("name", "工具")
                content = msg.get("content", "")
                enhanced_messages.append({
                    "role": "user",
                    "content": f"{tool_name}执行结果：{content}"
                })
        
        return enhanced_messages
    
    def _parse_tool_response(self, response_text: str) -> Dict[str, Any]:
        """解析响应，检查是否包含工具调用"""
        result = {
            "content": response_text,
            "tool_calls": None
        }
        
        try:
            # 尝试解析JSON格式的工具调用
            if "tool_calls" in response_text and "{" in response_text:
                # 提取JSON部分
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    parsed = json.loads(json_str)
                    
                    if "tool_calls" in parsed:
                        tool_calls = []
                        for i, call in enumerate(parsed["tool_calls"]):
                            tool_calls.append({
                                "id": f"call_{uuid.uuid4().hex[:8]}",
                                "type": "function",
                                "function": {
                                    "name": call["name"],
                                    "arguments": json.dumps(call["arguments"], ensure_ascii=False)
                                }
                            })
                        
                        result["tool_calls"] = tool_calls
                        # 移除工具调用JSON，只保留其他内容
                        result["content"] = response_text[:start_idx] + response_text[end_idx:]
                        result["content"] = result["content"].strip()
        
        except Exception as e:
            self.logger.debug(f"解析工具调用失败，当作普通响应处理: {e}")
        
        return result
    
    async def generate_streaming(self, messages: List[Dict[str, Any]], 
                               tools: List[Dict[str, Any]] = None,
                               max_tokens: int = None,
                               temperature: float = 0.7) -> AsyncGenerator[Dict[str, Any], None]:
        """流式生成响应"""
        # 文心一言的流式API可能不同，这里先实现非流式版本
        try:
            if tools:
                result = await self.generate_with_tools(messages, tools, max_tokens, temperature)
            else:
                content = await self.generate_from_messages(messages, max_tokens, temperature)
                result = {"content": content, "tool_calls": None}
            
            # 模拟流式输出
            if result["content"]:
                # 分批发送内容
                content = result["content"]
                chunk_size = 10
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i+chunk_size]
                    yield {
                        "type": "content",
                        "content": chunk,
                        "accumulated_content": content[:i+len(chunk)]
                    }
                    await asyncio.sleep(0.01)  # 模拟延迟
            
            # 发送最终结果
            yield {
                "type": "complete",
                "content": result["content"],
                "tool_calls": result["tool_calls"],
                "finish_reason": "stop"
            }
            
        except Exception as e:
            self.logger.error(f"文心一言流式生成失败: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    def is_tool_calling_supported(self) -> bool:
        """检查模型是否支持工具调用"""
        # 文心一言通过提示工程支持工具调用
        return True 