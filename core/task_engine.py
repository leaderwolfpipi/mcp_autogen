#!/usr/bin/env python3
"""
任务调度引擎
实现符合MCP标准的任务规划和执行引擎
"""

import asyncio
import json
import logging
import os
import time
import jmespath
import re
import urllib.parse
from typing import Dict, Any, List, Optional, Tuple
import ast

from .llm_clients.openai_client import OpenAIClient
from .tool_executor import ToolExecutor


class TaskEngine:
    """任务调度引擎"""
    
    def __init__(self, tool_registry, max_depth=5):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tool_registry = tool_registry
        self.max_depth = max_depth
        
        # 从环境变量获取OpenAI配置
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE")
        model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
        
        # 初始化LLM客户端（如果有API key的话）
        if api_key:
            try:
                self.llm = OpenAIClient(
                    api_key=api_key,
                    model=model,
                    base_url=base_url
                )
                self.logger.info("LLM客户端初始化成功")
            except Exception as e:
                self.logger.warning(f"LLM客户端初始化失败: {e}")
                self.llm = None
        else:
            self.logger.info("未设置OPENAI_API_KEY，LLM功能将受限")
            self.llm = None
        
        # 初始化工具执行器
        self.tool_executor = ToolExecutor(tool_registry)
    
    async def execute(self, query: str, context: dict) -> dict:
        """
        执行任务 - 支持智能模式判断
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            执行结果字典
        """
        start_time = time.time()
        
        try:
            # 1. 智能判断：是否需要工具执行
            task_mode = await self._detect_task_mode(query)
            self.logger.info(f"模式检测结果: {'任务模式' if task_mode else '闲聊模式'} - 查询: {query[:50]}...")
            
            if not task_mode:
                # 闲聊模式：直接用LLM回答，不触发工具执行
                return await self._handle_chat_mode(query, start_time)
            
            # 2. 任务模式：进行工具规划与执行
            # 将原始查询添加到上下文中，供后续处理使用
            enhanced_context = {**context, "original_query": query}
            
            # 生成执行计划
            self.logger.info(f"开始生成执行计划: {query[:50]}...")
            execution_plan = await self._generate_plan(query, enhanced_context)
            
            if not execution_plan:
                return {
                    "success": False,
                    "error": "Failed to generate execution plan",
                    "final_output": "无法生成执行计划，请尝试重新描述您的需求。",
                    "execution_time": time.time() - start_time
                }
            
            # 执行计划
            self.logger.info(f"开始执行计划，共{len(execution_plan)}个步骤")
            result = await self._execute_plan(execution_plan, enhanced_context)
            
            # 添加执行时间和模式标识
            result['execution_time'] = time.time() - start_time
            result['mode'] = 'task'
            
            return result
            
        except Exception as e:
            self.logger.error(f"任务执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "TASK_EXECUTION_ERROR",
                "final_output": f"任务执行失败: {str(e)}",
                "execution_time": time.time() - start_time,
                "mode": "error"
            }
    
    async def _detect_task_mode(self, query: str) -> bool:
        """
        智能检测查询是否需要工具执行
        
        使用通用的语义理解而不是穷举模式匹配
        
        Returns:
            True: 需要工具执行的任务模式
            False: 普通闲聊模式
        """
        # 1. 快速长度过滤
        if len(query.strip()) < 2:
            return False
        
        # 2. 使用LLM进行通用语义判断（优先使用）
        if self.llm and hasattr(self.llm, 'generate'):
            try:
                return await self._llm_detect_task_mode_universal(query)
            except Exception as e:
                self.logger.warning(f"LLM通用模式检测失败，使用简化判断: {e}")
        
        # 3. 简化的回退规则（仅保留最基本的）
        return self._basic_fallback_detection(query)
    
    async def _llm_detect_task_mode_universal(self, query: str) -> bool:
        """使用LLM进行通用语义检测，不依赖硬编码规则"""
        prompt = f"""判断用户查询的意图类型。

用户查询: "{query}"

分类标准：

【闲聊对话】- 纯社交交流，不需要查找信息或使用工具：
• 问候寒暄："你好"、"吃了吗"、"最近怎么样"、"身体好吗"
• 感谢告别："谢谢"、"再见"、"辛苦了"
• 确认回应："好的"、"知道了"、"是的"
• 关怀闲聊："工作怎么样"、"今天心情如何"、"休息一下吧"
• 一般性询问："你是机器人吗"、"忙不忙"、"睡得好吗"

【任务请求】- 需要获取信息、执行操作或使用工具：
• 知识询问："谁是XX"、"什么是XX"、"如何做XX"
• 搜索请求："搜索XX"、"查找XX"、"帮我找XX"
• 工具使用："翻译XX"、"分析XX"、"生成XX"、"处理XX"
• 信息获取：包含明确的信息需求或疑问词

关键判断：
- 社交性质的对话 = 闲聊对话
- 需要查询信息或执行任务 = 任务请求

回答格式：只回答"闲聊对话"或"任务请求"。"""
        
        try:
            response = await self.llm.generate(prompt, max_tokens=20, temperature=0.0)
            result = response.strip()
            self.logger.debug(f"LLM检测结果: '{query}' -> '{result}'")
            return "任务请求" in result
        except Exception as e:
            self.logger.warning(f"LLM任务检测失败: {e}")
            return True  # 默认当作任务处理
    
    def _basic_fallback_detection(self, query: str) -> bool:
        """基于语义理解的回退判断（当LLM不可用时）"""
        query = query.strip()
        
        # 1. 长度分析：很短的查询更可能是闲聊
        if len(query) <= 3:
            return False
        
        # 2. 句式分析
        # 疑问句通常表示需要获取信息（任务）
        has_question_mark = '？' in query or '?' in query
        
        # 疑问词检测（明确的信息需求）
        question_words = ['什么', '谁', '哪里', '哪个', '怎么', '如何', '为什么', '多少', '几']
        has_question_word = any(word in query for word in question_words)
        
        # 任务动词（明确的操作请求）
        task_verbs = ['搜索', '查找', '查询', '帮我', '请', '分析', '处理', '生成', '创建', '翻译', '计算']
        has_task_verb = any(verb in query for verb in task_verbs)
        
        # 3. 社交性指标
        # 问候词
        greeting_words = ['你好', 'hi', 'hello', '早上好', '下午好', '晚上好']
        has_greeting = any(word in query for word in greeting_words)
        
        # 感谢词
        thanks_words = ['谢谢', 'thanks', '感谢']
        has_thanks = any(word in query for word in thanks_words)
        
        # 关怀询问（社交性质）
        care_patterns = ['怎么样', '好吗', '如何', '还好', '忙不忙', '累不累']
        has_care = any(pattern in query for pattern in care_patterns)
        
        # 4. 语境分析
        # 如果包含"你"且不是询问具体信息，更可能是社交对话
        has_you = '你' in query or 'You' in query.lower()
        
        # AI身份相关询问（社交性质） - 更精确的模式
        ai_identity_patterns = ['你是谁', '你是什么', '机器人吗', '你会什么', '你能做什么']
        has_ai_identity_question = any(pattern in query for pattern in ai_identity_patterns)
        
        # 日常生活询问
        daily_patterns = ['吃了', '睡了', '起床', '下班', '上班', '回家']
        has_daily = any(pattern in query for pattern in daily_patterns)
        
        # 5. 知识性询问检测（新增）
        # 检测是否是询问具体人物、事物、概念等的知识性问题
        knowledge_indicators = [
            # 历史人物、现代人物
            r'[\u4e00-\u9fff]{2,4}是谁',  # 中文名字+是谁
            r'谁是[\u4e00-\u9fff]{2,4}',  # 谁是+中文名字
            # 概念询问
            r'什么是[\u4e00-\u9fff]+',    # 什么是+概念
            r'[\u4e00-\u9fff]+是什么',    # 概念+是什么
            # 地点询问
            r'[\u4e00-\u9fff]+在哪里',    # 地点+在哪里
            r'哪里有[\u4e00-\u9fff]+',    # 哪里有+事物
        ]
        import re
        has_knowledge_question = any(re.search(pattern, query) for pattern in knowledge_indicators)
        
        # 6. 判断逻辑（优化后）
        # 明确的社交指标优先
        if has_greeting or has_thanks or has_daily:
            return False
        
        # AI身份询问判断为闲聊
        if has_ai_identity_question:
            return False
            
        # 关怀性询问：如果是对"你"的关怀询问，更可能是闲聊
        if has_you and has_care:
            return False
        
        # 知识性询问优先判断为任务（新增逻辑）
        if has_knowledge_question:
            return True
            
        # 明确的任务指标
        if has_question_word or has_task_verb:
            return True
        
        # 疑问句但没有明确疑问词的情况
        if has_question_mark:
            # 如果是简短的疑问且包含关怀词，倾向于闲聊
            if len(query) <= 10 and has_care:
                return False
            # 否则可能是任务
            return True
        
        # 默认：根据长度判断
        # 较长的语句更可能包含具体需求（任务）
        return len(query) > 8
    
    async def _handle_chat_mode(self, query: str, start_time: float) -> dict:
        """处理闲聊模式"""
        try:
            final_output = "你好！有什么可以帮助您的吗？"  # 默认回复
            
            if self.llm and hasattr(self.llm, 'generate'):
                try:
                    # 使用LLM进行友好回答
                    chat_prompt = f"""
你是一个友好、专业的AI助手。用户说: "{query}"

请给出自然、友好的回应。要求：
1. 保持简洁明了，不要过于冗长
2. 语气亲切自然，如同朋友间的对话
3. 如果用户是问候，要礼貌回应
4. 如果用户表达感谢，要谦逊回复
5. 如果用户询问你的能力，可以简单介绍你能帮助搜索信息、处理文件等

直接回复，不要格式化标记。
"""
                    response = await self.llm.generate(chat_prompt, max_tokens=100, temperature=0.7)
                    if response and response.strip():
                        final_output = response.strip()
                except Exception as e:
                    self.logger.warning(f"LLM闲聊回复失败，使用规则回复: {e}")
                    final_output = self._generate_rule_based_chat_response(query)
            else:
                # LLM不可用时，使用规则回复
                final_output = self._generate_rule_based_chat_response(query)
            
            return {
                "success": True,
                "final_output": final_output,
                "execution_steps": [],
                "step_count": 0,
                "error_count": 0,
                "mode": "chat",
                "execution_time": time.time() - start_time
            }
            
        except Exception as e:
            self.logger.warning(f"闲聊模式处理失败: {e}")
            return {
                "success": True,
                "final_output": "你好！有什么可以帮助您的吗？",
                "execution_steps": [],
                "step_count": 0,
                "error_count": 0,
                "mode": "chat",
                "execution_time": time.time() - start_time
            }
    
    def _generate_rule_based_chat_response(self, query: str) -> str:
        """基于规则生成聊天回复（不依赖LLM）"""
        query_lower = query.lower().strip()
        
        # 问候回复
        if any(greeting in query_lower for greeting in ['你好', 'hi', 'hello', '早上好', '下午好', '晚上好']):
            greetings = [
                '你好！很高兴见到您，有什么可以帮助您的吗？',
                '您好！我是AI助手，随时准备为您提供帮助。',
                '您好！有什么需要我协助的吗？'
            ]
            return greetings[len(query) % len(greetings)]
        
        # 感谢回复
        if any(thanks in query_lower for thanks in ['谢谢', 'thanks', '感谢']):
            thanks_responses = [
                '不客气！很高兴能帮到您。',
                '不用谢！这是我应该做的。',
                '您太客气了！有其他需要帮助的吗？'
            ]
            return thanks_responses[len(query) % len(thanks_responses)]
        
        # 告别回复
        if any(goodbye in query_lower for goodbye in ['再见', 'bye', '拜拜', 'goodbye']):
            goodbye_responses = [
                '再见！希望下次还能为您提供帮助。',
                '拜拜！有需要随时找我哦。',
                '再见！祝您一切顺利！'
            ]
            return goodbye_responses[len(query) % len(goodbye_responses)]
        
        # 状态询问
        if any(status in query_lower for status in ['怎么样', '还好吗', '忙不忙']):
            status_responses = [
                '我很好，谢谢关心！作为AI助手，我随时准备为您提供帮助。',
                '我状态很好！随时准备为您服务。有什么需要帮助的吗？',
                '我不会感到忙碌，随时都可以为您提供帮助！'
            ]
            return status_responses[len(query) % len(status_responses)]
        
        # 能力询问
        if any(capability in query_lower for capability in ['你是谁', '你会什么', '你能做什么', '机器人']):
            capability_responses = [
                '我是一个AI助手，可以帮您搜索信息、处理文件、回答问题等。有什么需要帮助的吗？',
                '我可以帮您搜索网络信息、处理各种文件、回答问题、进行数据分析等。有什么具体需要帮助的吗？',
                '我是您的AI助手，可以为您提供信息搜索、文件处理、问题解答等服务。告诉我您需要什么帮助吧！'
            ]
            return capability_responses[len(query) % len(capability_responses)]
        
        # 确认回复
        if any(confirm in query_lower for confirm in ['好的', 'ok', '是的', '对的', '嗯', '行']):
            return '好的！有什么其他需要帮助的吗？'
        
        # 否定回复
        if any(negative in query_lower for negative in ['不是', '不对', '不行', 'no']):
            return '好的，我明白了。有什么其他可以帮助您的吗？'
        
        # 默认友好回复
        default_responses = [
            '我明白了。作为AI助手，我可以帮您搜索信息、处理文件等。有什么具体需要帮助的吗？',
            '很高兴和您聊天！我可以为您提供各种帮助，比如搜索信息、回答问题等。',
            '感谢您的交流！我随时准备为您提供帮助，有什么需要的尽管说。'
        ]
        
        # 根据查询长度和内容选择合适的回复
        if len(query) <= 5:
            return default_responses[0]
        elif len(query) <= 15:
            return default_responses[1]
        else:
            return default_responses[2]
    
    async def _generate_plan(self, query: str, context: dict) -> List[dict]:
        """生成执行计划"""
        try:
            # 工具概览（便于人读）
            tool_list_text = self._format_tool_list()
            # 结构化工具定义（精确 schema 注入）
            tools_json_block = json.dumps(self._get_tools_definitions_for_prompt(), ensure_ascii=False, indent=2)
            # 非敏感环境提示（供LLM参考）
            env_hints_block = json.dumps(self._collect_non_sensitive_env_hints(), ensure_ascii=False, indent=2)
            
            prompt = f"""
你是一个智能任务规划助手。请根据用户查询和可用工具，生成详细的执行计划。

[用户上下文]
{json.dumps(context, ensure_ascii=False, indent=2)}

[可用工具（概览）]
{tool_list_text}

[可用工具（JSON，包含精确的入参与输出Schema）]
{tools_json_block}

[可用默认环境提示（非敏感）]
{env_hints_block}

[用户查询]
{query}

请生成JSON格式的执行计划，格式如下：
{{
  "steps": [
    {{
      "tool": "工具名称",
      "purpose": "执行目的描述",
      "dependencies": [依赖的步骤索引列表],
      "parameters": {{"参数名": "参数值"}},
      "output_path": "结果字段路径"
    }}
  ]
}}

注意事项：
1. 步骤之间可能存在依赖关系，用dependencies字段表示
2. output_path用于从前面步骤的结果中提取数据，使用JMESPath语法：
   - 标准做法：使用"data.primary"（所有工具的主要输出都在这里）
   - 特殊情况：如需其他数据可使用"data.secondary.字段名"或"message"
3. 确保所有必需的参数都有合适的值
4. 如果查询很简单，可以只用一个步骤

通用设计原则：
- 所有工具都遵循统一的输出格式，主要数据放在data.primary字段
- 依赖步骤通常使用output_path: "data.primary"提取上一步的主要输出
- 系统会根据目标工具的参数签名自动进行智能数据映射
- 工具间的数据传递完全基于标准化的输出结构，无需考虑具体工具特性
- 生成参数时必须严格使用目标工具的inputSchema中定义的参数名与类型，填充所有required参数。
- 如果依赖上一步的数据，请直接将其映射到目标工具的正确参数名（依据inputSchema）。
- 若必填参数缺失，请参考[可用默认环境提示]（例如 bucket_name 可使用 DEFAULT_BUCKET_NAME），并在parameters中补齐。

只返回JSON，不要其他说明文字。
"""
            
            # 调用LLM生成计划
            response = await self.llm.generate(prompt, max_tokens=2000)
            
            # 解析JSON响应
            try:
                # 清理响应，移除代码块标记
                cleaned_response = response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # 移除开头的```json
                if cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]  # 移除开头的```
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # 移除结尾的```
                cleaned_response = cleaned_response.strip()
                
                self.logger.debug(f"清理后的响应: {cleaned_response}")
                
                plan_data = json.loads(cleaned_response)
                steps = plan_data.get('steps', [])
                
                # 验证计划
                if self._validate_plan(steps):
                    self.logger.info(f"执行计划生成成功，共{len(steps)}个步骤")
                    return steps
                else:
                    self.logger.warning("生成的执行计划验证失败")
                    return []
                    
            except json.JSONDecodeError as e:
                self.logger.error(f"解析执行计划JSON失败: {e}")
                self.logger.debug(f"原始LLM响应: {response}")
                self.logger.debug(f"清理后响应: {cleaned_response}")
                return []
                
        except Exception as e:
            self.logger.error(f"生成执行计划失败: {e}")
            return []
    
    def _format_tool_list(self) -> str:
        """格式化工具列表"""
        tool_list = self.tool_registry.get_tool_list()
        formatted_tools = []
        
        # 处理工具列表，支持列表和字典两种格式
        if isinstance(tool_list, list):
            # 如果是列表格式
            for tool_info in tool_list:
                tool_name = tool_info.get('name', '未知工具')
                description = tool_info.get('description', '无描述')
                
                # 尝试从inputSchema获取参数信息
                parameters = tool_info.get('inputSchema', tool_info.get('parameters', {}))
                
                tool_desc = f"- {tool_name}: {description}"
                
                # 添加参数信息
                if parameters.get('properties'):
                    tool_desc += "\n  参数:"
                    for param_name, param_info in parameters['properties'].items():
                        param_type = param_info.get('type', 'string')
                        param_desc = param_info.get('description', '')
                        required = param_name in parameters.get('required', [])
                        required_mark = "*" if required else ""
                        tool_desc += f"\n    - {param_name}{required_mark} ({param_type}): {param_desc}"
                
                formatted_tools.append(tool_desc)
        else:
            # 如果是字典格式（向后兼容）
            for tool_name, tool_info in tool_list.items():
                description = tool_info.get('description', '无描述')
                parameters = tool_info.get('parameters', {})
                
                tool_desc = f"- {tool_name}: {description}"
                
                # 添加参数信息
                if parameters.get('properties'):
                    tool_desc += "\n  参数:"
                    for param_name, param_info in parameters['properties'].items():
                        param_type = param_info.get('type', 'string')
                        param_desc = param_info.get('description', '')
                        required = param_name in parameters.get('required', [])
                        required_mark = "*" if required else ""
                        tool_desc += f"\n    - {param_name}{required_mark} ({param_type}): {param_desc}"
            
                formatted_tools.append(tool_desc)
        
        return "\n".join(formatted_tools)

    def _get_tools_definitions_for_prompt(self) -> List[dict]:
        """以JSON可嵌入形式返回工具定义（包含精确的入参与输出Schema）。"""
        tools_for_prompt: List[Dict[str, Any]] = []
        try:
            tool_list = self.tool_registry.get_tool_list()
            if isinstance(tool_list, list):
                for tool in tool_list:
                    tools_for_prompt.append({
                        "name": tool.get("name"),
                        "description": tool.get("description", ""),
                        "inputSchema": tool.get("inputSchema", {
                            "type": "object", "properties": {}, "required": []
                        }),
                        "outputSchema": tool.get("outputSchema")
                    })
            else:
                for name, tool in tool_list.items():
                    tools_for_prompt.append({
                        "name": name,
                        "description": tool.get("description", ""),
                        "inputSchema": tool.get("parameters", {
                            "type": "object", "properties": {}, "required": []
                        }),
                        "outputSchema": tool.get("outputSchema")
                    })
        except Exception as e:
            self.logger.warning(f"获取工具定义失败: {e}")
        return tools_for_prompt

    def _collect_non_sensitive_env_hints(self) -> Dict[str, Any]:
        """收集用于LLM对齐的非敏感环境提示，例如默认bucket/endpoint等，不包含密钥。"""
        hints: Dict[str, Any] = {}
        try:
            # 非敏感：endpoint、默认bucket（若存在）
            endpoint = os.getenv("MINIO_ENDPOINT")
            default_bucket = os.getenv("BUCKET_NAME") or os.getenv("DEFAULT_BUCKET_NAME")
            if endpoint:
                hints["MINIO_ENDPOINT"] = endpoint
            if default_bucket:
                hints["DEFAULT_BUCKET_NAME"] = default_bucket
        except Exception:
            pass
        return hints
    
    def _validate_plan(self, steps: List[dict]) -> bool:
        """验证执行计划"""
        if not steps or not isinstance(steps, list):
            return False
        
        # 获取可用工具列表
        tool_list = self.tool_registry.get_tool_list()
        if isinstance(tool_list, list):
            available_tools = set(tool['name'] for tool in tool_list)
        else:
            available_tools = set(tool_list.keys())
        
        for i, step in enumerate(steps):
            # 检查必需字段
            if not isinstance(step, dict):
                return False
            
            if 'tool' not in step:
                self.logger.warning(f"步骤{i}缺少tool字段")
                return False
            
            # 检查工具是否存在
            tool_name = step['tool']
            if tool_name not in available_tools:
                self.logger.warning(f"步骤{i}使用了不存在的工具: {tool_name}")
                return False
            
            # 检查依赖关系
            dependencies = step.get('dependencies', [])
            if dependencies:
                for dep in dependencies:
                    if not isinstance(dep, int) or dep < 0 or dep >= i:
                        self.logger.warning(f"步骤{i}的依赖关系无效: {dep}")
                        return False
        
        return True
    
    async def _execute_plan(self, plan: List[dict], context: dict) -> dict:
        """执行计划"""
        results = {}
        execution_steps = []
        
        for i, step in enumerate(plan):
            step_start_time = time.time()
            
            try:
                # 解析依赖
                resolved_params = self._resolve_dependencies(step, results)
                
                # 合并参数
                final_params = {**step.get('parameters', {}), **resolved_params}

                # 基于Schema对齐与校验（包含一次可选的LLM纠正）。不再做任何模式/规则补全。
                self.logger.info(f"参数对齐前: tool={step['tool']} raw_params_keys={list(final_params.keys())}")
                final_params = await self._align_parameters_with_schema(step['tool'], final_params, context)
                self.logger.info(f"参数对齐后: tool={step['tool']} aligned_params={final_params}")
                
                self.logger.info(f"执行步骤{i+1}/{len(plan)}: {step['tool']}")
                
                # 执行工具
                result = await self.tool_executor.execute(
                    step['tool'],
                    final_params
                )
                # 记录工具返回的关键信息，便于定位错误
                try:
                    status_dbg = result.get('status') if isinstance(result, dict) else 'unknown'
                    msg_dbg = result.get('message') if isinstance(result, dict) else ''
                    err_dbg = result.get('error') if isinstance(result, dict) else ''
                    self.logger.info(f"工具返回摘要: tool={step['tool']} status={status_dbg} message={msg_dbg} error={err_dbg}")
                except Exception:
                    pass
                
                # 记录执行步骤
                execution_step = {
                    'step_index': i,
                    'tool_name': step['tool'],
                    'purpose': step.get('purpose', ''),
                    'input_params': final_params,
                    'output': result,
                    'execution_time': time.time() - step_start_time,
                    'status': 'success' if result and not isinstance(result, dict) or not result.get('error') else 'error'
                }
                
                execution_steps.append(execution_step)
                
                # 存储结果
                results[str(i)] = {
                    'tool': step['tool'],
                    'input': final_params,
                    'output': result,
                    'status': execution_step['status']
                }
                
                self.logger.info(f"步骤{i+1}执行完成: {execution_step['status']}")
                
            except Exception as e:
                self.logger.error(f"步骤{i+1}执行失败: {e}")
                
                execution_step = {
                    'step_index': i,
                    'tool_name': step['tool'],
                    'purpose': step.get('purpose', ''),
                    'input_params': step.get('parameters', {}),
                    'output': None,
                    'execution_time': time.time() - step_start_time,
                    'status': 'error',
                    'error': str(e)
                }
                
                execution_steps.append(execution_step)
                
                # 存储错误结果
                results[str(i)] = {
                    'tool': step['tool'],
                    'input': step.get('parameters', {}),
                    'output': None,
                    'status': 'error',
                    'error': str(e)
                }
        
        # 聚合结果
        return await self._aggregate_results(results, execution_steps)

    async def _align_parameters_with_schema(self, tool_name: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        将参数与工具的 inputSchema 对齐：
        1) 使用 inputSchema.properties 作为真值来源，重命名/重映射未知参数到最佳匹配参数
        2) 本地校验 required 与类型；若仍存在缺失或明显不匹配，调用LLM进行一次纠正
        3) 返回对齐后的参数
        """
        tool_def = self._get_tool_definition(tool_name)
        if not tool_def:
            return params

        input_schema = tool_def.get('inputSchema') or {"type": "object", "properties": {}, "required": []}
        properties: Dict[str, Any] = input_schema.get('properties', {}) or {}
        required: List[str] = input_schema.get('required', []) or []
        try:
            self.logger.info(
                f"Schema摘要: tool={tool_name} properties={list(properties.keys())} required={required} raw_params={params}"
            )
        except Exception:
            pass

        # 1) 已知/未知键分离（无模式匹配）
        normalized: Dict[str, Any] = {}
        unknown_params: Dict[str, Any] = {}
        for key, value in params.items():
            if key in properties:
                normalized[key] = value
            elif key != '__extracted_values':
                unknown_params[key] = value

        # 处理依赖提取的原始值（不做模式匹配）
        extracted_values = params.get('__extracted_values')

        # 若恰好缺一个必填参数，尝试用单一来源填充（确定性规则）
        missing_required_now = [r for r in required if r not in normalized]
        if len(missing_required_now) == 1:
            target_key = missing_required_now[0]
            # 优先使用 extracted_values
            if extracted_values is not None:
                normalized[target_key] = extracted_values
                self.logger.info(f"使用依赖输出填充唯一必填参数: {target_key}")
            # 其次若只有一个未知参数，也可确定性赋值
            elif len(unknown_params) == 1:
                only_key, only_val = next(iter(unknown_params.items()))
                normalized[target_key] = only_val
                self.logger.info(f"使用唯一未知参数填充必填参数: {target_key} <- {only_key}")
                unknown_params.pop(only_key, None)
        
        # 将未知参数以辅助字段传递，供LLM对齐
        if unknown_params or extracted_values is not None:
            normalized['__unknown_params'] = unknown_params if unknown_params else {}
            if extracted_values is not None:
                normalized['__extracted_values'] = extracted_values

        # 2) 本地校验与轻量纠正
        local_ok, local_fixed = self._validate_parameters_against_schema(properties, required, {k: v for k, v in normalized.items() if k in properties})
        if local_ok:
            # 如果还有未知/提取值，尝试用LLM做一次参数并入
            if normalized.get('__unknown_params') or normalized.get('__extracted_values'):
                try:
                    llm_fixed = await self._llm_refine_parameters(tool_def, normalized, context)
                    self.logger.info(f"LLM对齐输出(截断): tool={tool_name} raw={str(llm_fixed)[:400]}")
                    final_ok, final_params = self._validate_parameters_against_schema(properties, required, {k: v for k, v in llm_fixed.items() if k in properties})
                    if final_ok:
                        return final_params
                except Exception as e:
                    self.logger.warning(f"LLM参数合并失败，使用本地对齐: {e}")
            return local_fixed

        # 3) LLM 一次纠正（严格控制：只在必要时使用）
        try:
            if self.llm and hasattr(self.llm, 'generate'):
                # 传入包含未知/提取值的上下文让LLM对齐
                context_params = dict(normalized)
                context_params.update(local_fixed)
                llm_fixed = await self._llm_refine_parameters(tool_def, context_params, context)
                # 再次本地校验
                final_ok, final_params = self._validate_parameters_against_schema(properties, required, llm_fixed)
                if final_ok:
                    self.logger.info(f"参数已通过LLM纠正并对齐Schema: {tool_name}")
                    return final_params
                else:
                    # 记录缺失的必填项以便定位
                    missing_after = [r for r in required if r not in (final_params or {})]
                    self.logger.warning(f"LLM纠正后仍未通过本地校验: tool={tool_name} missing={missing_after}, 使用本地纠正结果")
                    return local_fixed
        except Exception as e:
            self.logger.warning(f"LLM参数纠正失败，使用本地纠正结果: {e}")

        return local_fixed

    def _get_tool_definition(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """从工具注册表获取单个工具的定义（含 input/output schema 与描述）。"""
        try:
            tool_list = self.tool_registry.get_tool_list()
            if isinstance(tool_list, list):
                for tool in tool_list:
                    if tool.get('name') == tool_name:
                        return {
                            'name': tool.get('name'),
                            'description': tool.get('description', ''),
                            'inputSchema': tool.get('inputSchema', {"type": "object", "properties": {}, "required": []}),
                            'outputSchema': tool.get('outputSchema')
                        }
            else:
                # 兼容字典格式
                if tool_name in tool_list:
                    tool = tool_list[tool_name]
                    return {
                        'name': tool_name,
                        'description': tool.get('description', ''),
                        'inputSchema': tool.get('parameters', {"type": "object", "properties": {}, "required": []}),
                        'outputSchema': tool.get('outputSchema')
                    }
        except Exception as e:
            self.logger.warning(f"获取工具定义失败: {e}")
        return None

    def _validate_parameters_against_schema(self, properties: Dict[str, Any], required: List[str], params: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """轻量级本地校验：确保required存在、类型大致匹配，并尝试简单类型纠正。"""
        fixed = dict(params)
        # 检查必填
        missing = [r for r in required if r not in fixed]
        # 类型校验与简单纠正
        for name, prop in (properties or {}).items():
            if name not in fixed:
                continue
            expected_type = (prop or {}).get('type')
            value = fixed[name]
            try:
                if expected_type == 'integer' and isinstance(value, str) and value.isdigit():
                    fixed[name] = int(value)
                elif expected_type == 'number' and isinstance(value, str):
                    try:
                        fixed[name] = float(value)
                    except Exception:
                        pass
                elif expected_type == 'array' and isinstance(value, str):
                    # 尝试解析JSON数组格式
                    try:
                        if value.strip().startswith('[') and value.strip().endswith(']'):
                            # 尝试安全解析JSON/Python数组格式
                            parsed = ast.literal_eval(value.strip())
                            if isinstance(parsed, (list, tuple)):
                                fixed[name] = list(parsed)
                            else:
                                # 回退到逗号分割
                                fixed[name] = [v.strip() for v in value.split(',') if v.strip()]
                        else:
                            # 逗号分割
                            fixed[name] = [v.strip() for v in value.split(',') if v.strip()]
                    except (ValueError, SyntaxError):
                        # 解析失败，回退到逗号分割
                        fixed[name] = [v.strip() for v in value.split(',') if v.strip()]
                elif expected_type == 'boolean' and isinstance(value, str):
                    lowered = value.strip().lower()
                    if lowered in ['true', '1', 'yes', 'y']:
                        fixed[name] = True
                    elif lowered in ['false', '0', 'no', 'n']:
                        fixed[name] = False
            except Exception:
                # 保持原值，交给后续LLM或工具自身报错
                pass

        # 再次计算缺失
        missing = [r for r in required if r not in fixed]
        if missing:
            return False, fixed
        return True, fixed

    async def _llm_refine_parameters(self, tool_def: Dict[str, Any], params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用LLM根据 inputSchema 纠正参数。严格要求只返回JSON对象（参数字典），键必须为inputSchema.properties中定义的键。
        """
        name = tool_def.get('name')
        description = tool_def.get('description', '')
        input_schema = tool_def.get('inputSchema', {"type": "object", "properties": {}, "required": []})
        env_hints = self._collect_non_sensitive_env_hints()
        prompt = f"""
你是参数映射与校验助手。目标是为工具"{name}" 生成与其 inputSchema 完全一致的参数字典。

[工具描述]
{description}

[inputSchema]
{json.dumps(input_schema, ensure_ascii=False, indent=2)}

[当前参数]
{json.dumps(params, ensure_ascii=False, indent=2)}

[环境提示（非敏感，仅供参考）]
{json.dumps(env_hints, ensure_ascii=False, indent=2)}

注意：
- 仅输出JSON对象，不要任何说明文字；
- 键名必须严格来自 inputSchema.properties 的键，不能引入新键；
- 若存在辅助字段如 "__unknown_params"、"__extracted_values"，请仅将其作为参考，将其中的值合理归并进 Schema 定义的键；
- 若确实无法提供某必填值，可留空字符串、空数组或 null；
- 严格符合JSON格式。
"""
        try:
            response = await self.llm.generate(prompt, max_tokens=400, temperature=0.0)
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            fixed = json.loads(cleaned)
            if isinstance(fixed, dict):
                return fixed
        except Exception as e:
            self.logger.warning(f"LLM参数纠正解析失败: {e}")
        return params
    
    def _resolve_dependencies(self, step: dict, results: dict) -> dict:
        """解析依赖关系（无模式匹配）：
        - 优先由LLM在plan的parameters里给出正确参数；
        - 若存在依赖，仅在"目标工具恰好缺少且只有一个必填参数"时，直接将提取值赋给该参数；
        - 其他情况将原始依赖值放入保留键 '__extracted_values'，供后续 LLM 参数对齐阶段使用。
        """
        resolved: Dict[str, Any] = {}
        dependencies = step.get('dependencies', [])
        if not dependencies:
            return resolved

        # 准备工具schema信息
        tool_name = step.get('tool', '')
        tool_def = self._get_tool_definition(tool_name) or {}
        input_schema = tool_def.get('inputSchema') or {"type": "object", "properties": {}, "required": []}
        properties: Dict[str, Any] = input_schema.get('properties', {}) or {}
        required: List[str] = input_schema.get('required', []) or []

        extracted_values: List[Any] = []

        for dep_index in dependencies:
            dep_result = results.get(str(dep_index), {})
            dep_output = dep_result.get('output', {})

            # 使用output_path提取特定数据
            output_path = step.get('output_path')
            if output_path:
                # JsonPath 前缀转 JMESPath
                if output_path.startswith('$.'):
                    output_path = output_path[2:]
                    self.logger.info(f"将JsonPath语法 '{step['output_path']}' 转换为JMESPath语法 '{output_path}'")
                elif output_path.startswith('$'):
                    output_path = output_path[1:]
                    self.logger.info(f"将JsonPath语法 '{step['output_path']}' 转换为JMESPath语法 '{output_path}'")
                try:
                    value = jmespath.search(output_path, dep_output)
                except Exception as e:
                    self.logger.warning(f"提取依赖数据失败，路径: '{output_path}', 错误: {e}")
                    value = None
            else:
                # 默认 data.primary
                value = dep_output.get('data', {}).get('primary') if isinstance(dep_output, dict) else None

            if value is not None:
                extracted_values.append(value)

        if not extracted_values:
            return resolved

        # 仅当"恰好缺一个必填参数"时，直接赋值（确定性规则，无模式匹配）
        existing_keys = set((step.get('parameters') or {}).keys()) | set(resolved.keys())
        missing_required = [r for r in required if r not in existing_keys]
        if len(missing_required) == 1:
            resolved[missing_required[0]] = extracted_values[0] if len(extracted_values) == 1 else extracted_values
            self.logger.info(f"将依赖输出赋给唯一缺失的必填参数: {missing_required[0]}")
        else:
            # 交由后续 LLM 阶段对齐
            resolved['__extracted_values'] = extracted_values
            self.logger.info("已收集依赖输出，交由LLM在参数对齐阶段处理")

        return resolved
     
    def _get_tool_parameter_info(self, tool_name: str) -> dict:
        """兼容方法：返回 inputSchema.properties。"""
        try:
            tool_def = self._get_tool_definition(tool_name)
            if not tool_def:
                return {}
            schema = tool_def.get('inputSchema') or {}
            return (schema.get('properties') or {}) if isinstance(schema, dict) else {}
        except Exception as e:
            self.logger.warning(f"获取工具参数信息失败: {e}")
        return {}
    
    async def _aggregate_results(self, results: dict, execution_steps: List[dict]) -> dict:
        """聚合执行结果"""
        # 检查是否有错误
        has_errors = any(step['status'] == 'error' for step in execution_steps)
        
        # 智能处理结果，提取有价值的信息
        final_output = await self._extract_meaningful_output(execution_steps)
        
        if not final_output:
            if has_errors:
                final_output = "任务执行过程中遇到错误，请检查执行步骤详情。"
            else:
                final_output = "任务执行完成，但没有生成有效输出。"
        
        return {
            "success": not has_errors,
            "final_output": final_output,
            "execution_steps": execution_steps,
            "step_count": len(execution_steps),
            "error_count": sum(1 for step in execution_steps if step['status'] == 'error')
        }
    
    async def _extract_meaningful_output(self, execution_steps: List[dict]) -> str:
        """从执行步骤中提取有意义的输出"""
        
        # 获取最后一个成功步骤
        last_successful_step = None
        for step in reversed(execution_steps):
            if step['status'] == 'success' and step.get('output'):
                last_successful_step = step
                break
        
        if not last_successful_step:
            return ""
        
        tool_name = last_successful_step.get('tool_name', '')
        output = last_successful_step.get('output', {})
        input_params = last_successful_step.get('input_params', {})
        
        # 首先尝试通用格式化
        formatted_result = self._format_tool_output(output, tool_name, input_params)
        
        # 如果结果包含丰富的数据且有LLM，使用LLM进行智能总结
        if self._should_use_llm_summary(output, formatted_result):
            try:
                llm_summary = await self._generate_llm_summary(output, input_params, tool_name)
                if llm_summary:
                    # 对LLM总结结果也应用链接优化
                    return self._format_output_with_links(llm_summary)
            except Exception as e:
                self.logger.warning(f"LLM总结失败，使用格式化结果: {e}")
        
        # 对格式化结果应用链接优化
        return self._format_output_with_links(formatted_result)
    
    def _should_use_llm_summary(self, output: dict, formatted_result: str) -> bool:
        """判断是否应该使用LLM进行总结"""
        # 检查是否有LLM客户端可用
        has_llm = self.llm and hasattr(self.llm, 'generate')
        if not has_llm:
            return False
        
        # 检查是否有丰富的数据结构
        has_rich_data = (
            'data' in output and 'primary' in output.get('data', {}) and 
            isinstance(output['data']['primary'], list) and 
            len(output['data']['primary']) > 0
        )
        
        return has_rich_data
    
    async def _generate_llm_summary(self, output: dict, input_params: dict, tool_name: str) -> str:
        """使用LLM生成智能总结"""
        try:
            # 提取用户的原始查询
            user_query = input_params.get('query', '')
            
            # 提取搜索结果数据
            search_results = []
            if 'data' in output and 'primary' in output['data']:
                for item in output['data']['primary'][:3]:  # 只取前3个结果
                    if isinstance(item, dict):
                        title = item.get('title', '')
                        snippet = item.get('snippet', item.get('description', ''))
                        if title and snippet:
                            search_results.append({
                                'title': self._clean_text(title)[:600],  # 限制长度
                                'content': self._clean_text(snippet)[:600]
                            })
            
            if not search_results:
                return ""
            
            # 构建通用的智能总结提示词
            prompt = f"""
你是一个信息提取专家，需要从搜索结果中为用户查询"{user_query}"提供精准、简洁的回答。

搜索结果：
"""
            
            for i, result in enumerate(search_results, 1):
                prompt += f"{i}. {result['title']}\n   {result['content']}\n\n"
            
            prompt += f"""
任务要求：
1. 仔细分析用户查询"{user_query}"的核心需求
2. 从搜索结果中提取最直接回答用户问题的关键信息
3. 过滤掉重复、冗余、无关的内容
4. 生成一个结构清晰、语言流畅的完整回答（300-600字）

回答原则：
- 直接回答用户问题，突出核心信息
- 提供完整的背景信息和关键细节
- 包含具体的数值、时间、地点等关键数据
- 确保信息完整性，避免突然截断
- 如果是人物查询，包含生平、主要成就、历史地位等
- 如果是概念查询，包含定义、原理、应用等
- 语言简洁明了，但信息要充分完整
- 不要说"根据搜索结果"之类的套话

请提供完整而详细的回答：
"""
            
            # 调用LLM
            response = await self.llm.generate(prompt, max_tokens=600, temperature=0.3)
            
            if response and len(response.strip()) > 10:
                # 检查回答是否被截断
                if self._is_response_truncated(response):
                    self.logger.warning("检测到LLM回答可能被截断，尝试重新生成")
                    # 尝试用更高的token限制重新生成
                    extended_response = await self.llm.generate(prompt, max_tokens=600, temperature=0.3)
                    if extended_response and len(extended_response.strip()) > len(response.strip()):
                        return extended_response.strip()
                
                return response.strip()
            
        except Exception as e:
            self.logger.warning(f"LLM总结生成失败: {e}")
        
        return ""
    
    def _format_tool_output(self, output: dict, tool_name: str = "", input_params: dict = None) -> str:
        """通用的工具输出格式化"""
        if input_params is None:
            input_params = {}
            
        try:
            # 1. 优先处理结构化数据（如data.primary等），避免被通用message遮蔽
            structured_result = self._extract_structured_result(output, input_params)
            if structured_result:
                return structured_result

            # 2. 其次尝试提取直接的文本结果（跳过通用状态消息）
            direct_result = self._extract_direct_result(output)
            if direct_result and not self._is_generic_message(direct_result):
                return direct_result
            
            # 3. 如果是列表数据，格式化为摘要
            list_result = self._extract_list_result(output)
            if list_result:
                return list_result
            
            # 4. 最后兜底：返回简化的JSON或更友好的完成提示
            return self._extract_fallback_result(output, direct_result)
            
        except Exception as e:
            self.logger.warning(f"格式化工具输出失败: {e}")
            return "任务执行完成。"
    
    def _is_generic_message(self, message: str) -> bool:
        """判断是否是通用的状态消息"""
        generic_patterns = [
            r'搜索成功.*找到.*结果',
            r'.*执行完成',
            r'.*成功',
            r'任务.*完成'
        ]
        
        message_lower = message.lower()
        return any(re.search(pattern, message_lower) for pattern in generic_patterns)
    
    def _extract_direct_result(self, output: dict) -> str:
        """提取直接的文本结果"""
        # 优先级顺序：message > result(string) > content
        for key in ['message', 'content']:
            if key in output and isinstance(output[key], str) and output[key].strip():
                return output[key].strip()
        
        # 检查result字段
        if 'result' in output:
            result = output['result']
            if isinstance(result, str) and result.strip():
                return result.strip()
        
        return ""
    
    def _extract_structured_result(self, output: dict, input_params: dict = None) -> str:
        """提取结构化数据结果"""
        if input_params is None:
            input_params = {}
        
        # 优先处理通用的下载链接字段
        download_result = self._extract_download_links(output)
        if download_result:
            return download_result
            
        # 处理包含data字段的复杂结构
        if 'data' in output and isinstance(output['data'], dict):
            data = output['data']
            
            # 检查是否有primary数据（通常是搜索结果）
            if 'primary' in data and isinstance(data['primary'], list):
                return self._format_search_results_intelligently(data['primary'], data, input_params)
            
            # 检查是否有其他有意义的数据字段
            for key in ['results', 'items', 'entries', 'content']:
                if key in data and isinstance(data[key], (list, dict)):
                    return self._format_data_field(data[key], key)
        
        # 处理直接包含results的情况
        if 'result' in output and isinstance(output['result'], dict):
            result_dict = output['result']
            # 寻找文本字段
            for text_key in ['text', 'content', 'description', 'summary', 'answer']:
                if text_key in result_dict and isinstance(result_dict[text_key], str):
                    return result_dict[text_key].strip()
        
        return ""
    
    def _extract_download_links(self, output: dict) -> str:
        """通用的下载链接提取逻辑"""
        download_links = []
        
        # 检查 data.primary 中的下载链接（优先）
        if 'data' in output and isinstance(output['data'], dict):
            primary = output['data'].get('primary')
            if primary:
                if isinstance(primary, list):
                    # 列表格式：多个文件
                    for item in primary:
                        if isinstance(item, dict) and item.get('download_url'):
                            download_links.append(item)
                elif isinstance(primary, dict) and primary.get('download_url'):
                    # 单个文件
                    download_links.append(primary)
        
        # 检查顶层的 download_url
        if not download_links and output.get('download_url'):
            download_links.append(output)
        
        # 检查 results 中的下载链接
        if not download_links and 'results' in output and isinstance(output['results'], list):
            for item in output['results']:
                if isinstance(item, dict) and item.get('download_url'):
                    download_links.append(item)
        
        if not download_links:
            return ""
        
        return self._format_download_links(download_links)
    
    def _format_download_links(self, download_links: list) -> str:
        """格式化下载链接信息为Markdown链接格式"""
        if not download_links:
            return ""
        
        # 统计信息
        total_count = len(download_links)
        
        # 构建消息
        message_parts = []
        
        if total_count == 1:
            link_info = download_links[0]
            file_name = link_info.get('name') or link_info.get('original_name') or link_info.get('file_name') or '文件'
            download_url = link_info.get('download_url')
            expires_in = link_info.get('expires_in_seconds', 0)
            
            # 获取文件图标
            file_icon = self._get_file_icon(file_name)
            
            message_parts.append(f"✅ 文件上传成功")
            message_parts.append("")
            message_parts.append(f"📄 文件列表:")
            # 使用Markdown链接格式：[文件名](下载链接)
            message_parts.append(f"1. {file_icon} [{file_name}]({download_url})")
            
            if expires_in > 0:
                time_str = self._format_expiry_time(expires_in)
                message_parts.append(f"   ⏰ 有效期: {time_str}")
        else:
            message_parts.append(f"✅ 成功上传 {total_count} 个文件")
            message_parts.append("")
            message_parts.append("📁 文件列表:")
            
            for i, link_info in enumerate(download_links, 1):
                file_name = link_info.get('name') or link_info.get('original_name') or link_info.get('file_name') or f'文件_{i}'
                download_url = link_info.get('download_url')
                expires_in = link_info.get('expires_in_seconds', 0)
                
                # 获取文件图标
                file_icon = self._get_file_icon(file_name)
                
                # 使用Markdown链接格式
                message_parts.append(f"{i}. {file_icon} [{file_name}]({download_url})")
                
                if expires_in > 0:
                    time_str = self._format_expiry_time(expires_in)
                    message_parts.append(f"   ⏰ 有效期: {time_str}")
        
        return "\n".join(message_parts)
    
    def _get_file_icon(self, file_name: str) -> str:
        """根据文件扩展名返回对应的图标"""
        if not file_name:
            return "📄"
        
        # 获取文件扩展名
        extension = file_name.lower().split('.')[-1] if '.' in file_name else ''
        
        # 文件类型图标映射
        icon_mapping = {
            # 图片文件
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'bmp': '🖼️', 
            'svg': '🖼️', 'webp': '🖼️', 'ico': '🖼️', 'tiff': '🖼️', 'tif': '🖼️',
            
            # 文档文件
            'pdf': '📕', 'doc': '📘', 'docx': '📘', 'xls': '📗', 'xlsx': '📗',
            'ppt': '📙', 'pptx': '📙', 'txt': '📄', 'rtf': '📄',
            
            # 代码文件
            'js': '📜', 'ts': '📜', 'py': '📜', 'java': '📜', 'cpp': '📜', 
            'c': '📜', 'html': '📜', 'css': '📜', 'json': '📜', 'xml': '📜',
            'sql': '📜', 'sh': '📜', 'bat': '📜', 'php': '📜', 'rb': '📜',
            
            # 压缩文件
            'zip': '🗜️', 'rar': '🗜️', '7z': '🗜️', 'tar': '🗜️', 'gz': '🗜️',
            'bz2': '🗜️', 'xz': '🗜️',
            
            # 音频文件
            'mp3': '🎵', 'wav': '🎵', 'flac': '🎵', 'aac': '🎵', 'ogg': '🎵',
            'wma': '🎵', 'm4a': '🎵',
            
            # 视频文件
            'mp4': '🎬', 'avi': '🎬', 'mkv': '🎬', 'mov': '🎬', 'wmv': '🎬',
            'flv': '🎬', 'webm': '🎬', 'm4v': '🎬',
            
            # 其他常见格式
            'csv': '📊', 'log': '📝', 'md': '📋', 'yml': '⚙️', 'yaml': '⚙️',
            'ini': '⚙️', 'conf': '⚙️', 'cfg': '⚙️'
        }
        
        return icon_mapping.get(extension, '📄')  # 默认文档图标
    
    def _format_expiry_time(self, expires_in_seconds: int) -> str:
        """格式化过期时间"""
        if expires_in_seconds <= 0:
            return "永久"
        
        hours = expires_in_seconds // 3600
        minutes = (expires_in_seconds % 3600) // 60
        
        if hours > 24:
            days = hours // 24
            return f"{days}天"
        elif hours > 0:
            return f"{hours}小时{minutes}分钟"
        else:
            return f"{minutes}分钟"
    
    def _format_search_results_intelligently(self, primary_data: list, context: dict, input_params: dict) -> str:
        """智能格式化搜索结果"""
        if not primary_data:
            return "未找到相关结果。"
        
        user_query = input_params.get('query', '')
        
        # 通用格式化：基于数据类型而非具体用途
        return self._format_primary_data_universally(primary_data, context, user_query)
    
    def _format_primary_data_universally(self, primary_data: list, context: dict, user_query: str) -> str:
        """通用的主要数据格式化"""
        if not primary_data:
            return "没有生成数据。"
        
        # 获取统计信息
        counts = context.get('counts', {})
        total = counts.get('total', len(primary_data))
        successful = counts.get('successful', len(primary_data))
        failed = counts.get('failed', 0)
        
        # 基于数据类型进行通用格式化
        if isinstance(primary_data[0], str):
            return self._format_string_list(primary_data, counts, total, successful, failed)
        elif isinstance(primary_data[0], dict):
            return self._format_dict_list(primary_data, counts, total, successful, failed)
        else:
            return f"处理完成，生成了 {len(primary_data)} 项数据。"
    
    def _format_string_list(self, strings: list, counts: dict, total: int, successful: int, failed: int) -> str:
        """格式化字符串列表（URL、文件路径等）"""
        if len(strings) == 1:
            return f"处理完成！结果：{strings[0]}"
        
        # 构建统计信息
        stats = f"处理完成，共 {successful} 项"
        if failed > 0:
            stats += f"（失败 {failed} 项）"
        
        # 显示前几项结果
        display_count = min(3, len(strings))
        result_list = "\n".join(f"{i+1}. {strings[i]}" for i in range(display_count))
        
        if len(strings) > display_count:
            result_list += f"\n... 还有 {len(strings) - display_count} 项"
        
        return f"{stats}\n\n结果列表：\n{result_list}"
    
    def _format_dict_list(self, dicts: list, counts: dict, total: int, successful: int, failed: int) -> str:
        """格式化字典列表（搜索结果、结构化数据等）"""
        # 尝试从第一个结果中提取关键信息
        first_result = dicts[0] if dicts else None
        if first_result and isinstance(first_result, dict):
            title = first_result.get('title', '')
            snippet = first_result.get('snippet', first_result.get('description', ''))
            
            # 清理文本
            title = self._clean_text(title)
            snippet = self._clean_text(snippet)
            
            # 尝试提取结构化信息
            extracted_info = self._extract_structured_info_from_text(title + ' ' + snippet, "")
            
            if extracted_info:
                return extracted_info
        
        # 如果无法提取结构化信息，返回格式化的搜索结果摘要
        # 构造context字典
        context = {'counts': counts}
        return self._format_primary_data(dicts, context)
    
    def _extract_structured_info_from_text(self, text: str, query: str) -> str:
        """从文本中提取结构化信息"""
        # 简化：直接返回空，让主要的LLM总结方法处理所有逻辑
        return ""
    
    def _extract_fallback_result(self, output: dict, direct_result: str = "") -> str:
        """兜底的结果提取"""
        # 如果有直接结果但是是通用消息，尝试提供更多信息
        if direct_result and self._is_generic_message(direct_result):
            # 尝试从metadata获取更多信息
            if 'metadata' in output and 'tool_name' in output['metadata']:
                tool_name = output['metadata']['tool_name']
                if 'parameters' in output['metadata']:
                    params = output['metadata']['parameters']
                    if 'query' in params:
                        return f"✅ 已完成\"{params['query']}\"的查询"
                return f"✅ {tool_name} 执行完成"
        
        # 如果有直接结果，返回它
        if direct_result:
            return direct_result
        
        # 最后的尝试：如果有metadata，显示一个简单的完成消息
        if 'metadata' in output and 'tool_name' in output['metadata']:
            tool_name = output['metadata']['tool_name']
            return f"✅ {tool_name} 执行完成"
        
        # 如果什么都没有，但有任何内容，简化显示
        if output:
            # 过滤掉过于复杂或冗长的字段
            simple_info = {}
            for key, value in output.items():
                if key in ['status', 'message', 'result'] and isinstance(value, (str, int, float, bool)):
                    if isinstance(value, str) and len(value) < 600:
                        simple_info[key] = value
                    elif not isinstance(value, str):
                        simple_info[key] = value
            
            if simple_info:
                return json.dumps(simple_info, ensure_ascii=False, indent=2)
        
        return "任务执行完成。"
    
    def _format_primary_data(self, primary_data: list, context: dict) -> str:
        """格式化主要数据列表（如搜索结果）"""
        if not primary_data:
            return "未找到相关结果。"
        
        formatted_items = []
        max_items = min(3, len(primary_data))  # 最多显示3个结果
        
        for i, item in enumerate(primary_data[:max_items], 1):
            if isinstance(item, dict):
                # 提取标题和描述
                title = item.get('title', '').strip()
                description = item.get('snippet', item.get('description', item.get('content', ''))).strip()
                
                # 清理文本
                title = self._clean_text(title)
                description = self._clean_text(description)
                
                if title:
                    # 限制描述长度
                    if description and len(description) > 600:
                        description = description[:600] + "..."
                    
                    if description:
                        formatted_items.append(f"{i}. {title}\n   {description}")
                    else:
                        formatted_items.append(f"{i}. {title}")
        
        if formatted_items:
            result_text = "📋 结果摘要：\n\n" + "\n\n".join(formatted_items)
            
            # 添加统计信息
            if 'counts' in context:
                total = context['counts'].get('total', len(primary_data))
                result_text += f"\n\n📊 共找到 {total} 个结果"
            
            return result_text
        
        return "找到结果，但内容为空。"
    
    def _format_data_field(self, data, field_name: str) -> str:
        """格式化数据字段"""
        if isinstance(data, list):
            if not data:
                return f"未找到{field_name}数据。"
            
            # 如果是字符串列表，直接拼接
            if all(isinstance(item, str) for item in data):
                return "\n".join(f"• {item}" for item in data[:5])  # 最多5个
            
            # 如果是对象列表，提取关键信息
            items = []
            for i, item in enumerate(data[:3], 1):
                if isinstance(item, dict):
                    # 尝试找到描述性字段
                    for key in ['name', 'title', 'description', 'content', 'text']:
                        if key in item and isinstance(item[key], str):
                            items.append(f"{i}. {item[key]}")
                            break
                    else:
                        # 如果没有找到描述性字段，使用第一个字符串值
                        for value in item.values():
                            if isinstance(value, str) and len(value) < 600:
                                items.append(f"{i}. {value}")
                                break
            
            return "\n".join(items) if items else f"{field_name}数据处理完成。"
        
        elif isinstance(data, dict):
            # 对于字典，提取关键的键值对
            important_pairs = []
            for key, value in data.items():
                if isinstance(value, (str, int, float)) and str(value).strip():
                    # 只显示重要的、简短的信息
                    if len(str(value)) < 600:
                        important_pairs.append(f"{key}: {value}")
            
            if important_pairs:
                return "\n".join(important_pairs[:5])  # 最多5个键值对
        
        return f"{field_name}数据已获取。"
    
    def _extract_list_result(self, output: dict) -> str:
        """处理列表类型的结果"""
        # 检查顶层是否直接是列表结构
        if 'result' in output and isinstance(output['result'], list):
            result_list = output['result']
            return self._format_data_field(result_list, "结果")
        
        return ""
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
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

    def _is_response_truncated(self, response: str) -> bool:
        """检测回答是否被截断"""
        if not response:
            return False
        
        response = response.strip()
        
        # 检查是否以不完整的句子结尾
        truncation_indicators = [
            # 以连接词结尾（表示句子未完成）
            r'[，,]\s*$',
            r'(而且|并且|以及|与|和|或|然后|接着|后来|因此|所以|但是|不过|可是)\s*$',
            r'(的|在|为|从|向|到|由|被|把|对|关于)\s*$',
            # 以不完整的数字/年份结尾
            r'\d{1,3}$',  # 单独的不完整数字
            r'前\d*$',    # "前XX"未完成
            r'公元$',     # "公元"后面应该有年份
            # 以动词原形结尾（通常后面还有宾语）
            r'(是|在|有|成为|担任|参与|支持|反对|建立|创立|发生|担当)\s*$',
            # 其他常见的截断模式
            r'[。！？][^。！？]*[，,]\s*$',  # 句号后又有逗号结尾
        ]
        
        for pattern in truncation_indicators:
            if re.search(pattern, response):
                return True
        
        # 检查最后一句话是否过短（可能被截断）
        sentences = re.split(r'[。！？.!?]', response)
        if sentences:
            last_sentence = sentences[-1].strip()
            # 如果最后一句话很短且不是完整的表达，可能被截断
            if 1 < len(last_sentence) < 10 and not re.match(r'^(是的|对的|不是|确实|当然)$', last_sentence):
                return True
        
        return False 

    def _format_output_with_links(self, text: str) -> str:
        """
        通用的输出链接格式化方法
        将文本中的各种链接转换为Markdown格式，提供更好的用户体验
        """
        if not text or not isinstance(text, str):
            return text
        
        import re
        
        # 1. 处理已经存在的Markdown链接（保持不变）
        markdown_link_pattern = r'\[([^\]]+)\]\([^\)]+\)'
        existing_links = re.findall(markdown_link_pattern, text)
        
        # 2. 处理裸露的HTTP/HTTPS链接（不在Markdown格式中的）
        # 先保护已有的Markdown链接
        protected_text = text
        placeholders = {}
        
        # 保护现有的Markdown链接
        for i, match in enumerate(re.finditer(markdown_link_pattern, text)):
            placeholder = f"__PROTECTED_LINK_{i}__"
            placeholders[placeholder] = match.group(0)
            protected_text = protected_text.replace(match.group(0), placeholder, 1)
        
        # 匹配裸露的链接
        url_pattern = r'(?<![\[\(])(https?://[^\s\)]+)(?![\]\)])'
        
        def replace_bare_url(match):
            url = match.group(1)
            # 智能提取链接的友好名称
            friendly_name = self._extract_friendly_link_name(url)
            return f"[{friendly_name}]({url})"
        
        # 替换裸露的链接
        protected_text = re.sub(url_pattern, replace_bare_url, protected_text)
        
        # 恢复保护的链接
        for placeholder, original_link in placeholders.items():
            protected_text = protected_text.replace(placeholder, original_link)
        
        return protected_text
    
    def _extract_friendly_link_name(self, url: str) -> str:
        """从URL中提取友好的链接名称"""
        try:
            parsed = urllib.parse.urlparse(url)
            
            # 处理MinIO等对象存储链接
            if 'minio' in parsed.netloc.lower() or '.s3.' in parsed.netloc.lower():
                # 从路径中提取文件名
                path_parts = parsed.path.strip('/').split('/')
                if path_parts and path_parts[-1]:
                    filename = path_parts[-1]
                    # 移除查询参数中的时间戳等
                    if '?' in filename:
                        filename = filename.split('?')[0]
                    return filename
                return "下载文件"
            
            # 处理一般的文件下载链接
            path = parsed.path.strip('/')
            if path:
                path_parts = path.split('/')
                filename = path_parts[-1]
                
                # 如果文件名包含文件扩展名，使用文件名
                if '.' in filename and len(filename.split('.')[-1]) <= 5:
                    return filename
                
                # 否则使用最后两个路径部分
                if len(path_parts) >= 2:
                    return f"{path_parts[-2]}/{filename}"
                
                return filename
            
            # 使用域名作为友好名称
            domain = parsed.netloc.replace('www.', '')
            return domain or "链接"
            
        except Exception:
            # 如果URL解析失败，尝试从URL末尾提取可能的文件名
            url_parts = url.split('/')
            if url_parts:
                last_part = url_parts[-1].split('?')[0]  # 移除查询参数
                if last_part and '.' in last_part:
                    return last_part
            
            return "链接"