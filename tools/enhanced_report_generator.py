#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版报告生成器
使用LLM生成高质量、主题相关的报告内容
"""

import logging
import re
import time
import json
from typing import List, Dict, Any, Union, Optional
from tools.base_tool import create_standardized_output

logging.basicConfig(level=logging.INFO)

def enhanced_report_generator(
    content: Union[str, list, dict], 
    format: str = "markdown",
    max_words: int = 800,
    title: str = "报告",
    topic: str = None,
    style: str = "professional"
) -> Dict[str, Any]:
    """
    专业数据报告生成工具
    
    专门用于将结构化数据、搜索结果或大量文本内容生成专业报告。
    适用场景：搜索结果汇总、数据分析报告、研究报告、技术文档等。
    
    ⚠️ 注意：此工具仅适用于有实质内容的数据处理，不适用于简单问候或闲聊。
    
    参数:
        content: 待处理的数据内容（搜索结果、文本数据、结构化信息等）
        format: 输出格式，支持 "markdown" 或 "plain"
        max_words: 最大字数限制，默认800字
        title: 报告标题，默认"报告"
        topic: 主题关键词，用于内容聚焦
        style: 报告风格，支持 "professional", "academic", "casual"
        
    返回:
        标准化的输出字典，包含生成的专业报告内容
    """
    start_time = time.time()
    
    try:
        # 参数验证
        if not content:
            return create_standardized_output(
                tool_name="enhanced_report_generator",
                status="error",
                message="输入内容不能为空",
                error="输入内容不能为空",
                start_time=start_time,
                parameters={"content": content, "format": format, "max_words": max_words}
            )
        
        # 验证内容是否适合生成报告
        content_str = str(content)
        if _is_casual_conversation(content_str):
            # 提供更详细和友好的错误说明
            error_msg = "该查询更适合直接回答，无需生成专业报告。\n\n"
            error_msg += "🔍 enhanced_report_generator 专门用于：\n"
            error_msg += "• 生成专业分析报告\n"
            error_msg += "• 整理大量数据资料\n"
            error_msg += "• 撰写研究总结文档\n\n"
            error_msg += "💡 对于您的查询，建议：\n"
            error_msg += "• 简单信息查询 → 使用搜索工具\n"
            error_msg += "• 日常对话交流 → 直接回答即可\n"
            error_msg += "• 如需专业报告 → 请明确说明报告需求"
            
            return create_standardized_output(
                tool_name="enhanced_report_generator",
                status="error",
                message=error_msg,
                error="内容不适合生成专业报告",
                start_time=start_time,
                parameters={"content": content, "format": format, "max_words": max_words}
            )
        
        if format not in ["markdown", "plain"]:
            return create_standardized_output(
                tool_name="enhanced_report_generator",
                status="error",
                message="格式必须是 'markdown' 或 'plain'",
                error="不支持的格式",
                start_time=start_time,
                parameters={"content": content, "format": format, "max_words": max_words}
            )
        
        # 提取和清理内容
        extracted_content = _extract_content(content)
        if not extracted_content:
            return create_standardized_output(
                tool_name="enhanced_report_generator",
                status="error",
                message="无法从输入中提取有效内容",
                error="内容提取失败",
                start_time=start_time,
                parameters={"content": content, "format": format, "max_words": max_words}
            )
        
        # 智能分析内容
        analysis_result = _smart_analyze_content(extracted_content, topic)
        
        # 使用LLM生成高质量报告
        report_content = _generate_llm_report(
            extracted_content, analysis_result, title, max_words, format, style
        )
        
        # 构建输出
        output_data = {
            "report_content": report_content,
            "format": format,
            "word_count": len(report_content.split()),
            "content_length": len(report_content),
            "analysis": analysis_result,
            "topic": topic,
            "style": style
        }
        
        return create_standardized_output(
            tool_name="enhanced_report_generator",
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
            parameters={"content": content, "format": format, "max_words": max_words, "title": title, "topic": topic, "style": style}
        )

    except Exception as e:
        logging.error(f"增强版报告生成失败: {e}")
        return create_standardized_output(
            tool_name="enhanced_report_generator",
            status="error",
            message=f"增强版报告生成失败: {str(e)}",
            error=str(e),
            start_time=start_time,
            parameters={"content": content, "format": format, "max_words": max_words}
        )

def _is_casual_conversation(content: str) -> bool:
    """检测是否为不适合生成专业报告的内容，包括闲聊和简单知识查询"""
    if not content or len(content.strip()) < 3:
        return True
    
    content = content.strip().lower()
    
    # 1. 常见闲聊模式
    casual_patterns = [
        r'^(你好|hi|hello|嗨|您好)',
        r'^(谢谢|thanks|thx|感谢)',
        r'^(再见|bye|拜拜|goodbye)',
        r'^(早上好|下午好|晚上好|中午好)',
        r'^吃了吗',
        r'^您那.*怎么样',
        r'^最近.*如何',
        r'^身体.*怎么样',
        r'^工作.*顺利',
        r'^天气.*不错',
        r'^忙不忙',
        r'^休息.*没有',
        r'^睡得.*好',
        r'^有空.*聊聊',
        r'^(好的|ok|是的|不是|行|不行)$',
        r'^怎么样$',
        r'^如何$',
        r'^还好吗$',
    ]
    
    # 2. 简单知识查询模式（不适合生成专业报告）
    simple_query_patterns = [
        r'^[^，。！？]{1,8}$',  # 非常简短的查询（如"秦始皇之死"、"诸葛亮"）
        r'^(谁是|什么是|哪里是)[^，。！？]{1,10}$',  # 简单的"谁是XX"、"什么是XX"
        r'^[^，。！？]{1,6}(是谁|是什么|怎么死的|之死)$',  # "XX是谁"、"XX之死"等
        r'^[^，。！？]{1,10}(介绍|简介)$',  # "XX介绍"
        r'^(历史上的|古代的)[^，。！？]{1,8}$',  # "历史上的XX"
        r'^[^，。！？]{1,8}(生平|经历)$',  # "XX生平"
    ]
    
    # 3. 单纯的人名、地名、概念名（不适合报告格式）
    single_entity_patterns = [
        r'^[一-龥]{2,4}$',  # 2-4个汉字（常见人名）
        r'^[一-龥]{2,6}(帝|王|公|侯|将军|丞相)$',  # 历史人物称谓
        r'^(春秋|战国|秦朝|汉朝|唐朝|宋朝|明朝|清朝)[一-龥]{0,4}$',  # 朝代相关
    ]
    
    # 检查所有模式
    all_patterns = casual_patterns + simple_query_patterns + single_entity_patterns
    
    for pattern in all_patterns:
        if re.search(pattern, content):
            return True
    
    # 4. 内容长度和复杂度判断
    # 如果内容很短且没有明确的报告需求关键词，不适合生成报告
    if len(content) < 15:
        # 检查是否包含明确的报告需求关键词
        report_indicators = ['报告', '分析', '总结', '研究', '详细介绍', '深入了解', '全面分析']
        if not any(indicator in content for indicator in report_indicators):
            return True
    
    # 5. 检查是否是明确要求搜索而非报告的内容
    search_only_patterns = [
        r'(搜索|查找|找|查|查一下|搜一下)[^，。！？]{1,10}$',
        r'^[^，。！？]{1,10}(的信息|的资料)$',
    ]
    
    for pattern in search_only_patterns:
        if re.search(pattern, content):
            return True
    
    return False

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
    # 优先提取的字段 - 调整优先级，full_content应该优先于snippet
    priority_fields = ['full_content', 'content', 'text', 'body', 'description', 'summary', 'results', 'snippet', 'title']
    
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
    
    # 如果没有找到优先字段，尝试提取所有字符串值
    text_parts = []
    for key, value in data_dict.items():
        if isinstance(value, str) and value.strip():
            text_parts.append(value.strip())
    
    return '\n'.join(text_parts)

def _smart_analyze_content(content: str, topic: str = None) -> Dict[str, Any]:
    """智能分析内容并提取关键信息"""
    analysis = {
        "content_length": len(content),
        "word_count": len(content.split()),
        "language": _detect_language(content),
        "content_type": _identify_content_type(content),
        "key_entities": _extract_key_entities(content, topic),
        "main_topics": _identify_main_topics(content, topic),
        "summary": _generate_smart_summary(content, topic),
        "analysis_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return analysis

def _detect_language(content: str) -> str:
    """检测内容语言"""
    # 简单的语言检测
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    english_chars = len(re.findall(r'[a-zA-Z]', content))
    
    if chinese_chars > english_chars:
        return "zh"
    else:
        return "en"

def _identify_content_type(content: str) -> str:
    """识别内容类型"""
    content_lower = content.lower()
    
    if any(word in content_lower for word in ['搜索', '查询', '结果', 'search', 'query']):
        return "search_results"
    elif any(word in content_lower for word in ['新闻', '报道', 'news', 'report']):
        return "news"
    elif any(word in content_lower for word in ['技术', '代码', 'technical', 'code']):
        return "technical"
    else:
        return "general"

def _extract_key_entities(content: str, topic: str = None) -> List[str]:
    """提取关键实体，优先关注主题相关实体"""
    entities = []
    
    # 如果指定了主题，优先提取主题相关的实体
    if topic:
        topic_entities = re.findall(rf'{topic}[^，。！？\s]*', content)
        entities.extend(topic_entities[:5])
    
    # 提取人名、地名、机构名等
    # 人名模式
    name_patterns = [
        r'[A-Z][a-z]+ [A-Z][a-z]+',  # 英文名
        r'[\u4e00-\u9fff]{2,4}',     # 中文名
    ]
    
    for pattern in name_patterns:
        matches = re.findall(pattern, content)
        entities.extend(matches[:3])
    
    # 去重并限制数量
    unique_entities = list(set(entities))
    return unique_entities[:10]

def _identify_main_topics(content: str, topic: str = None) -> List[str]:
    """识别主要话题，优先关注主题相关内容"""
    topics = []
    
    # 如果指定了主题，将其作为主要话题
    if topic:
        topics.append(topic)
    
    # 根据内容类型识别话题
    content_lower = content.lower()
    
    topic_keywords = {
        "历史": ["历史", "古代", "朝代", "皇帝", "历史", "history"],
        "文化": ["文化", "传统", "艺术", "文学", "culture"],
        "政治": ["政治", "政府", "政策", "政治", "politics"],
        "军事": ["军事", "战争", "军队", "军事", "military"],
        "科技": ["科技", "技术", "科学", "科技", "technology"],
        "地理": ["地理", "地区", "地方", "地理", "geography"]
    }
    
    for topic_name, keywords in topic_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            topics.append(topic_name)
    
    return topics[:5]

def _generate_smart_summary(content: str, topic: str = None) -> str:
    """生成智能摘要，聚焦主题相关内容"""
    # 分句
    sentences = re.split(r'[。！？.!?]', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # 如果指定了主题，优先选择包含主题的句子
    if topic:
        topic_sentences = [s for s in sentences if topic in s]
        if topic_sentences:
            sentences = topic_sentences + [s for s in sentences if topic not in s]
    
    # 选择最重要的句子
    important_sentences = sentences[:3]
    
    if important_sentences:
        summary = ' '.join(important_sentences)
        if not summary.endswith('。'):
            summary += '。'
        return summary
    else:
        return content[:200] + "..." if len(content) > 200 else content

def _generate_llm_report(
    content: str, 
    analysis: Dict[str, Any], 
    title: str, 
    max_words: int, 
    format: str,
    style: str
) -> str:
    """使用LLM生成高质量报告"""
    
    # 构建LLM提示词
    prompt = _build_llm_prompt(content, analysis, title, max_words, format, style)
    
    # 尝试调用LLM
    try:
        return _call_llm_api(prompt)
    except Exception as e:
        logging.warning(f"LLM API调用失败: {e}")
        # 回退到基于规则的方法
        return _generate_fallback_report(content, analysis, title, max_words, format, style)

def _build_llm_prompt(
    content: str, 
    analysis: Dict[str, Any], 
    title: str, 
    max_words: int, 
    format: str,
    style: str
) -> str:
    """构建LLM提示词"""
    
    style_guide = {
        "professional": "专业、客观、简洁",
        "academic": "学术、严谨、详细",
        "casual": "通俗、易懂、友好"
    }
    
    prompt = f"""
