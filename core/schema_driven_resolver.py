#!/usr/bin/env python3
"""
Schema驱动的数据解析器
根据工具的实际输出Schema来适配数据，而不是要求工具适配固定的Pipeline格式
"""

import logging
import inspect
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
import re

@dataclass
class ToolSchema:
    """工具Schema定义"""
    name: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    return_type: Any
    description: str = ""

class SchemaDrivenResolver:
    """
    Schema驱动的数据解析器
    根据工具的实际输出Schema来适配数据
    """
    
    def __init__(self):
        self.logger = logging.getLogger("SchemaDrivenResolver")
        self.tool_schemas: Dict[str, ToolSchema] = {}
    
    def register_tool_schema(self, tool_name: str, tool_func: Callable, 
                           input_schema: Dict[str, Any] = None, 
                           output_schema: Dict[str, Any] = None) -> ToolSchema:
        """注册工具的Schema"""
        # 分析函数签名
        sig = inspect.signature(tool_func)
        
        # 如果没有提供Schema，则自动生成
        if input_schema is None:
            input_schema = self._generate_input_schema(sig)
        
        if output_schema is None:
            output_schema = self._generate_output_schema(sig)
        
        schema = ToolSchema(
            name=tool_name,
            input_schema=input_schema,
            output_schema=output_schema,
            return_type=sig.return_annotation,
            description=tool_func.__doc__ or ""
        )
        
        self.tool_schemas[tool_name] = schema
        self.logger.info(f"注册工具Schema: {tool_name}")
        return schema
    
    def extract_output_data(self, tool_name: str, tool_output: Any, 
                          requested_fields: List[str] = None) -> Dict[str, Any]:
        """
        根据工具的Schema提取输出数据
        
        Args:
            tool_name: 工具名称
            tool_output: 工具的实际输出
            requested_fields: 请求的字段列表，如果为None则提取所有可用字段
            
        Returns:
            适配后的输出数据
        """
        if tool_name not in self.tool_schemas:
            self.logger.warning(f"工具 {tool_name} 的Schema未注册，使用默认适配")
            return self._default_adaptation(tool_output, requested_fields)
        
        schema = self.tool_schemas[tool_name]
        return self._schema_based_extraction(schema, tool_output, requested_fields)
    
    def _schema_based_extraction(self, schema: ToolSchema, tool_output: Any, 
                                requested_fields: List[str] = None) -> Dict[str, Any]:
        """基于Schema的数据提取"""
        output_schema = schema.output_schema
        
        # 如果输出Schema定义了具体的字段结构
        if output_schema.get("type") == "object" and "properties" in output_schema:
            return self._extract_from_object_schema(output_schema, tool_output, requested_fields)
        
        # 如果输出是基本类型
        return self._extract_from_basic_type(schema.return_type, tool_output, requested_fields)
    
    def _extract_from_object_schema(self, output_schema: Dict[str, Any], 
                                   tool_output: Any, requested_fields: List[str] = None) -> Dict[str, Any]:
        """从对象Schema中提取数据"""
        properties = output_schema.get("properties", {})
        available_fields = list(properties.keys())
        
        if requested_fields is None:
            requested_fields = available_fields
        
        result = {}
        
        # 如果工具输出是字典，直接映射字段
        if isinstance(tool_output, dict):
            for field in requested_fields:
                if field in tool_output:
                    result[field] = tool_output[field]
                elif field in available_fields:
                    # 字段存在但工具输出中没有，使用默认值或空值
                    result[field] = self._get_default_value(properties[field])
        
        # 如果工具输出不是字典，尝试智能映射
        else:
            result = self._smart_field_mapping(tool_output, requested_fields, properties)
        
        return result
    
    def _extract_from_basic_type(self, return_type: Any, tool_output: Any, 
                                requested_fields: List[str] = None) -> Dict[str, Any]:
        """从基本类型中提取数据"""
        # 根据返回类型和请求字段进行智能映射
        if requested_fields is None:
            requested_fields = ["result"]
        
        result = {}
        
        # 常见的字段映射规则
        field_mappings = {
            "results": ["results", "data", "items", "list"],
            "formatted_text": ["formatted_text", "text", "content", "output"],
            "report_content": ["report_content", "content", "report", "output"],
            "status": ["status", "success", "state"],
            "message": ["message", "msg", "description", "info"]
        }
        
        for requested_field in requested_fields:
            # 查找映射的字段名
            mapped_fields = field_mappings.get(requested_field, [requested_field])
            
            # 如果工具输出是字典，尝试映射字段
            if isinstance(tool_output, dict):
                for mapped_field in mapped_fields:
                    if mapped_field in tool_output:
                        result[requested_field] = tool_output[mapped_field]
                        break
                else:
                    # 没有找到映射字段，使用默认值
                    result[requested_field] = self._get_default_for_type(return_type)
            
            # 如果工具输出不是字典，直接使用输出值
            else:
                # 对于非字典输出，根据请求字段进行智能映射
                if requested_field == "results" and isinstance(tool_output, list):
                    result[requested_field] = tool_output
                elif requested_field == "formatted_text" and isinstance(tool_output, str):
                    result[requested_field] = tool_output
                elif requested_field == "report_content" and isinstance(tool_output, str):
                    result[requested_field] = tool_output
                elif requested_field == "result":
                    result[requested_field] = tool_output
                else:
                    # 尝试将输出转换为请求的字段类型
                    result[requested_field] = self._convert_output_to_field_type(tool_output, requested_field)
        
        return result
    
    def _smart_field_mapping(self, tool_output: Any, requested_fields: List[str], 
                           properties: Dict[str, Any]) -> Dict[str, Any]:
        """智能字段映射"""
        result = {}
        
        for field in requested_fields:
            if field in properties:
                # 根据字段类型和工具输出类型进行智能映射
                field_type = properties[field].get("type", "string")
                
                if field_type == "string" and isinstance(tool_output, str):
                    result[field] = tool_output
                elif field_type == "array" and isinstance(tool_output, list):
                    result[field] = tool_output
                elif field_type == "object" and isinstance(tool_output, dict):
                    result[field] = tool_output
                else:
                    # 类型不匹配，尝试转换或使用默认值
                    result[field] = self._convert_to_type(tool_output, field_type)
            else:
                result[field] = self._get_default_for_type(type(tool_output))
        
        return result
    
    def _convert_to_type(self, value: Any, target_type: str) -> Any:
        """将值转换为目标类型"""
        if target_type == "string":
            return str(value)
        elif target_type == "array":
            if isinstance(value, list):
                return value
            else:
                return [value]
        elif target_type == "object":
            if isinstance(value, dict):
                return value
            else:
                return {"value": value}
        else:
            return value
    
    def _get_default_value(self, field_schema: Dict[str, Any]) -> Any:
        """获取字段的默认值"""
        if "default" in field_schema:
            return field_schema["default"]
        
        field_type = field_schema.get("type", "string")
        return self._get_default_for_type(field_type)
    
    def _get_default_for_type(self, type_info: Any) -> Any:
        """根据类型获取默认值"""
        if hasattr(type_info, '__name__'):
            type_name = type_info.__name__
        else:
            type_name = str(type_info)
        
        defaults = {
            "str": "",
            "string": "",
            "int": 0,
            "integer": 0,
            "float": 0.0,
            "number": 0.0,
            "bool": False,
            "boolean": False,
            "list": [],
            "array": [],
            "dict": {},
            "object": {}
        }
        
        return defaults.get(type_name, "")
    
    def _generate_input_schema(self, sig: inspect.Signature) -> Dict[str, Any]:
        """生成输入Schema"""
        properties = {}
        required = []
        
        for name, param in sig.parameters.items():
            param_type = self._get_mcp_type(param.annotation)
            properties[name] = {
                "type": param_type,
                "description": f"参数: {name}"
            }
            
            if param.default == inspect.Parameter.empty:
                required.append(name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def _generate_output_schema(self, sig: inspect.Signature) -> Dict[str, Any]:
        """生成输出Schema"""
        return_type = sig.return_annotation
        
        if return_type == inspect.Parameter.empty:
            return {
                "type": "object",
                "description": "工具执行结果"
            }
        
        # 基于返回类型生成Schema
        if hasattr(return_type, '__name__'):
            type_name = return_type.__name__
        else:
            type_name = str(return_type)
        
        if type_name in ['str', 'string']:
            return {"type": "string"}
        elif type_name in ['int', 'integer']:
            return {"type": "integer"}
        elif type_name in ['float', 'number']:
            return {"type": "number"}
        elif type_name in ['bool', 'boolean']:
            return {"type": "boolean"}
        elif type_name in ['list', 'array']:
            return {"type": "array", "items": {"type": "string"}}
        elif type_name in ['dict', 'object']:
            return {"type": "object"}
        else:
            return {"type": "string"}
    
    def _get_mcp_type(self, annotation: Any) -> str:
        """获取MCP类型"""
        if annotation == inspect.Parameter.empty:
            return "string"
        
        if hasattr(annotation, '__name__'):
            type_name = annotation.__name__
        else:
            type_name = str(annotation)
        
        type_mapping = {
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
            'object': 'object'
        }
        
        return type_mapping.get(type_name, 'string')
    
    def _default_adaptation(self, tool_output: Any, requested_fields: List[str] = None) -> Dict[str, Any]:
        """默认适配（当Schema未注册时使用）"""
        if requested_fields is None:
            requested_fields = ["result"]
        
        result = {}
        
        for field in requested_fields:
            if isinstance(tool_output, dict) and field in tool_output:
                result[field] = tool_output[field]
            else:
                result[field] = tool_output
        
        return result 

    def _convert_output_to_field_type(self, tool_output: Any, field_name: str) -> Any:
        """将工具输出转换为指定字段类型"""
        if field_name == "results":
            # 如果期望results字段，但输出不是列表，尝试转换
            if isinstance(tool_output, list):
                return tool_output
            elif isinstance(tool_output, str):
                # 字符串可以视为单个结果
                return [{"content": tool_output}]
            elif isinstance(tool_output, dict):
                # 字典可以视为单个结果
                return [tool_output]
            else:
                return [tool_output]
        
        elif field_name == "formatted_text":
            # 如果期望formatted_text字段，确保返回字符串
            if isinstance(tool_output, str):
                return tool_output
            else:
                return str(tool_output)
        
        elif field_name == "report_content":
            # 如果期望report_content字段，确保返回字符串
            if isinstance(tool_output, str):
                return tool_output
            else:
                return str(tool_output)
        
        else:
            # 其他字段，直接返回输出
            return tool_output 