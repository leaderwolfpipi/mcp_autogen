import logging
from typing import Dict, Any, List
from core.tool_registry import ToolRegistry, ToolRegistryError

# 工具编排器异常
class ToolOrchestratorError(Exception):
    pass

# 工具编排器
class ToolOrchestrator:
    def __init__(self, tool_registry: ToolRegistry):
        self.logger = logging.getLogger("ToolOrchestrator")
        self.tool_registry = tool_registry

    def decide(self, requirement: Dict[str, Any]) -> Dict[str, Any]:
        """
        决策工具组合/生成方案
        返回：
        {
            "plan_type": "pipeline" | "single" | "codegen",
            "pipeline": [ ... ]  # 若为pipeline，则包含工具列表
            "missing_tools": [ ... ]  # 若需生成新工具，则包含新生成的工具列表
        }
        """
        plan = {
            "plan_type": None,
            "pipeline": [],
            "missing_tools": []
        }
        components = requirement.get("components", [])
        for component in components:
            tool_type = component["tool_type"]
            params = component.get("params", {})
            tool = self.tool_registry.find_tool(tool_type)
            if tool:
                plan["pipeline"].append({"tool": tool_type, "params": params})
            else:
                plan["missing_tools"].append({"tool": tool_type, "params": params})
        if plan["missing_tools"]:
            plan["plan_type"] = "codegen"
        elif len(plan["pipeline"]) == 1:
            plan["plan_type"] = "single"
        else:
            plan["plan_type"] = "pipeline"
        return plan