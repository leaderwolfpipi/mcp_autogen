#!/usr/bin/env python3
"""
工具适配器 - 实现智能的工具自适应和动态扩展
解决pipeline输出结构与工具输入期望不匹配的问题

设计原则：
1. 通用性：不硬编码特定字段名，支持任意字段映射
2. 可扩展性：支持自定义映射规则和转换函数
3. 智能性：自动学习数据结构和转换模式
4. 容错性：优雅处理转换失败的情况
"""

import logging
import inspect
import asyncio
import time
from typing import Dict, Any, List, Optional, Callable, Union, Tuple, Type
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from abc import ABC, abstractmethod

# 避免循环导入，使用类型注解
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .placeholder_resolver import NodeOutput

class AdapterType(Enum):
    """适配器类型"""
    OUTPUT_MAPPER = "output_mapper"  # 输出映射适配器
    INPUT_TRANSFORMER = "input_transformer"  # 输入转换适配器
    DATA_CONVERTER = "data_converter"  # 数据格式转换器
    AUTO_GENERATED = "auto_generated"  # 自动生成的适配器
    CUSTOM = "custom"  # 自定义适配器

@dataclass
class MappingRule:
    """映射规则定义"""
    source_pattern: str  # 源字段模式（支持通配符）
    target_pattern: str  # 目标字段模式
    transformation: Optional[str] = None  # 转换函数名
    condition: Optional[str] = None  # 应用条件
    priority: int = 1  # 优先级（数字越小优先级越高）

@dataclass
class AdapterDefinition:
    """适配器定义"""
    name: str
    adapter_type: AdapterType
    source_tool: str
    target_tool: str
    mapping_rules: List[MappingRule] = field(default_factory=list)
    code: str = ""
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

class DataStructureAnalyzer:
    """数据结构分析器"""
    
    @staticmethod
    def analyze_structure(data: Any, max_depth: int = 3) -> Dict[str, Any]:
        """
        分析数据结构
        
        Args:
            data: 要分析的数据
            max_depth: 最大分析深度
            
        Returns:
            结构分析结果
        """
        return DataStructureAnalyzer._analyze_recursive(data, max_depth, 0)
    
    @staticmethod
    def _analyze_recursive(data: Any, max_depth: int, current_depth: int) -> Dict[str, Any]:
        """递归分析数据结构"""
        if current_depth >= max_depth:
            return {"type": "max_depth_reached", "value": str(data)[:100]}
        
        if data is None:
            return {"type": "null"}
        
        if isinstance(data, (str, int, float, bool)):
            return {
                "type": type(data).__name__,
                "value": data,
                "length": len(str(data)) if isinstance(data, str) else None
            }
        
        if isinstance(data, list):
            if not data:
                return {"type": "list", "empty": True}
            
            # 分析列表元素
            element_analysis = DataStructureAnalyzer._analyze_recursive(
                data[0], max_depth, current_depth + 1
            )
            
            return {
                "type": "list",
                "length": len(data),
                "element_type": element_analysis["type"],
                "element_analysis": element_analysis,
                "uniform": all(
                    DataStructureAnalyzer._analyze_recursive(item, max_depth, current_depth + 1)["type"] 
                    == element_analysis["type"] 
                    for item in data[:5]  # 只检查前5个元素
                )
            }
        
        if isinstance(data, dict):
            structure = {
                "type": "dict",
                "keys": list(data.keys()),
                "key_count": len(data),
                "fields": {}
            }
            
            for key, value in data.items():
                structure["fields"][key] = DataStructureAnalyzer._analyze_recursive(
                    value, max_depth, current_depth + 1
                )
            
            return structure
        
        # 处理其他类型（如PIL Image等）
        result = {
            "type": type(data).__name__,
            "attributes": [attr for attr in dir(data) if not attr.startswith('_')][:10],
            "has_size": hasattr(data, 'size'),
            "has_shape": hasattr(data, 'shape'),
            "string_repr": str(data)[:100]
        }
        
        # 特殊处理PIL Image
        if hasattr(data, 'save') and hasattr(data, 'size'):
            result["type"] = "PIL_Image"
            result["image_info"] = {
                "size": data.size,
                "mode": getattr(data, 'mode', 'unknown'),
                "format": getattr(data, 'format', 'unknown')
            }
        
        return result