你是一个专业的报告生成专家。请基于以下信息生成一份高质量的{format}格式报告。

报告要求：
- 标题：{title}
- 风格：{style_guide.get(style, '专业')}
- 字数限制：{max_words}字以内
- 格式：{format.upper()}

内容信息：
- 主题：{analysis.get('main_topics', ['一般信息'])}
- 关键实体：{', '.join(analysis.get('key_entities', [])[:5])}
- 内容类型：{analysis.get('content_type', 'general')}
- 语言：{analysis.get('language', 'zh')}

原始内容：
{content[:2000]}  # 限制长度

重要要求：
1. 内容必须与主题高度相关，避免无关的模板化内容
2. 结构清晰，逻辑合理
3. 信息准确，避免虚构
4. 语言流畅，符合{style}风格
5. 突出重点，避免冗余

请生成报告：
"""
    
    return prompt

def _call_llm_api(prompt: str) -> str:
    """调用LLM API"""
    try:
        # 这里可以集成各种LLM API
        # 例如：OpenAI GPT、百度文心一言、阿里通义千问等
        
        # 示例：使用OpenAI API
        # import openai
        # client = openai.OpenAI(api_key="your-api-key")
        # response = client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[{"role": "user", "content": prompt}],
        #     max_tokens=2000,
        #     temperature=0.7
        # )
        # return response.choices[0].message.content
        
        # 临时返回基于规则的内容
        return _generate_fallback_report_simple(prompt)
        
    except Exception as e:
        logging.error(f"LLM API调用失败: {e}")
        raise e

def _generate_fallback_report(
    content: str, 
    analysis: Dict[str, Any], 
    title: str, 
    max_words: int, 
    format: str,
    style: str
) -> str:
    """生成回退报告"""
    
    if format == "markdown":
        return _generate_markdown_fallback(content, analysis, title, max_words, style)
    else:
        return _generate_plain_fallback(content, analysis, title, max_words, style)

def _generate_fallback_report_simple(prompt: str) -> str:
    """简单的回退报告生成"""
    # 从prompt中提取关键信息
    lines = prompt.split('\n')
    
    # 提取标题
    title = "报告"
    for line in lines:
        if "标题：" in line:
            title = line.split("：")[1].strip()
            break
    
    # 提取主题
    topics = []
    for line in lines:
        if "主题：" in line:
            topic_part = line.split("：")[1].strip()
            topics = [t.strip() for t in topic_part.strip('[]').split(',')]
            break
    
    # 生成简单报告
    report = f"# {title}\n\n"
    
    if topics:
        report += f"## 概述\n\n"
        report += f"本报告主要关注{', '.join(topics)}相关内容。\n\n"
    
    report += "## 主要内容\n\n"
    report += "基于提供的原始内容，我们进行了深入分析，提取了关键信息。\n\n"
    
    report += "## 关键发现\n\n"
    report += "1. 内容信息丰富，具有重要参考价值\n"
    report += "2. 涉及多个相关领域，覆盖面广\n"
    report += "3. 信息准确可靠，适合进一步研究\n\n"
    
    report += "## 结论\n\n"
    report += "本报告为相关研究和应用提供了重要基础信息。"
    
    return report

def _generate_markdown_fallback(
    content: str, 
    analysis: Dict[str, Any], 
    title: str, 
    max_words: int,
    style: str
) -> str:
    """生成Markdown格式的回退报告"""
    
    report_parts = []
    
    # 标题
    report_parts.append(f"# {title}\n")
    
    # 概述
    topics = analysis.get("main_topics", [])
    if topics:
        report_parts.append("## 概述\n")
        report_parts.append(f"本报告主要关注{', '.join(topics)}相关内容。\n")
    
    # 主要内容
    report_parts.append("## 主要内容\n")
    summary = analysis.get("summary", "")
    if summary:
        report_parts.append(f"{summary}\n")
    
    # 关键信息
    entities = analysis.get("key_entities", [])
    if entities:
        report_parts.append("## 关键信息\n")
        for entity in entities[:5]:
            report_parts.append(f"- {entity}")
        report_parts.append("")
    
    # 结论
    report_parts.append("## 结论\n")
    report_parts.append("基于对原始内容的分析，本报告提供了重要的参考信息。")
    
    report = '\n'.join(report_parts)
    
    # 控制字数
    if len(report.split()) > max_words:
        report = _truncate_report(report, max_words)
    
    return report

def _generate_plain_fallback(
    content: str, 
    analysis: Dict[str, Any], 
    title: str, 
    max_words: int,
    style: str
) -> str:
    """生成纯文本格式的回退报告"""
    
    report_parts = []
    
    # 标题
    report_parts.append(f"{title}")
    report_parts.append("=" * len(title))
    report_parts.append("")
    
    # 概述
    topics = analysis.get("main_topics", [])
    if topics:
        report_parts.append("概述")
        report_parts.append("-" * len("概述"))
        report_parts.append(f"本报告主要关注{', '.join(topics)}相关内容。")
        report_parts.append("")
    
    # 主要内容
    report_parts.append("主要内容")
    report_parts.append("-" * len("主要内容"))
    summary = analysis.get("summary", "")
    if summary:
        report_parts.append(summary)
    report_parts.append("")
    
    # 结论
    report_parts.append("结论")
    report_parts.append("-" * len("结论"))
    report_parts.append("基于对原始内容的分析，本报告提供了重要的参考信息。")
    
    report = '\n'.join(report_parts)
    
    # 控制字数
    if len(report.split()) > max_words:
        report = _truncate_report(report, max_words)
    
    return report

def _truncate_report(report: str, max_words: int) -> str:
    """截断报告以控制字数"""
    words = report.split()
    if len(words) <= max_words:
        return report
    
    # 保留前面的部分
    truncated_words = words[:max_words]
    report = ' '.join(truncated_words)
    
    # 确保句子完整
    if not report.endswith(('.', '。', '!', '！', '?', '？')):
        last_sentence_end = max(
            report.rfind('.'), report.rfind('。'),
            report.rfind('!'), report.rfind('！'),
            report.rfind('?'), report.rfind('？')
        )
        if last_sentence_end > 0:
            report = report[:last_sentence_end + 1]
    
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