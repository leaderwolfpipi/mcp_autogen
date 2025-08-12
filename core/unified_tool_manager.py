#!/usr/bin/env python3
"""
统一工具管理器 - 整合数据库工具注册表和MCP工具标准化包装器
生产级别实现

工具来源说明：
- LOCAL: 本地工具（高频使用）
- USER_UPLOADED: 用户上传的工具
- AUTO_GENERATED: 自动生成的工具

所有工具都通过MCP协议包装，并最终保存到数据库中。
"""

import logging
import inspect
import json
import asyncio
import os
import re
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import traceback
from datetime import datetime
import hashlib

# 导入MCP相关定义
from .mcp_wrapper import (
    MCPToolType, MCPParameter, MCPTool, MCPWrapper,
    mcp_wrapper, register_mcp_tool, call_mcp_tool
)

class ToolSource(Enum):
    """工具来源枚举"""
    LOCAL = "local"  # 本地工具（高频使用）
    USER_UPLOADED = "user_uploaded"  # 用户上传的工具
    AUTO_GENERATED = "auto_generated"  # 自动生成的工具

@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str = ""
    source: ToolSource = ToolSource.LOCAL
    function: Optional[Callable] = None
    mcp_tool: Optional[MCPTool] = None
    signature: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    is_async: bool = False
    is_active: bool = True

