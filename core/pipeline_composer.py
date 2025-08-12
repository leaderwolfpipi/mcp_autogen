import logging
from typing import Dict, Any, List
from core.tool_registry import ToolRegistry, ToolRegistryError

class PipelineComposerError(Exception):
    pass

class PipelineComposer:
    def __init__(self, tool_registry: ToolRegistry):
        self.logger = logging.getLogger("PipelineComposer")
        self.tool_registry = tool_registry
        # 定义类型兼容性映射
        self.type_compatibility = {
            "image": ["image", "file", "any"],
            "file": ["file", "image", "any"],
            "text": ["text", "any"],
            "data": ["data", "any"],
            "any": ["image", "file", "text", "data", "any"]
        }

    def _is_compatible(self, output_type: str, input_type: str) -> bool:
        """
        检查类型兼容性
        """
        if not output_type or not input_type:
            return True  # 如果类型未定义，认为兼容

        # 检查直接兼容
        if output_type == input_type:
            return True

        # 检查映射兼容
        compatible_types = self.type_compatibility.get(output_type, [])
        return input_type in compatible_types

    def compose(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成pipeline结构，自动连接输入输出，类型检查
        返回：
        {
            "pipeline": [
                {"tool": "text_extractor", "params": {...}, "input_type": "text", "output_type": "text"},
                ...
            ]
        }
        """
        pipeline = []
        prev_output_type = None
        for step in plan.get("pipeline", []):
            tool_id = step["tool"]
            params = step.get("params", {})
            tool = self.tool_registry.find_tool(tool_id)
            if not tool:
                raise PipelineComposerError(f"工具不存在: {tool_id}")
            input_type = tool.get("input_type")
            output_type = tool.get("output_type")

            # 改进的类型兼容性检查
            if prev_output_type and input_type and not self._is_compatible(prev_output_type, input_type):
                self.logger.warning(f"工具{tool_id}输入类型{input_type}与上一步输出{prev_output_type}可能不兼容，但继续执行")
                # 不抛出异常，只记录警告

            pipeline.append({
                "tool": tool_id,
                "params": params,
                "input_type": input_type,
                "output_type": output_type
            })
            prev_output_type = output_type
        return {"pipeline": pipeline}