#!/usr/bin/env python3
"""
智能参数适配器 - 处理数据流语义不匹配问题
"""

import re
import logging
import os
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ParameterAdaptation:
    """参数适配信息"""
    original_param: str
    adapted_param: str
    adaptation_type: str
    confidence: float
    evidence: str

class SmartParameterAdapter:
    """智能参数适配器"""
    
    def __init__(self):
        self.logger = logging.getLogger("SmartParameterAdapter")
        
        # 工具语义映射
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
        
        # 参数语义模式
        self.param_semantic_patterns = {
            "file_path": [r".*file.*", r".*path.*", r".*filename.*", r".*document.*"],
            "file_content": [r".*content.*", r".*text.*", r".*data.*", r".*result.*"],
            "url": [r".*url.*", r".*link.*", r".*address.*", r".*endpoint.*"],
            "metadata": [r".*metadata.*", r".*info.*", r".*status.*", r".*message.*"]
        }
    
    def adapt_parameters(self, params: Dict[str, Any], tool_type: str, 
                        node_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        智能适配参数，处理数据流语义不匹配
        
        Args:
            params: 原始参数
            tool_type: 工具类型
            node_outputs: 节点输出
            
        Returns:
            适配后的参数
        """
        adapted_params = params.copy()
        
        # 获取工具的输入语义需求
        input_semantics = self.tool_semantic_mapping.get(tool_type, {}).get("input", [])
        
        # 分析每个参数的语义
        for param_name, param_value in params.items():
            param_semantic = self._analyze_param_semantic(param_name, param_value)
            
            # 检查是否需要适配
            if self._needs_adaptation(param_semantic, input_semantics, tool_type):
                adaptation = self._create_adaptation(param_name, param_value, param_semantic, 
                                                   input_semantics, tool_type, node_outputs)
                
                if adaptation:
                    adapted_params[param_name] = adaptation.adapted_param
                    self.logger.info(f"参数适配: {param_name} -> {adaptation.adaptation_type} "
                                   f"(置信度: {adaptation.confidence:.2f})")
        
        return adapted_params
    
    def _analyze_param_semantic(self, param_name: str, param_value: Any) -> str:
        """分析参数的语义类型"""
        # 基于参数名称分析
        for semantic_type, patterns in self.param_semantic_patterns.items():
            for pattern in patterns:
                if re.search(pattern, param_name, re.IGNORECASE):
                    return semantic_type
        
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
    
    def _needs_adaptation(self, param_semantic: str, input_semantics: List[str], tool_type: str) -> bool:
        """检查是否需要适配"""
        # 如果参数语义与工具输入语义匹配，不需要适配
        if param_semantic in input_semantics:
            return False
        
        # 检查是否有兼容的语义类型
        for input_semantic in input_semantics:
            if self._is_semantic_compatible(param_semantic, input_semantic, tool_type):
                return True
        
        return False
    
    def _is_semantic_compatible(self, source_semantic: str, target_semantic: str, tool_type: str) -> bool:
        """检查语义兼容性"""
        # 文件内容 -> 文件路径的转换
        if source_semantic == "file_content" and target_semantic == "file_path":
            if tool_type in ["file_writer", "minio_uploader"]:
                return True
        
        # 文件路径 -> 文件内容的转换
        if source_semantic == "file_path" and target_semantic == "file_content":
            return True
        
        # 相同语义类型
        if source_semantic == target_semantic:
            return True
        
        return False
    
    def _create_adaptation(self, param_name: str, param_value: Any, param_semantic: str,
                          input_semantics: List[str], tool_type: str, 
                          node_outputs: Dict[str, Any]) -> Optional[ParameterAdaptation]:
        """创建参数适配"""
        
        # 文件内容 -> 文件路径的适配
        if param_semantic == "file_content" and "file_path" in input_semantics:
            if tool_type in ["file_writer", "minio_uploader"]:
                adapted_value = self._content_to_file_path(param_value, param_name)
                if adapted_value:
                    return ParameterAdaptation(
                        original_param=param_value,
                        adapted_param=adapted_value,
                        adaptation_type="content_to_file_path",
                        confidence=0.8,
                        evidence=f"将文件内容转换为文件路径以适配 {tool_type}"
                    )
        
        # 文件路径 -> 文件内容的适配
        elif param_semantic == "file_path" and "file_content" in input_semantics:
            adapted_value = self._file_path_to_content(param_value)
            if adapted_value:
                return ParameterAdaptation(
                    original_param=param_value,
                    adapted_param=adapted_value,
                    adaptation_type="file_path_to_content",
                    confidence=0.7,
                    evidence=f"将文件路径转换为文件内容以适配 {tool_type}"
                )
        
        # 字典 -> 文件路径的适配（新增）
        elif param_semantic == "file_path" and isinstance(param_value, dict):
            adapted_value = self._extract_file_path_from_dict(param_value)
            if adapted_value:
                return ParameterAdaptation(
                    original_param=param_value,
                    adapted_param=adapted_value,
                    adaptation_type="dict_to_file_path",
                    confidence=0.9,
                    evidence=f"从字典中提取文件路径以适配 {tool_type}"
                )
        
        return None
    
    def _content_to_file_path(self, content: str, param_name: str) -> Optional[str]:
        """将文件内容转换为文件路径"""
        try:
            # 生成临时文件路径
            if param_name in ["file_path", "filename"]:
                # 如果参数名暗示需要文件路径，生成一个合适的文件名
                if content.startswith('# '):
                    # 从Markdown标题提取文件名
                    title_match = re.match(r'^#\s+(.+)$', content.split('\n')[0])
                    if title_match:
                        filename = re.sub(r'[^\w\s-]', '', title_match.group(1)).strip()
                        filename = re.sub(r'[-\s]+', '_', filename)
                        return f"{filename}.md"
                
                # 默认文件名
                return "generated_content.md"
            else:
                # 其他情况，使用参数名作为文件名
                return f"{param_name}.txt"
        
        except Exception as e:
            self.logger.warning(f"内容转文件路径失败: {e}")
            return None
    
    def _file_path_to_content(self, file_path: str) -> Optional[str]:
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
            return None
    
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
    
    def analyze_parameter_mismatch(self, params: Dict[str, Any], tool_type: str) -> List[Dict[str, Any]]:
        """分析参数不匹配问题"""
        mismatches = []
        
        input_semantics = self.tool_semantic_mapping.get(tool_type, {}).get("input", [])
        
        for param_name, param_value in params.items():
            param_semantic = self._analyze_param_semantic(param_name, param_value)
            
            if param_semantic not in input_semantics:
                # 检查是否有兼容的语义类型
                compatible = False
                for input_semantic in input_semantics:
                    if self._is_semantic_compatible(param_semantic, input_semantic, tool_type):
                        compatible = True
                        break
                
                if not compatible:
                    mismatches.append({
                        "param_name": param_name,
                        "param_value": str(param_value)[:100] + "..." if len(str(param_value)) > 100 else str(param_value),
                        "param_semantic": param_semantic,
                        "expected_semantics": input_semantics,
                        "issue": "语义不匹配"
                    })
        
        return mismatches
    
    def suggest_parameter_fixes(self, mismatches: List[Dict[str, Any]], tool_type: str) -> List[Dict[str, Any]]:
        """建议参数修复方案"""
        suggestions = []
        
        for mismatch in mismatches:
            param_name = mismatch["param_name"]
            param_semantic = mismatch["param_semantic"]
            expected_semantics = mismatch["expected_semantics"]
            
            for expected_semantic in expected_semantics:
                if self._is_semantic_compatible(param_semantic, expected_semantic, tool_type):
                    suggestions.append({
                        "param_name": param_name,
                        "current_semantic": param_semantic,
                        "target_semantic": expected_semantic,
                        "adaptation_type": f"{param_semantic}_to_{expected_semantic}",
                        "description": f"将 {param_semantic} 适配为 {expected_semantic}",
                        "confidence": 0.8
                    })
        
        return suggestions 