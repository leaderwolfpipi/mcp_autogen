#!/usr/bin/env python3
"""
MCP工具标准化包装器
将所有工具包装为标准的MCP工具
"""

import logging
import inspect
import json
import asyncio
import re
from typing import Dict, Any, List, Optional, Callable, Union, get_origin, get_args
from dataclasses import dataclass, field
from enum import Enum
import traceback

class MCPToolType(Enum):
    """MCP工具类型"""
    FUNCTION = "function"
    PROCEDURE = "procedure"
    RESOURCE = "resource"

@dataclass
class MCPParameter:
    """MCP参数定义"""
    name: str
    type: str
    description: str = ""
    required: bool = True
    default: Any = None
    enum: List[str] = field(default_factory=list)

@dataclass
class MCPTool:
    """MCP工具定义"""
    name: str
    description: str = ""
    inputSchema: Dict[str, Any] = field(default_factory=dict)
    outputSchema: Dict[str, Any] = field(default_factory=dict)
    parameters: List[MCPParameter] = field(default_factory=list)
    type: MCPToolType = MCPToolType.FUNCTION
    examples: List[Dict[str, Any]] = field(default_factory=list)

class MCPWrapper:
    """
    MCP工具标准化包装器
    """
    
    def __init__(self):
        self.logger = logging.getLogger("MCPWrapper")
        self.tools: Dict[str, MCPTool] = {}
        self.tool_functions: Dict[str, Callable] = {}
        
        # 类型映射
        self.type_mapping = {
            'str': 'string',
            'string': 'string',
            'int': 'integer',
            'integer': 'integer',
            'float': 'number',
            'number': 'number',
            'bool': 'boolean',
            'boolean': 'boolean',
            'list': 'array',
            'array': 'array',
            'dict': 'object',
            'object': 'object',
            'file_path': 'string',
            'image_path': 'string',
            'directory_path': 'string',
            'url': 'string'
        }

    def register_tool(self, tool_func: Callable, tool_name: str = None, 
                     description: str = "", examples: List[Dict[str, Any]] = None) -> MCPTool:
        """注册工具为MCP工具"""
        if tool_name is None:
            tool_name = tool_func.__name__
        
        # 分析函数签名
        sig = inspect.signature(tool_func)
        parameters = []
        input_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for name, param in sig.parameters.items():
            param_type = self._get_mcp_type(param.annotation, param.default)
            param_desc = self._extract_param_description(tool_func, name)
            
            mcp_param = MCPParameter(
                name=name,
                type=param_type,
                description=param_desc,
                required=param.default == inspect.Parameter.empty,
                default=param.default if param.default != inspect.Parameter.empty else None
            )
            parameters.append(mcp_param)
            
            # 构建输入schema（增强：支持 Union/List 等复杂注解）
            prop_schema = self._build_param_schema(param.annotation)
            # 合并描述
            if isinstance(prop_schema, dict):
                prop_schema = {**prop_schema, "description": param_desc}
            else:
                prop_schema = {"type": param_type, "description": param_desc}
            input_schema["properties"][name] = prop_schema
            
            if mcp_param.required:
                input_schema["required"].append(name)
        
        # 生成输出schema
        output_schema = self._generate_output_schema(tool_func, sig)
        
        # 创建MCP工具定义
        mcp_tool = MCPTool(
            name=tool_name,
            description=description or tool_func.__doc__ or "",
            inputSchema=input_schema,
            outputSchema=output_schema,
            parameters=parameters,
            examples=examples or []
        )
        
        self.tools[tool_name] = mcp_tool
        self.tool_functions[tool_name] = tool_func
        
        self.logger.info(f"注册MCP工具: {tool_name}")
        return mcp_tool

    def create_mcp_tool_from_function(self, tool_func: Callable, tool_name: str) -> MCPTool:
        """从函数创建MCP工具定义"""
        # 分析函数签名
        sig = inspect.signature(tool_func)
        parameters = []
        input_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for name, param in sig.parameters.items():
            param_type = self._get_mcp_type(param.annotation, param.default)
            param_desc = self._extract_param_description(tool_func, name)
            
            mcp_param = MCPParameter(
                name=name,
                type=param_type,
                description=param_desc,
                required=param.default == inspect.Parameter.empty,
                default=param.default if param.default != inspect.Parameter.empty else None
            )
            parameters.append(mcp_param)
            
            # 构建输入schema（增强）
            prop_schema = self._build_param_schema(param.annotation)
            if isinstance(prop_schema, dict):
                prop_schema = {**prop_schema, "description": param_desc}
            else:
                prop_schema = {"type": param_type, "description": param_desc}
            input_schema["properties"][name] = prop_schema
            
            if mcp_param.required:
                input_schema["required"].append(name)
        
        # 生成输出schema
        output_schema = self._generate_output_schema(tool_func, sig)
        
        # 创建MCP工具定义
        mcp_tool = MCPTool(
            name=tool_name,
            description=tool_func.__doc__ or "",
            inputSchema=input_schema,
            outputSchema=output_schema,
            parameters=parameters
        )
        
        return mcp_tool

    def create_mcp_tool_from_metadata(self, tool_name: str, description: str = "", 
                                    signature: Dict[str, Any] = None) -> MCPTool:
        """从元数据创建MCP工具定义"""
        # 从工具定义的签名或元数据中提取参数信息
        signature = signature or {}
        parameters = []
        input_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # 从签名中提取参数
        sig_params = signature.get("parameters", {})
        for param_name, param_info in sig_params.items():
            if isinstance(param_info, dict):
                param_type = param_info.get("type", "string")
                param_desc = param_info.get("description", "")
                param_required = param_info.get("required", True)
                param_default = param_info.get("default", None)
            else:
                param_type = str(param_info) if param_info else "string"
                param_desc = ""
                param_required = True
                param_default = None
            
            # 转换为MCP类型
            mcp_type = self._get_mcp_type_from_string(param_type)
            
            mcp_param = MCPParameter(
                name=param_name,
                type=mcp_type,
                description=param_desc,
                required=param_required,
                default=param_default
            )
            parameters.append(mcp_param)
            
            # 构建输入schema
            input_schema["properties"][param_name] = {
                "type": mcp_type,
                "description": param_desc
            }
            
            if param_required:
                input_schema["required"].append(param_name)
        
        # 生成输出schema
        output_type = signature.get("return_type", "Any")
        output_schema = self._generate_output_schema_from_string(output_type)
        
        # 创建MCP工具定义
        mcp_tool = MCPTool(
            name=tool_name,
            description=description or "",
            inputSchema=input_schema,
            outputSchema=output_schema,
            parameters=parameters
        )
        
        return mcp_tool

    def get_tool_list(self) -> List[Dict[str, Any]]:
        """获取工具列表（MCP格式）"""
        tool_list = []
        for tool_name, tool in self.tools.items():
            tool_info = {
                "name": tool_name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
                "outputSchema": tool.outputSchema
            }
            tool_list.append(tool_info)
        return tool_list

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用MCP工具"""
        try:
            if tool_name not in self.tool_functions:
                raise ValueError(f"工具不存在: {tool_name}")
            
            tool_func = self.tool_functions[tool_name]
            tool_def = self.tools[tool_name]
            
            # 验证参数
            validated_args = self._validate_arguments(arguments, tool_def)
            
            # 执行工具
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**validated_args)
            else:
                result = tool_func(**validated_args)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ]
            }
            
        except Exception as e:
            self.logger.error(f"工具执行失败 {tool_name}: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"工具执行失败: {str(e)}"
                    }
                ],
                "isError": True
            }

    def _generate_output_schema(self, tool_func: Callable, sig: inspect.Signature) -> Dict[str, Any]:
        """生成输出schema"""
        return_type = sig.return_annotation
        
        if return_type == inspect.Parameter.empty:
            # 如果没有类型注解，使用通用类型
            output_schema = {
                "type": "object",
                "description": "工具执行结果",
                "properties": {
                    "result": {
                        "type": "string",
                        "description": "执行结果"
                    },
                    "success": {
                        "type": "boolean",
                        "description": "是否成功"
                    }
                }
            }
        else:
            # 基于返回类型生成schema
            return_type_name = return_type.__name__ if hasattr(return_type, '__name__') else str(return_type)
            mcp_type = self.type_mapping.get(return_type_name, 'string')
            
            if mcp_type == 'string':
                output_schema = {
                    "type": "string",
                    "description": "工具执行结果"
                }
            elif mcp_type == 'boolean':
                output_schema = {
                    "type": "boolean",
                    "description": "工具执行结果"
                }
            elif mcp_type in ['integer', 'number']:
                output_schema = {
                    "type": mcp_type,
                    "description": "工具执行结果"
                }
            elif mcp_type == 'array':
                output_schema = {
                    "type": "array",
                    "description": "工具执行结果",
                    "items": {
                        "type": "string"
                    }
                }
            elif mcp_type == 'object':
                output_schema = {
                    "type": "object",
                    "description": "工具执行结果",
                    "properties": {
                        "data": {
                            "type": "object",
                            "description": "返回数据"
                        }
                    }
                }
            else:
                output_schema = {
                    "type": "string",
                    "description": "工具执行结果"
                }
        
        return output_schema

    def _generate_output_schema_from_string(self, return_type: str) -> Dict[str, Any]:
        """从字符串返回类型生成输出schema"""
        mcp_type = self._get_mcp_type_from_string(return_type)
        
        if mcp_type == 'string':
            return {
                "type": "string",
                "description": "工具执行结果"
            }
        elif mcp_type == 'boolean':
            return {
                "type": "boolean",
                "description": "工具执行结果"
            }
        elif mcp_type in ['integer', 'number']:
            return {
                "type": mcp_type,
                "description": "工具执行结果"
            }
        elif mcp_type == 'array':
            return {
                "type": "array",
                "description": "工具执行结果",
                "items": {
                    "type": "string"
                }
            }
        elif mcp_type == 'object':
            return {
                "type": "object",
                "description": "工具执行结果",
                "properties": {
                    "data": {
                        "type": "object",
                        "description": "返回数据"
                    }
                }
            }
        else:
            return {
                "type": "object",
                "description": "工具执行结果",
                "properties": {
                    "result": {
                        "type": "string",
                        "description": "执行结果"
                    },
                    "success": {
                        "type": "boolean",
                        "description": "是否成功"
                    }
                }
            }

    def _get_mcp_type(self, annotation: Any, default: Any) -> str:
        """获取MCP类型"""
        if annotation != inspect.Parameter.empty:
            type_name = annotation.__name__ if hasattr(annotation, '__name__') else str(annotation)
            return self.type_mapping.get(type_name, 'string')
        
        # 基于默认值推断
        if default is not None:
            if isinstance(default, str):
                return 'string'
            elif isinstance(default, int):
                return 'integer'
            elif isinstance(default, float):
                return 'number'
            elif isinstance(default, bool):
                return 'boolean'
            elif isinstance(default, list):
                return 'array'
            elif isinstance(default, dict):
                return 'object'
        
        return 'string'

    def _build_param_schema(self, annotation: Any) -> Dict[str, Any]:
        """根据类型注解构建更精确的JSON Schema，支持 Union[List[str], str] 等情况。"""
        if annotation == inspect.Parameter.empty or annotation is None:
            return {"type": "string"}

        origin = get_origin(annotation)
        args = get_args(annotation)

        # 处理 Union
        if origin is Union and args:
            variants: List[Dict[str, Any]] = []
            for arg in args:
                if arg is type(None):
                    # 可空在required层面处理；此处忽略
                    continue
                variants.append(self._build_param_schema(arg))
            # 去重
            unique_variants = []
            for v in variants:
                if v not in unique_variants:
                    unique_variants.append(v)
            if len(unique_variants) == 1:
                return unique_variants[0]
            return {"oneOf": unique_variants}

        # 处理 List/列表
        if origin in (list, List):
            item_type = args[0] if args else str
            item_schema = self._build_param_schema(item_type)
            # item_schema 可能返回 oneOf，这里简化为字符串数组优先
            if "oneOf" in item_schema:
                # 若是 union of primitives，默认到 string
                item_schema = {"type": "string"}
            return {"type": "array", "items": item_schema}

        # 基础类型
        if annotation in (str,):
            return {"type": "string"}
        if annotation in (int,):
            return {"type": "integer"}
        if annotation in (float,):
            return {"type": "number"}
        if annotation in (bool,):
            return {"type": "boolean"}
        if annotation in (dict, Dict):
            return {"type": "object"}

        # 未识别默认字符串
        return {"type": "string"}

    def _get_mcp_type_from_string(self, type_str: str) -> str:
        """从字符串类型转换为MCP类型"""
        type_lower = type_str.lower()
        if type_lower in ['str', 'string', 'text']:
            return 'string'
        elif type_lower in ['int', 'integer', 'number']:
            return 'integer'
        elif type_lower in ['float', 'double', 'decimal']:
            return 'number'
        elif type_lower in ['bool', 'boolean']:
            return 'boolean'
        elif type_lower in ['list', 'array']:
            return 'array'
        elif type_lower in ['dict', 'object', 'json']:
            return 'object'
        else:
            return 'string'

    def _extract_param_description(self, tool_func: Callable, param_name: str) -> str:
        """从文档字符串中提取参数描述"""
        try:
            doc = tool_func.__doc__ or ""
            # 简单的正则匹配参数描述
            pattern = rf":param {param_name}:(.*?)(?=:param|\n\n|$)"
            match = re.search(pattern, doc, re.DOTALL)
            if match:
                return match.group(1).strip()
        except:
            pass
        return ""

    def _validate_arguments(self, arguments: Dict[str, Any], tool_def: MCPTool) -> Dict[str, Any]:
        """验证参数"""
        validated = {}
        
        for param in tool_def.parameters:
            if param.name in arguments:
                validated[param.name] = arguments[param.name]
            elif param.required and param.default is None:
                raise ValueError(f"缺少必需参数: {param.name}")
            elif param.default is not None:
                validated[param.name] = param.default
        
        return validated

    def generate_mcp_schema(self) -> Dict[str, Any]:
        """生成MCP Schema"""
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "tools": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "inputSchema": {"type": "object"},
                            "outputSchema": {"type": "object"}
                        },
                        "required": ["name", "inputSchema", "outputSchema"]
                    }
                }
            }
        }

    def export_tools_manifest(self) -> Dict[str, Any]:
        """导出工具清单"""
        return {
            "tools": self.get_tool_list(),
            "schema": self.generate_mcp_schema()
        }

class MCPToolDecorator:
    """MCP工具装饰器"""
    
    def __init__(self, wrapper: MCPWrapper):
        self.wrapper = wrapper
    
    def __call__(self, tool_name: str = None, description: str = "", 
                 examples: List[Dict[str, Any]] = None):
        def decorator(func: Callable) -> Callable:
            self.wrapper.register_tool(func, tool_name, description, examples)
            return func
        return decorator

# 全局MCP包装器实例
mcp_wrapper = MCPWrapper()
mcp_tool = MCPToolDecorator(mcp_wrapper)

# 便捷函数
def register_mcp_tool(tool_func: Callable, tool_name: str = None, 
                     description: str = "", examples: List[Dict[str, Any]] = None) -> MCPTool:
    """注册工具为MCP工具"""
    return mcp_wrapper.register_tool(tool_func, tool_name, description, examples)

def get_mcp_tools() -> List[Dict[str, Any]]:
    """获取MCP工具列表"""
    return mcp_wrapper.get_tool_list()

async def call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """调用MCP工具"""
    return await mcp_wrapper.call_tool(tool_name, arguments)

def export_mcp_manifest() -> Dict[str, Any]:
    """导出MCP工具清单"""
    return mcp_wrapper.export_tools_manifest()

# 导出MCP相关的类和函数，供其他模块使用
__all__ = [
    'MCPToolType', 'MCPParameter', 'MCPTool', 'MCPWrapper', 'MCPToolDecorator',
    'mcp_wrapper', 'mcp_tool', 'register_mcp_tool', 'get_mcp_tools', 
    'call_mcp_tool', 'export_mcp_manifest'
]