import os
import logging
from typing import Any

class OutputValidatorError(Exception):
    pass

class OutputValidator:
    def __init__(
        self, 
        use_llm: bool = False, 
        llm_model: str = "gpt-3.5-turbo", 
        api_key: str = None, 
        api_base: str = None
    ):
        self.logger = logging.getLogger("OutputValidator")
        self.use_llm = use_llm
        self.llm_model = llm_model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.api_base = api_base or os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")

    def validate(self, output: Any, expected_type: str = None, requirement: str = None) -> bool:
        """
        验证输出结果类型和内容
        :param output: pipeline最终输出
        :param expected_type: 期望的类型（如"str"、"int"等）
        :param requirement: 可选，原始需求描述，用于LLM语义验证
        :return: True/False
        """
        try:
            # 1. 类型检查
            if expected_type:
                if expected_type == "str" and not isinstance(output, str):
                    raise OutputValidatorError("输出类型应为str")
                if expected_type == "int" and not isinstance(output, int):
                    raise OutputValidatorError("输出类型应为int")
                # 可扩展更多类型

            # 2. LLM语义验证
            if self.use_llm:
                import openai
                openai.api_key = self.api_key
                openai.api_base = self.api_base

                # 构造prompt
                system_prompt = (
                    "你是一个AI结果验证助手。请根据用户需求和期望类型，判断给定的输出结果是否合理、符合需求。"
                    "只返回'YES'或'NO'，不要有多余解释。"
                )
                user_prompt = (
                    f"用户需求: {requirement or '未知'}\n"
                    f"期望类型: {expected_type or '未知'}\n"
                    f"输出结果: {output}\n"
                    "请判断输出结果是否合理、符合需求？"
                )
                response = openai.ChatCompletion.create(
                    model=self.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0,
                    max_tokens=10
                )
                result = response["choices"][0]["message"]["content"].strip().upper()
                if "YES" in result:
                    return True
                elif "NO" in result:
                    return False
                else:
                    self.logger.warning(f"LLM返回无法判定: {result}")
                    return False
            return True
        except Exception as e:
            self.logger.error(f"结果验证失败: {e}")
            return False