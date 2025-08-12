 #!/usr/bin/env python3
"""
集成流水线系统
结合参数适配器和MCP工具标准化
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from .universal_adapter import UniversalAdapter, ToolDefinition
from .mcp_wrapper import MCPWrapper, MCPTool, register_mcp_tool, call_mcp_tool

@dataclass
class PipelineStep:
    """流水线步骤"""
    tool_name: str
    params: Dict[str, Any] = field(default_factory=dict)
    adapter_config: Dict[str, Any] = field(default_factory=dict)
    error_handling: str = "continue"  # continue, retry, fail
    retry_count: int = 3
    timeout: int = 30

@dataclass
class PipelineDefinition:
    """流水线定义"""
    name: str
    description: str = ""
    steps: List[PipelineStep] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    error_handling: str = "continue"
    timeout: int = 300

class IntegratedPipeline:
    """
    集成流水线系统
    """
    
    def __init__(self):
        self.logger = logging.getLogger("IntegratedPipeline")
        self.adapter = UniversalAdapter()
        self.mcp_wrapper = MCPWrapper()
        self.pipelines: Dict[str, PipelineDefinition] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # 自动注册所有工具
        self._auto_register_tools()

    def _auto_register_tools(self):
        """自动注册所有可用工具"""
        try:
            import importlib
            import os
            
            tools_dir = "tools"
            if os.path.exists(tools_dir):
                for filename in os.listdir(tools_dir):
                    if filename.endswith('.py') and not filename.startswith('__'):
                        tool_name = filename[:-3]
                        try:
                            module = importlib.import_module(f"tools.{tool_name}")
                            if hasattr(module, tool_name):
                                tool_func = getattr(module, tool_name)
                                
                                # 注册到适配器
                                tool_def = self.adapter.auto_discover_tool(tool_func)
                                self.adapter.register_tool(tool_def)
                                
                                # 注册到MCP包装器
                                self.mcp_wrapper.register_tool(tool_func, tool_name)
                                
                                self.logger.info(f"自动注册工具: {tool_name}")
                        except Exception as e:
                            self.logger.warning(f"自动注册工具失败 {tool_name}: {e}")
        except Exception as e:
            self.logger.error(f"自动注册工具失败: {e}")

    def register_pipeline(self, pipeline_def: PipelineDefinition) -> None:
        """注册流水线"""
        self.pipelines[pipeline_def.name] = pipeline_def
        self.logger.info(f"注册流水线: {pipeline_def.name}")

    async def execute_pipeline(self, pipeline_name: str, input_data: Any = None, 
                             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行流水线"""
        if pipeline_name not in self.pipelines:
            raise ValueError(f"流水线不存在: {pipeline_name}")
        
        pipeline = self.pipelines[pipeline_name]
        context = context or {}
        
        self.logger.info(f"开始执行流水线: {pipeline_name}")
        
        result = input_data
        step_results = []
        
        for i, step in enumerate(pipeline.steps):
            try:
                self.logger.info(f"执行步骤 [{i+1}/{len(pipeline.steps)}]: {step.tool_name}")
                
                # 1. 参数适配
                if i > 0 and result is not None:
                    adapter = self.adapter.create_adapter(
                        pipeline.steps[i-1].tool_name, 
                        step.tool_name
                    )
                    adapted_params = adapter(result, **step.params)
                else:
                    adapted_params = step.params.copy()
                
                # 2. 上下文注入
                adapted_params.update(context)
                
                # 3. 执行工具
                tool_result = await call_mcp_tool(step.tool_name, adapted_params)
                
                if tool_result.get("isError"):
                    if step.error_handling == "fail":
                        raise Exception(f"工具执行失败: {tool_result['content'][0]['text']}")
                    elif step.error_handling == "retry":
                        # 重试逻辑
                        for retry in range(step.retry_count):
                            self.logger.warning(f"重试步骤 {step.tool_name} ({retry + 1}/{step.retry_count})")
                            await asyncio.sleep(1)  # 等待1秒后重试
                            tool_result = await call_mcp_tool(step.tool_name, adapted_params)
                            if not tool_result.get("isError"):
                                break
                        else:
                            if pipeline.error_handling == "continue":
                                self.logger.error(f"步骤执行失败，继续执行: {step.tool_name}")
                                continue
                            else:
                                raise Exception(f"步骤执行失败: {step.tool_name}")
                    else:  # continue
                        self.logger.warning(f"步骤执行失败，继续执行: {step.tool_name}")
                        continue
                
                # 4. 提取结果
                if tool_result.get("content"):
                    result = tool_result["content"][0]["text"]
                else:
                    result = tool_result
                
                # 5. 记录步骤结果
                step_result = {
                    "step_index": i,
                    "tool_name": step.tool_name,
                    "input_params": adapted_params,
                    "output": result,
                    "success": not tool_result.get("isError"),
                    "error": tool_result.get("content", [{}])[0].get("text") if tool_result.get("isError") else None
                }
                step_results.append(step_result)
                
                self.logger.info(f"步骤执行完成: {step.tool_name}")
                
            except Exception as e:
                self.logger.error(f"步骤执行异常: {step.tool_name} - {e}")
                step_result = {
                    "step_index": i,
                    "tool_name": step.tool_name,
                    "input_params": adapted_params if 'adapted_params' in locals() else step.params,
                    "output": None,
                    "success": False,
                    "error": str(e)
                }
                step_results.append(step_result)
                
                if pipeline.error_handling == "fail":
                    raise
                elif pipeline.error_handling == "continue":
                    continue
        
        # 记录执行历史
        execution_record = {
            "pipeline_name": pipeline_name,
            "input_data": input_data,
            "output_data": result,
            "step_results": step_results,
            "success": all(step["success"] for step in step_results),
            "timestamp": asyncio.get_event_loop().time()
        }
        self.execution_history.append(execution_record)
        
        return {
            "result": result,
            "step_results": step_results,
            "success": all(step["success"] for step in step_results),
            "pipeline_name": pipeline_name
        }

    def create_pipeline_from_steps(self, name: str, steps: List[Dict[str, Any]], 
                                  description: str = "") -> PipelineDefinition:
        """从步骤列表创建流水线"""
        pipeline_steps = []
        
        for step_data in steps:
            step = PipelineStep(
                tool_name=step_data["tool"],
                params=step_data.get("params", {}),
                adapter_config=step_data.get("adapter_config", {}),
                error_handling=step_data.get("error_handling", "continue"),
                retry_count=step_data.get("retry_count", 3),
                timeout=step_data.get("timeout", 30)
            )
            pipeline_steps.append(step)
        
        pipeline_def = PipelineDefinition(
            name=name,
            description=description,
            steps=pipeline_steps
        )
        
        self.register_pipeline(pipeline_def)
        return pipeline_def

    def get_pipeline_status(self, pipeline_name: str) -> Dict[str, Any]:
        """获取流水线状态"""
        if pipeline_name not in self.pipelines:
            return {"error": f"流水线不存在: {pipeline_name}"}
        
        pipeline = self.pipelines[pipeline_name]
        recent_executions = [
            record for record in self.execution_history 
            if record["pipeline_name"] == pipeline_name
        ][-5:]  # 最近5次执行
        
        return {
            "name": pipeline_name,
            "description": pipeline.description,
            "steps_count": len(pipeline.steps),
            "recent_executions": recent_executions,
            "success_rate": self._calculate_success_rate(recent_executions)
        }

    def _calculate_success_rate(self, executions: List[Dict[str, Any]]) -> float:
        """计算成功率"""
        if not executions:
            return 0.0
        
        successful = sum(1 for exec_record in executions if exec_record["success"])
        return successful / len(executions)

    def export_pipeline_manifest(self) -> Dict[str, Any]:
        """导出流水线清单"""
        return {
            "pipelines": [
                {
                    "name": pipeline.name,
                    "description": pipeline.description,
                    "steps": [
                        {
                            "tool_name": step.tool_name,
                            "params": step.params,
                            "error_handling": step.error_handling
                        }
                        for step in pipeline.steps
                    ]
                }
                for pipeline in self.pipelines.values()
            ],
            "tools": self.mcp_wrapper.get_tool_list(),
            "execution_history": self.execution_history[-10:]  # 最近10次执行
        }

# 全局集成流水线实例
integrated_pipeline = IntegratedPipeline()

# 便捷函数
def register_pipeline(pipeline_def: PipelineDefinition) -> None:
    """注册流水线"""
    integrated_pipeline.register_pipeline(pipeline_def)

async def execute_pipeline(pipeline_name: str, input_data: Any = None, 
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
    """执行流水线"""
    return await integrated_pipeline.execute_pipeline(pipeline_name, input_data, context)

def create_pipeline(name: str, steps: List[Dict[str, Any]], description: str = "") -> PipelineDefinition:
    """创建流水线"""
    return integrated_pipeline.create_pipeline_from_steps(name, steps, description)

def get_pipeline_status(pipeline_name: str) -> Dict[str, Any]:
    """获取流水线状态"""
    return integrated_pipeline.get_pipeline_status(pipeline_name)

def export_manifest() -> Dict[str, Any]:
    """导出清单"""
    return integrated_pipeline.export_pipeline_manifest()