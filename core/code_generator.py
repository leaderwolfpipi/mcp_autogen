import logging
import os
import json
from typing import Dict, Any, List, Optional

class CodeGeneratorError(Exception):
    pass

class CodeGenerator:
    def __init__(
        self,
        use_llm: bool = False,
        llm_model: str = "gpt-4o",
        api_key: str = None,
        api_base: str = None
    ):
        self.logger = logging.getLogger("CodeGenerator")
        self.use_llm = use_llm
        self.llm_model = llm_model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.api_base = api_base or os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")

    def generate(self, tool_spec: Dict[str, Any]) -> str:
        """
        生成完整的Python工具实现
        tool_spec: {"tool": "custom_tool", "params": {...}}
        """
        tool_name = tool_spec["tool"]
        params = tool_spec.get("params", {})
        
        try:
            if self.use_llm:
                return self._generate_with_llm(tool_name, params)
            else:
                return self._generate_with_template(tool_name, params)
        except Exception as e:
            self.logger.error(f"代码生成失败: {e}")
            raise CodeGeneratorError(f"代码生成失败: {e}")

    def _generate_with_llm(self, tool_name: str, params: Dict[str, Any]) -> str:
        """
        使用LLM生成完整的工具实现
        """
        import openai
        
        # 构造详细的prompt
        system_prompt = (
            "你是一个专业的Python工具开发专家。请根据工具名称和参数，生成一个完整的、可直接运行的Python函数。\n"
            "要求：\n"
            "1. 函数名必须与工具名完全一致\n"
            "2. 参数类型注解必须准确\n"
            "3. 实现具体的业务逻辑，不要只是TODO或raise NotImplementedError\n"
            "4. 包含适当的错误处理和日志\n"
            "5. 添加清晰的文档字符串，文档字符串的第一行应该是简洁明了的功能描述（不超过300字符）\n"
            "6. 文档字符串应包含参数说明、返回值说明和功能描述\n"
            "7. 如果是图片处理，使用PIL/Pillow；如果是文本处理，使用正则或字符串方法\n"
            "8. 如果是API调用，使用requests库\n"
            "9. 如果需要的工具函数已经存在但参数不能满足当前问题，请直接优化修改已存在的函数并做出向后兼容的调整\n"
            "10. 向后兼容调整包括：为新增参数设置默认值，保持原有参数顺序，添加参数验证但不破坏原有调用方式\n"
            "11. 只返回Python代码，不要有多余解释或提问\n"
            "12. 如果参数信息不完整，请基于参数名和常见用法进行合理推断\n"
            "13. 确保生成的代码语法正确，使用半角标点符号\n"
            "14. 文档字符串格式示例：\n"
            "    \"\"\"\n"
            "    简洁的功能描述（第一行，不超过300字符）\n"
            "    \n"
            "    详细的功能说明，包括使用场景、参数说明、返回值说明等。\n"
            "    \n"
            "    参数:\n"
            "        param1: 参数1的说明\n"
            "        param2: 参数2的说明\n"
            "    \n"
            "    返回:\n"
            "        返回值的说明\n"
            "    \"\"\"\n"
        )
        
        user_prompt = f"""
        工具名称: {tool_name}
        参数: {json.dumps(params, ensure_ascii=False)}
        
        请生成一个完整的Python函数实现，包含具体的业务逻辑。
        
        重要提示：
        - 基于工具名称和参数进行合理推断，直接生成可运行的代码
        - 如果参数信息不完整，请基于常见用法和最佳实践进行实现
        - 确保所有标点符号都是半角字符（英文标点）
        - 如果发现需要的工具函数已经存在但参数不满足需求，请：
          1. 分析现有函数的参数结构
          2. 添加必要的新参数，并为它们设置合理的默认值
          3. 保持原有参数的顺序和名称不变
          4. 确保新增参数不会影响现有调用方式
          5. 在文档字符串中说明新增参数的作用和默认值
        
        - 向后兼容原则：
          - 原有参数必须保持相同的名称和位置
          - 新增参数必须设置默认值
          - 原有调用方式必须仍然有效
          - 在函数开头添加参数验证，但不破坏原有逻辑
        
        - 直接生成代码，不要提问或解释
        
        示例：
        - text_translator: 实现文本翻译（可调用翻译API或简单替换）
        - image_resizer: 实现图片缩放（使用PIL）
        - text_extractor: 实现图片文字提取（使用OCR或模拟）
        - image_upscaler: 实现图片放大（使用PIL）
        - image_processor: 实现通用图片处理（支持多种操作）
        """
        
        client = openai.OpenAI(api_key=self.api_key, base_url=self.api_base)
        response = client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=1024
        )
        
        code = response.choices[0].message.content
        return self._extract_code(code)

    def _generate_with_template(self, tool_name: str, params: Dict[str, Any]) -> str:
        """
        基于模板生成工具实现，支持现有工具的参数扩展
        """
        # 检查是否存在现有工具文件
        existing_tool_path = os.path.join("tools", f"{tool_name}.py")
        existing_params = {}
        
        if os.path.exists(existing_tool_path):
            self.logger.info(f"发现现有工具文件: {existing_tool_path}")
            # 尝试解析现有函数的参数
            existing_params = self._parse_existing_function_params(existing_tool_path, tool_name)
            self.logger.info(f"现有工具参数: {existing_params}")
        
        # 合并参数，保持向后兼容
        merged_params = self._merge_params_with_backward_compatibility(existing_params, params)
        param_str = self._generate_param_string(merged_params)
        
        # 根据工具名和参数智能生成实现
        if "text_translator" in tool_name:
            return self._generate_text_translator(tool_name, param_str, merged_params, existing_params)
        elif "image" in tool_name and ("resizer" in tool_name or "upscaler" in tool_name or "rotator" in tool_name or "scaler" in tool_name):
            return self._generate_image_processor(tool_name, param_str, merged_params, existing_params)
        elif "text_extractor" in tool_name:
            return self._generate_text_extractor(tool_name, param_str, merged_params, existing_params)
        elif "search" in tool_name:
            return self._generate_search_tool(tool_name, param_str, merged_params, existing_params)
        else:
            return self._generate_generic_tool(tool_name, param_str, merged_params, existing_params)

    def _generate_search_tool(self, tool_name: str, param_str: str, params: Dict, existing_params: Dict) -> str:
        """生成搜索工具"""
        # 生成向后兼容说明
        backward_compat_note = ""
        if existing_params:
            backward_compat_note = f"""
    
    向后兼容说明:
    - 此函数已从现有工具扩展而来，保持原有参数兼容性
    - 原有参数: {list(existing_params.keys())}
    - 新增参数: {[k for k in params.keys() if k not in existing_params]}
    - 所有原有调用方式仍然有效
    """
        
        return f'''import logging
import os
import requests
from typing import Any, Dict, List, Optional

def {tool_name}({param_str}):
    """
    搜索工具函数 - {tool_name}
    
    参数说明:
    {chr(10).join([f"    {k}: {v}" for k, v in params.items()])}
    
    注意: 这是一个自动生成的搜索工具，支持多种搜索方式。
    如果参数信息不完整或功能描述不清晰，请检查工具配置。{backward_compat_note}
    """
    logger = logging.getLogger("{tool_name}")
    
    try:
        # 参数验证
        query = locals().get('query', '')
        if not query:
            logger.error("搜索查询不能为空")
            return {{"status": "error", "message": "搜索查询不能为空", "results": []}}
        
        # 尝试使用Google Custom Search API
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        google_cse_id = os.environ.get("GOOGLE_CSE_ID")
        
        if google_api_key and google_cse_id:
            try:
                logger.info(f"使用Google Custom Search API搜索: {{query}}")
                url = "https://www.googleapis.com/customsearch/v1"
                params = {{
                    "key": google_api_key,
                    "cx": google_cse_id,
                    "q": query,
                    "num": 5
                }}
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                items = data.get("items", [])
                
                results = []
                for item in items:
                    results.append({{
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    }})
                
                logger.info(f"Google搜索成功，找到 {{len(results)}} 个结果")
                return {{
                    "status": "success",
                    "message": f"搜索成功，找到 {{len(results)}} 个结果",
                    "results": results,
                    "source": "google"
                }}
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Google搜索失败: {{e}}")
                # 继续尝试其他搜索方式
            except Exception as e:
                logger.warning(f"Google搜索出错: {{e}}")
                # 继续尝试其他搜索方式
        
        # 尝试使用DuckDuckGo搜索
        try:
            logger.info(f"使用DuckDuckGo搜索: {{query}}")
            url = "https://api.duckduckgo.com/"
            params = {{
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # 提取相关主题
            for topic in data.get("RelatedTopics", [])[:5]:
                if "Text" in topic:
                    results.append({{
                        "title": topic.get("Text", ""),
                        "link": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", "")
                    }})
            
            # 提取摘要
            if data.get("Abstract"):
                results.insert(0, {{
                    "title": data.get("Heading", "摘要"),
                    "link": data.get("AbstractURL", ""),
                    "snippet": data.get("Abstract", "")
                }})
            
            logger.info(f"DuckDuckGo搜索成功，找到 {{len(results)}} 个结果")
            return {{
                "status": "success",
                "message": f"搜索成功，找到 {{len(results)}} 个结果",
                "results": results,
                "source": "duckduckgo"
            }}
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"DuckDuckGo搜索失败: {{e}}")
        except Exception as e:
            logger.warning(f"DuckDuckGo搜索出错: {{e}}")
        
        # 如果所有搜索都失败，返回模拟结果
        logger.warning("所有搜索API都失败，返回模拟结果")
        mock_results = [
            {{
                "title": f"关于 {{query}} 的搜索结果1",
                "link": "https://example.com/result1",
                "snippet": f"这是关于 {{query}} 的模拟搜索结果1"
            }},
            {{
                "title": f"关于 {{query}} 的搜索结果2", 
                "link": "https://example.com/result2",
                "snippet": f"这是关于 {{query}} 的模拟搜索结果2"
            }},
            {{
                "title": f"关于 {{query}} 的搜索结果3",
                "link": "https://example.com/result3", 
                "snippet": f"这是关于 {{query}} 的模拟搜索结果3"
            }}
        ]
        
        return {{
            "status": "success",
            "message": f"搜索完成，找到 {{len(mock_results)}} 个结果（模拟数据）",
            "results": mock_results,
            "source": "mock"
        }}
            
    except Exception as e:
        logger.error(f"搜索工具执行失败: {{e}}")
        return {{
            "status": "error",
            "message": f"搜索失败: {{str(e)}}",
            "results": []
        }}
    finally:
        logger.info(f"搜索工具执行完成: {tool_name}")
'''

    def _parse_existing_function_params(self, file_path: str, function_name: str) -> Dict[str, Any]:
        """
        解析现有函数文件的参数
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的正则表达式匹配函数定义
            import re
            pattern = rf"def\s+{function_name}\s*\(([^)]*)\):"
            match = re.search(pattern, content)
            
            if match:
                params_str = match.group(1).strip()
                if params_str:
                    params = {}
                    for param in params_str.split(','):
                        param = param.strip()
                        if '=' in param:
                            # 处理带默认值的参数
                            name_part, default = param.split('=', 1)
                            name = name_part.strip()
                            # 提取参数名（去掉类型注解）
                            if ':' in name:
                                name = name.split(':')[0].strip()
                            params[name] = default.strip()
                        else:
                            # 处理没有默认值的参数
                            name = param.strip()
                            # 提取参数名（去掉类型注解）
                            if ':' in name:
                                name = name.split(':')[0].strip()
                            params[name] = None
                    return params
            
            return {}
        except Exception as e:
            self.logger.warning(f"解析现有函数参数失败: {e}")
            return {}

    def _merge_params_with_backward_compatibility(self, existing_params: Dict[str, Any], new_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并参数，保持向后兼容
        """
        merged = {}
        
        # 首先添加现有参数（保持顺序）
        for param_name, default_value in existing_params.items():
            if param_name in new_params:
                # 如果新参数中有相同的参数，使用新值
                merged[param_name] = new_params[param_name]
            else:
                # 保持原有默认值
                merged[param_name] = default_value
        
        # 然后添加新的参数
        for param_name, param_value in new_params.items():
            if param_name not in merged:
                merged[param_name] = param_value
        
        return merged

    def _generate_param_string(self, params: Dict[str, Any]) -> str:
        """
        生成参数字符串，正确处理类型注解和默认值
        """
        param_parts = []
        for param_name, param_value in params.items():
            if param_value is None:
                # 没有默认值的参数
                param_parts.append(f"{param_name}")
            else:
                # 有默认值的参数，需要正确处理不同类型的值
                if isinstance(param_value, str):
                    # 字符串需要用引号包围
                    default_value = f'"{param_value}"'
                elif isinstance(param_value, (list, dict)):
                    # 列表和字典需要转换为字符串表示
                    default_value = repr(param_value)
                else:
                    # 其他类型直接使用
                    default_value = str(param_value)
                
                param_parts.append(f"{param_name} = {default_value}")
        return ", ".join(param_parts)

    def _generate_text_translator(self, tool_name: str, param_str: str, params: Dict, existing_params: Dict) -> str:
        """生成文本翻译工具"""
        # 生成向后兼容说明
        backward_compat_note = ""
        if existing_params:
            backward_compat_note = f"""
    
    向后兼容说明:
    - 此函数已从现有工具扩展而来，保持原有参数兼容性
    - 原有参数: {list(existing_params.keys())}
    - 新增参数: {[k for k in params.keys() if k not in existing_params]}
    - 所有原有调用方式仍然有效
    """
        
        return f'''import requests
import hashlib
import random
import os
import logging
from typing import Optional, Any

def {tool_name}({param_str}):
    """
    文本翻译工具 - 支持多语言翻译
    
    参数说明:
    {chr(10).join([f"    {k}: {v}" for k, v in params.items()])}
    
    注意: 这是一个自动生成的翻译工具，可能需要根据具体需求进行调整。{backward_compat_note}
    """
    logger = logging.getLogger("{tool_name}")
    
    try:
        # 参数验证
        if not text:
            logger.error("翻译文本不能为空")
            return "错误: 翻译文本不能为空"
        
        if not isinstance(text, str):
            logger.error(f"翻译文本必须是字符串类型，当前类型: {{type(text)}}")
            return f"错误: 翻译文本必须是字符串类型"
        
        logger.info(f"开始翻译文本: {{text[:50]}}...")
        
        # 获取语言参数（从函数参数中获取）
        source_lang = source_lang if 'source_lang' in locals() else 'auto'
        target_lang = target_lang if 'target_lang' in locals() else 'en'
        
        # 使用百度翻译API（需要配置环境变量）
        appid = os.environ.get("BAIDU_FANYI_APPID", "")
        secret_key = os.environ.get("BAIDU_FANYI_SECRET", "")
        
        if not appid or not secret_key:
            # 如果没有配置API，返回模拟翻译
            logger.warning("未配置百度翻译API，返回模拟翻译结果")
            return f"[{{source_lang}}->{{target_lang}}]: {{text}}"
        
        salt = str(random.randint(32768, 65536))
        sign = hashlib.md5((appid + text + salt + secret_key).encode('utf-8')).hexdigest()
        
        url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        params_api = {{
            'q': text,
            'from': source_lang,
            'to': target_lang,
            'appid': appid,
            'salt': salt,
            'sign': sign
        }}
        
        logger.info(f"调用百度翻译API: {{source_lang}} -> {{target_lang}}")
        response = requests.get(url, params=params_api, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if "trans_result" in result:
            translated_text = result["trans_result"][0]["dst"]
            logger.info(f"翻译成功: {{translated_text[:50]}}...")
            return translated_text
        else:
            logger.error(f"翻译API返回错误: {{result}}")
            return f"[翻译失败]: {{text}}"
            
    except requests.exceptions.RequestException as e:
        logger.error(f"网络请求失败: {{e}}")
        return f"[网络错误]: {{text}} ({{str(e)}})"
    except Exception as e:
        logger.error(f"翻译处理失败: {{e}}")
        return f"[翻译错误]: {{text}} ({{str(e)}})"
    finally:
        logger.info(f"文本翻译工具执行完成: {tool_name}")
'''

    def _generate_image_processor(self, tool_name: str, param_str: str, params: Dict, existing_params: Dict) -> str:
        """生成图片处理工具"""
        # 生成向后兼容说明
        backward_compat_note = ""
        if existing_params:
            backward_compat_note = f"""
    
    向后兼容说明:
    - 此函数已从现有工具扩展而来，保持原有参数兼容性
    - 原有参数: {list(existing_params.keys())}
    - 新增参数: {[k for k in params.keys() if k not in existing_params]}
    - 所有原有调用方式仍然有效
    """
        
        return f'''import os
import logging
from typing import Union

def {tool_name}({param_str}):
    """
    图片处理工具 - 支持缩放和放大
    
    参数说明:
    {chr(10).join([f"    {k}: {v}" for k, v in params.items()])}
    
    注意: 这是一个自动生成的图片处理工具，可能需要根据具体需求进行调整。{backward_compat_note}
    """
    logger = logging.getLogger("{tool_name}")
    
    try:
        # 检查PIL依赖
        try:
            from PIL import Image
        except ImportError:
            logger.error("PIL/Pillow未安装，请运行: pip install Pillow")
            return f"错误: PIL/Pillow未安装，请运行: pip install Pillow"
        
        # 获取参数值
        image_path = locals().get('image_path', None)
        scale_factor = locals().get('scale_factor', 2.0)
        angle = locals().get('angle', 90.0)
        
        # 参数验证
        if not image_path:
            logger.error("图片参数不能为空")
            return "错误: 图片参数不能为空"
        
        # 处理不同类型的图片输入
        if isinstance(image_path, str):
            if not os.path.exists(image_path):
                logger.error(f"图片文件不存在: {{image_path}}")
                return f"错误: 图片文件不存在 - {{image_path}}"
            img = Image.open(image_path)
            logger.info(f"打开图片文件: {{image_path}}")
        elif hasattr(image_path, 'resize'):
            # 如果是PIL Image对象
            img = image_path
            logger.info("使用PIL Image对象")
        elif hasattr(image_path, 'read'):
            # 如果是文件对象
            img = Image.open(image_path)
            logger.info("从文件对象打开图片")
        else:
            logger.error(f"无效的图片输入类型: {{type(image_path)}}")
            return f"错误: 无效的图片输入类型 - {{type(image_path)}}"
        
        # 获取原始尺寸
        width, height = img.size
        logger.info(f"原始图片尺寸: {{width}}x{{height}}")
        
        # 根据工具类型执行不同操作
        if "rotator" in tool_name:
            # 图片旋转
            if not isinstance(angle, (int, float)):
                logger.warning(f"无效的旋转角度: {{angle}}，使用默认值90")
                angle = 90.0
            
            rotated_img = img.rotate(angle, expand=True)
            new_width, new_height = rotated_img.size
            logger.info(f"旋转图片 {{angle}}度，新尺寸: {{new_width}}x{{new_height}}")
            
            # 保存处理后的图片
            output_path = f"rotated_{{os.path.basename(str(image_path))}}"
            rotated_img.save(output_path)
            logger.info(f"旋转图片已保存到: {{output_path}}")
            return rotated_img
            
        elif "scaler" in tool_name:
            # 图片缩放
            if not isinstance(scale_factor, (int, float)) or scale_factor <= 0:
                logger.warning(f"无效的缩放因子: {{scale_factor}}，使用默认值2")
                scale_factor = 2.0
            
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"缩放图片到: {{new_width}}x{{new_height}}")
            
            # 保存处理后的图片
            output_path = f"scaled_{{os.path.basename(str(image_path))}}"
            resized_img.save(output_path)
            logger.info(f"缩放图片已保存到: {{output_path}}")
            return resized_img
            
        else:
            # 通用图片处理
            if not isinstance(scale_factor, (int, float)) or scale_factor <= 0:
                logger.warning(f"无效的缩放因子: {{scale_factor}}，使用默认值2")
                scale_factor = 2.0
            
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"处理图片到: {{new_width}}x{{new_height}}")
            
            # 保存处理后的图片
            output_path = f"processed_{{os.path.basename(str(image_path))}}"
            resized_img.save(output_path)
            logger.info(f"处理图片已保存到: {{output_path}}")
            return resized_img
        
    except ImportError as e:
        logger.error(f"依赖导入失败: {{e}}")
        return f"错误: 缺少必要依赖 - {{e}}"
    except Exception as e:
        logger.error(f"图片处理失败: {{e}}")
        return f"图片处理失败: {{str(e)}}"
    finally:
        logger.info(f"图片处理工具执行完成: {tool_name}")
'''

    def _generate_text_extractor(self, tool_name: str, param_str: str, params: Dict, existing_params: Dict) -> str:
        """生成文本提取工具"""
        return f'''import os
import re
import logging
from typing import Optional

def {tool_name}({param_str}):
    """
    图片文字提取工具 - 模拟OCR功能
    
    参数说明:
    {chr(10).join([f"    {k}: {v}" for k, v in params.items()])}
    
    注意: 这是一个自动生成的OCR工具，可能需要根据具体需求进行调整。
    目前使用模拟OCR，实际使用时建议集成真实的OCR服务。
    """
    logger = logging.getLogger("{tool_name}")
    
    try:
        # 参数验证
        if not image:
            logger.error("图片参数不能为空")
            return "错误: 图片参数不能为空"
        
        logger.info(f"开始提取图片文字: {{image}}")
        
        # 检查PIL依赖
        try:
            from PIL import Image
        except ImportError:
            logger.error("PIL/Pillow未安装，请运行: pip install Pillow")
            return "错误: PIL/Pillow未安装，请运行: pip install Pillow"
        
        # 检查pytesseract依赖
        try:
            import pytesseract
        except ImportError:
            logger.warning("pytesseract未安装，使用模拟OCR")
            # 使用模拟OCR
        if isinstance(image, str) and os.path.exists(image):
            filename = os.path.basename(image)
            if "text" in filename.lower():
                    result = "这是从图片中提取的示例文本"
            elif "document" in filename.lower():
                    result = "文档内容：这是一个示例文档的文本内容"
                else:
                    result = "Hello World - 这是从图片中提取的示例文本"
            else:
                result = "示例文本：从图片中提取的文字内容"
            
            logger.info(f"模拟OCR结果: {{result}}")
            return result
        
        # 处理不同类型的图片输入
        if isinstance(image, str):
            if not os.path.exists(image):
                logger.error(f"图片文件不存在: {{image}}")
                return f"错误: 图片文件不存在 - {{image}}"
            img = Image.open(image)
            logger.info(f"打开图片文件: {{image}}")
        elif hasattr(image, 'size'):  # 检查是否为PIL Image对象
            img = image
            logger.info("使用PIL Image对象")
        else:
            logger.error(f"无效的图片输入类型: {{type(image)}}")
            return f"错误: 无效的图片输入类型 - {{type(image)}}"

        logger.info("开始OCR处理...")
        
        # 执行OCR
        extracted_text = pytesseract.image_to_string(img, lang='eng+chi_sim')
        
        if not extracted_text.strip():
            extracted_text = "未检测到文字内容"
            logger.warning("OCR未检测到文字内容")
        else:
            logger.info(f"OCR提取成功，文字长度: {{len(extracted_text)}}")
        
        return extracted_text.strip()

    except Exception as e:
        logger.error(f"OCR处理失败: {{e}}")
        return f"OCR处理失败: {{str(e)}}"
    finally:
        logger.info(f"文本提取工具执行完成: {{tool_name}}")
'''

    def _generate_generic_tool(self, tool_name: str, param_str: str, params: Dict, existing_params: Dict) -> str:
        """生成通用工具"""
        # 生成向后兼容说明
        backward_compat_note = ""
        if existing_params:
            backward_compat_note = f"""
    
    向后兼容说明:
    - 此函数已从现有工具扩展而来，保持原有参数兼容性
    - 原有参数: {list(existing_params.keys())}
    - 新增参数: {[k for k in params.keys() if k not in existing_params]}
    - 所有原有调用方式仍然有效
    """
        
        return f'''import logging
import os
from typing import Any, Dict, List, Optional

def {tool_name}({param_str}):
    """
    通用工具函数 - {tool_name}
    
    参数说明:
    {chr(10).join([f"    {k}: {v}" for k, v in params.items()])}
    
    注意: 这是一个自动生成的工具函数，可能需要根据具体需求进行调整。
    如果参数信息不完整或功能描述不清晰，请检查工具配置。{backward_compat_note}
    """
    logger = logging.getLogger("{tool_name}")
    
    try:
        # 参数验证
        logger.info(f"开始执行工具: {tool_name}")
        logger.info(f"接收参数: {{locals()}}")
        
        # 根据参数类型实现具体逻辑
        param_values = locals()
        if "text" in str(param_values):
            # 文本处理
            text_param = param_values.get('text', '示例文本')
            logger.info(f"处理文本: {{text_param}}")
            return f"处理文本: {{text_param}}"
        elif "image" in str(param_values):
            # 图片处理
            image_param = param_values.get('image', '示例图片')
            logger.info(f"处理图片: {{image_param}}")
            return f"处理图片: {{image_param}}"
        elif "file" in str(param_values):
            # 文件处理
            file_param = param_values.get('file', '示例文件')
            logger.info(f"处理文件: {{file_param}}")
            return f"处理文件: {{file_param}}"
        else:
            # 通用处理
            logger.info(f"通用处理参数: {{param_values}}")
            return f"处理参数: {{param_values}}"
            
    except Exception as e:
        logger.error(f"工具执行失败: {{e}}")
        return f"处理失败: {{str(e)}}"
    finally:
        logger.info(f"工具执行完成: {tool_name}")
'''

    def _type_hint(self, value):
        """类型推断"""
        if isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "str"
        elif isinstance(value, dict):
            return "dict"
        elif isinstance(value, list):
            return "list"
        else:
            return "Any"

    def _extract_code(self, text: str) -> str:
        """提取Python代码块"""
        import re
        # 优先提取markdown代码块
        match = re.search(r"```python\s*([\s\S]+?)```", text)
        if match:
            return match.group(1).strip()
        # 其次尝试提取以def开头的代码
        match = re.search(r"(def\s+\w+\s*\(.*?\):[\s\S]+)", text)
        if match:
            return match.group(1).strip()
        # 否则原样返回
        return text.strip()

    def generate_and_save(self, tool_spec: Dict[str, Any], output_dir: str = "tools") -> str:
        """
        生成代码并保存到文件
        """
        tool_name = tool_spec["tool"]
        code = self.generate(tool_spec)
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存到文件
        file_path = os.path.join(output_dir, f"{tool_name}.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        
        self.logger.info(f"工具代码已生成并保存到: {file_path}")
        return file_path