class MappingRuleEngine:
    """映射规则引擎"""
    
    def __init__(self):
        self.rules: List[MappingRule] = []
        self._load_default_rules()
    
    def _load_default_rules(self):
        """加载默认映射规则"""
        # 通用类型转换规则
        self.rules.extend([
            MappingRule(
                source_pattern="*",
                target_pattern="*",
                transformation="identity",
                priority=100
            ),
            MappingRule(
                source_pattern="*.list",
                target_pattern="*.array",
                transformation="list_to_array",
                priority=10
            ),
            MappingRule(
                source_pattern="*.string",
                target_pattern="*.number",
                transformation="string_to_number",
                priority=10
            ),
            MappingRule(
                source_pattern="*.number",
                target_pattern="*.string",
                transformation="number_to_string",
                priority=10
            )
        ])
    
    def add_rule(self, rule: MappingRule):
        """添加映射规则"""
        self.rules.append(rule)
        # 按优先级排序
        self.rules.sort(key=lambda r: r.priority)
    
    def find_matching_rules(self, source_structure: Dict[str, Any], 
                          target_structure: Dict[str, Any]) -> List[MappingRule]:
        """查找匹配的映射规则"""
        matching_rules = []
        
        for rule in self.rules:
            if self._rule_matches(rule, source_structure, target_structure):
                matching_rules.append(rule)
        
        return matching_rules
    
    def _rule_matches(self, rule: MappingRule, source_structure: Dict[str, Any], 
                     target_structure: Dict[str, Any]) -> bool:
        """检查规则是否匹配"""
        # 简化的模式匹配实现
        # 这里可以实现更复杂的模式匹配逻辑
        return True  # 暂时返回True，后续可以扩展

class TransformationEngine:
    """转换引擎"""
    
    def __init__(self):
        self.transformers: Dict[str, Callable] = {}
        self._load_default_transformers()
    
    def _load_default_transformers(self):
        """加载默认转换器"""
        self.transformers.update({
            "identity": lambda x: x,
            "list_to_array": lambda x: x if isinstance(x, list) else [x],
            "array_to_list": lambda x: list(x) if hasattr(x, '__iter__') else [x],
            "string_to_number": lambda x: float(x) if isinstance(x, str) and x.replace('.', '').replace('-', '').isdigit() else x,
            "number_to_string": lambda x: str(x) if isinstance(x, (int, float)) else x,
            "dict_to_list": lambda x: list(x.values()) if isinstance(x, dict) else x,
            "list_to_dict": lambda x: {f"item_{i}": item for i, item in enumerate(x)} if isinstance(x, list) else x,
            "flatten_list": lambda x: [item for sublist in x for item in (sublist if isinstance(sublist, list) else [sublist])] if isinstance(x, list) else x,
            "wrap_single": lambda x: [x] if not isinstance(x, list) else x,
            "unwrap_single": lambda x: x[0] if isinstance(x, list) and len(x) == 1 else x
        })
    
    def register_transformer(self, name: str, transformer: Callable):
        """注册转换器"""
        self.transformers[name] = transformer
    
    def apply_transformation(self, data: Any, transformation: str) -> Any:
        """应用转换"""
        if transformation not in self.transformers:
            logging.warning(f"未知的转换器: {transformation}")
            return data
        
        try:
            return self.transformers[transformation](data)
        except Exception as e:
            logging.error(f"应用转换器 {transformation} 失败: {e}")
            return data

class AdapterStatistics:
    """适配器统计信息"""
    
    def __init__(self):
        self.total_adaptations = 0
        self.successful_adaptations = 0
        self.failed_adaptations = 0
        self.adaptation_times = []
        self.adapter_usage = {}
        self.error_counts = {}
    
    def record_adaptation(self, adapter_name: str, success: bool, duration: float):
        """记录适配操作"""
        self.total_adaptations += 1
        if success:
            self.successful_adaptations += 1
        else:
            self.failed_adaptations += 1
        
        self.adaptation_times.append(duration)
        
        if adapter_name not in self.adapter_usage:
            self.adapter_usage[adapter_name] = {"success": 0, "failed": 0, "total_time": 0}
        
        self.adapter_usage[adapter_name]["success" if success else "failed"] += 1
        self.adapter_usage[adapter_name]["total_time"] += duration
    
    def record_error(self, error_type: str):
        """记录错误"""
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_time = sum(self.adaptation_times) / len(self.adaptation_times) if self.adaptation_times else 0
        
        return {
            "total_adaptations": self.total_adaptations,
            "successful_adaptations": self.successful_adaptations,
            "failed_adaptations": self.failed_adaptations,
            "success_rate": self.successful_adaptations / self.total_adaptations if self.total_adaptations > 0 else 0,
            "average_time": avg_time,
            "min_time": min(self.adaptation_times) if self.adaptation_times else 0,
            "max_time": max(self.adaptation_times) if self.adaptation_times else 0,
            "adapter_usage": self.adapter_usage,
            "error_counts": self.error_counts
        }

