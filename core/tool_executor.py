#!/usr/bin/env python3
"""
工具执行器
负责执行具体的工具调用，包括参数验证、执行控制和结果处理
"""

import logging
import time
import asyncio
import jsonschema
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, TimeoutError


class ToolExecutor:
    """工具执行器"""
    
    def __init__(self, tool_registry, timeout=30):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tool_registry = tool_registry
        self.timeout = timeout
        
        # 线程池用于执行可能阻塞的同步工具
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    async def execute(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            
        Returns:
            工具执行结果
        """
        start_time = time.time()
        
        try:
            # 检查工具是否存在
            if not self._tool_exists(tool_name):
                return {
                    "error": f"Tool {tool_name} not found",
                    "error_code": "TOOL_NOT_FOUND",
                    "execution_time": time.time() - start_time
                }
            
            # 获取工具信息
            tool_info = self._get_tool_info(tool_name)
            
            # 参数验证（优先使用 inputSchema，其次兼容旧的 parameters 字段）
            validation_result = self._validate_parameters(tool_info, parameters, tool_name)
            if not validation_result["valid"]:
                return {
                    "error": validation_result["error"],
                    "error_code": "PARAMETER_VALIDATION_ERROR",
                    "execution_time": time.time() - start_time
                }
            # 使用校正后的参数继续执行
            parameters = validation_result.get("corrected_params", parameters)
            
            # 执行工具
            self.logger.info(f"执行工具: {tool_name}")
            
            # 直接调用工具注册表的async方法
            result = await self._execute_tool_async(tool_name, parameters)
            
            # 添加执行时间
            result["execution_time"] = time.time() - start_time
            
            return result
            
        except Exception as e:
            self.logger.error(f"工具执行异常: {tool_name}, 错误: {e}")
            return {
                "error": f"Tool execution failed: {str(e)}",
                "error_code": "EXECUTION_ERROR",
                "execution_time": time.time() - start_time
            }
    
    async def _execute_tool_async(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行工具的内部方法"""
        try:
            # 检查工具注册表是否有execute_tool方法（统一接口）
            if hasattr(self.tool_registry, 'execute_tool'):
                # 调用统一工具管理器的async execute_tool方法
                result = await self.tool_registry.execute_tool(tool_name, **parameters)
            else:
                # 兼容旧的同步接口，在线程池中执行
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.executor,
                    self._execute_tool_sync_fallback,
                    tool_name,
                    parameters
                )
            
            # 标准化结果格式到统一schema
            normalized = self._normalize_tool_output(tool_name, parameters, result)
            return normalized
                
        except Exception as e:
            self.logger.error(f"工具异步执行失败: {tool_name}, 错误: {e}")
            return {
                "error": f"Tool async execution failed: {str(e)}",
                "error_code": "ASYNC_EXECUTION_ERROR"
            }
    
    def _normalize_tool_output(self, tool_name: str, parameters: Dict[str, Any], result: Any) -> Dict[str, Any]:
        """将工具原始输出规范化为统一结构：
        {
          status: 'success' | 'error',
          data: { primary: Any, secondary?: Any },
          message?: str,
          metadata?: { tool_name, parameters, ... },
          error?: Any
        }
        保持向后兼容：不删除原有字段（如result），只补齐统一结构所需字段。
        """
        try:
            # 起始：把非字典结果包一层
            if not isinstance(result, dict):
                return {
                    "status": "success",
                    "data": {"primary": result},
                    "message": f"Tool {tool_name} executed successfully",
                    "metadata": {
                        "tool_name": tool_name,
                        "parameters": parameters
                    },
                    "result": result  # 向后兼容
                }

            output: Dict[str, Any] = dict(result)  # 复制，避免原地修改外部对象

            # 1) status
            status = output.get("status")
            if not status:
                status = "error" if output.get("error") else "success"
                output["status"] = status

            # 2) data.primary / data.secondary
            data_block = output.get("data")
            if not isinstance(data_block, dict):
                data_block = {}
            # 若没有primary但有result，则映射为primary
            if "primary" not in data_block and "result" in output:
                data_block["primary"] = output.get("result")
            # 确保存在data字段
            output["data"] = data_block

            # 3) message（保留原message，不生成冗余通用文案）
            if "message" not in output:
                output["message"] = ""

            # 4) metadata
            metadata = output.get("metadata")
            if not isinstance(metadata, dict):
                metadata = {}
            if "tool_name" not in metadata:
                metadata["tool_name"] = tool_name
            if "parameters" not in metadata:
                metadata["parameters"] = parameters
            output["metadata"] = metadata

            return output
        except Exception:
            # 失败时，回退到宽松封装
            return {
                "status": "success" if not isinstance(result, dict) or not result.get("error") else "error",
                "data": {"primary": result if not isinstance(result, dict) else result.get("result")},
                "message": (result.get("message") if isinstance(result, dict) else "") or "",
                "metadata": {"tool_name": tool_name, "parameters": parameters},
                **(result if isinstance(result, dict) else {})
            }
    
    def _execute_tool_sync_fallback(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """同步执行工具的兼容方法（仅用于没有async接口的旧工具注册表）"""
        try:
            # 假设旧的工具注册表有execute_tool同步方法
            if hasattr(self.tool_registry, 'execute_tool'):
                # 这种情况下不应该被调用，因为我们优先使用async版本
                result = self.tool_registry.execute_tool(tool_name, **parameters)
            else:
                # 如果没有execute_tool方法，尝试其他接口
                result = self.tool_registry.call_tool(tool_name, parameters)
            
            # 标准化结果格式
            return self._normalize_tool_output(tool_name, parameters, result)
                
        except Exception as e:
            self.logger.error(f"工具同步执行失败: {tool_name}, 错误: {e}")
            return {
                "error": f"Tool sync execution failed: {str(e)}",
                "error_code": "SYNC_EXECUTION_ERROR"
            }
    
    def _tool_exists(self, tool_name: str) -> bool:
        """检查工具是否存在"""
        tool_list = self.tool_registry.get_tool_list()
        if isinstance(tool_list, list):
            return any(tool.get('name') == tool_name for tool in tool_list)
        else:
            return tool_name in tool_list
    
    def _get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """获取工具信息"""
        tool_list = self.tool_registry.get_tool_list()
        if isinstance(tool_list, list):
            for tool in tool_list:
                if tool.get('name') == tool_name:
                    return tool
            return {}
        else:
            return tool_list.get(tool_name, {})
    
    def _validate_parameters(self, tool_info: Dict[str, Any], parameters: Dict[str, Any], tool_name: str = "unknown") -> Dict[str, Any]:
        """验证工具参数"""
        try:
            # 获取参数schema：优先 inputSchema（标准），兼容旧的 parameters
            param_schema = tool_info.get('inputSchema') or tool_info.get('parameters', {})
            
            if not param_schema:
                # 如果没有schema，直接返回参数
                return {"valid": True, "error": None}
            
            # 使用jsonschema验证
            jsonschema.validate(parameters, param_schema)
            
            # 自动类型转换和修复
            corrected_params = self._auto_correct_parameters(parameters, param_schema)
            
            return {"valid": True, "error": None, "corrected_params": corrected_params}
            
        except jsonschema.ValidationError as e:
            return {
                "valid": False,
                "error": f"Parameter validation failed for {tool_name}: {str(e)}",
                "validation_details": {
                    "message": e.message,
                    "path": list(e.path),
                    "schema_path": list(e.schema_path)
                }
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Parameter processing failed for {tool_name}: {str(e)}",
                "validation_details": {}
            }
    
    def _auto_correct_parameters(self, parameters: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """自动修正参数类型"""
        corrected = {}
        properties = schema.get('properties', {})
        
        for param_name, param_value in parameters.items():
            if param_name in properties:
                param_spec = properties[param_name]
                expected_type = param_spec.get('type', 'string')
                
                try:
                    # 类型转换
                    if expected_type == 'number' and isinstance(param_value, str):
                        corrected[param_name] = float(param_value)
                    elif expected_type == 'integer' and isinstance(param_value, str):
                        corrected[param_name] = int(param_value)
                    elif expected_type == 'boolean' and isinstance(param_value, str):
                        corrected[param_name] = param_value.lower() in ('true', '1', 'yes', 'on')
                    elif expected_type == 'string' and not isinstance(param_value, str):
                        corrected[param_name] = str(param_value)
                    elif expected_type == 'array' and isinstance(param_value, str):
                        # 尝试解析字符串数组
                        try:
                            import json
                            corrected[param_name] = json.loads(param_value)
                        except:
                            corrected[param_name] = param_value.split(',')
                    else:
                        corrected[param_name] = param_value
                except (ValueError, TypeError):
                    # 转换失败，保持原值
                    corrected[param_name] = param_value
            else:
                corrected[param_name] = param_value
        
        # 添加默认值
        for param_name, param_spec in properties.items():
            if param_name not in corrected and 'default' in param_spec:
                corrected[param_name] = param_spec['default']
        
        return corrected
    
    def _process_result(self, result: Any, tool_name: str) -> Dict[str, Any]:
        """处理工具执行结果"""
        if result is None:
            return {
                "result": None,
                "message": f"Tool {tool_name} completed with no output"
            }
        
        # 如果结果已经是字典格式，直接返回
        if isinstance(result, dict):
            # 确保有基本的结构
            if 'result' not in result and 'error' not in result:
                return {"result": result}
            return result
        
        # 其他类型转换为标准格式
        return {
            "result": result,
            "message": f"Tool {tool_name} executed successfully"
        }
    
    def get_tool_status(self, tool_name: str) -> Dict[str, Any]:
        """获取工具状态信息"""
        if not self._tool_exists(tool_name):
            return {
                "exists": False,
                "error": "Tool not found"
            }
        
        tool_info = self._get_tool_info(tool_name)
        
        return {
            "exists": True,
            "name": tool_name,
            "description": tool_info.get('description', ''),
            "parameters": tool_info.get('parameters', {}),
            "source": tool_info.get('source', 'unknown'),
            "metadata": tool_info.get('metadata', {})
        }
    
    def list_available_tools(self) -> List[str]:
        """列出所有可用工具"""
        tool_list = self.tool_registry.get_tool_list()
        return list(tool_list.keys())
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True) 