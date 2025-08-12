#!/usr/bin/env python3
"""
语义依赖分析器 - 通用性设计
"""

import re
import logging
from typing import Dict, Any, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class SemanticDependency:
    """语义依赖关系"""
    source_node_id: str
    target_node_id: str
    confidence: float
    dependency_type: str
    evidence: str

class SemanticDependencyAnalyzer:
    """语义依赖分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger("SemanticDependencyAnalyzer")
        
        # 工具类型分类
        self.tool_categories = {
            "data_source": {"search_tool", "smart_search", "web_searcher"},
            "data_processor": {"enhanced_report_generator", "report_generator", "text_processor"},
            "file_operator": {"file_writer", "file_uploader", "minio_uploader"},
            "storage": {"minio_uploader", "file_uploader"}
        }
        
        # 数据流语义映射
        self.tool_semantic_mapping = {
            "file_writer": {
                "input": ["file_content", "file_path"],
                "output": ["file_path", "status"]
            },
            "minio_uploader": {
                "input": ["file_path"],
                "output": ["url", "status"]
            },
            "enhanced_report_generator": {
                "input": ["file_content", "metadata"],
                "output": ["file_content", "metadata"]
            },
            "smart_search": {
                "input": ["metadata"],
                "output": ["file_content", "metadata"]
            }
        }
    
    def analyze_dependencies(self, components: List[Dict[str, Any]]) -> List[SemanticDependency]:
        """分析组件间的语义依赖关系"""
        dependencies = []
        
        # 基于占位符引用的依赖分析
        placeholder_deps = self._analyze_placeholder_dependencies(components)
        dependencies.extend(placeholder_deps)
        
        # 基于数据流语义的依赖分析
        data_flow_deps = self._analyze_data_flow_dependencies(components)
        dependencies.extend(data_flow_deps)
        
        # 去重和合并
        merged_deps = self._merge_dependencies(dependencies)
        
        return merged_deps
    
    def _analyze_data_flow_dependencies(self, components: List[Dict[str, Any]]) -> List[SemanticDependency]:
        """基于数据流语义的依赖分析"""
        dependencies = []
        
        for target_comp in components:
            target_id = target_comp["id"]
            target_tool_type = target_comp.get("tool_type", "")
            
            # 获取目标组件的输入语义需求
            target_input_semantics = self._get_tool_input_semantics(target_tool_type)
            
            # 查找能够提供所需输入的源组件
            for source_comp in components:
                if source_comp["id"] == target_id:
                    continue
                    
                source_id = source_comp["id"]
                source_tool_type = source_comp.get("tool_type", "")
                source_output_semantics = self._get_tool_output_semantics(source_tool_type)
                
                # 检查语义匹配度
                match_score = self._calculate_semantic_match_score(
                    source_output_semantics, target_input_semantics, target_tool_type
                )
                
                if match_score > 0.6:  # 语义匹配阈值
                    dependencies.append(SemanticDependency(
                        source_node_id=source_id,
                        target_node_id=target_id,
                        confidence=match_score,
                        dependency_type="data_flow_semantic",
                        evidence=f"数据流语义匹配: {source_output_semantics} -> {target_input_semantics}"
                    ))
        
        return dependencies
    
    def _get_tool_input_semantics(self, tool_type: str) -> List[str]:
        """获取工具的输入语义"""
        return self.tool_semantic_mapping.get(tool_type, {}).get("input", [])
    
    def _get_tool_output_semantics(self, tool_type: str) -> List[str]:
        """获取工具的输出语义"""
        return self.tool_semantic_mapping.get(tool_type, {}).get("output", [])
    
    def _calculate_semantic_match_score(self, source_outputs: List[str], 
                                      target_inputs: List[str], 
                                      target_tool_type: str) -> float:
        """计算语义匹配分数"""
        if not source_outputs or not target_inputs:
            return 0.0
        
        # 直接匹配
        for source_output in source_outputs:
            for target_input in target_inputs:
                if source_output == target_input:
                    return 0.9
        
        # 语义兼容性检查
        for source_output in source_outputs:
            for target_input in target_inputs:
                compatibility_score = self._check_semantic_compatibility(
                    source_output, target_input, target_tool_type
                )
                if compatibility_score > 0.5:
                    return compatibility_score
        
        return 0.0
    
    def _check_semantic_compatibility(self, source_output: str, target_input: str, target_tool_type: str) -> float:
        """检查语义兼容性"""
        # 文件内容 -> 文件路径的转换
        if source_output == "file_content" and target_input == "file_path":
            if target_tool_type in ["file_writer", "minio_uploader"]:
                return 0.8  # 高兼容性：内容可以写入文件生成路径
        
        # 文件路径 -> 文件内容的转换
        if source_output == "file_path" and target_input == "file_content":
            return 0.7  # 中等兼容性：路径可以读取内容
        
        # 相同语义类型
        if source_output == target_input:
            return 0.9
        
        # 默认低兼容性
        return 0.3
    
    def _analyze_placeholder_dependencies(self, components: List[Dict[str, Any]]) -> List[SemanticDependency]:
        """基于占位符引用的依赖分析"""
        dependencies = []
        placeholder_pattern = r'\$([^.]+)\.output(?:\.([^.]+))?'
        
        for target_comp in components:
            params = target_comp.get("params", {})
            placeholder_refs = self._extract_placeholder_references(params, placeholder_pattern)
            
            for ref in placeholder_refs:
                referenced_node_id = ref["node_id"]
                source_node_id = self._find_matching_source_node(referenced_node_id, components)
                
                if source_node_id:
                    dependencies.append(SemanticDependency(
                        source_node_id=source_node_id,
                        target_node_id=target_comp["id"],
                        confidence=0.9,
                        dependency_type="placeholder_reference",
                        evidence=f"占位符引用: ${referenced_node_id}.output"
                    ))
        
        return dependencies
    
    def _find_matching_source_node(self, referenced_id: str, components: List[Dict[str, Any]]) -> Optional[str]:
        """查找匹配的源节点"""
        # 策略1: 精确匹配
        for comp in components:
            if comp["id"] == referenced_id:
                return comp["id"]
        
        # 策略2: 模糊匹配
        for comp in components:
            if self._is_similar_node_id(referenced_id, comp["id"]):
                return comp["id"]
        
        # 策略3: 基于工具类型的语义匹配
        for comp in components:
            if self._is_semantically_related(referenced_id, comp):
                return comp["id"]
        
        return None
    
    def _is_similar_node_id(self, id1: str, id2: str) -> bool:
        """判断两个节点ID是否相似"""
        suffixes = ['_node', '_tool', '_processor', '_handler', '_generator']
        
        base1 = id1
        base2 = id2
        
        for suffix in suffixes:
            if base1.endswith(suffix):
                base1 = base1[:-len(suffix)]
            if base2.endswith(suffix):
                base2 = base2[:-len(suffix)]
        
        if base1 == base2:
            return True
        
        if base1 in base2 or base2 in base1:
            return True
        
        similarity = self._calculate_string_similarity(base1, base2)
        return similarity > 0.7
    
    def _is_semantically_related(self, referenced_id: str, component: Dict[str, Any]) -> bool:
        """判断节点ID与组件是否语义相关"""
        tool_type = component.get("tool_type", "")
        keywords = self._extract_keywords(referenced_id)
        tool_keywords = self._extract_keywords(tool_type)
        match_score = self._calculate_keyword_match(keywords, tool_keywords)
        return match_score > 0.5
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """提取关键词"""
        words = re.split(r'[_\-\s]+', text.lower())
        stop_words = {'node', 'tool', 'processor', 'handler', 'generator', 'writer', 'uploader'}
        return {word for word in words if word and word not in stop_words}
    
    def _calculate_keyword_match(self, keywords1: Set[str], keywords2: Set[str]) -> float:
        """计算关键词匹配度"""
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        return intersection / union if union > 0 else 0.0
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """计算字符串相似度"""
        if not str1 or not str2:
            return 0.0
        
        common_chars = sum(1 for c in str1 if c in str2)
        total_chars = len(str1) + len(str2)
        return (2 * common_chars) / total_chars if total_chars > 0 else 0.0
    
    def _extract_placeholder_references(self, params: Dict[str, Any], pattern: str) -> List[Dict[str, str]]:
        """提取占位符引用"""
        references = []
        
        def extract_from_value(value):
            if isinstance(value, str):
                matches = re.finditer(pattern, value)
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
    
    def _merge_dependencies(self, dependencies: List[SemanticDependency]) -> List[SemanticDependency]:
        """合并和去重依赖关系"""
        dep_groups = defaultdict(list)
        
        for dep in dependencies:
            key = (dep.source_node_id, dep.target_node_id)
            dep_groups[key].append(dep)
        
        merged_deps = []
        
        for (source_id, target_id), deps in dep_groups.items():
            if len(deps) == 1:
                merged_deps.append(deps[0])
            else:
                max_confidence = max(dep.confidence for dep in deps)
                combined_evidence = "; ".join(dep.evidence for dep in deps)
                dependency_types = list(set(dep.dependency_type for dep in deps))
                
                merged_deps.append(SemanticDependency(
                    source_node_id=source_id,
                    target_node_id=target_id,
                    confidence=max_confidence,
                    dependency_type="+".join(dependency_types),
                    evidence=combined_evidence
                ))
        
        return merged_deps
    
    def build_execution_order(self, components: List[Dict[str, Any]]) -> List[str]:
        """基于语义依赖分析构建执行顺序"""
        dependencies = self.analyze_dependencies(components)
        
        # 构建依赖图
        dependency_graph = defaultdict(set)
        node_ids = {comp["id"] for comp in components}
        
        for dep in dependencies:
            if dep.confidence > 0.3:
                dependency_graph[dep.target_node_id].add(dep.source_node_id)
        
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
            for dep in dependency_graph.get(node_id, []):
                if dep in node_ids:
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
            execution_order = self._heuristic_execution_order(components, dependency_graph)
        
        return execution_order
    
    def _heuristic_execution_order(self, components: List[Dict[str, Any]], 
                                 dependency_graph: Dict[str, Set[str]]) -> List[str]:
        """启发式执行顺序构建"""
        node_ids = {comp["id"] for comp in components}
        
        # 计算每个节点的入度和出度
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        
        for node_id in node_ids:
            in_degree[node_id] = len(dependency_graph.get(node_id, set()))
            for dep in dependency_graph.get(node_id, set()):
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