class UnifiedToolManager:
    """
    统一工具管理器
    整合数据库注册表和MCP工具标准化包装器
    """
    
    def __init__(self, db_registry=None):
        self.logger = logging.getLogger("UnifiedToolManager")
        self.db_registry = db_registry
        
        # 工具存储
        self.tools: Dict[str, ToolDefinition] = {}
        self.function_cache: Dict[str, Callable] = {}
        self.tool_sources: Dict[str, ToolSource] = {}
        
        # 验证数据库注册表配置
        if self.db_registry:
            self.logger.info("数据库注册表已配置，将支持工具持久化")
        else:
            self.logger.warning("数据库注册表未配置，工具将无法持久化到数据库")
        
        # 初始化系统
        self._initialize_system()
    
    def _initialize_system(self):
        """初始化系统"""
        self.logger.info("初始化统一工具管理系统...")
        
        # 发现本地工具
        self._discover_local_tools()
        
        # 发现数据库工具
        self._discover_database_tools()
        
        # 生成MCP工具
        self._generate_mcp_tools()
        
        self.logger.info(f"系统初始化完成，共发现 {len(self.tools)} 个工具")
    
    def _discover_local_tools(self):
        """发现本地工具"""
        try:
            import tools
            import inspect
            
            def is_tool_function(obj):
                """判断是否为工具函数"""
                # 必须是可调用的
                if not callable(obj):
                    return False
                
                # 不能是内置函数或类型
                if obj.__name__ in ['Any', 'Dict', 'List', 'Optional', 'Union', 'Tuple', 'Callable']:
                    return False
                
                # 不能是类
                if inspect.isclass(obj):
                    return False
                
                # 不能是模块
                if inspect.ismodule(obj):
                    return False
                
                # 必须来自tools包
                if not hasattr(obj, '__module__') or not obj.__module__.startswith('tools.'):
                    return False
                
                # 不能以下划线开头
                if obj.__name__.startswith('_'):
                    return False
                
                # 排除一些常见的非工具函数
                exclude_names = {
                    'logger', 'logging', 'os', 'sys', 're', 'json', 'time', 'datetime',
                    'requests', 'urllib', 'pathlib', 'shutil', 'subprocess', 'threading',
                    'asyncio', 'concurrent', 'functools', 'itertools', 'collections'
                }
                if obj.__name__ in exclude_names:
                    return False
                
                return True
            
            for attr_name in dir(tools):
                attr = getattr(tools, attr_name)
                # 检查属性是否为工具函数
                if is_tool_function(attr):
                    tool_def = ToolDefinition(
                        name=attr_name,
                        source=ToolSource.LOCAL,
                        function=attr,
                        description=attr.__doc__ or "",
                        signature=self._analyze_function_signature(attr),
                        is_async=asyncio.iscoroutinefunction(attr)
                    )
                    self.tools[attr_name] = tool_def
                    self.tool_sources[attr_name] = ToolSource.LOCAL
                    self.function_cache[attr_name] = attr
                    self.logger.info(f"发现本地工具: {attr_name}")
        except ImportError as e:
            self.logger.warning(f"本地tools模块未找到: {e}")
    
    def _discover_database_tools(self):
        """发现数据库中的工具"""
        if not self.db_registry:
            self.logger.info("数据库注册表未配置，跳过数据库工具发现")
            return
        
        try:
            db_tools = self.db_registry.list_tools()
            for tool_info in db_tools:
                tool_name = tool_info.get("tool_id")
                if tool_name:
                    # 根据数据库中的source字段确定工具来源
                    db_source = tool_info.get("source", "auto_generated")
                    if db_source == "user_uploaded":
                        source = ToolSource.USER_UPLOADED
                    elif db_source == "local":
                        source = ToolSource.LOCAL
                    else:
                        source = ToolSource.AUTO_GENERATED
                    
                    tool_def = ToolDefinition(
                        name=tool_name,
                        source=source,
                        description=tool_info.get("description", ""),
                        metadata=tool_info,
                        signature=self._parse_db_tool_signature(tool_info),
                        created_at=datetime.fromisoformat(tool_info.get("created_at", datetime.now().isoformat())),
                        updated_at=datetime.fromisoformat(tool_info.get("updated_at", datetime.now().isoformat()))
                    )
                    self.tools[tool_name] = tool_def
                    self.tool_sources[tool_name] = source
                    self.logger.info(f"发现数据库工具: {tool_name} (来源: {source.value})")
            
            self.logger.info(f"从数据库发现 {len(db_tools)} 个工具")
        except Exception as e:
            self.logger.error(f"发现数据库工具失败: {e}")
    
    def _generate_mcp_tools(self):
        """为所有工具生成MCP工具定义"""
        for tool_name, tool_def in self.tools.items():
            # 所有工具都需要MCP包装，无论是否有函数
            if tool_def.function:
                # 有函数的情况，从函数生成MCP工具
                mcp_tool = mcp_wrapper.create_mcp_tool_from_function(tool_def.function, tool_name)
            else:
                # 没有函数的情况，从元数据生成MCP工具
                mcp_tool = mcp_wrapper.create_mcp_tool_from_metadata(
                    tool_name, tool_def.description, tool_def.signature
                )
            
            tool_def.mcp_tool = mcp_tool
    
    def register_tool(self, tool_func: Callable, tool_name: str = None, 
                     description: str = "", source: ToolSource = ToolSource.LOCAL,
                     metadata: Dict[str, Any] = None) -> ToolDefinition:
        """注册工具"""
        if tool_name is None:
            tool_name = tool_func.__name__
        
        # 创建工具定义
        tool_def = ToolDefinition(
            name=tool_name,
            description=description or tool_func.__doc__ or "",
            source=source,
            function=tool_func,
            signature=self._analyze_function_signature(tool_func),
            metadata=metadata or {},
            is_async=asyncio.iscoroutinefunction(tool_func)
        )
        
        # 生成MCP工具定义
        mcp_tool = mcp_wrapper.create_mcp_tool_from_function(tool_func, tool_name)
        tool_def.mcp_tool = mcp_tool
        
        # 存储工具
        self.tools[tool_name] = tool_def
        self.function_cache[tool_name] = tool_func
        self.tool_sources[tool_name] = source
        
        self.logger.info(f"注册工具: {tool_name} (来源: {source.value})")
        return tool_def
    
    async def get_tool(self, tool_name: str) -> Optional[Callable]:
        """获取工具函数"""
        if tool_name in self.function_cache:
            return self.function_cache[tool_name]
        
        if tool_name not in self.tools:
            return None
        
        tool_def = self.tools[tool_name]
        
        # 所有工具都可能有函数，优先返回缓存的函数
        if tool_def.function:
            return tool_def.function
        
        # 如果是数据库中的工具，尝试加载
        if tool_def.source in [ToolSource.USER_UPLOADED, ToolSource.AUTO_GENERATED]:
            return await self._load_database_tool(tool_name, tool_def)
        
        return None
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行工具"""
        tool_func = await self.get_tool(tool_name)
        if not tool_func:
            raise ValueError(f"工具不存在: {tool_name}")
        
        if asyncio.iscoroutinefunction(tool_func):
            return await tool_func(**kwargs)
        else:
            return tool_func(**kwargs)
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用MCP工具"""
        try:
            if tool_name not in self.tools:
                raise ValueError(f"工具不存在: {tool_name}")
            
            tool_func = await self.get_tool(tool_name)
            if not tool_func:
                raise ValueError(f"工具函数不存在: {tool_name}")
            
            # 使用MCP包装器调用工具
            return await mcp_wrapper.call_tool(tool_name, arguments)
            
        except Exception as e:
            self.logger.error(f"MCP工具执行失败 {tool_name}: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"工具执行失败: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def _load_database_tool(self, tool_name: str, tool_def: ToolDefinition) -> Optional[Callable]:
        """从数据库加载工具函数"""
        try:
            # 首先尝试从数据库获取工具代码
            tool_code = self.db_registry.get_tool_code(tool_name)
            
            if tool_code:
                # 有代码，直接编译
                tool_func = self._compile_tool_from_code(tool_name, tool_code)
                if tool_func:
                    self.function_cache[tool_name] = tool_func
                    tool_def.function = tool_func
                    tool_def.is_async = asyncio.iscoroutinefunction(tool_func)
                    self.logger.info(f"成功从数据库代码加载工具: {tool_name}")
                    return tool_func
            
            # 如果没有代码，根据元数据生成
            tool_info = self.db_registry.find_tool(tool_name)
            if tool_info:
                return await self._generate_tool_from_metadata(tool_name, tool_info)
            
            return None
            
        except Exception as e:
            self.logger.error(f"从数据库加载工具 {tool_name} 失败: {e}")
            return None
    
    async def _generate_tool_from_metadata(self, tool_name: str, tool_info: Dict[str, Any]) -> Optional[Callable]:
        """根据元数据生成工具函数"""
        try:
            from .code_generator import CodeGenerator
            
            code_generator = CodeGenerator(use_llm=False)
            
            tool_spec = {
                "tool": tool_name,
                "params": tool_info.get("params", {}),
                "description": tool_info.get("description", ""),
                "input_type": tool_info.get("input_type", "any"),
                "output_type": tool_info.get("output_type", "any")
            }
            
            code = code_generator.generate(tool_spec)
            tool_func = self._compile_tool_from_code(tool_name, code)
            
            if tool_func:
                self.function_cache[tool_name] = tool_func
                self.logger.info(f"根据元数据生成工具: {tool_name}")
                return tool_func
            
            return None
            
        except Exception as e:
            self.logger.error(f"根据元数据生成工具失败: {e}")
            return None
    
    def _compile_tool_from_code(self, tool_name: str, code: str) -> Optional[Callable]:
        """从代码编译工具函数"""
        try:
            module_namespace = {}
            exec(code, module_namespace)
            
            if tool_name in module_namespace:
                tool_func = module_namespace[tool_name]
                self.logger.info(f"成功编译工具函数: {tool_name}")
                return tool_func
            else:
                self.logger.error(f"编译的代码中没有找到函数: {tool_name}")
                return None
        except Exception as e:
            self.logger.error(f"编译工具 {tool_name} 失败: {e}")
            return None
    
    async def save_tool_to_database(self, tool_name: str, tool_func: Callable, 
                                  description: str = "", source: str = "auto_generated"):
        """保存工具到数据库"""
        if not self.db_registry:
            self.logger.error("数据库注册表未配置，无法保存工具到数据库")
            return False
        
        try:
            self.logger.info(f"开始保存工具到数据库: {tool_name}")
            
            # 分析工具函数
            signature = self._analyze_function_signature(tool_func)
            
            # 提取工具代码
            tool_code = self._extract_tool_code(tool_func)
            
            # 准备工具信息
            tool_info = {
                "tool_id": tool_name,
                "description": description or f"工具: {tool_name}",
                "input_type": "any",
                "output_type": "any",
                "params": signature.get("parameters", {}),
                "code": tool_code,
                "source": source,  # 所有工具都保存到数据库，source表示工具来源
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # 保存到数据库
            result = self.db_registry.register_tool(tool_info)
            
            if result:
                # 更新本地缓存
                tool_source = ToolSource.USER_UPLOADED if source == "user_uploaded" else ToolSource.AUTO_GENERATED
                tool_def = ToolDefinition(
                    name=tool_name,
                    source=tool_source,
                    function=tool_func,
                    description=description,
                    metadata=tool_info,
                    signature=signature,
                    is_async=asyncio.iscoroutinefunction(tool_func)
                )
                
                self.tools[tool_name] = tool_def
                self.function_cache[tool_name] = tool_func
                self.tool_sources[tool_name] = tool_source
                
                # 重新生成MCP工具定义
                mcp_tool = mcp_wrapper.create_mcp_tool_from_function(tool_func, tool_name)
                tool_def.mcp_tool = mcp_tool
                
                self.logger.info(f"✅ 成功保存工具到数据库: {tool_name} (来源: {source})")
                return True
            else:
                self.logger.error(f"❌ 数据库注册工具失败: {tool_name}")
                return False
            
        except Exception as e:
            self.logger.error(f"保存工具到数据库失败: {e}")
            return False
    
    def _extract_tool_code(self, tool_func: Callable) -> str:
        """提取工具函数代码"""
        try:
            # 首先检查是否有原始代码属性（函数包装器）
            if hasattr(tool_func, '_original_code'):
                return tool_func._original_code
            
            # 尝试从本地tools目录读取代码文件
            tool_name = tool_func.__name__
            local_file_path = f"tools/{tool_name}.py"
            
            if os.path.exists(local_file_path):
                try:
                    with open(local_file_path, "r", encoding="utf-8") as f:
                        code = f.read()
                    return code
                except Exception as e:
                    self.logger.warning(f"读取本地文件失败: {e}")
            
            # 尝试获取源代码
            try:
                source_code = inspect.getsource(tool_func)
                return source_code
            except (OSError, TypeError):
                # 如果无法获取源代码，构造基本代码
                func_name = tool_func.__name__
                sig = inspect.signature(tool_func)
                
                # 构造参数列表
                param_list = []
                for name, param in sig.parameters.items():
                    if param.default == inspect.Parameter.empty:
                        param_list.append(name)
                    else:
                        param_list.append(f"{name}={repr(param.default)}")
                
                param_str = ", ".join(param_list)
                
                # 构造基本函数代码
                basic_code = f"""def {func_name}({param_str}):
    \"\"\"
    动态生成的工具函数: {func_name}
    这是一个自动生成的函数，无法显示完整源代码。
    \"\"\"
    # 动态生成的函数实现
    # 参数: {param_str}
    pass"""
                
                return basic_code
                
        except Exception as e:
            self.logger.error(f"提取工具代码失败: {e}")
            func_name = getattr(tool_func, '__name__', 'unknown_function')
            return f"# 无法提取代码的函数: {func_name}\ndef {func_name}(*args, **kwargs):\n    pass"
    
    def exists(self, tool_name: str) -> bool:
        """检查工具是否存在"""
        return tool_name in self.tools
    
    def get_source(self, tool_name: str) -> Optional[ToolSource]:
        """获取工具来源"""
        if tool_name in self.tools:
            return self.tools[tool_name].source
        return None
    
    def get_tool_list(self) -> List[Dict[str, Any]]:
        """获取工具列表"""
        tool_list = []
        for tool_name, tool_def in self.tools.items():
            tool_info = {
                "name": tool_name,
                "description": tool_def.description,
                "source": tool_def.source.value,
                "is_async": tool_def.is_async,
                "is_active": tool_def.is_active,
                "created_at": tool_def.created_at.isoformat(),
                "updated_at": tool_def.updated_at.isoformat(),
                "version": tool_def.version
            }
            
            # 如果有MCP工具定义，添加schema信息
            if tool_def.mcp_tool:
                tool_info["inputSchema"] = tool_def.mcp_tool.inputSchema
                tool_info["outputSchema"] = tool_def.mcp_tool.outputSchema
            
            tool_list.append(tool_info)
        return tool_list
    
    def get_mcp_tool_list(self) -> List[Dict[str, Any]]:
        """获取MCP工具列表"""
        mcp_tool_list = []
        for tool_name, tool_def in self.tools.items():
            if tool_def.mcp_tool:
                tool_info = {
                    "name": tool_name,
                    "description": tool_def.mcp_tool.description,
                    "inputSchema": tool_def.mcp_tool.inputSchema,
                    "outputSchema": tool_def.mcp_tool.outputSchema
                }
                mcp_tool_list.append(tool_info)
        return mcp_tool_list
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """列出所有工具（向后兼容）"""
        return {tool["name"]: tool for tool in self.get_tool_list()}
    
    def generate_mcp_schema(self) -> Dict[str, Any]:
        """生成MCP Schema"""
        return mcp_wrapper.generate_mcp_schema()
    
    def export_tools_manifest(self) -> Dict[str, Any]:
        """导出工具清单"""
        return {
            "tools": self.get_tool_list(),
            "mcp_tools": self.get_mcp_tool_list(),
            "schema": self.generate_mcp_schema(),
            "total_tools": len(self.tools),
            "total_mcp_tools": len([t for t in self.tools.values() if t.mcp_tool]),
            "exported_at": datetime.now().isoformat()
        }
    
    def _analyze_function_signature(self, func: Callable) -> Dict[str, Any]:
        """分析函数签名"""
        try:
            sig = inspect.signature(func)
            params = {}
            
            for name, param in sig.parameters.items():
                params[name] = {
                    "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                    "required": param.default == inspect.Parameter.empty,
                    "default": param.default if param.default != inspect.Parameter.empty else None
                }
            
            return {
                "parameters": params,
                "return_type": "Any"
            }
        except Exception as e:
            self.logger.error(f"分析函数签名失败: {e}")
            return {"parameters": {}, "return_type": "Any"}
    
    def _parse_db_tool_signature(self, tool_info: Dict[str, Any]) -> Dict[str, Any]:
        """解析数据库工具签名"""
        try:
            params = tool_info.get("params", {})
            return {
                "parameters": params,
                "return_type": tool_info.get("output_type", "Any")
            }
        except Exception as e:
            self.logger.error(f"解析数据库工具签名失败: {e}")
            return {"parameters": {}, "return_type": "Any"}

# 全局统一工具管理器实例
unified_tool_manager = None

def get_unified_tool_manager(db_registry=None) -> UnifiedToolManager:
    """获取全局统一工具管理器实例"""
    global unified_tool_manager
    if unified_tool_manager is None:
        unified_tool_manager = UnifiedToolManager(db_registry)
    elif db_registry is not None and unified_tool_manager.db_registry is None:
        # 如果之前没有db_registry，但现在有，则更新
        unified_tool_manager.db_registry = db_registry
        unified_tool_manager.logger.info("更新数据库注册表配置")
        # 重新发现数据库工具
        unified_tool_manager._discover_database_tools()
    return unified_tool_manager

# 便捷函数
def register_tool(tool_func: Callable, tool_name: str = None, 
                 description: str = "", source: ToolSource = ToolSource.LOCAL,
                 metadata: Dict[str, Any] = None) -> ToolDefinition:
    """注册工具"""
    manager = get_unified_tool_manager()
    return manager.register_tool(tool_func, tool_name, description, source, metadata)

async def get_tool(tool_name: str) -> Optional[Callable]:
    """获取工具函数"""
    manager = get_unified_tool_manager()
    return await manager.get_tool(tool_name)

async def execute_tool(tool_name: str, **kwargs) -> Any:
    """执行工具"""
    manager = get_unified_tool_manager()
    return await manager.execute_tool(tool_name, **kwargs)

async def call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """调用MCP工具"""
    manager = get_unified_tool_manager()
    return await manager.call_mcp_tool(tool_name, arguments)

def get_tool_list() -> List[Dict[str, Any]]:
    """获取工具列表"""
    manager = get_unified_tool_manager()
    return manager.get_tool_list()

def get_mcp_tool_list() -> List[Dict[str, Any]]:
    """获取MCP工具列表"""
    manager = get_unified_tool_manager()
    return manager.get_mcp_tool_list()

def export_tools_manifest() -> Dict[str, Any]:
    """导出工具清单"""
    manager = get_unified_tool_manager()
    return manager.export_tools_manifest() 