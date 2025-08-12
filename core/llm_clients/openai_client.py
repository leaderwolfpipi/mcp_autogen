#!/usr/bin/env python3
"""
OpenAI客户端 - 支持MCP协议的工具调用
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, List, Optional, AsyncGenerator
import openai
from openai import AsyncOpenAI


class OpenAIClient:
    """OpenAI客户端"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4-turbo", base_url: str = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model = model
        
        # 初始化异步客户端
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    async def generate(self, prompt: str, max_tokens: int = None, temperature: float = 0.7) -> str:
        """简单文本生成"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"OpenAI生成失败: {e}")
            raise
    
    async def generate_from_messages(self, messages: List[Dict[str, Any]], 
                                   max_tokens: int = None, 
                                   temperature: float = 0.7) -> str:
        """从消息列表生成响应"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"OpenAI消息生成失败: {e}")
            raise
    
    async def generate_with_tools(self, messages: List[Dict[str, Any]], 
                                tools: List[Dict[str, Any]],
                                max_tokens: int = None,
                                temperature: float = 0.7) -> Dict[str, Any]:
        """支持工具调用的生成"""
        try:
            # 构建请求参数
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }
            
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = "auto"
            
            response = await self.client.chat.completions.create(**request_params)
            
            choice = response.choices[0]
            message = choice.message
            
            result = {
                "content": message.content,
                "tool_calls": None
            }
            
            # 处理工具调用
            if message.tool_calls:
                result["tool_calls"] = []
                for tool_call in message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })
            
            return result
            
        except Exception as e:
            self.logger.error(f"OpenAI工具调用生成失败: {e}")
            raise
    
    async def generate_streaming(self, messages: List[Dict[str, Any]], 
                               tools: List[Dict[str, Any]] = None,
                               max_tokens: int = None,
                               temperature: float = 0.7) -> AsyncGenerator[Dict[str, Any], None]:
        """流式生成响应"""
        try:
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": True
            }
            
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = "auto"
            
            stream = await self.client.chat.completions.create(**request_params)
            
            content_buffer = ""
            tool_calls_buffer = {}
            
            async for chunk in stream:
                delta = chunk.choices[0].delta
                
                # 处理内容流
                if delta.content:
                    content_buffer += delta.content
                    yield {
                        "type": "content",
                        "content": delta.content,
                        "accumulated_content": content_buffer
                    }
                
                # 处理工具调用流
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        call_id = tool_call_delta.id or f"call_{len(tool_calls_buffer)}"
                        
                        if call_id not in tool_calls_buffer:
                            tool_calls_buffer[call_id] = {
                                "id": call_id,
                                "type": "function",
                                "function": {
                                    "name": "",
                                    "arguments": ""
                                }
                            }
                        
                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                tool_calls_buffer[call_id]["function"]["name"] += tool_call_delta.function.name
                            if tool_call_delta.function.arguments:
                                tool_calls_buffer[call_id]["function"]["arguments"] += tool_call_delta.function.arguments
                
                # 检查是否完成
                if chunk.choices[0].finish_reason:
                    final_result = {
                        "type": "complete",
                        "content": content_buffer,
                        "tool_calls": list(tool_calls_buffer.values()) if tool_calls_buffer else None,
                        "finish_reason": chunk.choices[0].finish_reason
                    }
                    yield final_result
                    break
                    
        except Exception as e:
            self.logger.error(f"OpenAI流式生成失败: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    def is_tool_calling_supported(self) -> bool:
        """检查模型是否支持工具调用"""
        # GPT-4 和 GPT-3.5-turbo 的新版本支持工具调用
        supported_models = [
            "gpt-4", "gpt-4-turbo", "gpt-4-turbo-preview",
            "gpt-3.5-turbo", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-1106"
        ]
        return any(model in self.model for model in supported_models) 