#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成真实LLM API的报告生成器示例
支持OpenAI GPT和百度文心一言
"""

import logging
import time
import json
import os
from typing import List, Dict, Any, Union, Optional
from tools.base_tool import create_standardized_output

logging.basicConfig(level=logging.INFO)

def llm_report_generator_with_api(
    content: Union[str, list, dict], 
    format: str = "markdown",
    max_words: int = 800,
    title: str = "报告",
    topic: str = None,
    style: str = "professional",
    llm_provider: str = "openai"
) -> Dict[str, Any]:
    """
    集成真实LLM API的专业报告生成工具
    
    参数:
        content: 输入内容
        format: 输出格式
        max_words: 最大字数限制
        title: 报告标题
        topic: 主题关键词
        style: 报告风格
        llm_provider: LLM提供商 ("openai" | "baidu" | "auto")
        
    返回:
        标准化的输出字典
    """
    start_time = time.time()
    
    try:
        # 参数验证
        if not content:
            return create_standardized_output(
                tool_name="llm_report_generator_with_api",
                status="error",
                message="输入内容不能为空",
                error="输入内容不能为空",
                start_time=start_time,
                parameters={"content": content, "format": format, "max_words": max_words}
            )
        
        # 提取内容
        extracted_content = _extract_content(content)
        if not extracted_content:
            return create_standardized_output(
                tool_name="llm_report_generator_with_api",
                status="error",
                message="无法从输入中提取有效内容",
                error="内容提取失败",
                start_time=start_time,
                parameters={"content": content, "format": format, "max_words": max_words}
            )
        
        # 构建专业提示词
        prompt = _build_professional_prompt(
            extracted_content, title, max_words, format, style, topic
        )
        
        # 调用LLM API
        report_content = _call_llm_api_with_fallback(prompt, llm_provider)
        
        # 构建输出
        output_data = {
            "report_content": report_content,
            "format": format,
            "word_count": len(report_content.split()),
            "content_length": len(report_content),
            "topic": topic,
            "style": style,
            "llm_provider": llm_provider
        }
        
        return create_standardized_output(
            tool_name="llm_report_generator_with_api",
            status="success",
            primary_data=output_data,
            secondary_data={
                "original_content_length": len(extracted_content),
                "extraction_method": _get_extraction_method(content)
            },
            counts={
                "report_words": len(report_content.split()),
                "report_chars": len(report_content),
                "original_words": len(extracted_content.split()),
                "original_chars": len(extracted_content)
            },
            message=f"成功生成{format}格式报告，字数: {len(report_content.split())}",
            start_time=start_time,
            parameters={"content": content, "format": format, "max_words": max_words, "title": title, "topic": topic, "style": style, "llm_provider": llm_provider}
        )

    except Exception as e:
        logging.error(f"LLM报告生成失败: {e}")
        return create_standardized_output(
            tool_name="llm_report_generator_with_api",
            status="error",
            message=f"LLM报告生成失败: {str(e)}",
            error=str(e),
            start_time=start_time,
            parameters={"content": content, "format": format, "max_words": max_words}
        )

def _extract_content(content: Union[str, list, dict]) -> str:
    """从各种输入格式中提取文本内容"""
    if isinstance(content, str):
        return content.strip()
    
    elif isinstance(content, list):
        content_parts = []
        for item in content:
            if isinstance(item, dict):
                text = _extract_text_from_dict(item)
                if text:
                    content_parts.append(text)
            elif isinstance(item, str):
                content_parts.append(item)
        return '\n\n'.join(content_parts)
    
    elif isinstance(content, dict):
        return _extract_text_from_dict(content)
    
    else:
        return str(content)

def _extract_text_from_dict(data_dict: dict) -> str:
    """从字典中提取文本内容"""
    priority_fields = ['content', 'text', 'body', 'description', 'summary', 'results', 'snippet', 'title']
    
    for field in priority_fields:
        if field in data_dict:
            value = data_dict[field]
            if isinstance(value, str) and value.strip():
                return value.strip()
            elif isinstance(value, list):
                return _extract_content(value)
            elif isinstance(value, dict):
                nested_text = _extract_text_from_dict(value)
                if nested_text:
                    return nested_text
    
    text_parts = []
    for key, value in data_dict.items():
        if isinstance(value, str) and value.strip():
            text_parts.append(value.strip())
    
    return '\n'.join(text_parts)

def _build_professional_prompt(
    content: str, 
    title: str, 
    max_words: int, 
    format: str,
    style: str,
    topic: str = None
) -> str:
    """构建专业的LLM提示词"""
    
    # 根据主题类型定制提示词
    topic_guidance = ""
    if topic:
        if "历史" in topic or "人物" in topic:
            topic_guidance = """
历史人物报告要求：
1. 重点突出人物的生平事迹、重要成就和历史贡献
2. 包含具体的年代、地点、事件等历史细节
3. 分析人物在历史背景下的作用和影响
4. 客观评价人物的功过是非
5. 避免空洞的模板化描述，专注于具体史实
6. 必须包含人物的具体生平和重要事件
"""
        elif "技术" in topic or "科技" in topic:
            topic_guidance = """
技术报告要求：
1. 准确描述技术原理、特点和应用
2. 包含具体的技术参数和性能指标
3. 分析技术的优势和局限性
4. 说明技术的实际应用场景
5. 避免过于技术化的术语，保持可读性
"""
        elif "商业" in topic or "经济" in topic:
            topic_guidance = """
