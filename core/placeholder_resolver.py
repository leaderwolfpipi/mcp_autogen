#!/usr/bin/env python3
"""
占位符解析器
用于解析和替换pipeline中的占位符引用
"""

import re
import logging
import os
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from collections import defaultdict

# 导入工具适配器
from .tool_adapter import get_tool_adapter
from .semantic_dependency_analyzer import SemanticDependencyAnalyzer
from .smart_parameter_adapter import SmartParameterAdapter

@dataclass
class NodeOutput:
    """节点输出信息"""
    node_id: str
    output_type: str
    output_key: str
    value: Any
    description: str

class PlaceholderResolver:
    """占位符解析器"""
    
    def __init__(self):
        self.logger = logging.getLogger("PlaceholderResolver")
        # 占位符模式：$node_id.output 或 $node_id.output.key 或 $node_id.output.key1.key2...
        self.placeholder_pattern = r'\$([a-zA-Z_][a-zA-Z0-9_]*)\.output(?:\.([a-zA-Z_][a-zA-Z0-9_\.]*))?'
        
        # 初始化工具适配器
        self.tool_adapter = get_tool_adapter()
        
        # 初始化语义依赖分析器
        self.semantic_analyzer = SemanticDependencyAnalyzer()
        
        # 初始化智能参数适配器
        self.parameter_adapter = SmartParameterAdapter()
        
    def resolve_placeholders(self, params: Dict[str, Any], node_outputs: Dict[str, NodeOutput]) -> Dict[str, Any]:
        """
        解析参数中的占位符并替换为实际值
        包含智能参数适配功能
        
        Args:
            params: 包含占位符的参数字典
            node_outputs: 节点输出映射 {node_id: NodeOutput}
            
        Returns:
            解析后的参数字典
        """
        # 首先进行占位符解析
        resolved_params = {}
        
        for key, value in params.items():
            if isinstance(value, str):
                resolved_value = self._resolve_string_placeholder(value, node_outputs)
                resolved_params[key] = resolved_value
            elif isinstance(value, dict):
                resolved_params[key] = self.resolve_placeholders(value, node_outputs)
            elif isinstance(value, list):
                resolved_params[key] = [
                    self.resolve_placeholders(item, node_outputs) if isinstance(item, dict)
                    else self._resolve_string_placeholder(item, node_outputs) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                resolved_params[key] = value
        
        # 然后进行智能参数适配
        adapted_params = self._adapt_parameters_intelligently(resolved_params, node_outputs)
        
        return adapted_params
    
    def _adapt_parameters_intelligently(self, params: Dict[str, Any], 
                                      node_outputs: Dict[str, NodeOutput]) -> Dict[str, Any]:
        """智能参数适配"""
        # 分析参数语义不匹配
        mismatches = []
        for param_name, param_value in params.items():
            param_semantic = self._analyze_param_semantic(param_name, param_value)
            
            # 检查是否需要适配
            if self._needs_semantic_adaptation(param_name, param_value, param_semantic):
                adaptation = self._create_semantic_adaptation(param_name, param_value, param_semantic)
                if adaptation:
                    params[param_name] = adaptation
                    self.logger.info(f"智能参数适配: {param_name} -> {type(adaptation).__name__}")
        
        return params
    
    def _analyze_param_semantic(self, param_name: str, param_value: Any) -> str:
        """分析参数语义"""
        # 基于参数名称分析
        if any(keyword in param_name.lower() for keyword in ['file', 'path', 'filename']):
            return "file_path"
        elif any(keyword in param_name.lower() for keyword in ['content', 'text', 'data']):
            return "file_content"
        elif any(keyword in param_name.lower() for keyword in ['url', 'link']):
            return "url"
        
        # 基于参数值分析
        if isinstance(param_value, str):
            if param_value.startswith(('http://', 'https://')):
                return "url"
            elif os.path.sep in param_value or param_value.endswith(('.txt', '.md', '.pdf')):
                return "file_path"
            elif len(param_value) > 100:  # 长文本可能是内容
                return "file_content"
        elif isinstance(param_value, dict):
            # 分析字典结构
            return self._analyze_dict_semantic(param_value, param_name)
        
        return "unknown"
    
    def _analyze_dict_semantic(self, data: Dict[str, Any], param_name: str) -> str:
        """分析字典的语义类型"""
        # 检查是否包含文件路径信息
        if "file_path" in data:
            return "file_path"
        elif "content" in data or "text" in data:
            return "file_content"
        elif "url" in data or "link" in data:
            return "url"
        elif "status" in data and "message" in data:
            return "metadata"
        
        # 检查字典的值类型
        for key, value in data.items():
            if isinstance(value, str):
                if value.endswith(('.txt', '.md', '.pdf')) or os.path.sep in value:
                    return "file_path"
                elif len(value) > 100:
                    return "file_content"
        
        return "unknown"
    
    def _needs_semantic_adaptation(self, param_name: str, param_value: Any, param_semantic: str) -> bool:
        """检查是否需要语义适配"""
        # 如果参数名暗示需要文件路径，但值是内容
        if param_semantic == "file_content" and any(keyword in param_name.lower() for keyword in ['file', 'path']):
            return True
        
        # 如果参数名暗示需要内容，但值是文件路径
        if param_semantic == "file_path" and any(keyword in param_name.lower() for keyword in ['content', 'text']):
            return True
        
        # 如果参数名暗示需要文件路径，但值是字典
        if param_semantic == "file_path" and isinstance(param_value, dict):
            return True
        
        return False
    
    def _create_semantic_adaptation(self, param_name: str, param_value: Any, param_semantic: str) -> Any:
        """创建语义适配"""
        # 文件内容 -> 文件路径的适配
        if param_semantic == "file_content" and any(keyword in param_name.lower() for keyword in ['file', 'path']):
            return self._content_to_file_path(param_value, param_name)
        
        # 文件路径 -> 文件内容的适配
        elif param_semantic == "file_path" and any(keyword in param_name.lower() for keyword in ['content', 'text']):
            return self._file_path_to_content(param_value)
        
        # 字典 -> 文件路径的适配（新增）
        elif param_semantic == "file_path" and isinstance(param_value, dict):
            extracted_path = self._extract_file_path_from_dict(param_value)
            if extracted_path:
                return extracted_path
        
        return param_value
    
    def _content_to_file_path(self, content: str, param_name: str) -> str:
        """将文件内容转换为文件路径"""
        try:
            # 生成合适的文件名
            if content.startswith('# '):
                # 从Markdown标题提取文件名
                title_match = re.match(r'^#\s+(.+)$', content.split('\n')[0])
                if title_match:
                    filename = re.sub(r'[^\w\s-]', '', title_match.group(1)).strip()
                    filename = re.sub(r'[-\s]+', '_', filename)
                    return f"{filename}.md"
            
            # 默认文件名
            return "generated_content.md"
        
        except Exception as e:
            self.logger.warning(f"内容转文件路径失败: {e}")
            return "generated_content.md"
    
    def _file_path_to_content(self, file_path: str) -> str:
        """将文件路径转换为文件内容"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # 如果文件不存在，返回路径本身作为内容
                return f"文件路径: {file_path}"
        
        except Exception as e:
            self.logger.warning(f"文件路径转内容失败: {e}")
            return f"文件路径: {file_path}"
    
    def _extract_file_path_from_dict(self, data: Dict[str, Any]) -> Optional[str]:
        """从字典中提取文件路径"""
        try:
            # 直接查找 file_path 键
            if "file_path" in data:
                file_path = data["file_path"]
                if isinstance(file_path, str):
                    return file_path
                elif isinstance(file_path, dict) and "file_path" in file_path:
                    return file_path["file_path"]
            
            # 查找其他可能的文件路径键
            for key in ["path", "filename", "file", "location"]:
                if key in data:
                    value = data[key]
                    if isinstance(value, str) and (value.endswith(('.txt', '.md', '.pdf')) or os.path.sep in value):
                        return value
            
            # 查找包含文件路径的嵌套字典
            for key, value in data.items():
                if isinstance(value, dict):
                    nested_path = self._extract_file_path_from_dict(value)
                    if nested_path:
                        return nested_path
            
            return None
            
        except Exception as e:
            self.logger.warning(f"从字典提取文件路径失败: {e}")
            return None
    
    def _resolve_string_placeholder(self, value: str, node_outputs: Dict[str, NodeOutput]) -> Any:
        """
        解析字符串中的占位符
        
        Args:
            value: 可能包含占位符的字符串
            node_outputs: 节点输出映射
            
        Returns:
            解析后的值
        """
        if not isinstance(value, str):
            return value
            
        # 查找所有占位符
        matches = re.finditer(self.placeholder_pattern, value)
        
        if not matches:
            return value
            
        resolved_value = value
        
        for match in matches:
            node_id = match.group(1)
            output_key = match.group(2)  # 可能为None
            
            if node_id not in node_outputs:
                self.logger.warning(f"节点 {node_id} 的输出未找到")
                continue
                
            node_output = node_outputs[node_id]
            
            # 确定要使用的值
            if output_key:
                # 如果指定了具体的输出键，尝试从输出值中获取
                self.logger.info(f"尝试提取嵌套值: {output_key} 从节点 {node_id}")
                replacement_value = self._extract_nested_value(node_output.value, output_key)
                self.logger.info(f"提取结果: {replacement_value}")
                
                # 如果直接提取失败，尝试在data子字典中查找
                if replacement_value is None and isinstance(node_output.value, dict) and 'data' in node_output.value:
                    self.logger.info(f"尝试在data子字典中查找键: {output_key}")
                    replacement_value = self._extract_nested_value(node_output.value['data'], output_key)
                    self.logger.info(f"在data中查找结果: {replacement_value}")
                
                # 向后兼容：处理旧格式字段映射
                if replacement_value is None and isinstance(node_output.value, dict):
                    # 搜索类工具的字段映射
                    search_field_mappings = {
                        "results": ["data.primary", "results"],
                        "primary": ["data.primary", "results"],
                        "rotated_images": ["data.primary", "rotated_images"],
                        "scaled_images": ["data.primary", "scaled_images"],
                        "paths": ["paths", "data.primary"]
                    }
                    
                    if output_key in search_field_mappings:
                        for field_path in search_field_mappings[output_key]:
                            self.logger.info(f"尝试向后兼容字段映射: {field_path}")
                            replacement_value = self._extract_nested_value(node_output.value, field_path)
                            if replacement_value is not None:
                                self.logger.info(f"向后兼容映射成功: {field_path} -> {replacement_value}")
                                break
                
                if replacement_value is None:
                    # 尝试使用工具适配器自动适配
                    self.logger.info(f"尝试自动适配节点 {node_id} 的输出以匹配键 {output_key}")
                    adapted_output = self.tool_adapter.auto_adapt_output(
                        node_output, 
                        {output_key: "expected_type"}  # 简化的期望结构
                    )
                    
                    if isinstance(adapted_output, dict) and output_key in adapted_output:
                        replacement_value = adapted_output[output_key]
                        self.logger.info(f"自动适配成功，找到键 {output_key}")
                    else:
                        self.logger.warning(f"节点 {node_id} 的输出中没有键 {output_key}，且自动适配失败")
                        continue
            else:
                # 没有指定具体键，使用智能提取
                replacement_value = self._extract_primary_value(node_output)
                
            # 替换占位符
            placeholder = match.group(0)
            # 如果占位符是整个值，直接返回替换值
            if resolved_value.strip() == placeholder:
                return replacement_value
            else:
                # 否则进行字符串替换
                resolved_value = resolved_value.replace(placeholder, str(replacement_value))
            
        return resolved_value
    
    def _extract_nested_value(self, data: Any, key_path: str) -> Any:
        """
        从嵌套数据结构中提取值
        
        Args:
            data: 数据对象
            key_path: 键路径，支持点号分隔的嵌套路径
            
        Returns:
            提取的值，如果不存在则返回None
        """
        self.logger.info(f"_extract_nested_value: 数据={data}, 键路径={key_path}")
        
        if not isinstance(data, dict):
            self.logger.info(f"_extract_nested_value: 数据不是字典，返回None")
            return None
            
        # 分割键路径
        keys = key_path.split('.')
        current = data
        
        self.logger.info(f"_extract_nested_value: 键路径分割={keys}")
        
        for key in keys:
            self.logger.info(f"_extract_nested_value: 处理键={key}, 当前值={current}")
            if isinstance(current, dict) and key in current:
                current = current[key]
                self.logger.info(f"_extract_nested_value: 找到键{key}, 新值={current}")
            else:
                self.logger.info(f"_extract_nested_value: 键{key}不存在或当前值不是字典，返回None")
                return None
                
        self.logger.info(f"_extract_nested_value: 最终结果={current}")
        return current
    
    def _extract_primary_value(self, node_output: NodeOutput) -> Any:
        """
        从节点输出中提取主要值 - 真正通用的实现
        
        Args:
            node_output: 节点输出对象
            
        Returns:
            提取的主要值
        """
        # 如果输出是字典，尝试使用output_key
        if isinstance(node_output.value, dict):
            if node_output.output_key in node_output.value:
                return node_output.value[node_output.output_key]
            # 如果output_key不存在，返回整个字典
            return node_output.value
        
        # 如果输出不是字典，直接返回
        return node_output.value
    
    def validate_pipeline_dependencies(self, components: List[Dict[str, Any]]) -> List[str]:
        """
        验证pipeline中的依赖关系
        
        Args:
            components: pipeline组件列表
            
        Returns:
            错误信息列表
        """
        errors = []
        node_ids = {comp["id"] for comp in components}
        
        for i, component in enumerate(components):
            params = component.get("params", {})
            
            # 检查参数中的占位符引用
            placeholder_refs = self._extract_placeholder_references(params)
            
            for ref in placeholder_refs:
                node_id = ref["node_id"]
                
                # 检查引用的节点是否存在
                if node_id not in node_ids:
                    errors.append(f"组件 {component['id']} 引用了不存在的节点: {node_id}")
                    continue
                    
                # 检查是否引用了后续节点（循环依赖）
                ref_index = next((j for j, c in enumerate(components) if c["id"] == node_id), -1)
                if ref_index > i:
                    errors.append(f"组件 {component['id']} 引用了后续节点 {node_id}，可能造成循环依赖")
                    
        return errors
    
    def _extract_placeholder_references(self, params: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        提取参数中的所有占位符引用
        
        Args:
            params: 参数字典
            
        Returns:
            占位符引用列表
        """
        references = []
        
        def extract_from_value(value):
            if isinstance(value, str):
                matches = re.finditer(self.placeholder_pattern, value)
                for match in matches:
                    references.append({
                        "node_id": match.group(1),
                        "output_key": match.group(2)
                    })
            elif isinstance(value, dict):
                for v in value.values():
                    extract_from_value(v)
            elif isinstance(value, list):
                for v in value:
                    extract_from_value(v)
        
        extract_from_value(params)
        return references
    
    def build_execution_order(self, components: List[Dict[str, Any]]) -> List[str]:
        """
        构建pipeline的执行顺序（拓扑排序）
        使用语义依赖分析确保通用性
        
        Args:
            components: pipeline组件列表
            
        Returns:
            按依赖顺序排列的节点ID列表
        """
        self.logger.info(f"🔍 开始构建执行顺序，节点数量: {len(components)}")
        
        # 首先尝试传统的占位符引用分析
        traditional_order = self._build_traditional_execution_order(components)
        
        # 然后使用语义依赖分析
        semantic_order = self.semantic_analyzer.build_execution_order(components)
        
        # 比较两种方法的结果
        self.logger.info(f"📊 传统方法执行顺序: {' -> '.join(traditional_order)}")
        self.logger.info(f"📊 语义分析方法执行顺序: {' -> '.join(semantic_order)}")
        
        # 选择更合理的执行顺序
        final_order = self._select_best_execution_order(components, traditional_order, semantic_order)
        
        self.logger.info(f"📋 最终执行顺序: {' -> '.join(final_order)}")
        return final_order
    
    def _build_traditional_execution_order(self, components: List[Dict[str, Any]]) -> List[str]:
        """传统的基于占位符引用的执行顺序构建"""
        # 构建依赖图
        dependencies = {}
        node_ids = {comp["id"] for comp in components}
        
        for component in components:
            node_id = component["id"]
            dependencies[node_id] = set()
            
            # 检查该节点依赖的其他节点
            params = component.get("params", {})
            placeholder_refs = self._extract_placeholder_references(params)
            
            for ref in placeholder_refs:
                if ref["node_id"] in node_ids:
                    dependencies[node_id].add(ref["node_id"])
        
        # 拓扑排序 - 修复循环依赖检测
        execution_order = []
        visited = set()
        temp_visited = set()
        
        def visit(node_id):
            """深度优先搜索，检测循环依赖"""
            if node_id in temp_visited:
                # 检测到循环依赖，记录但不抛出异常
                self.logger.warning(f"检测到循环依赖: {node_id}")
                return False
            if node_id in visited:
                return True
                
            temp_visited.add(node_id)
            
            # 访问所有依赖节点
            for dep in dependencies.get(node_id, []):
                if not visit(dep):
                    temp_visited.remove(node_id)
                    return False
                
            temp_visited.remove(node_id)
            visited.add(node_id)
            execution_order.append(node_id)
            return True
        
        # 尝试拓扑排序
        success = True
        for node_id in node_ids:
            if node_id not in visited:
                if not visit(node_id):
                    success = False
                    break
        
        # 如果拓扑排序失败，使用启发式排序
        if not success or len(execution_order) != len(node_ids):
            self.logger.warning("拓扑排序失败，使用启发式排序")
            execution_order = self._heuristic_execution_order(components, dependencies)
        
        return execution_order
    
    def _heuristic_execution_order(self, components: List[Dict[str, Any]], 
                                 dependencies: Dict[str, Set[str]]) -> List[str]:
        """启发式执行顺序构建"""
        node_ids = {comp["id"] for comp in components}
        
        # 计算每个节点的入度和出度
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        
        for node_id in node_ids:
            in_degree[node_id] = len(dependencies.get(node_id, set()))
            for dep in dependencies.get(node_id, set()):
                out_degree[dep] += 1
        
        # 基于工具类型的优先级
        tool_priority = {
            "data_source": 1,      # 数据源优先
            "data_processor": 2,   # 数据处理器
            "file_operator": 3,    # 文件操作
            "storage": 4           # 存储最后
        }
        
        # 计算每个节点的综合优先级
        node_priorities = {}
        for comp in components:
            node_id = comp["id"]
            tool_type = comp.get("tool_type", "")
            
            # 基础优先级（基于工具类型）
            base_priority = self._get_tool_category_priority(tool_type, tool_priority)
            
            # 依赖优先级（入度越小优先级越高）
            dep_priority = -in_degree[node_id]
            
            # 输出优先级（出度越大优先级越高）
            output_priority = out_degree[node_id]
            
            # 综合优先级
            node_priorities[node_id] = (base_priority, dep_priority, output_priority, node_id)
        
        # 按优先级排序
        sorted_nodes = sorted(node_priorities.values(), key=lambda x: (x[0], x[1], x[2], x[3]))
        execution_order = [node[3] for node in sorted_nodes]
        
        return execution_order
    
    def _get_tool_category_priority(self, tool_type: str, tool_priority: Dict[str, int]) -> int:
        """获取工具类型的基础优先级"""
        # 工具类型分类
        tool_categories = {
            "data_source": {"search_tool", "smart_search", "web_searcher"},
            "data_processor": {"enhanced_report_generator", "report_generator", "text_processor"},
            "file_operator": {"file_writer", "file_uploader", "minio_uploader"},
            "storage": {"minio_uploader", "file_uploader"}
        }
        
        # 查找工具类型所属的类别
        for category, tools in tool_categories.items():
            if tool_type in tools:
                return tool_priority.get(category, 5)  # 默认优先级5
        
        return 5  # 未知工具类型默认优先级
    
    def _select_best_execution_order(self, components: List[Dict[str, Any]], 
                                   traditional_order: List[str], 
                                   semantic_order: List[str]) -> List[str]:
        """选择最佳的执行顺序"""
        # 如果两种方法结果相同，直接返回
        if traditional_order == semantic_order:
            self.logger.info("✅ 两种方法结果一致，使用传统方法")
            return traditional_order
        
        # 计算传统方法的依赖覆盖率
        traditional_coverage = self._calculate_dependency_coverage(components, traditional_order)
        
        # 计算语义分析方法的依赖覆盖率
        semantic_coverage = self._calculate_dependency_coverage(components, semantic_order)
        
        self.logger.info(f"📊 传统方法依赖覆盖率: {traditional_coverage:.2f}")
        self.logger.info(f"📊 语义分析方法依赖覆盖率: {semantic_coverage:.2f}")
        
        # 选择覆盖率更高的方法
        if semantic_coverage > traditional_coverage:
            self.logger.info("✅ 选择语义分析方法（覆盖率更高）")
            return semantic_order
        else:
            self.logger.info("✅ 选择传统方法（覆盖率更高）")
            return traditional_order
    
    def _calculate_dependency_coverage(self, components: List[Dict[str, Any]], execution_order: List[str]) -> float:
        """计算执行顺序的依赖覆盖率"""
        if len(components) <= 1:
            return 1.0
        
        # 统计所有可能的依赖关系
        total_dependencies = 0
        satisfied_dependencies = 0
        
        for i, component in enumerate(components):
            params = component.get("params", {})
            placeholder_refs = self._extract_placeholder_references(params)
            
            for ref in placeholder_refs:
                total_dependencies += 1
                
                # 检查依赖是否在执行顺序中得到满足
                source_node_id = ref["node_id"]
                target_node_id = component["id"]
                
                try:
                    source_index = execution_order.index(source_node_id)
                    target_index = execution_order.index(target_node_id)
                    
                    if source_index < target_index:
                        satisfied_dependencies += 1
                except ValueError:
                    # 如果节点不在执行顺序中，跳过
                    pass
        
        return satisfied_dependencies / total_dependencies if total_dependencies > 0 else 1.0
    
    def validate_execution_order(self, components: List[Dict[str, Any]], execution_order: List[str]) -> List[str]:
        """
        验证执行顺序的正确性
        
        Args:
            components: pipeline组件列表
            execution_order: 执行顺序
            
        Returns:
            验证错误列表
        """
        errors = []
        node_ids = {comp["id"] for comp in components}
        
        # 检查所有节点都在执行顺序中
        for node_id in node_ids:
            if node_id not in execution_order:
                errors.append(f"节点 {node_id} 不在执行顺序中")
        
        # 检查执行顺序中的节点都存在
        for node_id in execution_order:
            if node_id not in node_ids:
                errors.append(f"执行顺序中的节点 {node_id} 不存在")
        
        # 检查依赖关系是否满足
        dependencies = {}
        for component in components:
            node_id = component["id"]
            dependencies[node_id] = set()
            
            params = component.get("params", {})
            placeholder_refs = self._extract_placeholder_references(params)
            
            for ref in placeholder_refs:
                if ref["node_id"] in node_ids:
                    dependencies[node_id].add(ref["node_id"])
        
        # 验证每个节点的依赖都在其之前执行
        for i, node_id in enumerate(execution_order):
            node_deps = dependencies.get(node_id, set())
            for dep in node_deps:
                if dep in execution_order[:i]:
                    continue  # 依赖已满足
                else:
                    errors.append(f"节点 {node_id} 的依赖 {dep} 在其之后执行")
        
        return errors
    
    def create_node_output(self, node_id: str, output_def: Dict[str, Any], actual_output: Any) -> NodeOutput:
        """
        创建节点输出对象
        
        Args:
            node_id: 节点ID
            output_def: 输出定义
            actual_output: 实际输出值
            
        Returns:
            NodeOutput对象
        """
        return NodeOutput(
            node_id=node_id,
            output_type=output_def.get("type", "any"),
            output_key=output_def.get("key", "output"),
            value=actual_output,
            description=output_def.get("description", "")
        )

# 使用示例
def demo_placeholder_resolution():
    """演示占位符解析功能"""
    resolver = PlaceholderResolver()
    
    # 模拟节点输出
    node_outputs = {
        "rotate_node": NodeOutput(
            node_id="rotate_node",
            output_type="image_path",
            output_key="rotated_image",
            value="/path/to/rotated.jpg",
            description="旋转后的图片路径"
        ),
        "scale_node": NodeOutput(
            node_id="scale_node",
            output_type="image_path",
            output_key="scaled_image",
            value="/path/to/scaled.jpg",
            description="缩放后的图片路径"
        ),
        "process_node": NodeOutput(
            node_id="process_node",
            output_type="json",
            output_key="result",
            value={"status": "success", "file_path": "/path/to/processed.jpg"},
            description="处理结果"
        )
    }
    
    # 测试参数解析
    test_params = {
        "image_path": "$rotate_node.output",
        "scale_factor": 2.0,
        "output_path": "$scale_node.output",
        "config": {
            "input_file": "$process_node.output.file_path",
            "status": "$process_node.output.status"
        }
    }
    
    resolved_params = resolver.resolve_placeholders(test_params, node_outputs)
    
    print("原始参数:", test_params)
    print("解析后参数:", resolved_params)
    
    # 测试pipeline验证
    test_components = [
        {
            "id": "rotate_node",
            "tool_type": "image_rotator",
            "params": {"image_path": "input.jpg"},
            "output": {"type": "image_path", "key": "rotated_image"}
        },
        {
            "id": "scale_node",
            "tool_type": "image_scaler",
            "params": {"image_path": "$rotate_node.output"},
            "output": {"type": "image_path", "key": "scaled_image"}
        },
        {
            "id": "upload_node",
            "tool_type": "file_uploader",
            "params": {"file_path": "$scale_node.output"},
            "output": {"type": "json", "key": "upload_result"}
        }
    ]
    
    errors = resolver.validate_pipeline_dependencies(test_components)
    if errors:
        print("Pipeline验证错误:", errors)
    else:
        print("Pipeline验证通过")
        
    execution_order = resolver.build_execution_order(test_components)
    print("执行顺序:", execution_order)

if __name__ == "__main__":
    demo_placeholder_resolution() 