import yaml
import os
import ast
import inspect
from typing import Dict, Any, List, Optional
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from functools import lru_cache

Base = declarative_base()

class ToolModel(Base):
    __tablename__ = 'tools'
    id = Column(Integer, primary_key=True)
    tool_id = Column(String(64), unique=True, nullable=False)
    description = Column(Text)
    input_type = Column(String(32))
    output_type = Column(String(32))
    params = Column(JSON)
    code = Column(Text)  # 新增：存储工具代码
    source = Column(String(32), default="auto_generated")  # 新增：工具来源 (user_uploaded/auto_generated)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ToolRegistryError(Exception):
    """自定义异常：工具库相关错误"""
    pass

class ToolRegistry:
    def __init__(self, db_url: str):
        self.logger = logging.getLogger("ToolRegistry")
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def list_tools(self, limit=100, offset=0) -> List[Dict[str, Any]]:
        """分页查询数据库"""
        session = self.Session()
        try:
            tools = session.query(ToolModel).offset(offset).limit(limit).all()
            return [self._to_dict(tool) for tool in tools]
        finally:
            session.close()
    
    def get_tool_list(self) -> List[Dict[str, Any]]:
        """获取所有工具列表（兼容TaskEngine调用）"""
        return self.list_tools(limit=1000)  # 返回足够多的工具

    @lru_cache(maxsize=10000)
    def find_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """查找工具，使用LRU缓存"""
        session = self.Session()
        try:
            tool = session.query(ToolModel).filter_by(tool_id=tool_id).first()
            return self._to_dict(tool) if tool else None
        finally:
            session.close()

    def register_tool(self, tool: Dict[str, Any]):
        """注册新工具到数据库并清除缓存"""
        session = self.Session()
        try:
            existing_tool = session.query(ToolModel).filter_by(tool_id=tool["tool_id"]).first()
            if existing_tool:
                # 工具已存在，更新信息
                existing_tool.description = tool.get("description", existing_tool.description)
                existing_tool.input_type = tool.get("input_type", existing_tool.input_type)
                existing_tool.output_type = tool.get("output_type", existing_tool.output_type)
                existing_tool.params = tool.get("params", existing_tool.params)
                existing_tool.code = tool.get("code", existing_tool.code)
                existing_tool.source = tool.get("source", existing_tool.source)
                session.commit()
                self.logger.info(f"更新已存在工具: {tool['tool_id']}")
            else:
                # 新工具，添加到数据库
                new_tool = ToolModel(
                    tool_id=tool["tool_id"],
                    description=tool.get("description"),
                    input_type=tool.get("input_type"),
                    output_type=tool.get("output_type"),
                    params=tool.get("params", {}),
                    code=tool.get("code", ""),
                    source=tool.get("source", "auto_generated")
                )
                session.add(new_tool)
                session.commit()
                self.logger.info(f"注册新工具: {tool['tool_id']}")
            
            # 清除LRU缓存
            self.find_tool.cache_clear()
            
        finally:
            session.close()

    def register_tool_with_code(self, tool_id: str, code: str, description: str = "", 
                               input_type: str = "any", output_type: str = "any", 
                               params: Dict[str, Any] = None, source: str = "auto_generated"):
        """注册带代码的工具"""
        tool_info = {
            "tool_id": tool_id,
            "description": description,
            "input_type": input_type,
            "output_type": output_type,
            "params": params or {},
            "code": code,
            "source": source
        }
        self.register_tool(tool_info)

    def get_tool_code(self, tool_id: str) -> Optional[str]:
        """获取工具代码"""
        tool = self.find_tool(tool_id)
        return tool.get("code") if tool else None

    def update_tool_code(self, tool_id: str, code: str):
        """更新工具代码"""
        session = self.Session()
        try:
            tool = session.query(ToolModel).filter_by(tool_id=tool_id).first()
            if tool:
                tool.code = code
                session.commit()
                self.find_tool.cache_clear()
                self.logger.info(f"更新工具代码: {tool_id}")
            else:
                raise ToolRegistryError(f"工具不存在: {tool_id}")
        finally:
            session.close()

    def unregister_tool(self, tool_id: str):
        """注销工具"""
        session = self.Session()
        try:
            tool = session.query(ToolModel).filter_by(tool_id=tool_id).first()
            if not tool:
                raise ToolRegistryError(f"工具不存在: {tool_id}")
            session.delete(tool)
            session.commit()
            # 清除LRU缓存
            self.find_tool.cache_clear()
            self.logger.info(f"注销工具: {tool_id}")
        finally:
            session.close()

    def validate_tool_params(self, tool_id: str, params: Dict[str, Any]) -> bool:
        """验证工具参数"""
        tool = self.find_tool(tool_id)
        if not tool:
            raise ToolRegistryError(f"工具不存在: {tool_id}")
        expected_params = tool.get("params", {})
        for key, typ in expected_params.items():
            if key not in params:
                raise ToolRegistryError(f"缺少参数: {key}")
            if typ == "str" and not isinstance(params[key], str):
                raise ToolRegistryError(f"参数{key}应为str")
            if typ == "int" and not isinstance(params[key], int):
                raise ToolRegistryError(f"参数{key}应为int")
        return True

    def auto_register_from_file(self, tool_file_path: str, source: str = "auto_generated") -> bool:
        """从生成的工具文件中自动提取信息并注册到数据库"""
        try:
            if not os.path.exists(tool_file_path):
                self.logger.warning(f"工具文件不存在: {tool_file_path}")
                return False
            
            # 读取文件代码
            with open(tool_file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            tool_id = os.path.basename(tool_file_path).replace('.py', '')
            tool_info = self._extract_tool_info_from_code(code)
            
            if tool_info:
                # 添加代码和来源信息
                tool_info["code"] = code
                tool_info["source"] = source
                
                # 注册或更新工具
                self.register_tool(tool_info)
                self.logger.info(f"自动注册/更新工具: {tool_id} (来源: {source})")
                return True
            else:
                self.logger.warning(f"无法从文件提取工具信息: {tool_file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"自动注册工具失败: {e}")
            return False

    def _extract_tool_info_from_code(self, code: str) -> Optional[Dict[str, Any]]:
        """从代码中提取工具信息"""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    tool_id = node.name
                    params = {}
                    
                    for arg in node.args.args:
                        if arg.arg != 'self':
                            if arg.annotation:
                                if isinstance(arg.annotation, ast.Name):
                                    params[arg.arg] = arg.annotation.id
                                else:
                                    params[arg.arg] = "Any"
                            else:
                                params[arg.arg] = "Any"
                    
                    description = ""
                    if node.body and isinstance(node.body[0], ast.Expr):
                        if isinstance(node.body[0].value, ast.Constant):
                            description = node.body[0].value.value
                    
                    input_type = self._infer_input_type(params)
                    output_type = self._infer_output_type(tool_id, description)
                    
                    return {
                        "tool_id": tool_id,
                        "description": description or f"自动生成的工具: {tool_id}",
                        "input_type": input_type,
                        "output_type": output_type,
                        "params": params
                    }
            return None
        except Exception as e:
            self.logger.error(f"解析工具代码失败: {e}")
            return None

    def _extract_tool_info_from_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """从Python文件中提取工具信息（保持向后兼容）"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self._extract_tool_info_from_code(content)
        except Exception as e:
            self.logger.error(f"解析工具文件失败: {e}")
            return None

    def _infer_input_type(self, params: Dict[str, str]) -> str:
        """根据参数推断输入类型"""
        if "image" in params:
            return "image"
        elif "text" in params:
            return "text"
        elif "file" in params:
            return "file"
        else:
            return "any"

    def _infer_output_type(self, tool_id: str, description: str) -> str:
        """根据工具名和描述推断输出类型"""
        tool_lower = tool_id.lower()
        desc_lower = description.lower()
        
        if "translator" in tool_lower or "翻译" in desc_lower:
            return "text"
        elif "resizer" in tool_lower or "upscaler" in tool_lower:
            return "image"
        elif "extractor" in tool_lower or "ocr" in desc_lower:
            return "text"
        elif "processor" in tool_lower:
            return "any"
        else:
            return "any"

    def _to_dict(self, tool: ToolModel) -> Dict[str, Any]:
        """工具模型转字典"""
        return {
            "tool_id": tool.tool_id,
            "description": tool.description,
            "input_type": tool.input_type,
            "output_type": tool.output_type,
            "params": tool.params,
            "code": tool.code,
            "source": tool.source
        }