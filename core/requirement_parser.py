import os
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from .tool_category_manager import ToolCategoryManager

class RequirementParserError(Exception):
    """自定义异常：需求解析相关错误"""
    pass

class RequirementParser:
    def __init__(
        self,
        use_llm: bool = True,
        llm_model: str = None,
        api_key: str = None,
        api_base: str = None,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        category_manager: Optional[ToolCategoryManager] = None
    ):
        self.logger = logging.getLogger("RequirementParser")
        self.use_llm = use_llm
        self.llm_model = llm_model or os.environ.get("OPENAI_MODEL", "gpt-4o")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.api_base = api_base or os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.available_tools = available_tools or []
        self.category_manager = category_manager or ToolCategoryManager()

    def parse(self, user_input: str) -> Dict[str, Any]:
        """
        解析用户需求，输出结构化JSON，支持智能节点衔接
        """
        try:
            self.logger.info(f"===LLM解析开始: {user_input}")
            
            # 首先尝试使用LLM进行解析（包括闲聊判断）
            if self.use_llm or self.api_key:
                try:
                    import openai
                    client = openai.OpenAI(
                        api_key=self.api_key, 
                        base_url=self.api_base
                    )
                    
                    # 构建可用工具列表
                    available_tools_text = self._build_available_tools_text()
                    
                    # 动态生成工具输出字段说明
                    tool_output_guide = self._generate_tool_output_schema_guide()
                    
                    system_prompt = (
                        "你是一个AI需求解析助手Qiqi。请首先判断用户输入是闲聊还是任务请求：\n"
                        "\n"
                        "【🎯 闲聊判断规则】\n"
                        "以下情况属于闲聊，请直接回复 'CHAT_ONLY'：\n"
                        "- 问候语：你好、hello、hi、早上好、晚上好等\n"
                        "- 日常对话：今天怎么样？、在吗？、忙吗？等\n"
                        "- 简单问题：你是谁？、你会什么？、现在几点了？等\n"
                        "- 感谢表达：谢谢、感谢、辛苦了等\n"
                        "- 告别语：再见、拜拜、goodbye等\n"
                        "- 无具体任务的对话：聊天、闲聊、随便聊聊等\n"
                        "\n"
                        "【🔧 任务请求判断规则】\n"
                        "以下情况属于任务请求，需要返回流水线JSON：\n"
                        "- 搜索信息：搜索xxx、查找xxx、查询xxx等\n"
                        "- 文件处理：上传文件、下载文件、处理文档等\n"
                        "- 图像处理：旋转图片、放大图片、处理图像等\n"
                        "- 文本处理：翻译文本、总结文档、生成报告等\n"
                        "- 数据分析：分析数据、生成图表、统计信息等\n"
                        "- 代码相关：写代码、调试程序、代码优化等\n"
                        "- 其他具体任务：需要调用工具完成的操作\n"
                        "\n"
                        "【📋 判断示例】\n"
                        "闲聊示例（返回 'CHAT_ONLY'）：\n"
                        "- 用户：你好\n"
                        "- 用户：今天天气怎么样？\n"
                        "- 用户：你是谁？\n"
                        "- 用户：谢谢你的帮助\n"
                        "\n"
                        "任务请求示例（返回JSON）：\n"
                        "- 用户：搜索人工智能的最新发展\n"
                        "- 用户：帮我旋转这张图片90度\n"
                        "- 用户：翻译这段英文文本\n"
                        "- 用户：生成一份项目报告\n"
                        "\n"
                        "【⚠️ 特殊情况处理】\n"
                        "- 如果用户先闲聊后提出任务，按任务请求处理\n"
                        "- 如果用户的问题需要实时信息（如天气、时间），按任务请求处理\n"
                        "- 如果用户的问题涉及文件操作，按任务请求处理\n"
                        "\n"
                        "【🔍 判断流程】\n"
                        "1. 首先分析用户输入的内容和意图\n"
                        "2. 判断是否包含具体的任务需求\n"
                        "3. 如果是闲聊，直接返回 'CHAT_ONLY'\n"
                        "4. 如果是任务请求，继续生成流水线JSON\n"
                        "\n"
                        "现在请判断用户输入，如果是闲聊请回复 'CHAT_ONLY'，如果是任务请求请生成如下结构化JSON：\n"
                        "{\n"
                        '  "pipeline_id": "auto_generated_uuid",\n'
                        '  "components": [\n'
                        '    {\n'
                        '      "id": "unique_node_id",\n'
                        '      "tool_type": "xxx",\n'
                        '      "params": {...},\n'
                        '      "output": {\n'
                        '        "type": "object",\n'
                        '        "fields": {\n'
                        '          "field_name": "field_description",\n'
                        '          "temp_path": "临时文件路径",\n'
                        '          "status": "执行状态",\n'
                        '          "message": "执行消息"\n'
                        '        }\n'
                        '      }\n'
                        '    },\n'
                        '    ...\n'
                        '  ]\n'
                        "}\n"
                        "关键规则：\n"
                        "1. 每个组件必须有唯一的id字段，用于节点间引用\n"
                        "2. output字段必须包含完整的输出结构，使用fields对象描述所有可能的输出字段\n"
                        "3. 后续节点通过 $node_id.output.field_name 引用前一个节点的具体输出字段\n"
                        "4. params中的参数可以是具体值，也可以是占位符引用前一个节点的输出\n"
                        "5. 第一个节点的params必须包含所有必需的输入参数\n"
                        "6. pipeline_id字段请保持为'auto_generated_uuid'，系统会自动替换为实际UUID\n"
                        "7. 只能使用以下可用工具，不要使用不存在的工具：\n"
                        f"{available_tools_text}\n"
                        "\n"
                        "【🎯 重要工具选择指导】\n"
                        "- 对于搜索任务，必须优先选择 smart_search 或 ai_enhanced_search_tool_function\n"
                        "- 不要选择 baidu_search_tool 或 search_tool，因为它们没有AI依赖管理功能\n"
                        "- AI增强工具能够自动处理依赖问题，提供更好的用户体验\n"
                        "- 如果用户要求搜索，请使用 smart_search 作为首选工具\n"
                        "- 对于搜索任务，只选择一个搜索工具即可，不要同时使用多个搜索工具\n"
                        "- 如果用户提到'google或baidu'，优先选择 smart_search，它会自动处理多引擎搜索\n"
                        "\n"
                        "【📋 工具输出字段说明】\n"
                        f"{tool_output_guide}\n"
                        "\n"
                        "【📋 工具选择和使用原则】\n"
                        "⚠️ 重要：工具选择必须严格匹配任务需求\n"
                        "⚠️ 重要：参数格式必须完全符合工具要求\n"
                        "⚠️ 重要：不要假设工具功能，必须基于实际文档\n"
                        "\n"
                        "工具选择指导：\n"
                        "1. 仔细阅读工具描述和参数说明\n"
                        "2. 确保工具支持所需的具体操作\n"
                        "3. 参数类型和格式必须完全匹配\n"
                        "4. 必需参数不能遗漏，可选参数根据需要提供\n"
                        "5. 工具输出格式必须基于实际schema\n"
                        "\n"
                        "常见错误避免：\n"
                        "❌ 不要使用不支持的操作（如用image_processor做rotate）\n"
                        "❌ 不要假设参数格式（如用angle参数给不支持的工具）\n"
                        "❌ 不要忽略必需参数\n"
                        "❌ 不要使用错误的输出字段名\n"
                        "\n"
                        "【📋 工具功能对比说明】\n"
                        "🖼️ 图像处理工具：\n"
                        "  • image_rotator: 专门用于图像旋转，支持angle参数\n"
                        "  • image_scaler: 专门用于图像缩放，支持scale_factor参数\n"
                        "  • image_processor: 通用图像处理，仅支持scale和enhance操作\n"
                        "  • image_scaler_directory: 批量图像缩放，处理目录中的所有图像\n"
                        "\n"
                        "🔍 搜索工具：\n"
                        "  • smart_search: 智能搜索，支持多引擎和内容增强\n"
                        "  • search_tool: 基础搜索功能\n"
                        "  • baidu_search_tool: 百度搜索专用\n"
                        "\n"
                        "📁 文件处理工具：\n"
                        "  • minio_uploader: 上传文件到MinIO存储\n"
                        "  • file_writer: 写入文件到本地\n"
                        "\n"
                        "【📋 通用输出字段规则】\n"
                        "- 所有工具的输出都遵循统一的标准化格式\n"
                        "- 主要输出数据位于data.primary字段\n"
                        "- 次要输出数据位于data.secondary字段\n"
                        "- 元数据位于metadata字段\n"
                        "- 文件路径位于paths字段\n"
                        "- status字段表示执行状态\n"
                        "- message字段描述执行结果\n"
                        "\n"
                        "通用设计原则说明：\n"
                        "1. 每个工具的output.fields必须基于该工具的实际输出结构\n"
                        "2. 工具间的数据传递通过占位符引用：$node_id.output.field_name\n"
                        "3. 字段路径必须准确反映工具的实际输出层次结构\n"
                        "4. 不要假设工具的输出格式，必须基于实际schema\n"
                        "\n"
                        "❌ 错误示例（避免这样做）：\n"
                        "• 使用image_processor执行rotate操作（不支持）\n"
                        "• 给image_processor传递angle参数（不支持）\n"
                        "• 使用错误的输出字段名（如results而不是data.primary）\n"
                        "• 忽略必需参数或使用错误的参数类型\n"
                        "\n"
                        "示例1 - 图像旋转+缩放+上传（正确的工具选择）：\n"
                        "用户：旋转图片45度，放大2倍，上传到minio\n"
                        "输出：\n"
                        "{\n"
                        '  "pipeline_id": "auto_generated_uuid",\n'
                        '  "components": [\n'
                        '    {\n'
                        '      "id": "rotate_node",\n'
                        '      "tool_type": "image_rotator",\n'
                        '      "params": {\n'
                        '        "image_path": "input.jpg",\n'
                        '        "angle": 45\n'
                        '      },\n'
                        '      "output": {\n'
                        '        "type": "object",\n'
                        '        "fields": {\n'
                        '          "data.primary": "旋转后的图片路径列表",\n'
                        '          "paths": "文件路径列表",\n'
                        '          "status": "执行状态",\n'
                        '          "message": "执行消息"\n'
                        '        }\n'
                        '      }\n'
                        '    },\n'
                        '    {\n'
                        '      "id": "scale_node",\n'
                        '      "tool_type": "image_scaler",\n'
                        '      "params": {\n'
                        '        "image_path": "$rotate_node.output.data.primary",\n'
                        '        "scale_factor": 2\n'
                        '      },\n'
                        '      "output": {\n'
                        '        "type": "object",\n'
                        '        "fields": {\n'
                        '          "data.primary": "缩放后的图片路径列表",\n'
                        '          "paths": "文件路径列表",\n'
                        '          "status": "执行状态",\n'
                        '          "message": "执行消息"\n'
                        '        }\n'
                        '      }\n'
                        '    },\n'
                        '    {\n'
                        '      "id": "upload_node",\n'
                        '      "tool_type": "minio_uploader",\n'
                        '      "params": {\n'
                        '        "bucket_name": "kb-dev",\n'
                        '        "file_path": "$scale_node.output.data.primary"\n'
                        '      },\n'
                        '      "output": {\n'
                        '        "type": "object",\n'
                        '        "fields": {\n'
                        '          "data.primary": "上传后的URL列表",\n'
                        '          "status": "执行状态",\n'
                        '          "message": "执行消息"\n'
                        '        }\n'
                        '      }\n'
                        '    }\n'
                        '  ]\n'
                        "}\n"
                        "\n"
                        "示例2 - 搜索+处理（正确的工具选择）：\n"
                        "用户：搜索信息并生成报告\n"
                        "输出：\n"
                        "{\n"
                        '  "pipeline_id": "auto_generated_uuid",\n'
                        '  "components": [\n'
                        '    {\n'
                        '      "id": "search_node",\n'
                        '      "tool_type": "smart_search",\n'
                        '      "params": {\n'
                        '        "query": "查询内容",\n'
                        '        "max_results": 3\n'
                        '      },\n'
                        '      "output": {\n'
                        '        "type": "object",\n'
                        '        "fields": {\n'
                        '          "data.primary": "搜索结果列表",\n'
                        '          "data.secondary": "次要输出数据",\n'
                        '          "metadata": "元数据",\n'
                        '          "paths": "文件路径",\n'
                        '          "status": "执行状态",\n'
                        '          "message": "执行消息"\n'
                        '        }\n'
                        '      }\n'
                        '    },\n'
                        '    {\n'
                        '      "id": "processor_node",\n'
                        '      "tool_type": "text_processor",\n'
                        '      "params": {\n'
                        '        "input_data": "$search_node.output.data.primary"\n'
                        '      },\n'
                        '      "output": {\n'
                        '        "type": "object",\n'
                        '        "fields": {\n'
                        '          "data.primary": "处理后的数据",\n'
                        '          "status": "执行状态",\n'
                        '          "message": "执行消息"\n'
                        '        }\n'
                        '      }\n'
                        '    }\n'
                        '  ]\n'
                        "}\n"
                        "\n"
                        "重要提示：\n"
                        "- 首先判断是闲聊还是任务请求\n"
                        "- 闲聊直接返回 'CHAT_ONLY'\n"
                        "- 任务请求才生成流水线JSON\n"
                        "- output.fields必须包含工具可能输出的所有字段\n"
                        "- 对于图片处理工具，必须包含paths字段作为文件路径\n"
                        "- 对于文本处理工具，必须包含具体的文本字段\n"
                        "- 对于搜索工具，必须包含data.primary字段作为搜索结果\n"
                        "- 所有工具输出都应包含status和message字段\n"
                        "- 占位符引用必须使用完整的字段路径：$node_id.output.field_name\n"
                        "- 只能使用上述可用工具列表中的工具，不要使用不存在的工具\n"
                        "- 对于搜索任务，只选择一个搜索工具，优先使用 smart_search\n"
                        "\n"
                        "只返回JSON或'CHAT_ONLY'，不要有多余解释。"
                    )
                    response = client.chat.completions.create(
                        model=self.llm_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_input}
                        ],
                        temperature=0.1,
                        max_tokens=1024
                    )
                    result = response.choices[0].message.content
                    self.logger.info(f"===LLM解析结果: {result}")
                    
                    # 检查是否是闲聊情况
                    if result.strip() == 'CHAT_ONLY':
                        # 闲聊情况，返回特殊结构表示需要调用LLM知识
                        return {
                            "pipeline_id": str(uuid.uuid4()),
                            "chat_only": True,
                            "user_input": user_input,
                            "components": []
                        }
                    
                    # 只提取JSON部分，防止模型输出多余内容
                    json_str = self._extract_json(result)
                    self.logger.info(f"===LLM解析JSON: {json_str}")
                    
                    # 解析JSON并替换pipeline_id占位符
                    parsed_result = json.loads(json_str)
                    
                    # 检查并替换pipeline_id占位符
                    if parsed_result.get("pipeline_id") == "auto_generated_uuid":
                        parsed_result["pipeline_id"] = str(uuid.uuid4())
                        self.logger.info(f"===替换pipeline_id为: {parsed_result['pipeline_id']}")
                    elif "pipeline_id" not in parsed_result:
                        # 如果LLM没有返回pipeline_id，则添加一个
                        parsed_result["pipeline_id"] = str(uuid.uuid4())
                        self.logger.info(f"===添加pipeline_id: {parsed_result['pipeline_id']}")
                    
                    return parsed_result
                    
                except Exception as llm_error:
                    self.logger.warning(f"LLM解析失败，回退到规则解析: {llm_error}")
                    # LLM失败，回退到规则解析
                    return self._rule_based_parse(user_input)
            else:
                # 没有LLM配置，直接使用规则解析
                return self._rule_based_parse(user_input)
                
        except Exception as e:
            self.logger.error(f"需求解析失败: {e}")
            raise RequirementParserError(f"需求解析失败: {e}")

    def _build_available_tools_text(self) -> str:
        """构建可用工具文本"""
        if not self.available_tools:
            return "当前没有可用的工具"
        
        tools_text = []
        for tool in self.available_tools:
            tool_name = tool.get('name', 'unknown')
            description = tool.get('description', '无描述')
            
            # 提取参数信息
            input_schema = tool.get('inputSchema', {})
            properties = input_schema.get('properties', {})
            required = input_schema.get('required', [])
            
            # 构建详细的工具描述
            tool_desc = f"🔧 {tool_name}: {description}"
            
            if properties:
                param_details = []
                for param_name, param_schema in properties.items():
                    param_type = param_schema.get('type', 'any')
                    param_desc = param_schema.get('description', '')
                    is_required = param_name in required
                    required_mark = " (必需)" if is_required else " (可选)"
                    
                    if param_desc:
                        param_details.append(f"    • {param_name}({param_type}){required_mark}: {param_desc}")
                    else:
                        param_details.append(f"    • {param_name}({param_type}){required_mark}")
                
                tool_desc += "\n" + "\n".join(param_details)
            
            tools_text.append(tool_desc)
        
        return "\n\n".join(tools_text)

    def _generate_tool_output_schema_guide(self) -> str:
        """动态生成工具输出字段说明"""
        if not self.available_tools:
            return "当前没有可用的工具"
        
        # 使用工具分类管理器进行分类
        categorized_tools = self.category_manager.categorize_tools(self.available_tools)
        
        # 生成分类说明
        guide_parts = []
        
        for category_name, tools in categorized_tools.items():
            if tools:
                emoji = self.category_manager.get_category_emoji(category_name)
                guide_parts.append(f"{emoji} {category_name}：")
                for tool_name, schema in tools:
                    fields = self._extract_output_fields(schema)
                    guide_parts.append(f"  - {tool_name}: {fields}")
        
        return "\n".join(guide_parts)

    def _extract_output_fields(self, schema: Dict[str, Any]) -> str:
        """从输出schema中提取字段信息"""
        if not schema:
            return "{status, message}"
        
        properties = schema.get('properties', {})
        if not properties:
            return "{status, message}"
        
        # 提取字段名
        fields = list(properties.keys())
        
        # 确保包含基本字段
        if 'status' not in fields:
            fields.append('status')
        if 'message' not in fields:
            fields.append('message')
        
        # 按重要性排序
        priority_fields = ['status', 'message']
        other_fields = [f for f in fields if f not in priority_fields]
        sorted_fields = priority_fields + sorted(other_fields)
        
        return "{" + ", ".join(sorted_fields) + "}"

    def update_available_tools(self, tools: List[Dict[str, Any]]):
        """更新可用工具列表"""
        self.available_tools = tools
        self.logger.info(f"更新可用工具列表，共 {len(tools)} 个工具")

    def add_custom_category(self, category_name: str, keywords: List[str] = None, 
                          output_patterns: List[str] = None, emoji: str = "🔧"):
        """添加自定义工具分类"""
        from .tool_category_manager import CategoryRule
        category = CategoryRule(
            name=category_name,
            keywords=keywords or [],
            output_patterns=output_patterns or [],
            emoji=emoji
        )
        self.category_manager.add_category(category)

    def _rule_based_parse(self, user_input: str) -> Dict[str, Any]:
        """
        基于规则的解析，用于LLM不可用时的回退
        """
        import re
        
        # 搜索相关规则
        if any(keyword in user_input for keyword in ["搜索", "查找", "查询", "搜索", "查找"]):
            # 提取搜索关键词
            search_keywords = ["搜索", "查找", "查询", "搜索", "查找"]
            query = user_input
            for keyword in search_keywords:
                if keyword in query:
                    query = query.replace(keyword, "").strip()
                    break
            
            # 如果查询为空，使用原始输入
            if not query:
                query = user_input
            
            return {
                "pipeline_id": str(uuid.uuid4()),
                "components": [
                    {
                        "id": "search_node",
                        "tool_type": "search_tool",
                        "params": {
                            "query": query,
                            "max_results": 3
                        },
                        "output": {
                            "type": "object",
                            "fields": {
                                "results": "搜索结果列表",
                                "status": "执行状态",
                                "message": "执行消息"
                            }
                        }
                    }
                ]
            }
        elif "翻译" in user_input and "图片" in user_input:
            return {
                "pipeline_id": str(uuid.uuid4()),
                "components": [
                    {
                        "id": "translate_node",
                        "tool_type": "text_translator", 
                        "params": {"source_lang": "zh", "target_lang": "en"},
                        "output": {
                            "type": "object",
                            "fields": {
                                "translated_text": "翻译后的文本",
                                "status": "执行状态",
                                "message": "执行消息"
                            }
                        }
                    },
                    {
                        "id": "upscale_node",
                        "tool_type": "image_upscaler", 
                        "params": {"image_path": "$translate_node.output.translated_text"},
                        "output": {
                            "type": "object",
                            "fields": {
                                "temp_path": "放大后的图片临时路径",
                                "upscaled_image_path": "放大后的图片路径",
                                "status": "执行状态",
                                "message": "执行消息"
                            }
                        }
                    }
                ]
            }
        elif "旋转" in user_input and ("放大" in user_input or "缩放" in user_input):
            # 复合操作：旋转+缩放（必须在单独操作之前）
            angle_match = re.search(r'(\d+)度', user_input)
            scale_match = re.search(r'(\d+)倍', user_input)
            angle = int(angle_match.group(1)) if angle_match else 90
            scale_factor = int(scale_match.group(1)) if scale_match else 2
            
            return {
                "pipeline_id": str(uuid.uuid4()),
                "components": [
                    {
                        "id": "rotate_node",
                        "tool_type": "image_rotator", 
                        "params": {
                            "image_path": "input_image.jpg",
                            "angle": angle
                        },
                        "output": {
                            "type": "object",
                            "fields": {
                                "temp_path": "旋转后的图片临时路径",
                                "rotated_image_path": "旋转后的图片路径",
                                "status": "执行状态",
                                "message": "执行消息"
                            }
                        }
                    },
                    {
                        "id": "scale_node",
                        "tool_type": "image_scaler", 
                        "params": {
                            "image_path": "$rotate_node.output.temp_path",
                            "scale_factor": scale_factor
                        },
                        "output": {
                            "type": "object",
                            "fields": {
                                "temp_path": "缩放后的图片临时路径",
                                "scaled_image_path": "缩放后的图片路径",
                                "status": "执行状态",
                                "message": "执行消息"
                            }
                        }
                    }
                ]
            }
        elif "旋转" in user_input and ("图片" in user_input or "图像" in user_input):
            # 提取旋转角度
            angle_match = re.search(r'(\d+)度', user_input)
            angle = int(angle_match.group(1)) if angle_match else 90
            
            return {
                "pipeline_id": str(uuid.uuid4()),
                "components": [
                    {
                        "id": "rotate_node",
                        "tool_type": "image_rotator", 
                        "params": {
                            "image_path": "input_image.jpg",
                            "angle": angle
                        },
                        "output": {
                            "type": "object",
                            "fields": {
                                "temp_path": "旋转后的图片临时路径",
                                "rotated_image_path": "旋转后的图片路径",
                                "status": "执行状态",
                                "message": "执行消息"
                            }
                        }
                    }
                ]
            }
        elif ("放大" in user_input or "缩放" in user_input) and ("图片" in user_input or "图像" in user_input):
            # 提取缩放因子
            scale_match = re.search(r'(\d+)倍', user_input)
            scale_factor = int(scale_match.group(1)) if scale_match else 2
            
            return {
                "pipeline_id": str(uuid.uuid4()),
                "components": [
                    {
                        "id": "scale_node",
                        "tool_type": "image_scaler", 
                        "params": {
                            "image_path": "input_image.jpg",
                            "scale_factor": scale_factor
                        },
                        "output": {
                            "type": "object",
                            "fields": {
                                "temp_path": "缩放后的图片临时路径",
                                "scaled_image_path": "缩放后的图片路径",
                                "status": "执行状态",
                                "message": "执行消息"
                            }
                        }
                    }
                ]
            }
        elif "翻译" in user_input:
            return {
                "pipeline_id": str(uuid.uuid4()),
                "components": [
                    {
                        "id": "translate_node",
                        "tool_type": "text_translator", 
                        "params": {"source_lang": "zh", "target_lang": "en"},
                        "output": {
                            "type": "object",
                            "fields": {
                                "translated_text": "翻译后的文本",
                                "status": "执行状态",
                                "message": "执行消息"
                            }
                        }
                    }
                ]
            }
        else:
            # 默认返回一个模板
            return {
                "pipeline_id": str(uuid.uuid4()),
                "components": [
                    {
                        "id": "process_node",
                        "tool_type": "text_processor", 
                        "params": {"lang": "zh"},
                        "output": {
                            "type": "object",
                            "fields": {
                                "processed_text": "处理后的文本",
                                "status": "执行状态",
                                "message": "执行消息"
                            }
                        }
                    },
                    {
                        "id": "generate_node",
                        "tool_type": "image_generator", 
                        "params": {"text": "$process_node.output.processed_text", "style": "anime"},
                        "output": {
                            "type": "object",
                            "fields": {
                                "temp_path": "生成的图片临时路径",
                                "generated_image_path": "生成的图片路径",
                                "status": "执行状态",
                                "message": "执行消息"
                            }
                        }
                    }
                ]
            }

    def _extract_json(self, text: str) -> str:
        """
        提取字符串中的JSON对象，防止LLM输出多余内容
        """
        import re
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return match.group(0)
        raise RequirementParserError("未能从LLM输出中提取到有效JSON")