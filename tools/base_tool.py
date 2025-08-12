"""
基础工具类 - 定义通用的工具输出结构
"""

import time
import logging
import json
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod

def ensure_json_serializable(data: Any) -> Any:
    """
    确保数据是JSON可序列化的
    
    Args:
        data: 要检查的数据
        
    Returns:
        JSON可序列化的数据
    """
    if data is None:
        return None
    elif isinstance(data, (str, int, float, bool)):
        return data
    elif isinstance(data, list):
        return [ensure_json_serializable(item) for item in data]
    elif isinstance(data, dict):
        return {key: ensure_json_serializable(value) for key, value in data.items()}
    elif hasattr(data, 'save'):  # PIL Image对象
        return f"<PIL.Image.Image object at {id(data)}>"
    elif hasattr(data, '__dict__'):  # 其他对象
        return str(data)
    else:
        return str(data)

class BaseTool(ABC):
    """基础工具类，定义通用的输出结构"""
    
    def __init__(self, tool_name: str, version: str = "1.0.0"):
        self.tool_name = tool_name
        self.version = version
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_success_output(self, 
                            primary_data: Any,
                            secondary_data: Optional[Dict] = None,
                            counts: Optional[Dict] = None,
                            paths: Optional[List[str]] = None,
                            message: Optional[str] = None,
                            parameters: Optional[Dict] = None,
                            start_time: Optional[float] = None) -> Dict[str, Any]:
        """
        创建标准化的成功输出
        
        Args:
            primary_data: 主要输出数据
            secondary_data: 次要输出数据
            counts: 统计信息
            paths: 文件路径列表
            message: 处理消息
            parameters: 输入参数
            start_time: 开始时间
            
        Returns:
            标准化的输出字典
        """
        processing_time = time.time() - start_time if start_time else 0
        
        output = {
            "status": "success",
            "data": {
                "primary": primary_data,
                "secondary": secondary_data or {},
                "counts": counts or {}
            },
            "metadata": {
                "tool_name": self.tool_name,
                "version": self.version,
                "parameters": parameters or {},
                "processing_time": processing_time
            },
            "paths": paths or [],
            "message": message or f"{self.tool_name} executed successfully"
        }
        
        return output
    
    def create_error_output(self,
                          error: str,
                          parameters: Optional[Dict] = None,
                          start_time: Optional[float] = None) -> Dict[str, Any]:
        """
        创建标准化的错误输出
        
        Args:
            error: 错误信息
            parameters: 输入参数
            start_time: 开始时间
            
        Returns:
            标准化的错误输出字典
        """
        processing_time = time.time() - start_time if start_time else 0
        
        output = {
            "status": "error",
            "data": {
                "primary": None,
                "secondary": {},
                "counts": {}
            },
            "metadata": {
                "tool_name": self.tool_name,
                "version": self.version,
                "parameters": parameters or {},
                "processing_time": processing_time
            },
            "paths": [],
            "message": f"{self.tool_name} failed: {error}",
            "error": error
        }
        
        return output
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行工具的主要逻辑
        
        Returns:
            标准化的输出字典
        """
        pass

def create_standardized_output(tool_name: str,
                             status: str,
                             primary_data: Any = None,
                             secondary_data: Optional[Dict] = None,
                             counts: Optional[Dict] = None,
                             paths: Optional[List[str]] = None,
                             message: Optional[str] = None,
                             parameters: Optional[Dict] = None,
                             error: Optional[str] = None,
                             start_time: Optional[float] = None,
                             version: str = "1.0.0") -> Dict[str, Any]:
    """
    创建标准化的工具输出（函数式接口）
    
    Args:
        tool_name: 工具名称
        status: 执行状态 ("success" | "error")
        primary_data: 主要输出数据
        secondary_data: 次要输出数据
        counts: 统计信息
        paths: 文件路径列表
        message: 处理消息
        parameters: 输入参数
        error: 错误信息
        start_time: 开始时间
        version: 工具版本
        
    Returns:
        标准化的输出字典
    """
    processing_time = time.time() - start_time if start_time else 0
    
    output = {
        "status": status,
        "data": {
            "primary": ensure_json_serializable(primary_data),
            "secondary": ensure_json_serializable(secondary_data or {}),
            "counts": ensure_json_serializable(counts or {})
        },
        "metadata": {
            "tool_name": tool_name,
            "version": version,
            "parameters": ensure_json_serializable(parameters or {}),
            "processing_time": processing_time
        },
        "paths": ensure_json_serializable(paths or []),
        "message": message or f"{tool_name} {'executed successfully' if status == 'success' else 'failed'}"
    }
    
    if error:
        output["error"] = error
    
    return output 