class AdapterConfiguration:
    """适配器配置管理"""
    
    def __init__(self):
        self.config = {
            "max_analysis_depth": 3,
            "similarity_threshold": 0.3,
            "enable_caching": True,
            "cache_size": 1000,
            "enable_parallel": False,
            "max_workers": 4,
            "timeout": 30.0,
            "retry_count": 3,
            "log_level": "INFO"
        }
    
    def update_config(self, **kwargs):
        """更新配置"""
        self.config.update(kwargs)
    
    def get_config(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def load_from_file(self, file_path: str):
        """从文件加载配置"""
        try:
            import yaml
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                self.config.update(config_data)
        except Exception as e:
            logging.warning(f"加载配置文件失败: {e}")
    
    def save_to_file(self, file_path: str):
        """保存配置到文件"""
        try:
            import yaml
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")

# 扩展ToolAdapter类
class ToolAdapter:
    """工具适配器 - 智能适配工具间的数据格式不匹配"""
    
    def __init__(self):
        self.logger = logging.getLogger("ToolAdapter")
        self.adapters: Dict[str, AdapterDefinition] = {}
        self.adapter_cache: Dict[str, Callable] = {}
        
        # 初始化组件
        self.structure_analyzer = DataStructureAnalyzer()
        self.rule_engine = MappingRuleEngine()
        self.transformation_engine = TransformationEngine()
        
        # 新增组件
        self.statistics = AdapterStatistics()
        self.config = AdapterConfiguration()
        
        # 缓存管理
        self._cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
    def analyze_compatibility(self, source_output: 'NodeOutput', target_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析源工具输出与目标工具输入的兼容性
        
        Args:
            source_output: 源工具的输出
            target_params: 目标工具的参数定义
            
        Returns:
            兼容性分析结果
        """
        analysis = {
            "is_compatible": True,
            "missing_keys": [],
            "type_mismatches": [],
            "suggested_mappings": [],
            "confidence": 1.0,
            "source_structure": None,
            "target_structure": None
        }
        
        try:
            # 分析源输出结构
            source_structure = self.structure_analyzer.analyze_structure(source_output.value)
            analysis["source_structure"] = source_structure
            
            # 分析目标参数结构
            target_structure = self._analyze_target_structure(target_params)
            analysis["target_structure"] = target_structure
            
            # 查找匹配的映射规则
            matching_rules = self.rule_engine.find_matching_rules(source_structure, target_structure)
            
            # 生成映射建议
            analysis["suggested_mappings"] = self._generate_mapping_suggestions(
                source_structure, target_structure, matching_rules
            )
            
            # 检查兼容性问题
            compatibility_issues = self._check_compatibility_issues(
                source_structure, target_structure, analysis["suggested_mappings"]
            )
            
            analysis["missing_keys"] = compatibility_issues["missing_keys"]
            analysis["type_mismatches"] = compatibility_issues["type_mismatches"]
            analysis["is_compatible"] = len(compatibility_issues["missing_keys"]) == 0 and len(compatibility_issues["type_mismatches"]) == 0
            
            # 计算置信度
            analysis["confidence"] = self._calculate_compatibility_confidence(analysis)
            
        except Exception as e:
            self.logger.error(f"兼容性分析失败: {e}")
            analysis["is_compatible"] = False
            analysis["confidence"] = 0.0
        
        return analysis
    
    def create_adapter(self, source_tool: str, target_tool: str, 
                      source_output: 'NodeOutput', target_params: Dict[str, Any]) -> Optional[AdapterDefinition]:
        """
        创建适配器来解决兼容性问题
        
        Args:
            source_tool: 源工具名称
            target_tool: 目标工具名称
            source_output: 源工具输出
            target_params: 目标工具参数
            
        Returns:
            创建的适配器定义
        """
        try:
            # 分析兼容性
            analysis = self.analyze_compatibility(source_output, target_params)
            
            if analysis["is_compatible"]:
                self.logger.info(f"工具 {source_tool} 和 {target_tool} 兼容，无需适配器")
                return None
            
            # 生成适配器代码
            adapter_code = self._generate_adaptive_adapter_code(
                source_tool, target_tool, source_output, target_params, analysis
            )
            
            # 创建适配器定义
            adapter_name = f"{source_tool}_to_{target_tool}_adapter"
            adapter_def = AdapterDefinition(
                name=adapter_name,
                adapter_type=AdapterType.AUTO_GENERATED,
                source_tool=source_tool,
                target_tool=target_tool,
                mapping_rules=[MappingRule(
                    source_pattern="*",
                    target_pattern="*",
                    transformation="adaptive"
                )],
                code=adapter_code,
                metadata={"analysis": analysis}
            )
            
            # 注册适配器
            self.adapters[adapter_name] = adapter_def
            
            # 编译并缓存适配器
            adapter_func = self._compile_adapter(adapter_name, adapter_code)
            if adapter_func:
                self.adapter_cache[adapter_name] = adapter_func
                self.logger.info(f"成功创建适配器: {adapter_name}")
                return adapter_def
            
        except Exception as e:
            self.logger.error(f"创建适配器失败: {e}")
        
        return None
    
    def apply_adapter(self, adapter_name: str, source_data: Any) -> Any:
        """
        应用适配器转换数据（增强版）
        
        Args:
            adapter_name: 适配器名称
            source_data: 源数据
            
        Returns:
            转换后的数据
        """
        if adapter_name not in self.adapter_cache:
            self.logger.error(f"适配器 {adapter_name} 未找到")
            self.statistics.record_error("adapter_not_found")
            return source_data
        
        # 检查缓存
        cache_key = f"{adapter_name}:{hash(str(source_data))}"
        if self.config.get_config("enable_caching") and cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]
        
        self._cache_misses += 1
        start_time = time.time()
        
        try:
            adapter_func = self.adapter_cache[adapter_name]
            result = adapter_func(source_data)
            
            # 记录成功
            duration = time.time() - start_time
            self.statistics.record_adaptation(adapter_name, True, duration)
            
            # 缓存结果
            if self.config.get_config("enable_caching"):
                if len(self._cache) >= self.config.get_config("cache_size"):
                    # 简单的LRU缓存：删除最旧的条目
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                self._cache[cache_key] = result
            
            self.logger.info(f"适配器 {adapter_name} 应用成功，耗时: {duration:.4f}秒")
            return result
            
        except Exception as e:
            # 记录失败
            duration = time.time() - start_time
            self.statistics.record_adaptation(adapter_name, False, duration)
            self.statistics.record_error("adapter_execution_failed")
            
            self.logger.error(f"应用适配器 {adapter_name} 失败: {e}")
            return source_data
    
    def auto_adapt_output(self, source_output: 'NodeOutput', target_expectation: Dict[str, Any]) -> Any:
        """
        自动适配输出以匹配目标期望
        
        Args:
            source_output: 源工具输出
            target_expectation: 目标期望的结构
            
        Returns:
            适配后的输出
        """
        try:
            self.logger.info(f"🔄 自动适配输出开始:")
            self.logger.info(f"   源节点: {source_output.node_id}")
            self.logger.info(f"   源输出键: {source_output.output_key}")
            self.logger.info(f"   源输出值类型: {type(source_output.value)}")
            self.logger.info(f"   源输出值: {source_output.value}")
            self.logger.info(f"   目标期望: {target_expectation}")
            
            # 分析源数据结构
            source_structure = self.structure_analyzer.analyze_structure(source_output.value)
            self.logger.info(f"   分析得到的源结构: {source_structure}")
            
            # 尝试智能映射
            self.logger.info("   尝试智能映射...")
            adapted_output = self._intelligent_mapping(source_output.value, source_structure, target_expectation)
            
            if adapted_output is not None:
                self.logger.info(f"✅ 智能映射成功，返回: {adapted_output}")
                return adapted_output
            
            self.logger.warning("❌ 智能映射失败，尝试创建适配器...")
            
            # 如果智能映射失败，尝试创建适配器
            adapter_def = self.create_adapter(
                source_output.node_id, 
                "target_tool",  # 这里需要从上下文获取
                source_output, 
                target_expectation
            )
            
            if adapter_def:
                self.logger.info(f"   创建适配器成功: {adapter_def.name}")
                return self.apply_adapter(adapter_def.name, source_output.value)
            
            # 最后的fallback：返回原始数据
            self.logger.warning("⚠️  无法适配输出，返回原始数据")
            return source_output.value
            
        except Exception as e:
            self.logger.error(f"❌ 自动适配输出失败: {e}")
            return source_output.value
    
    def _analyze_target_structure(self, target_params: Dict[str, Any]) -> Dict[str, Any]:
        """分析目标参数结构"""
        structure = {
            "type": "dict",
            "required_keys": [],
            "optional_keys": [],
            "type_requirements": {},
            "patterns": {}
        }
        
        for key, value in target_params.items():
            if isinstance(value, str) and value.startswith('$'):
                # 这是一个占位符引用
                structure["required_keys"].append(key)
                # 尝试推断类型
                if "image" in key.lower() or "path" in key.lower():
                    structure["type_requirements"][key] = "string"
                elif "angle" in key.lower() or "size" in key.lower():
                    structure["type_requirements"][key] = "number"
                elif "list" in key.lower() or "array" in key.lower():
                    structure["type_requirements"][key] = "list"
            else:
                structure["optional_keys"].append(key)
                structure["type_requirements"][key] = type(value).__name__
        
        return structure
    
    def _generate_mapping_suggestions(self, source_structure: Dict[str, Any], 
                                    target_structure: Dict[str, Any],
                                    matching_rules: List[MappingRule]) -> List[Dict[str, Any]]:
        """生成映射建议"""
        suggestions = []
        
        # 基于结构相似性生成建议
        if source_structure["type"] == "dict" and target_structure["type"] == "dict":
            source_keys = source_structure.get("keys", [])
            target_keys = target_structure.get("required_keys", [])
            
            for target_key in target_keys:
                # 寻找最佳匹配的源键
                best_match = self._find_best_key_match(target_key, source_keys)
                if best_match:
                    suggestions.append({
                        "type": "key_mapping",
                        "source_key": best_match,
                        "target_key": target_key,
                        "confidence": self._calculate_key_similarity(target_key, best_match)
                    })
        
        # 基于类型转换生成建议
        for rule in matching_rules:
            if rule.transformation:
                suggestions.append({
                    "type": "type_conversion",
                    "transformation": rule.transformation,
                    "priority": rule.priority
                })
        
        return suggestions
    
    def _find_best_key_match(self, target_key: str, source_keys: List[str]) -> Optional[str]:
        """找到最佳匹配的源键"""
        if not source_keys:
            return None
        
        # 精确匹配
        if target_key in source_keys:
            return target_key
        
        # 模糊匹配
        best_match = None
        best_score = 0
        
        for source_key in source_keys:
            score = self._calculate_key_similarity(target_key, source_key)
            if score > best_score and score > 0.3:  # 设置最小相似度阈值
                best_score = score
                best_match = source_key
        
        return best_match
    
    def _calculate_key_similarity(self, key1: str, key2: str) -> float:
        """计算键相似度"""
        if key1 == key2:
            return 1.0
        
        # 转换为小写进行比较
        k1, k2 = key1.lower(), key2.lower()
        
        # 包含关系
        if k1 in k2 or k2 in k1:
            return 0.8
        
        # 公共字符比例
        common_chars = set(k1) & set(k2)
        total_chars = set(k1) | set(k2)
        if total_chars:
            return len(common_chars) / len(total_chars)
        
        return 0.0
    
    def _check_compatibility_issues(self, source_structure: Dict[str, Any], 
                                  target_structure: Dict[str, Any],
                                  suggested_mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检查兼容性问题"""
        issues = {
            "missing_keys": [],
            "type_mismatches": []
        }
        
        if target_structure["type"] == "dict":
            target_keys = target_structure.get("required_keys", [])
            source_keys = source_structure.get("keys", [])
            
            for target_key in target_keys:
                # 检查是否有映射建议
                has_mapping = any(
                    mapping["target_key"] == target_key 
                    for mapping in suggested_mappings 
                    if mapping["type"] == "key_mapping"
                )
                
                if not has_mapping:
                    issues["missing_keys"].append(target_key)
        
        return issues
    
    def _calculate_compatibility_confidence(self, analysis: Dict[str, Any]) -> float:
        """计算兼容性置信度"""
        total_issues = len(analysis["missing_keys"]) + len(analysis["type_mismatches"])
        
        if total_issues == 0:
            return 1.0
        
        # 基于问题数量和类型计算置信度
        confidence = 1.0 - (total_issues * 0.2)
        return max(0.0, confidence)
    
    def _generate_adaptive_adapter_code(self, source_tool: str, target_tool: str, 
                                      source_output: 'NodeOutput', target_params: Dict[str, Any],
                                      analysis: Dict[str, Any]) -> str:
        """生成自适应适配器代码"""
        adapter_name = f"{source_tool}_to_{target_tool}_adapter"
        
        # 分析源数据和目标期望
        source_structure = analysis.get("source_structure", {})
        target_structure = analysis.get("target_structure", {})
        
        # 生成智能适配逻辑
        adaptation_logic = self._generate_adaptation_logic(source_structure, target_structure, target_params)
        
        code = f'''
import json
import logging
import tempfile
import os
from typing import Any, Dict, List

def {adapter_name}(source_data: Any) -> Any:
    """
    自适应适配器：{source_tool} -> {target_tool}
    基于结构分析自动生成
    """
    logger = logging.getLogger("{adapter_name}")
    
    try:
        # 输入验证
        if source_data is None:
            logger.warning("源数据为空")
            return None
        
        # 创建输出副本
        if isinstance(source_data, dict):
            output = source_data.copy()
        else:
            output = {{"data": source_data}}
        
        # 应用映射规则
        mappings = {analysis["suggested_mappings"]}
        
        for mapping in mappings:
            if mapping["type"] == "key_mapping":
                source_key = mapping["source_key"]
                target_key = mapping["target_key"]
                
                if isinstance(output, dict) and source_key in output:
                    if target_key not in output:
                        output[target_key] = output[source_key]
                        logger.info(f"映射键: {{source_key}} -> {{target_key}}")
            
            elif mapping["type"] == "type_conversion":
                transformation = mapping["transformation"]
                logger.info(f"应用类型转换: {{transformation}}")
        
        # 智能结构适配
        {adaptation_logic}
        
        logger.info("自适应适配器转换完成")
        return output
        
    except Exception as e:
        logger.error(f"自适应适配器转换失败: {{e}}")
        return source_data
'''
        
        return code
    
    def _generate_adaptation_logic(self, source_structure: Dict[str, Any], 
                                 target_structure: Dict[str, Any], 
                                 target_params: Dict[str, Any]) -> str:
        """生成智能适配逻辑"""
        logic_parts = []
        
        # 处理PIL Image对象到文件路径的转换
        if source_structure.get("type") == "list" and source_structure.get("element_type") == "PIL_Image":
            logic_parts.append("""
        # 处理PIL Image列表到文件路径的转换
        if isinstance(output, dict):
            for key, value in list(output.items()):
                if isinstance(value, list) and value:
                    # 检查是否为PIL Image列表
                    if hasattr(value[0], 'save'):
                        # 将PIL Image列表转换为临时文件路径列表
                        temp_paths = []
                        for i, img in enumerate(value):
                            if hasattr(img, 'save'):
                                temp_dir = tempfile.mkdtemp()
                                temp_path = os.path.join(temp_dir, f"image_{i}.png")
                                img.save(temp_path)
                                temp_paths.append(temp_path)
                        
                        # 如果只有一个图片，返回单个路径；否则返回路径列表
                        if len(temp_paths) == 1:
                            output[key] = temp_paths[0]
                        else:
                            output[key] = temp_paths
                        
                        logger.info(f"将PIL Image列表转换为文件路径: {{key}}")
""")
        
        # 处理列表到单个值的转换
        logic_parts.append("""
        # 智能列表处理
        if isinstance(output, dict):
            for key, value in list(output.items()):
                if isinstance(value, list):
                    if len(value) == 1:
                        # 单元素列表解包
                        output[key] = value[0]
                        logger.info(f"解包单元素列表: {{key}}")
                    elif len(value) > 1:
                        # 多元素列表保持原样
                        pass
                elif not isinstance(value, list) and key.endswith("s"):
                    # 单值包装为列表
                    output[key] = [value]
                    logger.info(f"包装单值为列表: {{key}}")
""")
        
        # 处理特定字段的智能映射
        if "image_path" in target_params or "images" in target_params:
            logic_parts.append("""
        # 智能图像路径映射
        if isinstance(output, dict):
            # 寻找图像相关的数据
            image_data = None
            for key, value in output.items():
                if isinstance(value, list) and value:
                    if hasattr(value[0], 'save'):  # PIL Image
                        image_data = value
                        break
                    elif isinstance(value[0], str) and value[0].lower().endswith(('.png', '.jpg', '.jpeg')):
                        image_data = value
                        break
            
            # 映射到期望的字段
            if image_data is not None:
                if "image_path" in output and not output["image_path"]:
                    output["image_path"] = image_data[0] if len(image_data) == 1 else image_data
                if "images" in output and not output["images"]:
                    output["images"] = image_data
                logger.info("智能映射图像数据")
""")
        
        return "\n".join(logic_parts)
    
    def _compile_adapter(self, adapter_name: str, code: str) -> Optional[Callable]:
        """编译适配器代码"""
        try:
            # 创建本地命名空间
            local_namespace = {}
            
            # 执行代码
            exec(code, globals(), local_namespace)
            
            # 获取函数
            adapter_func = local_namespace.get(adapter_name)
            
            if adapter_func and callable(adapter_func):
                return adapter_func
            
        except Exception as e:
            self.logger.error(f"编译适配器 {adapter_name} 失败: {e}")
        
        return None
    
    def _intelligent_mapping(self, source_data: Any, source_structure: Dict[str, Any], 
                           target_expectation: Dict[str, Any]) -> Optional[Any]:
        """智能映射数据"""
        try:
            self.logger.info(f"🔍 智能映射开始:")
            self.logger.info(f"   源数据类型: {type(source_data)}")
            self.logger.info(f"   源数据结构: {source_structure}")
            self.logger.info(f"   目标期望: {target_expectation}")
            
            # 处理PIL Image列表的特殊情况
            if isinstance(source_data, list) and source_data:
                if hasattr(source_data[0], 'save'):  # PIL Image列表
                    self.logger.info("   检测到PIL Image列表，转换为临时文件路径")
                    # 将PIL Image列表转换为临时文件路径
                    import tempfile
                    import os
                    
                    temp_paths = []
                    for i, img in enumerate(source_data):
                        if hasattr(img, 'save'):
                            temp_dir = tempfile.mkdtemp()
                            temp_path = os.path.join(temp_dir, f"image_{i}.png")
                            img.save(temp_path)
                            temp_paths.append(temp_path)
                    
                    # 根据目标期望返回合适的格式
                    if "image_path" in target_expectation:
                        result = {"image_path": temp_paths[0] if len(temp_paths) == 1 else temp_paths}
                        self.logger.info(f"   返回image_path格式: {result}")
                        return result
                    elif "images" in target_expectation:
                        result = {"images": temp_paths}
                        self.logger.info(f"   返回images格式: {result}")
                        return result
                    else:
                        result = {"data": temp_paths}
                        self.logger.info(f"   返回data格式: {result}")
                        return result
            
            # 处理字典数据
            if isinstance(source_data, dict):
                self.logger.info("   检测到字典数据，进行智能映射")
                mapped_data = source_data.copy()
                
                # 基于结构分析进行智能映射
                if source_structure["type"] == "dict":
                    source_keys = source_structure.get("keys", [])
                    self.logger.info(f"   源字典键: {source_keys}")
                    
                    for target_key in target_expectation:
                        self.logger.info(f"   处理目标键: {target_key}")
                        if target_key not in mapped_data:
                            # 寻找最佳匹配
                            best_match = self._find_best_key_match(target_key, source_keys)
                            self.logger.info(f"   最佳匹配键: {best_match}")
                            
                            # 智能选择最佳匹配
                            if best_match and best_match in mapped_data:
                                mapped_data[target_key] = mapped_data[best_match]
                                self.logger.info(f"   映射 {best_match} -> {target_key}: {mapped_data[target_key]}")
                            else:
                                self.logger.warning(f"   未找到键 {target_key} 的匹配")
                        else:
                            self.logger.info(f"   键 {target_key} 已存在: {mapped_data[target_key]}")
                
                self.logger.info(f"   最终映射结果: {mapped_data}")
                return mapped_data
            
            self.logger.warning(f"   不支持的数据类型: {type(source_data)}")
            return None
            
        except Exception as e:
            self.logger.error(f"智能映射失败: {e}")
            return None

    def get_adapter_statistics(self) -> Dict[str, Any]:
        """获取适配器统计信息"""
        stats = self.statistics.get_statistics()
        stats.update({
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": self._cache_hits / (self._cache_hits + self._cache_misses) if (self._cache_hits + self._cache_misses) > 0 else 0,
            "total_adapters": len(self.adapters),
            "cached_adapters": len(self.adapter_cache)
        })
        return stats
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        self.adapter_cache.clear()
        self.logger.info("缓存已清空")
    
    def export_adapters(self, file_path: str):
        """导出适配器定义"""
        try:
            export_data = {
                "adapters": {},
                "statistics": self.get_adapter_statistics(),
                "config": self.config.config
            }
            
            for name, adapter in self.adapters.items():
                export_data["adapters"][name] = {
                    "name": adapter.name,
                    "adapter_type": adapter.adapter_type.value,
                    "source_tool": adapter.source_tool,
                    "target_tool": adapter.target_tool,
                    "mapping_rules": [
                        {
                            "source_pattern": rule.source_pattern,
                            "target_pattern": rule.target_pattern,
                            "transformation": rule.transformation,
                            "priority": rule.priority
                        }
                        for rule in adapter.mapping_rules
                    ],
                    "code": adapter.code,
                    "is_active": adapter.is_active,
                    "created_at": adapter.created_at,
                    "metadata": adapter.metadata
                }
            
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"适配器定义已导出到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"导出适配器失败: {e}")
    
    def import_adapters(self, file_path: str):
        """导入适配器定义"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 导入配置
            if "config" in import_data:
                self.config.update_config(**import_data["config"])
            
            # 导入适配器
            for name, adapter_data in import_data.get("adapters", {}).items():
                adapter_def = AdapterDefinition(
                    name=adapter_data["name"],
                    adapter_type=AdapterType(adapter_data["adapter_type"]),
                    source_tool=adapter_data["source_tool"],
                    target_tool=adapter_data["target_tool"],
                    mapping_rules=[
                        MappingRule(
                            source_pattern=rule["source_pattern"],
                            target_pattern=rule["target_pattern"],
                            transformation=rule["transformation"],
                            priority=rule["priority"]
                        )
                        for rule in adapter_data["mapping_rules"]
                    ],
                    code=adapter_data["code"],
                    is_active=adapter_data["is_active"],
                    created_at=adapter_data["created_at"],
                    metadata=adapter_data.get("metadata", {})
                )
                
                self.adapters[name] = adapter_def
                
                # 编译适配器
                if adapter_def.code:
                    adapter_func = self._compile_adapter(name, adapter_def.code)
                    if adapter_func:
                        self.adapter_cache[name] = adapter_func
            
            self.logger.info(f"成功导入 {len(import_data.get('adapters', {}))} 个适配器")
            
        except Exception as e:
            self.logger.error(f"导入适配器失败: {e}")
    
    def get_adapter_info(self, adapter_name: str) -> Optional[Dict[str, Any]]:
        """获取适配器详细信息"""
        if adapter_name not in self.adapters:
            return None
        
        adapter = self.adapters[adapter_name]
        usage_stats = self.statistics.adapter_usage.get(adapter_name, {})
        
        return {
            "name": adapter.name,
            "adapter_type": adapter.adapter_type.value,
            "source_tool": adapter.source_tool,
            "target_tool": adapter.target_tool,
            "is_active": adapter.is_active,
            "created_at": adapter.created_at,
            "usage_count": usage_stats.get("success", 0) + usage_stats.get("failed", 0),
            "success_rate": usage_stats.get("success", 0) / (usage_stats.get("success", 0) + usage_stats.get("failed", 0)) if (usage_stats.get("success", 0) + usage_stats.get("failed", 0)) > 0 else 0,
            "total_time": usage_stats.get("total_time", 0),
            "mapping_rules": [
                {
                    "source_pattern": rule.source_pattern,
                    "target_pattern": rule.target_pattern,
                    "transformation": rule.transformation,
                    "priority": rule.priority
                }
                for rule in adapter.mapping_rules
            ],
            "metadata": adapter.metadata
        }
    
    def list_adapters(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """列出所有适配器"""
        adapters = []
        for name in self.adapters:
            adapter_info = self.get_adapter_info(name)
            if adapter_info and (not active_only or adapter_info["is_active"]):
                adapters.append(adapter_info)
        return adapters
    
    def enable_adapter(self, adapter_name: str):
        """启用适配器"""
        if adapter_name in self.adapters:
            self.adapters[adapter_name].is_active = True
            self.logger.info(f"适配器 {adapter_name} 已启用")
        else:
            self.logger.warning(f"适配器 {adapter_name} 不存在")
    
    def disable_adapter(self, adapter_name: str):
        """禁用适配器"""
        if adapter_name in self.adapters:
            self.adapters[adapter_name].is_active = False
            self.logger.info(f"适配器 {adapter_name} 已禁用")
        else:
            self.logger.warning(f"适配器 {adapter_name} 不存在")
    
    def delete_adapter(self, adapter_name: str):
        """删除适配器"""
        if adapter_name in self.adapters:
            del self.adapters[adapter_name]
            if adapter_name in self.adapter_cache:
                del self.adapter_cache[adapter_name]
            self.logger.info(f"适配器 {adapter_name} 已删除")
        else:
            self.logger.warning(f"适配器 {adapter_name} 不存在")
    
    def validate_adapter(self, adapter_name: str) -> Dict[str, Any]:
        """验证适配器"""
        if adapter_name not in self.adapters:
            return {"valid": False, "error": "适配器不存在"}
        
        adapter = self.adapters[adapter_name]
        validation_result = {"valid": True, "warnings": [], "errors": []}
        
        # 检查代码语法
        try:
            compile(adapter.code, '<string>', 'exec')
        except SyntaxError as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"语法错误: {e}")
        
        # 检查映射规则
        for rule in adapter.mapping_rules:
            if not rule.source_pattern or not rule.target_pattern:
                validation_result["warnings"].append("映射规则模式为空")
        
        # 检查转换器
        for rule in adapter.mapping_rules:
            if rule.transformation and rule.transformation not in self.transformation_engine.transformers:
                validation_result["warnings"].append(f"未知的转换器: {rule.transformation}")
        
        return validation_result
    
    def benchmark_adapter(self, adapter_name: str, test_data: Any, iterations: int = 100) -> Dict[str, Any]:
        """性能基准测试"""
        if adapter_name not in self.adapter_cache:
            return {"error": "适配器不存在或未编译"}
        
        adapter_func = self.adapter_cache[adapter_name]
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            try:
                result = adapter_func(test_data)
                end_time = time.time()
                times.append(end_time - start_time)
            except Exception as e:
                return {"error": f"执行失败: {e}"}
        
        return {
            "iterations": iterations,
            "total_time": sum(times),
            "average_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "std_deviation": (sum((t - sum(times)/len(times))**2 for t in times) / len(times))**0.5
        }

# 全局适配器实例
_global_adapter = None

def get_tool_adapter() -> ToolAdapter:
    """获取全局工具适配器实例"""
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = ToolAdapter()
    return _global_adapter