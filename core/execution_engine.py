import logging
from typing import Dict, Any, List, Callable
import importlib
import re
import json
import subprocess
import sys
from .parameter_bridge import ParameterBridge

class ExecutionEngineError(Exception):
    pass

class ExecutionEngine:
    def __init__(
        self, 
        tool_registry, 
        use_llm_for_placeholder: bool = False,
        auto_install_deps: bool = True
    ):
        self.logger = logging.getLogger("ExecutionEngine")
        self.tool_registry = tool_registry
        self.use_llm_for_placeholder = use_llm_for_placeholder
        self.auto_install_deps = auto_install_deps
        self.execution_history = []  # 记录执行历史，用于上下文判断
        self.parameter_bridge = ParameterBridge()  # 参数衔接系统

    def _auto_install_dependency(self, package_name: str) -> bool:
        """
        自动安装缺失的依赖包
        """
        try:
            self.logger.info(f"尝试自动安装依赖: {package_name}")
            
            # 包名映射（处理一些特殊情况）
            package_mapping = {
                'PIL': 'Pillow',
                'cv2': 'opencv-python',
                'sklearn': 'scikit-learn',
                'tensorflow': 'tensorflow',
                'torch': 'torch',
                'minio': 'minio',
                'pytesseract': 'pytesseract',
                'requests': 'requests',
                'numpy': 'numpy',
                'pandas': 'pandas'
            }
            
            install_name = package_mapping.get(package_name, package_name)
            
            # 使用pip安装
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", install_name
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.logger.info(f"成功安装依赖: {install_name}")
                return True
            else:
                self.logger.error(f"安装依赖失败: {install_name}, 错误: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"自动安装依赖时出错: {e}")
            return False

    def _get_tool_dependencies(self, tool_id: str) -> List[str]:
        """
        获取工具的依赖列表
        """
        # 预定义的依赖映射
        tool_dependencies = {
            'image_resizer': ['PIL'],
            'image_upscaler': ['PIL'],
            'ocr': ['PIL', 'pytesseract'],
            'text_translator': ['requests'],
            'text_extractor': ['PIL'],
            'file_uploader': ['minio'],
            'image_processor': ['PIL', 'numpy'],
            'text_analyzer': ['numpy', 'pandas'],
            'data_processor': ['pandas', 'numpy'],
            'ml_predictor': ['sklearn', 'numpy'],
            'image_classifier': ['PIL', 'tensorflow'],
            'text_classifier': ['sklearn', 'numpy']
        }
        
        return tool_dependencies.get(tool_id, [])

    def run(self, pipeline: Dict[str, Any], input_data: Any = None) -> Dict[str, Any]:
        """
        执行pipeline，支持智能占位符替换和参数衔接
        """
        result = input_data
        pipeline_steps = pipeline.get("pipeline", [])
        self.execution_history = []  # 重置执行历史
        
        for idx, step in enumerate(pipeline_steps):
            tool_id = step["tool"]
            params = step.get("params", {}).copy()  # 复制一份，避免修改原数据
            
            # 智能占位符替换
            if result is not None:
                params = self._replace_placeholders(params, result, idx)
            
            tool_func = self._load_tool(tool_id)
            try:
                self.logger.info(f"执行工具[{idx+1}/{len(pipeline_steps)}]: {tool_id}")
                
                # 使用参数衔接系统处理参数
                bridged_params, warnings = self.parameter_bridge.bridge_parameters(
                    tool_func, params, result
                )
                
                # 记录警告信息
                for warning in warnings:
                    self.logger.warning(f"工具{tool_id}参数警告: {warning}")
                
                # 执行工具
                output = tool_func(**bridged_params)
                result = output
                
                # 记录执行历史
                self.execution_history.append({
                    'step': idx,
                    'tool': tool_id,
                    'output': result,
                    'params': bridged_params,
                    'warnings': warnings
                })
                
            except Exception as e:
                self.logger.error(f"工具{tool_id}执行失败: {e}")
                raise ExecutionEngineError(f"工具{tool_id}执行失败: {e}")
        
        return {"result": result}

    def _replace_placeholders(self, params: Dict, previous_output: Any, step_index: int) -> Dict:
        """
        混合策略：规则 + 语义 + 上下文 + LLM兜底
        """
        # 1. 规则匹配（快速）
        params = self._rule_based_replacement(params, previous_output, step_index)
        
        # 2. 语义匹配（智能）
        params = self._semantic_based_replacement(params, previous_output, step_index)
        
        # 3. LLM解析（兜底，可选）
        if self._has_unresolved_placeholders(params):
            params = self._llm_based_replacement(params, previous_output, step_index)
        
        return params

    def _rule_based_replacement(self, params: Dict, previous_output: Any, step_index: int) -> Dict:
        """
        规则匹配：基于预定义模式的快速替换
        """
        import copy
        params = copy.deepcopy(params)
        
        # 预定义的占位符模式
        rule_patterns = {
            r"<extracted_text>": previous_output,
            r"<previous_output>": previous_output,
            r"<last_output>": previous_output,
            r"<step_\d+_output>": previous_output,
            r"<current_output>": previous_output,
            r"<result>": previous_output,
            r"<output>": previous_output,
            r"output_of_previous_step": previous_output,
            r"previous_step_output": previous_output,
            r"last_step_result": previous_output,
            r"step_output": previous_output,
            r"extracted_text": previous_output,
            r"processed_result": previous_output
        }
        
        # 只替换字符串类型的参数，避免替换固定配置参数
        protected_params = ['destination', 'service', 'storage_service', 'bucket_name', 'source_lang', 'target_lang']
        
        for key, value in params.items():
            if isinstance(value, str):
                # 检查是否是占位符模式，但跳过受保护的参数
                if key not in protected_params:
                    for pattern, replacement in rule_patterns.items():
                        if re.search(pattern, value):
                            params[key] = re.sub(pattern, str(replacement), value)
                            self.logger.info(f"占位符替换: {key} = {value} -> {replacement}")
            elif isinstance(value, dict):
                params[key] = self._rule_based_replacement(value, previous_output, step_index)
        
        return params

    def _semantic_based_replacement(self, params: Dict, previous_output: Any, step_index: int) -> Dict:
        """
        语义匹配：基于关键词和上下文的智能替换
        """
        import copy
        params = copy.deepcopy(params)
        
        # 输出语义关键词
        output_keywords = [
            'output', 'result', 'text', 'image', 'data', 'content',
            'extracted', 'detected', 'processed', 'generated',
            'previous', 'last', 'step', 'output', 'response'
        ]
        
        # 通用占位符模式
        placeholder_pattern = r"<([^>]+)>"
        
        for key, value in params.items():
            if isinstance(value, str):
                matches = re.findall(placeholder_pattern, value)
                for match in matches:
                    if self._should_replace_by_semantic(match, step_index):
                        params[key] = value.replace(f"<{match}>", str(previous_output))
            elif isinstance(value, dict):
                params[key] = self._semantic_based_replacement(value, previous_output, step_index)
        
        return params

    def _should_replace_by_semantic(self, placeholder: str, step_index: int) -> bool:
        """
        基于语义判断是否应该替换占位符
        """
        placeholder_lower = placeholder.lower()
        
        # 检查是否包含输出语义关键词
        output_keywords = [
            'output', 'result', 'text', 'image', 'data', 'content',
            'extracted', 'detected', 'processed', 'generated',
            'previous', 'last', 'step', 'output', 'response'
        ]
        
        for keyword in output_keywords:
            if keyword in placeholder_lower:
                return True
        
        # 检查是否包含数字（可能是步骤引用）
        if re.search(r'\d+', placeholder):
            return True
        
        return False

    def _has_unresolved_placeholders(self, params: Dict) -> bool:
        """
        检查是否还有未解析的占位符
        """
        placeholder_pattern = r"<([^>]+)>"
        
        def check_dict(d):
            for key, value in d.items():
                if isinstance(value, str):
                    if re.search(placeholder_pattern, value):
                        return True
                elif isinstance(value, dict):
                    if check_dict(value):
                        return True
            return False
        
        return check_dict(params)

    def _llm_based_replacement(self, params: Dict, previous_output: Any, step_index: int) -> Dict:
        """
        LLM解析：用大模型智能解析复杂占位符
        """
        if not self.use_llm_for_placeholder:
            self.logger.warning("LLM占位符解析未启用，跳过复杂占位符")
            return params
        
        try:
            import openai
            import os
            
            # 构造上下文信息
            context = {
                'previous_output': previous_output,
                'step_index': step_index,
                'execution_history': self.execution_history[-3:] if self.execution_history else [],  # 最近3步
                'current_params': params
            }
            
            # 构造prompt
            prompt = f"""
            请判断以下参数中的占位符是否应该被替换为上一步的输出结果。
            
            上下文信息：
            - 上一步输出: {previous_output}
            - 当前步骤: {step_index}
            - 执行历史: {json.dumps(context['execution_history'], ensure_ascii=False)}
            - 当前参数: {json.dumps(params, ensure_ascii=False)}
            
            请返回JSON格式，只包含需要替换的占位符：
            {{"replacements": {{"占位符": "替换值"}}}}
            
            只返回JSON，不要有多余解释。
            """
            
            # 调用LLM（需要配置API）
            api_key = os.environ.get("OPENAI_API_KEY")
            api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
            
            if api_key:
                client = openai.OpenAI(api_key=api_key, base_url=api_base)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "你是一个占位符解析助手，只返回JSON格式的替换规则。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=256
                )
                result_text = response.choices[0].message.content
                
                try:
                    result = json.loads(result_text)
                    replacements = result.get("replacements", {})
                    
                    # 应用替换
                    for placeholder, replacement in replacements.items():
                        params = self._apply_replacement(params, placeholder, replacement)
                    
                    self.logger.info(f"LLM解析占位符完成: {replacements}")
                except json.JSONDecodeError:
                    self.logger.warning(f"LLM返回格式错误: {result_text}")
            else:
                self.logger.warning("未配置LLM API，跳过复杂占位符解析")
        
        except Exception as e:
            self.logger.error(f"LLM占位符解析失败: {e}")
        
        return params

    def _apply_replacement(self, params: Dict, placeholder: str, replacement: str) -> Dict:
        """
        在参数中应用占位符替换
        """
        import copy
        params = copy.deepcopy(params)
        
        def replace_in_dict(d):
            for key, value in d.items():
                if isinstance(value, str):
                    if f"<{placeholder}>" in value:
                        d[key] = value.replace(f"<{placeholder}>", replacement)
                elif isinstance(value, dict):
                    replace_in_dict(value)
        
        replace_in_dict(params)
        return params

    def _load_tool(self, tool_id: str) -> Callable:
        """
        动态加载工具实现（假设tools目录下有同名py文件和函数）
        """
        try:
            # 直接尝试导入模块
            module = importlib.import_module(f"tools.{tool_id}")
            func = getattr(module, tool_id)
            return func
        except ImportError as e:
            # 如果是依赖缺失导致的导入失败，尝试自动安装
            if self.auto_install_deps:
                self.logger.info(f"检测到依赖缺失，尝试自动安装: {e}")
                if self._try_install_missing_dependencies(tool_id, str(e)):
                    # 重新尝试导入
                    try:
                        module = importlib.import_module(f"tools.{tool_id}")
                        func = getattr(module, tool_id)
                        return func
                    except Exception as retry_e:
                        self.logger.error(f"自动安装依赖后仍无法加载工具: {retry_e}")
                        raise ExecutionEngineError(f"加载工具{tool_id}失败: {retry_e}")
                else:
                    raise ExecutionEngineError(f"自动安装依赖失败，无法加载工具{tool_id}")
            else:
                raise ExecutionEngineError(f"加载工具{tool_id}失败: {e}")
        except Exception as e:
            self.logger.error(f"加载工具{tool_id}失败: {e}")
            raise ExecutionEngineError(f"加载工具{tool_id}失败: {e}")

    def _try_install_missing_dependencies(self, tool_id: str, error_msg: str) -> bool:
        """
        根据错误信息尝试安装缺失的依赖
        """
        try:
            # 从错误信息中提取缺失的模块名
            import re
            missing_module_match = re.search(r"No module named '([^']+)'", error_msg)
            if missing_module_match:
                missing_module = missing_module_match.group(1)
                return self._auto_install_dependency(missing_module)
            
            # 如果没有匹配到，尝试使用预定义的依赖列表
            dependencies = self._get_tool_dependencies(tool_id)
            for dep in dependencies:
                try:
                    importlib.import_module(dep)
                except ImportError:
                    if not self._auto_install_dependency(dep):
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"尝试安装缺失依赖时出错: {e}")
            return False