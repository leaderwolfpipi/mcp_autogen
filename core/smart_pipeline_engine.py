#!/usr/bin/env python3
"""
智能Pipeline执行引擎
整合LLM意图识别、占位符解析和自动工具生成
"""

import asyncio
import logging
import time
import importlib.util
import os
from typing import Dict, Any, List, Optional, Callable

from .requirement_parser import RequirementParser
from .placeholder_resolver import PlaceholderResolver, NodeOutput
from .code_generator import CodeGenerator
from .unified_tool_manager import get_unified_tool_manager
from .tool_adapter import get_tool_adapter

class SmartPipelineEngine:
    """智能Pipeline执行引擎"""
    
    def __init__(self, use_llm: bool = True, llm_config: Dict[str, Any] = None, db_registry=None):
        self.logger = logging.getLogger("SmartPipelineEngine")
        
        # 初始化统一工具系统
        self.tool_system = get_unified_tool_manager(db_registry)
        
        # 获取可用工具列表
        available_tools = self.tool_system.get_tool_list()
        
        # 初始化需求解析器，传入可用工具列表
        self.requirement_parser = RequirementParser(
            use_llm=use_llm, 
            available_tools=available_tools,
            **(llm_config or {})
        )
        
        self.placeholder_resolver = PlaceholderResolver()
        
        # 初始化代码生成器
        self.code_generator = CodeGenerator(
            use_llm=use_llm,
            llm_model=llm_config.get("llm_model", "gpt-4o") if llm_config else "gpt-4o"
        )
        
        # 自动生成的工具缓存
        self.auto_generated_tools: Dict[str, Callable] = {}
        
        # 初始化工具适配器
        self.tool_adapter = get_tool_adapter()
        
        self.logger.info(f"智能Pipeline引擎初始化完成，可用工具数量: {len(available_tools)}")
    
    async def execute_from_natural_language(self, user_input: str) -> Dict[str, Any]:
        """
        从自然语言输入执行智能Pipeline
        """
        start_time = time.time()
        
        try:
            # 1. 解析用户需求
            self.logger.info(f"🔍 解析用户需求: {user_input}")
            requirement = self.requirement_parser.parse(user_input)
            self.logger.info(f"📋 解析结果: {requirement}")
            
            # 检查是否是闲聊情况
            if requirement.get("chat_only", False):
                self.logger.info("💬 检测到闲聊，调用LLM直接回答")
                return await self._handle_chat_only(requirement.get("user_input", user_input), start_time)
            
            # 2. 获取组件和执行顺序
            components = requirement.get("components", [])
            if not components:
                return {
                    "success": False,
                    "errors": ["未能解析出有效的执行组件"],
                    "execution_time": time.time() - start_time
                }
            
            # 3. 确定执行顺序
            execution_order = self._determine_execution_order(components)
            self.logger.info(f"📊 执行顺序: {execution_order}")
            
            # 4. 执行Pipeline
            result = await self._execute_pipeline(components, execution_order, start_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 执行失败: {e}")
            return {
                "success": False,
                "errors": [str(e)],
                "execution_time": time.time() - start_time
            }

    async def execute_from_natural_language_with_streaming(self, user_input: str, callback=None) -> Dict[str, Any]:
        """
        从自然语言输入执行智能Pipeline（流式版本）
        """
        start_time = time.time()
        
        try:
            # 1. 解析用户需求
            self.logger.info(f"🔍 解析用户需求: {user_input}")
            requirement = self.requirement_parser.parse(user_input)
            self.logger.info(f"📋 解析结果: {requirement}")
            
            # 检查是否是闲聊情况
            if requirement.get("chat_only", False):
                self.logger.info("💬 检测到闲聊，调用LLM直接回答")
                return await self._handle_chat_only(requirement.get("user_input", user_input), start_time)
            
            # 2. 获取组件和执行顺序
            components = requirement.get("components", [])
            if not components:
                return {
                    "success": False,
                    "errors": ["未能解析出有效的执行组件"],
                    "execution_time": time.time() - start_time
                }
            
            # 3. 确定执行顺序
            execution_order = self._determine_execution_order(components)
            self.logger.info(f"📊 执行顺序: {execution_order}")
            
            # 4. 执行Pipeline（流式版本）
            result = await self._execute_pipeline_with_streaming(components, execution_order, start_time, callback)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 执行失败: {e}")
            return {
                "success": False,
                "errors": [str(e)],
                "execution_time": time.time() - start_time
            }
    
    async def _execute_pipeline(self, components: List[Dict[str, Any]], 
                              execution_order: List[str], 
                              start_time: float) -> Dict[str, Any]:
        """执行pipeline"""
        
        # 验证执行顺序
        validation_errors = self.placeholder_resolver.validate_execution_order(components, execution_order)
        if validation_errors:
            self.logger.error(f"❌ 执行顺序验证失败:")
            for error in validation_errors:
                self.logger.error(f"  - {error}")
            return {
                "success": False,
                "errors": validation_errors,
                "execution_time": time.time() - start_time
            }
        
        self.logger.info(f"✅ 执行顺序验证通过")
        
        node_results = []
        node_outputs: Dict[str, NodeOutput] = {}
        errors = []
        detailed_logs = []
        
        # 将组件按ID索引
        components_by_id = {comp["id"]: comp for comp in components}
        
        for node_id in execution_order:
            try:
                component = components_by_id[node_id]
                tool_type = component['tool_type']
                
                # 记录详细的执行开始信息
                execution_start = time.time()
                self.logger.info(f"🚀 执行节点: {node_id} ({tool_type})")
                detailed_logs.append({
                    "timestamp": execution_start,
                    "node_id": node_id,
                    "tool_type": tool_type,
                    "action": "start",
                    "message": f"开始执行节点 {node_id} ({tool_type})"
                })
                
                # 1. 解析占位符
                self.logger.info(f"📝 解析占位符: {node_id}")
                resolved_params = self.placeholder_resolver.resolve_placeholders(
                    component["params"], node_outputs
                )
                self.logger.info(f"📝 解析后的参数: {resolved_params}")
                
                # 1.5. 检查兼容性并自动适配
                self.logger.info(f"🔍 检查工具兼容性: {tool_type}")
                compatibility_result = await self._check_and_adapt_compatibility(
                    node_id, tool_type, resolved_params, node_outputs
                )
                
                if compatibility_result["needs_adaptation"]:
                    self.logger.info(f"🔄 应用自动适配: {compatibility_result['adapter_name']}")
                    resolved_params = compatibility_result["adapted_params"]
                
                # 2. 获取或生成工具函数
                self.logger.info(f"🔧 获取工具函数: {tool_type}")
                tool_func = await self._get_or_generate_tool(tool_type, resolved_params)
                
                if tool_func is None:
                    error_msg = f"工具 {tool_type} 不存在且无法自动生成"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
                    detailed_logs.append({
                        "timestamp": time.time(),
                        "node_id": node_id,
                        "tool_type": tool_type,
                        "action": "error",
                        "message": error_msg
                    })
                    break
                
                # 3. 执行工具
                self.logger.info(f"⚡ 执行工具: {tool_type}")
                execution_params = resolved_params
                
                if asyncio.iscoroutinefunction(tool_func):
                    result = await tool_func(**execution_params)
                else:
                    result = tool_func(**execution_params)
                
                execution_time = time.time() - execution_start
                
                # 4. 创建节点输出对象
                output_def = component.get("output", {})
                node_output = self.placeholder_resolver.create_node_output(
                    node_id, output_def, result
                )
                node_outputs[node_id] = node_output
                
                # 5. 记录详细结果
                tool_source = self.tool_system.get_source(tool_type)
                source_value = tool_source.value if tool_source else "unknown"
                
                # 提取结果摘要用于日志
                result_summary = self._extract_result_summary(result)
                
                node_result = {
                    "node_id": node_id,
                    "tool_type": tool_type,
                    "input_params": execution_params,
                    "output": result,
                    "status": "success",
                    "tool_source": source_value,
                    "execution_time": execution_time,
                    "result_summary": result_summary
                }
                node_results.append(node_result)
                
                # 记录详细的成功信息
                self.logger.info(f"✅ 节点 {node_id} 执行成功 (来源: {source_value}, 耗时: {execution_time:.2f}秒)")
                self.logger.info(f"📊 结果摘要: {result_summary}")
                
                detailed_logs.append({
                    "timestamp": time.time(),
                    "node_id": node_id,
                    "tool_type": tool_type,
                    "action": "success",
                    "message": f"节点执行成功，耗时: {execution_time:.2f}秒",
                    "result_summary": result_summary
                })
                
            except Exception as e:
                execution_time = time.time() - execution_start
                error_msg = f"节点 {node_id} 执行失败: {e}"
                self.logger.error(error_msg)
                
                node_results.append({
                    "node_id": node_id,
                    "tool_type": component.get("tool_type", "unknown"),
                    "error": str(e),
                    "status": "failed",
                    "execution_time": execution_time
                })
                
                detailed_logs.append({
                    "timestamp": time.time(),
                    "node_id": node_id,
                    "tool_type": component.get("tool_type", "unknown"),
                    "action": "error",
                    "message": error_msg,
                    "execution_time": execution_time
                })
                break
        
        total_execution_time = time.time() - start_time
        
        return {
            "success": len(errors) == 0,
            "node_results": node_results,
            "final_output": self._get_final_output(node_outputs, execution_order),
            "execution_time": total_execution_time,
            "errors": errors,
            "detailed_logs": detailed_logs,
            "execution_summary": {
                "total_nodes": len(execution_order),
                "successful_nodes": len([r for r in node_results if r["status"] == "success"]),
                "failed_nodes": len([r for r in node_results if r["status"] == "failed"]),
                "total_execution_time": total_execution_time,
                "average_node_time": total_execution_time / len(node_results) if node_results else 0
            }
        }
    
    def _get_final_output(self, node_outputs: Dict[str, NodeOutput], execution_order: List[str]) -> Any:
        """获取最终输出"""
        if not node_outputs or not execution_order:
            return None
        
        last_node_id = execution_order[-1]
        last_node_output = node_outputs.get(last_node_id)
        
        if not last_node_output:
            return None
        
        # 使用智能提取逻辑，优先处理结构化数据
        output_value = last_node_output.value
        
        # 如果输出是字典，尝试智能提取
        if isinstance(output_value, dict):
            # 1. 优先处理结构化数据（如data.primary等）
            if 'data' in output_value and isinstance(output_value['data'], dict):
                data = output_value['data']
                if 'primary' in data and isinstance(data['primary'], list) and len(data['primary']) > 0:
                    # 从搜索结果中提取关键信息
                    return self._extract_structured_info_from_search_results(data['primary'], output_value)
            
            # 2. 检查是否有其他有意义的数据字段
            for key in ['result', 'content', 'text', 'answer']:
                if key in output_value and output_value[key]:
                    value = output_value[key]
                    # 避免返回通用状态消息
                    if isinstance(value, str) and not self._is_generic_message(value):
                        return value
            
            # 3. 如果有message但不是通用消息，使用它
            if 'message' in output_value and output_value['message']:
                message = output_value['message']
                if isinstance(message, str) and not self._is_generic_message(message):
                    return message
            
            # 4. 兜底：使用output_key或整个字典
            if last_node_output.output_key in output_value:
                return output_value[last_node_output.output_key]
            return output_value
        
        # 如果输出不是字典，直接返回
        return output_value
    
    def _extract_structured_info_from_search_results(self, primary_data: list, context: dict) -> str:
        """从搜索结果中提取结构化信息"""
        if not primary_data:
            return "未找到相关结果。"
        
        # 尝试从第一个结果中提取关键信息
        first_result = primary_data[0] if primary_data else None
        if first_result and isinstance(first_result, dict):
            title = first_result.get('title', '')
            snippet = first_result.get('snippet', first_result.get('description', ''))
            
            # 清理文本
            title = self._clean_text(title)
            snippet = self._clean_text(snippet)
            
            # 检查是否是天气查询（根据metadata推断）
            metadata = context.get('metadata', {})
            parameters = metadata.get('parameters', {})
            query = parameters.get('query', '')
            
            if any(keyword in query.lower() for keyword in ['天气', 'weather', '气温', '温度']):
                weather_info = self._extract_weather_info(title + ' ' + snippet, query)
                if weather_info:
                    return weather_info
        
        # 如果无法提取结构化信息，返回格式化的搜索结果摘要
        return self._format_search_results_summary(primary_data, context)
    
    def _extract_weather_info(self, text: str, query: str) -> str:
        """提取天气信息"""
        import re
        weather_info = []
        
        # 提取地点
        location = query.replace('天气', '').replace('weather', '').strip()
        if location:
            weather_info.append(f"📍 {location}")
        
        # 提取温度信息（兼容无°/℃符号及不同分隔符）
        range_match = re.search(r'(\d{1,2})\s*(?:°|℃)?\s*(?:~|至|-)\s*(\d{1,2})\s*(?:°|℃)?\s*[Cc]?', text)
        if range_match:
            low, high = range_match.group(1), range_match.group(2)
            weather_info.append(f"🌡️ 温度: {low}°C~{high}°C")
        else:
            single_match = re.search(r'(\d{1,2})\s*(?:°|℃)?\s*[Cc]?', text)
            if single_match:
                temp = single_match.group(1)
                weather_info.append(f"🌡️ 温度: {temp}°C")
        
        # 提取天气状况
        weather_conditions = ['晴', '阴', '多云', '小雨', '中雨', '大雨', '暴雨', '雪', '雷雨', '雾霾', '雾']
        for condition in weather_conditions:
            if condition in text:
                weather_info.append(f"☁️ 天气: {condition}")
                break
        
        # 提取风力信息
        wind_pattern = r'(东风|西风|南风|北风|东南风|西南风|东北风|西北风)(\d+级)?'
        wind_match = re.search(wind_pattern, text)
        if wind_match:
            wind_dir = wind_match.group(1)
            wind_level = wind_match.group(2) if wind_match.group(2) else ''
            weather_info.append(f"💨 风力: {wind_dir}{wind_level}")
        
        # 提取空气质量
        air_qualities = ['优', '良', '轻度污染', '中度污染', '重度污染', '严重污染']
        for quality in air_qualities:
            if quality in text:
                weather_info.append(f"🌬️ 空气质量: {quality}")
                break
        
        if weather_info:
            return "\n".join(weather_info)
        
        return ""
    
    def _format_search_results_summary(self, primary_data: list, context: dict) -> str:
        """格式化搜索结果摘要"""
        if not primary_data:
            return "未找到相关结果。"
        
        formatted_items = []
        max_items = min(3, len(primary_data))
        
        for i, item in enumerate(primary_data[:max_items], 1):
            if isinstance(item, dict):
                title = item.get('title', '').strip()
                description = item.get('snippet', item.get('description', item.get('content', ''))).strip()
                
                title = self._clean_text(title)
                description = self._clean_text(description)
                
                if title:
                    if description and len(description) > 150:
                        description = description[:150] + "..."
                    
                    if description:
                        formatted_items.append(f"{i}. {title}\n   {description}")
                    else:
                        formatted_items.append(f"{i}. {title}")
        
        if formatted_items:
            result_text = "📋 结果摘要：\n\n" + "\n\n".join(formatted_items)
            
            # 添加统计信息
            counts = context.get('data', {}).get('counts', {})
            if counts and 'total' in counts:
                total = counts['total']
                result_text += f"\n\n📊 共找到 {total} 个结果"
            
            return result_text
        
        return "找到结果，但内容为空。"
    
    def _is_generic_message(self, message: str) -> bool:
        """判断是否是通用的状态消息"""
        import re
        generic_patterns = [
            r'搜索成功.*找到.*结果',
            r'.*执行完成',
            r'.*成功',
            r'任务.*完成'
        ]
        
        message_lower = message.lower()
        return any(re.search(pattern, message_lower) for pattern in generic_patterns)
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        import re
        if not text:
            return ""
        
        # 移除特殊字符和控制字符
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除一些常见的无用字符，但保留更多有意义的字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff,.!?;:()、。，！？；：（）\-_]', '', text)
        
        return text.strip()
    
    async def _get_or_generate_tool(self, tool_type: str, params: Dict[str, Any] = None) -> Optional[Callable]:
        """获取或自动生成工具函数"""
        # 1. 检查统一工具系统
        tool_func = await self.tool_system.get_tool(tool_type)
        if tool_func:
            return tool_func
        
        # 2. 检查自动生成的工具
        if tool_type in self.auto_generated_tools:
            return self.auto_generated_tools[tool_type]
        
        # 3. 尝试自动生成工具
        generated_tool = await self._auto_generate_tool_with_codegen(tool_type, params or {})
        if generated_tool:
            self.auto_generated_tools[tool_type] = generated_tool
            # 注意：工具注册和保存已在_auto_generate_tool_with_codegen中处理
            self.logger.info(f"自动生成工具: {tool_type}")
            return generated_tool
        
        return None
    
    async def _auto_generate_tool_with_codegen(self, tool_type: str, params: Dict[str, Any]) -> Optional[Callable]:
        """使用CodeGenerator自动生成工具函数"""
        try:
            self.logger.info(f"🔧 使用CodeGenerator生成工具: {tool_type}")
            
            # 1. 检查是否存在现有工具文件
            existing_tool_path = f"tools/{tool_type}.py"
            existing_params = {}
            
            if os.path.exists(existing_tool_path):
                self.logger.info(f"发现现有工具文件: {existing_tool_path}")
                existing_params = self.code_generator._parse_existing_function_params(existing_tool_path, tool_type)
                self.logger.info(f"现有工具参数: {existing_params}")
            
            # 2. 合并参数，确保向后兼容
            merged_params = self.code_generator._merge_params_with_backward_compatibility(existing_params, params)
            
            # 3. 构造工具规格
            tool_spec = {
                "tool": tool_type,
                "params": merged_params,
                "existing_params": existing_params
            }
            
            # 4. 使用CodeGenerator生成代码
            code = self.code_generator.generate(tool_spec)
            self.logger.info(f"代码生成完成，长度: {len(code)} 字符")
            
            # 5. 保存代码到本地tools目录
            self._save_code_to_file(tool_type, code)
            
            # 6. 动态编译和执行代码
            tool_func = self._compile_and_load_tool(tool_type, code)
            
            if tool_func:
                self.logger.info(f"✅ 工具 {tool_type} 生成并加载成功")
                
                # 7. 注册到统一工具系统
                self.tool_system.register_tool(tool_func, tool_type)
                
                # 8. 从函数文档字符串中提取描述信息
                description = self._extract_function_description(tool_func)
                
                # 9. 保存到数据库
                try:
                    await self.tool_system.save_tool_to_database(
                        tool_type, 
                        tool_func, 
                        description=description,
                        source="auto_generated"
                    )
                    self.logger.info(f"💾 工具 {tool_type} 已保存到数据库")
                except Exception as db_error:
                    self.logger.warning(f"保存工具到数据库失败: {db_error}")
                
                return tool_func
            else:
                self.logger.error(f"❌ 工具 {tool_type} 编译失败")
                return None
                
        except Exception as e:
            self.logger.error(f"自动生成工具 {tool_type} 失败: {e}")
            return None
    
    def _save_code_to_file(self, tool_name: str, code: str):
        """保存代码到本地tools目录"""
        try:
            # 确保tools目录存在
            os.makedirs("tools", exist_ok=True)
            
            # 保存代码到文件
            file_path = f"tools/{tool_name}.py"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            self.logger.info(f"💾 代码已保存到本地文件: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存代码到文件失败: {e}")
    
    def _create_tool_with_code(self, tool_func: Callable, original_code: str) -> Callable:
        """创建一个带有原始代码的函数包装器"""
        def tool_with_code(*args, **kwargs):
            return tool_func(*args, **kwargs)
        
        # 设置函数属性
        tool_with_code.__name__ = tool_func.__name__
        tool_with_code.__doc__ = tool_func.__doc__
        tool_with_code.__module__ = tool_func.__module__
        
        # 添加原始代码属性
        tool_with_code._original_code = original_code
        
        return tool_with_code
    
    def _extract_function_description(self, tool_func: Callable) -> str:
        """从函数文档字符串中提取描述信息"""
        try:
            import inspect
            
            # 获取函数的文档字符串
            doc = inspect.getdoc(tool_func)
            if doc:
                # 提取前3行作为描述
                lines = doc.strip().split('\n')
                # 过滤掉空行，取前3行非空行
                non_empty_lines = [line.strip() for line in lines if line.strip()]
                first_three_lines = non_empty_lines[:3]
                
                # 用换行符连接前3行
                description = '\n'.join(first_three_lines)
                
                # 如果总长度超过300字符，截取前297个字符并添加省略号
                if len(description) > 300:
                    description = description[:297] + "..."
                
                return description
            else:
                # 如果没有文档字符串，使用函数名生成基本描述
                func_name = tool_func.__name__
                return f"工具函数: {func_name}"
                
        except Exception as e:
            self.logger.warning(f"提取函数描述失败: {e}")
            return f"工具函数: {tool_func.__name__}"
    
    def _compile_and_load_tool(self, tool_name: str, code: str) -> Optional[Callable]:
        """编译并加载工具函数"""
        try:
            module_namespace = {}
            exec(code, module_namespace)
            
            if tool_name in module_namespace:
                tool_func = module_namespace[tool_name]
                self.logger.info(f"工具函数 {tool_name} 加载成功")
                return tool_func
            else:
                self.logger.error(f"生成的代码中没有找到函数 {tool_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"编译工具 {tool_name} 失败: {e}")
            self.logger.debug(f"生成的代码:\n{code}")
            return None
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息"""
        if self.tool_system.exists(tool_name):
            source = self.tool_system.get_source(tool_name)
            return {
                "name": tool_name,
                "source": source.value if source else "unknown",
                "exists": True
            }
        elif tool_name in self.auto_generated_tools:
            return {
                "name": tool_name,
                "source": "generated",
                "exists": True
            }
        else:
            return {
                "name": tool_name,
                "source": "unknown",
                "exists": False
            }
    
    def list_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """列出所有可用工具"""
        return {tool["name"]: tool for tool in self.tool_system.get_tool_list()}

    async def _check_and_adapt_compatibility(self, node_id: str, tool_type: str, 
                                           resolved_params: Dict[str, Any], 
                                           node_outputs: Dict[str, NodeOutput]) -> Dict[str, Any]:
        """
        检查工具兼容性并自动适配
        
        Args:
            node_id: 当前节点ID
            tool_type: 工具类型
            resolved_params: 解析后的参数
            node_outputs: 节点输出映射
            
        Returns:
            兼容性检查结果
        """
        result = {
            "needs_adaptation": False,
            "adapter_name": None,
            "adapted_params": resolved_params,
            "compatibility_analysis": None
        }
        
        try:
            # 分析参数中的占位符引用
            placeholder_refs = self._extract_placeholder_references(resolved_params)
            
            for ref in placeholder_refs:
                source_node_id = ref["node_id"]
                
                if source_node_id in node_outputs:
                    source_output = node_outputs[source_node_id]
                    
                    # 分析兼容性
                    analysis = self.tool_adapter.analyze_compatibility(
                        source_output, resolved_params
                    )
                    
                    if not analysis["is_compatible"]:
                        self.logger.info(f"检测到兼容性问题: {analysis['missing_keys']} 缺失, {analysis['type_mismatches']} 类型不匹配")
                        
                        # 创建适配器
                        adapter_def = self.tool_adapter.create_adapter(
                            source_node_id, tool_type, source_output, resolved_params
                        )
                        
                        if adapter_def:
                            result["needs_adaptation"] = True
                            result["adapter_name"] = adapter_def.name
                            result["compatibility_analysis"] = analysis
                            
                            # 应用适配器到所有相关参数
                            adapted_params = resolved_params.copy()
                            for key, value in resolved_params.items():
                                if isinstance(value, str) and f"${source_node_id}.output" in value:
                                    # 应用适配器
                                    adapted_value = self.tool_adapter.apply_adapter(
                                        adapter_def.name, source_output.value
                                    )
                                    adapted_params[key] = adapted_value
                            
                            result["adapted_params"] = adapted_params
                            break
        
        except Exception as e:
            self.logger.error(f"兼容性检查失败: {e}")
        
        return result
    
    def _extract_placeholder_references(self, params: Dict[str, Any]) -> List[Dict[str, str]]:
        """提取参数中的占位符引用"""
        references = []
        
        def extract_from_value(value):
            if isinstance(value, str):
                # 使用占位符解析器的模式
                import re
                pattern = r'\$([a-zA-Z_][a-zA-Z0-9_]*)\.output(?:\.([a-zA-Z_][a-zA-Z0-9_]*))?'
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

    def _extract_result_summary(self, result: Any) -> str:
        """提取结果摘要用于日志显示"""
        if isinstance(result, dict):
            if 'results' in result:
                return f"返回 {len(result['results'])} 个结果"
            elif 'formatted_text' in result:
                content_length = len(result['formatted_text'])
                return f"格式化文本，长度: {content_length} 字符"
            elif 'report_content' in result:
                content_length = len(result['report_content'])
                return f"报告内容，长度: {content_length} 字符"
            elif 'status' in result:
                return f"状态: {result['status']}"
            else:
                return f"字典结果，包含 {len(result)} 个字段"
        elif isinstance(result, list):
            return f"列表结果，包含 {len(result)} 个元素"
        elif isinstance(result, str):
            return f"字符串结果，长度: {len(result)} 字符"
        else:
            return f"其他类型结果: {type(result).__name__}"

    def _determine_execution_order(self, components: List[Dict[str, Any]]) -> List[str]:
        """确定执行顺序"""
        # 使用placeholder_resolver来确定执行顺序
        return self.placeholder_resolver.build_execution_order(components)

    async def _execute_pipeline_with_streaming(self, components: List[Dict[str, Any]], 
                                             execution_order: List[str], 
                                             start_time: float,
                                             callback=None) -> Dict[str, Any]:
        """
        执行Pipeline（流式版本）
        """
        node_outputs = {}
        node_results = []
        errors = []
        detailed_logs = []
        
        # 将组件按ID索引
        components_by_id = {comp["id"]: comp for comp in components}
        
        for node_id in execution_order:
            try:
                component = components_by_id[node_id]
                tool_type = component['tool_type']
                
                # 记录详细的执行开始信息
                execution_start = time.time()
                self.logger.info(f"🚀 执行节点: {node_id} ({tool_type})")
                detailed_logs.append({
                    "timestamp": execution_start,
                    "node_id": node_id,
                    "tool_type": tool_type,
                    "action": "start",
                    "message": f"开始执行节点 {node_id} ({tool_type})"
                })
                
                # 1. 解析占位符
                self.logger.info(f"📝 解析占位符: {node_id}")
                resolved_params = self.placeholder_resolver.resolve_placeholders(
                    component["params"], node_outputs
                )
                self.logger.info(f"📝 解析后的参数: {resolved_params}")
                
                # 1.5. 检查兼容性并自动适配
                self.logger.info(f"🔍 检查工具兼容性: {tool_type}")
                compatibility_result = await self._check_and_adapt_compatibility(
                    node_id, tool_type, resolved_params, node_outputs
                )
                
                if compatibility_result["needs_adaptation"]:
                    self.logger.info(f"🔄 应用自动适配: {compatibility_result['adapter_name']}")
                    resolved_params = compatibility_result["adapted_params"]
                
                # 2. 获取或生成工具函数
                self.logger.info(f"🔧 获取工具函数: {tool_type}")
                tool_func = await self._get_or_generate_tool(tool_type, resolved_params)
                
                if tool_func is None:
                    error_msg = f"工具 {tool_type} 不存在且无法自动生成"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
                    detailed_logs.append({
                        "timestamp": time.time(),
                        "node_id": node_id,
                        "tool_type": tool_type,
                        "action": "error",
                        "message": error_msg
                    })
                    break
                
                # 3. 执行工具
                self.logger.info(f"⚡ 执行工具: {tool_type}")
                execution_params = resolved_params
                
                if asyncio.iscoroutinefunction(tool_func):
                    result = await tool_func(**execution_params)
                else:
                    result = tool_func(**execution_params)
                
                execution_time = time.time() - execution_start
                
                # 4. 创建节点输出对象
                output_def = component.get("output", {})
                node_output = self.placeholder_resolver.create_node_output(
                    node_id, output_def, result
                )
                node_outputs[node_id] = node_output
                
                # 5. 记录详细结果
                tool_source = self.tool_system.get_source(tool_type)
                source_value = tool_source.value if tool_source else "unknown"
                
                # 提取结果摘要用于日志
                result_summary = self._extract_result_summary(result)
                
                node_result = {
                    "node_id": node_id,
                    "tool_type": tool_type,
                    "input_params": execution_params,
                    "output": result,
                    "status": "success",
                    "tool_source": source_value,
                    "execution_time": execution_time,
                    "result_summary": result_summary
                }
                node_results.append(node_result)
                
                # 6. 实时回调结果（流式输出）
                if callback:
                    try:
                        callback(node_result)
                    except Exception as callback_error:
                        self.logger.warning(f"回调函数执行失败: {callback_error}")
                
                # 记录详细的成功信息
                self.logger.info(f"✅ 节点 {node_id} 执行成功 (来源: {source_value}, 耗时: {execution_time:.2f}秒)")
                self.logger.info(f"📊 结果摘要: {result_summary}")
                
                detailed_logs.append({
                    "timestamp": time.time(),
                    "node_id": node_id,
                    "tool_type": tool_type,
                    "action": "success",
                    "message": f"节点执行成功，耗时: {execution_time:.2f}秒",
                    "result_summary": result_summary
                })
                
            except Exception as e:
                error_msg = f"节点 {node_id} 执行失败: {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
                
                detailed_logs.append({
                    "timestamp": time.time(),
                    "node_id": node_id,
                    "tool_type": component.get('tool_type', 'unknown') if 'component' in locals() else 'unknown',
                    "action": "error",
                    "message": error_msg
                })
                
                # 记录失败的节点结果
                node_result = {
                    "node_id": node_id,
                    "tool_type": component.get('tool_type', 'unknown') if 'component' in locals() else 'unknown',
                    "input_params": execution_params if 'execution_params' in locals() else {},
                    "output": None,
                    "status": "error",
                    "error": str(e),
                    "execution_time": time.time() - execution_start if 'execution_start' in locals() else 0
                }
                node_results.append(node_result)
                
                # 实时回调失败结果
                if callback:
                    try:
                        callback(node_result)
                    except Exception as callback_error:
                        self.logger.warning(f"回调函数执行失败: {callback_error}")
                
                break
        
        # 构建最终结果
        final_result = {
            "success": len(errors) == 0,
            "node_results": node_results,
            "node_outputs": {k: v.to_dict() for k, v in node_outputs.items()},
            "execution_time": time.time() - start_time,
            "errors": errors,
            "detailed_logs": detailed_logs
        }
        
        if final_result["success"]:
            # 获取最终输出
            final_output = self._get_final_output(node_outputs, execution_order)
            final_result["final_output"] = final_output
        
        return final_result

    async def _handle_chat_only(self, user_input: str, start_time: float) -> Dict[str, Any]:
        """
        处理闲聊情况，直接调用LLM回答用户问题
        """
        self.logger.info(f"💬 调用LLM回答用户问题: {user_input}")
        try:
            # 尝试使用LLM回答
            try:
                # 直接使用requirement_parser的LLM配置
                import openai
                client = openai.OpenAI(
                    api_key=self.requirement_parser.api_key, 
                    base_url=self.requirement_parser.api_base
                )
                
                # 构建闲聊回答的system prompt
                chat_system_prompt = (
                    "你是一个友好的AI助手。请用自然、友好的方式回答用户的问题。\n"
                    "回答要求：\n"
                    "1. 保持友好和礼貌\n"
                    "2. 回答要简洁明了\n"
                    "3. 如果是问候，要热情回应\n"
                    "4. 如果是感谢，要谦虚回应\n"
                    "5. 如果是告别，要礼貌告别\n"
                    "6. 如果是简单问题，要给出有用的回答\n"
                    "7. 不要过于冗长，保持对话的自然性"
                )
                
                # 调用LLM回答
                response = client.chat.completions.create(
                    model=self.requirement_parser.llm_model,
                    messages=[
                        {"role": "system", "content": chat_system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                llm_response = response.choices[0].message.content
                self.logger.info(f"💬 LLM回答内容: {llm_response}")
                
            except Exception as llm_error:
                # LLM调用失败，使用预设回答
                self.logger.warning(f"LLM调用失败，使用预设回答: {llm_error}")
                llm_response = self._get_preset_chat_response(user_input)
            
            # 构建最终结果
            final_result = {
                "success": True,
                "node_results": [], # 闲聊不涉及节点执行
                "final_output": llm_response,
                "execution_time": time.time() - start_time,
                "errors": [],
                "detailed_logs": [],
                "execution_summary": {
                    "total_nodes": 0,
                    "successful_nodes": 0,
                    "failed_nodes": 0,
                    "total_execution_time": time.time() - start_time,
                    "average_node_time": 0
                }
            }
            
            return final_result
        except Exception as e:
            self.logger.error(f"❌ LLM回答失败: {e}")
            return {
                "success": False,
                "errors": [str(e)],
                "execution_time": time.time() - start_time
            }
    
    def _get_preset_chat_response(self, user_input: str) -> str:
        """
        获取预设的闲聊回答
        """
        # 问候语
        if any(keyword in user_input for keyword in ["你好", "hello", "hi", "早上好", "晚上好", "下午好"]):
            return "你好！很高兴见到你！我是你的AI助手，有什么可以帮助你的吗？"
        
        # 询问身份
        elif any(keyword in user_input for keyword in ["你是谁", "你会什么", "你是什么"]):
            return "我是你的AI助手，可以帮助你完成各种任务，比如搜索信息、处理图片、翻译文本等。有什么需要我帮忙的吗？"
        
        # 询问时间
        elif "现在几点" in user_input or "时间" in user_input:
            import datetime
            current_time = datetime.datetime.now().strftime("%H:%M")
            return f"现在是 {current_time}。"
        
        # 询问天气
        elif "天气" in user_input:
            return "抱歉，我无法获取实时天气信息。建议你查看天气预报网站或使用天气APP获取准确的天气信息。"
        
        # 感谢
        elif any(keyword in user_input for keyword in ["谢谢", "感谢", "辛苦了"]):
            return "不客气！很高兴能帮到你。如果还有其他问题，随时可以问我！"
        
        # 告别
        elif any(keyword in user_input for keyword in ["再见", "拜拜", "goodbye", "bye"]):
            return "再见！祝你有愉快的一天！如果还有问题，随时欢迎回来找我。"
        
        # 询问状态
        elif any(keyword in user_input for keyword in ["在吗", "忙吗", "怎么样", "如何"]):
            return "我在呢！随时准备为你服务。有什么需要帮助的吗？"
        
        # 默认回答
        else:
            return "我理解你的问题，但可能需要更具体的信息才能给你最好的帮助。你可以尝试搜索相关信息，或者告诉我你具体想要做什么。"

# 使用示例
async def demo_smart_pipeline():
    """演示智能pipeline执行"""
    engine = SmartPipelineEngine(use_llm=False)
    
    print("🎯 智能Pipeline演示")
    print("=" * 60)
    
    result = await engine.execute_from_natural_language(
        "请将图片旋转45度，然后放大3倍，最后上传到云存储"
    )
    
    print(f"执行结果: {'成功' if result['success'] else '失败'}")
    print(f"执行时间: {result['execution_time']:.2f}秒")
    if result['errors']:
        print(f"错误信息: {result['errors']}")
    else:
        print(f"最终输出: {result['final_output']}")
        
        # 显示工具来源信息
        for node_result in result['node_results']:
            tool_source = node_result.get('tool_source', 'unknown')
            print(f"工具 {node_result['tool_type']}: {tool_source}")

if __name__ == "__main__":
    asyncio.run(demo_smart_pipeline()) 