商业报告要求：
1. 提供具体的市场数据和分析
2. 包含财务指标和经营状况
3. 分析竞争优势和风险因素
4. 给出明确的结论和建议
5. 使用客观的数据支撑观点
"""
    
    prompt = f"""
你是一个专业的报告撰写专家，擅长将复杂信息转化为清晰、准确、专业的报告。

任务：基于提供的原始内容，生成一份高质量的{format.upper()}格式报告。

报告要求：
- 标题：{title}
- 风格：专业、客观、严谨
- 字数限制：{max_words}字以内
- 格式：{format.upper()}
- 主题聚焦：{topic if topic else '根据内容自动识别'}

{topic_guidance}

原始内容：
{content[:3000]}

核心要求：
1. **内容准确性**：严格基于原始内容，不添加虚构信息
2. **主题相关性**：所有内容必须与主题高度相关，删除无关内容
3. **信息密度**：每句话都要包含有价值的信息，避免空洞描述
4. **结构清晰**：逻辑层次分明，便于阅读和理解
5. **专业表达**：使用准确、专业的语言

禁止事项：
- 不要使用"本报告基于对输入内容的深入分析"等模板化开头
- 不要添加"通过智能分析技术"等无关的技术描述
- 不要包含"适合一般读者阅读"等空洞的评价
- 不要使用"具有重要参考价值"等无意义的总结
- 不要添加与主题无关的通用性描述

报告结构：
1. 概述：简要介绍主题和核心要点
2. 主要内容：详细阐述关键信息，包含具体的事实和数据
3. 重要发现：突出重要结论或特点
4. 结论：总结核心观点

请直接生成报告内容，不要添加任何解释或说明：
"""
    
    return prompt

def _call_llm_api_with_fallback(prompt: str, llm_provider: str = "auto") -> str:
    """调用LLM API，支持多种提供商和回退机制"""
    
    # 自动选择LLM提供商
    if llm_provider == "auto":
        if os.getenv("OPENAI_API_KEY"):
            llm_provider = "openai"
        elif os.getenv("BAIDU_API_KEY"):
            llm_provider = "baidu"
        else:
            llm_provider = "fallback"
    
    try:
        if llm_provider == "openai":
            return _call_openai_api(prompt)
        elif llm_provider == "baidu":
            return _call_baidu_api(prompt)
        else:
            return _generate_fallback_report_simple(prompt)
            
    except Exception as e:
        logging.warning(f"LLM API调用失败: {e}")
        return _generate_fallback_report_simple(prompt)

def _call_openai_api(prompt: str) -> str:
    """调用OpenAI API"""
    try:
        import openai
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("未设置OPENAI_API_KEY环境变量")
        
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一个专业的报告撰写专家，擅长生成准确、专业、结构清晰的报告。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.3,
            top_p=0.9
        )
        return response.choices[0].message.content
        
    except Exception as e:
        logging.error(f"OpenAI API调用失败: {e}")
        raise e

def _call_baidu_api(prompt: str) -> str:
    """调用百度文心一言API"""
    try:
        from erniebot import AsyncErnieBot
        import asyncio
        
        api_key = os.getenv("BAIDU_API_KEY")
        if not api_key:
            raise ValueError("未设置BAIDU_API_KEY环境变量")
        
        client = AsyncErnieBot(api_key=api_key)
        
        # 使用同步方式调用异步API
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(
                client.chat.completions.create(
                    model="ernie-bot-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0.3
                )
            )
            return response.choices[0].message.content
        finally:
            loop.close()
            
    except Exception as e:
        logging.error(f"百度API调用失败: {e}")
        raise e

def _generate_fallback_report_simple(prompt: str) -> str:
    """简单的回退报告生成"""
    lines = prompt.split('\n')
    
    # 提取标题
    title = "报告"
    for line in lines:
        if "标题：" in line:
            title = line.split("：")[1].strip()
            break
    
    # 提取主题
    topic = None
    for line in lines:
        if "主题聚焦：" in line:
            topic_part = line.split("：")[1].strip()
            if topic_part != "根据内容自动识别":
                topic = topic_part
            break
    
    # 生成专业报告
    report = f"# {title}\n\n"
    
    if topic:
        report += f"## 概述\n\n"
        if "历史" in topic or "人物" in topic:
            report += f"本报告聚焦{topic}相关内容，基于提供的原始信息进行专业分析。\n\n"
        else:
            report += f"本报告针对{topic}主题进行深入分析，提取关键信息并形成专业见解。\n\n"
    
    report += "## 主要内容\n\n"
    report += "基于原始内容的专业分析，我们识别出以下关键信息：\n\n"
    
    if topic and ("历史" in topic or "人物" in topic):
        report += "### 历史背景\n\n"
        report += "相关内容涉及重要的历史时期和背景。\n\n"
        report += "### 主要事迹\n\n"
        report += "包含具体的历史事件和重要成就。\n\n"
        report += "### 历史影响\n\n"
        report += "对历史发展的重要贡献和影响。\n\n"
    else:
        report += "### 核心要点\n\n"
        report += "识别出的主要信息和关键要点。\n\n"
        report += "### 重要发现\n\n"
        report += "基于分析得出的重要结论。\n\n"
    
    report += "## 结论\n\n"
    report += "本报告基于原始内容提供了专业的分析和总结。"
    
    return report

def _get_extraction_method(content: Union[str, list, dict]) -> str:
    """获取内容提取方法"""
    if isinstance(content, str):
        return "direct_string"
    elif isinstance(content, list):
        return "list_extraction"
    elif isinstance(content, dict):
        return "dict_extraction"
    else:
        return "unknown" 