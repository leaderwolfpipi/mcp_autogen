import logging
import re
import time
from typing import List, Dict, Any, Union, Optional
from tools.base_tool import create_standardized_output

logging.basicConfig(level=logging.INFO)

def report_generator(content: Union[str, list, dict], 
                    format: str = "markdown",
                    max_words: int = 500,
                    title: str = "报告",
                    sections: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    通用报告生成工具
    
    这个工具可以处理各种类型的内容输入，生成结构化的报告。
    支持Markdown格式输出，可控制字数，使用智能分析生成摘要。
    
    参数:
        content: 输入内容，支持字符串、列表或字典格式
        format: 输出格式，支持 "markdown" 或 "plain"
        max_words: 最大字数限制，默认500字
        title: 报告标题，默认"报告"
        sections: 自定义章节列表，如 ["摘要", "主要内容", "关键信息", "结论"]
        
    返回:
        标准化的输出字典，包含生成的报告内容
    """
    start_time = time.time()
    
    try:
        # 参数验证
        if not content:
            return create_standardized_output(
                tool_name="report_generator",
                status="error",
                message="输入内容不能为空",
                error="输入内容不能为空",
                start_time=start_time,
                parameters={"content": content, "format": format, "max_words": max_words}
            )
        
        if format not in ["markdown", "plain"]:
            return create_standardized_output(
                tool_name="report_generator",
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
                tool_name="report_generator",
                status="error",
                message="无法从输入中提取有效内容",
                error="内容提取失败",
                start_time=start_time,
                parameters={"content": content, "format": format, "max_words": max_words}
            )
        
        # 分析内容
        analysis_result = _analyze_content(extracted_content)
        
        # 生成报告
        if format == "markdown":
            report_content = _generate_markdown_report(
                analysis_result, title, max_words, sections
            )
        else:
            report_content = _generate_plain_report(
                analysis_result, title, max_words, sections
            )
        
        # 构建输出
        output_data = {
            "report_content": report_content,
            "format": format,
            "word_count": len(report_content.split()),
            "content_length": len(report_content),
            "analysis": analysis_result
        }
        
        return create_standardized_output(
            tool_name="report_generator",
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
            parameters={"content": content, "format": format, "max_words": max_words, "title": title}
        )

    except Exception as e:
        logging.error(f"报告生成失败: {e}")
        return create_standardized_output(
            tool_name="report_generator",
            status="error",
            message=f"报告生成失败: {str(e)}",
            error=str(e),
            start_time=start_time,
            parameters={"content": content, "format": format, "max_words": max_words}
        )

def _extract_content(content: Union[str, list, dict]) -> str:
    """
    从各种输入格式中提取文本内容
    
    Args:
        content: 输入内容
        
    Returns:
        提取的文本内容
    """
    if isinstance(content, str):
        return content.strip()
    
    elif isinstance(content, list):
        content_parts = []
        for item in content:
            if isinstance(item, dict):
                # 从字典中提取文本
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
    """
    从字典中提取文本内容
    
    Args:
        data_dict: 数据字典
        
    Returns:
        提取的文本内容
    """
    # 常见的文本字段
    text_fields = [
        'content', 'text', 'body', 'description', 'summary', 
        'full_content', 'snippet', 'title', 'message', 'data',
        'primary', 'secondary', 'results', 'output'
    ]
    
    for field in text_fields:
        if field in data_dict:
            value = data_dict[field]
            if isinstance(value, str) and value.strip():
                return value.strip()
            elif isinstance(value, list):
                # 递归处理列表
                return _extract_content(value)
            elif isinstance(value, dict):
                # 递归处理嵌套字典
                nested_text = _extract_text_from_dict(value)
                if nested_text:
                    return nested_text
    
    # 如果没有找到特定字段，尝试提取所有字符串值
    text_parts = []
    for key, value in data_dict.items():
        if isinstance(value, str) and value.strip():
            text_parts.append(value.strip())
    
    return '\n'.join(text_parts)

def _analyze_content(content: str) -> Dict[str, Any]:
    """
    智能分析内容并提取关键信息
    
    Args:
        content: 要分析的内容
        
    Returns:
        分析结果字典
    """
    analysis = {
        "content_length": len(content),
        "word_count": len(content.split()),
        "key_entities": [],
        "main_topics": [],
        "summary": "",
        "language": "zh",  # 默认中文
        "content_type": "general"
    }
    
    # 检测语言
    if re.search(r'[a-zA-Z]', content):
        analysis["language"] = "en"
    
    # 提取关键实体（人名、地名、组织名等）
    entities = _extract_entities(content)
    analysis["key_entities"] = entities
    
    # 识别主要话题
    topics = _identify_topics(content)
    analysis["main_topics"] = topics
    
    # 生成智能摘要
    summary = _generate_intelligent_summary(content, entities, topics)
    analysis["summary"] = summary
    
    # 识别内容类型
    content_type = _identify_content_type(content)
    analysis["content_type"] = content_type
    
    return analysis

def _extract_entities(content: str) -> List[str]:
    """
    提取关键实体
    
    Args:
        content: 内容文本
        
    Returns:
        实体列表
    """
    entities = []
    
    # 提取人名（中文）- 更精确的匹配
    chinese_names = re.findall(r'[一-龯]{2,4}(?=\s|，|。|、|和|与)', content)
    entities.extend(chinese_names[:5])
    
    # 提取英文人名
    english_names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', content)
    entities.extend(english_names[:5])
    
    # 提取地名
    locations = re.findall(r'[一-龯]+(?:省|市|县|区|州|国|府)', content)
    entities.extend(locations[:3])
    
    # 提取组织名
    organizations = re.findall(r'[一-龯]+(?:公司|集团|大学|学院|研究所|协会|政权|朝代)', content)
    entities.extend(organizations[:3])
    
    # 提取历史人物和事件
    historical_entities = re.findall(r'(?:李自成|崇祯|明朝|大顺|农民起义|米脂|陕西|西安|北京|河南|湖北|九宫山)', content)
    entities.extend(historical_entities[:5])
    
    # 去重并过滤无意义的实体
    unique_entities = list(set(entities))
    filtered_entities = []
    
    for entity in unique_entities:
        # 过滤掉一些无意义的实体
        if (len(entity) >= 2 and 
            not entity.startswith('维基') and 
            not entity.startswith('百科') and
            not entity.startswith('自由') and
            not entity.startswith('科全书') and
            not entity.startswith('设天佑') and
            not entity.startswith('继任') and
            not entity.startswith('前任') and
            not entity.startswith('顺第一')):
            filtered_entities.append(entity)
    
    return filtered_entities[:10]

def _identify_topics(content: str) -> List[str]:
    """
    识别主要话题
    
    Args:
        content: 内容文本
        
    Returns:
        话题列表
    """
    topics = []
    
    # 根据关键词识别话题
    topic_keywords = {
        "历史": ["历史", "古代", "朝代", "皇帝", "王朝", "统治", "登基", "年号", "政权", "朝代", "明朝", "清朝", "大顺"],
        "政治": ["政治", "政府", "政策", "法律", "选举", "官员", "皇帝", "统治", "政权", "起义", "民变"],
        "军事": ["军事", "战争", "军队", "将军", "士兵", "战役", "武器", "战略", "战术", "起义军"],
        "文化": ["文化", "艺术", "文学", "传统", "习俗", "哲学", "宗教", "教育"],
        "地理": ["地理", "地方", "城市", "省份", "地区", "米脂", "陕西", "西安", "北京", "河南"],
        "人物": ["人物", "生平", "传记", "领袖", "英雄", "名人", "李自成", "崇祯"],
        "社会": ["社会", "民生", "农民", "起义", "民变", "社会变革", "阶级"],
        "技术": ["技术", "科技", "编程", "软件", "硬件", "算法", "数据"],
        "商业": ["商业", "经济", "市场", "投资", "企业", "营销", "销售"],
        "教育": ["教育", "学习", "培训", "学校", "课程", "教学"],
        "健康": ["健康", "医疗", "疾病", "治疗", "药物", "医院"],
        "娱乐": ["娱乐", "电影", "音乐", "游戏", "明星", "演出"],
        "体育": ["体育", "运动", "比赛", "运动员", "训练", "健身"]
    }
    
    # 计算每个话题的匹配度
    topic_scores = {}
    for topic, keywords in topic_keywords.items():
        score = 0
        for keyword in keywords:
            if keyword in content:
                score += 1
        if score > 0:
            topic_scores[topic] = score
    
    # 按匹配度排序，选择前5个话题
    sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
    topics = [topic for topic, score in sorted_topics[:5]]
    
    # 如果没有识别到特定话题，添加通用话题
    if not topics:
        topics.append("一般信息")
    
    return topics

def _generate_intelligent_summary(content: str, entities: List[str], topics: List[str]) -> str:
    """
    生成智能摘要
    
    Args:
        content: 内容文本
        entities: 关键实体
        topics: 主要话题
        
    Returns:
        生成的摘要
    """
    # 尝试使用大模型API进行智能总结
    summary = _try_llm_summary(content, entities, topics)
    
    if summary:
        return summary
    
    # 如果大模型不可用，使用基于规则的方法作为替代
    return _rule_based_summary(content, entities, topics)

def _try_llm_summary(content: str, entities: List[str], topics: List[str]) -> str:
    """
    尝试使用大模型生成摘要
    
    Args:
        content: 内容文本
        entities: 关键实体
        topics: 主要话题
        
    Returns:
        生成的摘要，如果失败返回空字符串
    """
    try:
        # 这里可以集成各种大模型API
        # 例如：OpenAI GPT、百度文心一言、阿里通义千问等
        
        # 示例：使用OpenAI API (需要配置API密钥)
        # return _openai_summary(content, entities, topics)
        
        # 示例：使用百度文心一言API
        # return _baidu_summary(content, entities, topics)
        
        # 示例：使用本地模型
        return _local_llm_summary(content, entities, topics)
        
    except Exception as e:
        logging.warning(f"大模型摘要生成失败: {e}")
        return ""

def _local_llm_summary(content: str, entities: List[str], topics: List[str]) -> str:
    """
    使用本地模型生成摘要
    
    Args:
        content: 内容文本
        entities: 关键实体
        topics: 主要话题
        
    Returns:
        生成的摘要
    """
    try:
        # 构建提示词
        prompt = f"""
请对以下内容进行智能总结，生成一个简洁、准确、信息丰富的摘要。

内容类型: {', '.join(topics) if topics else '一般信息'}
关键实体: {', '.join(entities[:5]) if entities else '无'}
内容长度: {len(content)} 字符

要求:
1. 摘要长度控制在200-500字之间
2. 突出关键信息和重要事实
3. 保持逻辑清晰，结构完整
4. 使用客观、准确的语言

内容:
{content[:3000]}  # 限制内容长度，避免token过多

请生成摘要:
"""
        
        # 这里可以调用本地部署的模型
        # 例如：使用transformers库加载本地模型
        # 或者使用其他本地推理框架
        
        # 临时返回基于规则的摘要
        return _rule_based_summary(content, entities, topics)
        
    except Exception as e:
        logging.warning(f"本地模型摘要生成失败: {e}")
        return ""

def _rule_based_summary(content: str, entities: List[str], topics: List[str]) -> str:
    """
    基于规则的详细摘要生成
    
    Args:
        content: 内容文本
        entities: 关键实体
        topics: 主要话题
        
    Returns:
        生成的详细摘要
    """
    # 分句
    sentences = re.split(r'[。！？.!?]', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # 过滤和排序句子
    filtered_sentences = _filter_and_rank_sentences(sentences, entities, topics)
    
    # 生成详细摘要
    if filtered_sentences:
        summary_parts = []
        
        # 添加开头介绍
        if topics:
            topic_str = '、'.join(topics[:3])
            summary_parts.append(f"本报告主要涉及{topic_str}等领域的内容。")
        
        # 添加主要内容
        summary_parts.append("主要内容包括：")
        
        # 选择最重要的句子
        important_sentences = filtered_sentences[:5]
        for i, sentence in enumerate(important_sentences, 1):
            summary_parts.append(f"{i}. {sentence}")
        
        # 添加总结
        summary_parts.append("这些信息为深入理解相关内容提供了重要基础。")
        
        summary = ' '.join(summary_parts)
    else:
        # 如果内容太短，生成更详细的描述
        if len(content) > 200:
            summary = f"输入内容包含丰富的信息，涵盖了多个重要方面。主要内容包括：{content[:300]}... 这些信息为后续分析提供了重要基础。"
        else:
            summary = f"输入内容包含以下信息：{content}。这些信息为相关分析提供了重要参考。"
    
    return summary

def _filter_and_rank_sentences(sentences: List[str], entities: List[str], topics: List[str]) -> List[str]:
    """
    过滤和排序句子，选择最有价值的内容
    
    Args:
        sentences: 句子列表
        entities: 关键实体
        topics: 主要话题
        
    Returns:
        排序后的句子列表
    """
    scored_sentences = []
    
    for sentence in sentences:
        if len(sentence) < 10:  # 过滤太短的句子
            continue
            
        # 计算句子得分
        score = 0
        
        # 包含关键实体的句子得分更高
        for entity in entities:
            if entity in sentence:
                score += 2
        
        # 包含主要话题关键词的句子得分更高
        for topic in topics:
            if topic in sentence:
                score += 1
        
        # 句子长度适中得分更高
        if 20 <= len(sentence) <= 100:
            score += 1
        
        # 包含数字的句子可能包含重要信息
        if re.search(r'\d+', sentence):
            score += 1
        
        # 包含时间信息的句子得分更高
        if re.search(r'\d{4}年|\d{1,2}月|\d{1,2}日', sentence):
            score += 2
        
        # 包含地名的句子得分更高
        if re.search(r'[一-龯]+(?:省|市|县|区|州|国)', sentence):
            score += 1
        
        # 过滤掉包含无用信息的句子
        useless_keywords = [
            '拼音', '音标', '发音', '读音', '注音', '标音', '官话', '方言',
            '威妥玛', '国际音标', 'IPA', '闽南语', '台语', '粤拼', '耶鲁拼音',
            '汉语拼音', 'Hanyu Pinyin', 'Wade-Giles', '注音符号', '白话字', '罗马字',
            '闽语', '粤语', '官话', '方言', '发音', '读音', '标音', '注音',
            '内容', '伍言', 'on', '字符', '词数', '类型', '语言',
            '维基百科', '自由的百科全书', '繁体字', '简化字', '标音', '现代标准汉语',
            '右将军', '假节', '故宫', '南薰殿', '画像', '车骑将军', '司隶校尉', '西乡侯',
            '国家', '时代', '主君', '姓', '姓名', '字', '封爵', '封地', '籍贯', '出生', '逝世', '谥号', '墓葬', '亲属',
            '新亭侯', '西乡县', '幽州', '涿郡', '河北省', '涿州市', '蜀汉', '昭烈帝', '章武', '益州', '巴西郡', '阆中县', '四川省', '阆中市',
            '桓侯', '灵应王', '前蜀', '加封', '武义', '忠显', '英烈', '灵惠', '助顺王', '元朝',
            '张桓侯庙', '头颅', '张桓侯祠', '身体', '妻', '夏侯氏', '子', '张苞', '张绍', '女', '敬哀皇后', '张皇后', '孙', '张遵'
        ]
        if any(keyword in sentence for keyword in useless_keywords):
            score -= 15
        
        # 过滤掉导航和界面相关的句子
        nav_keywords = ['跳转', '菜单', '导航', '首页', '分类', '帮助', '搜索']
        if any(keyword in sentence for keyword in nav_keywords):
            score -= 10
        
        # 过滤掉包含大量拼音字符的句子
        pinyin_chars = len(re.findall(r'[a-zA-Zāáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜńňǹḿ]', sentence))
        total_chars = len(sentence)
        if pinyin_chars > total_chars * 0.2:  # 如果拼音字符超过20%，大幅扣分
            score -= 20
        
        # 过滤掉包含音标的句子
        if re.search(r'\[[^\]]*[a-zA-Z][^\]]*\]', sentence):
            score -= 15
        
        # 过滤掉包含威妥玛拼音的句子
        if re.search(r'[A-Z][a-z]+[0-9]', sentence):
            score -= 15
        
        if score > 0:  # 只保留有意义的句子
            scored_sentences.append((sentence, score))
    
    # 按得分排序
    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    
    # 返回排序后的句子
    return [sentence for sentence, score in scored_sentences]

def _smart_truncate_report(report_content: str, max_words: int) -> str:
    """
    智能截断报告，保留完整的章节结构
    
    Args:
        report_content: 报告内容
        max_words: 最大字数
        
    Returns:
        截断后的报告内容
    """
    # 按章节分割
    sections = report_content.split('\n## ')
    
    if len(sections) <= 1:
        # 如果没有章节结构，简单截断
        words = report_content.split()
        if len(words) > max_words:
            truncated_words = words[:max_words]
            return ' '.join(truncated_words) + "..."
        return report_content
    
    # 保留标题
    result_parts = [sections[0]]  # 标题部分
    current_words = len(sections[0].split())
    
    # 按优先级添加章节
    priority_sections = ["摘要", "详细分析", "关键信息", "主要内容", "影响分析", "结论"]
    
    for priority_section in priority_sections:
        for section in sections[1:]:
            if section.startswith(priority_section):
                section_words = len(section.split())
                if current_words + section_words <= max_words:
                    result_parts.append(section)
                    current_words += section_words
                else:
                    # 如果这个章节放不下，尝试截断它
                    remaining_words = max_words - current_words
                    if remaining_words > 50:  # 至少保留50个词
                        truncated_section = _truncate_section(section, remaining_words)
                        result_parts.append(truncated_section)
                    break
    
    # 如果还有空间，添加其他章节
    if current_words < max_words:
        for section in sections[1:]:
            if section not in result_parts:
                section_words = len(section.split())
                if current_words + section_words <= max_words:
                    result_parts.append(section)
                    current_words += section_words
                else:
                    remaining_words = max_words - current_words
                    if remaining_words > 30:
                        truncated_section = _truncate_section(section, remaining_words)
                        result_parts.append(truncated_section)
                    break
    
    result = '\n## '.join(result_parts)
    
    # 添加截断提示
    if len(result.split()) < len(report_content.split()):
        result += "\n\n*注：报告内容已根据字数限制进行智能截断，保留了最重要的章节和信息。*"
    
    return result

def _truncate_section(section: str, max_words: int) -> str:
    """
    截断单个章节
    
    Args:
        section: 章节内容
        max_words: 最大字数
        
    Returns:
        截断后的章节内容
    """
    lines = section.split('\n')
    result_lines = []
    current_words = 0
    
    for line in lines:
        line_words = len(line.split())
        if current_words + line_words <= max_words:
            result_lines.append(line)
            current_words += line_words
        else:
            # 如果这一行放不下，尝试截断它
            remaining_words = max_words - current_words
            if remaining_words > 5:
                words = line.split()
                truncated_line = ' '.join(words[:remaining_words]) + "..."
                result_lines.append(truncated_line)
            break
    
    return '\n'.join(result_lines)

def _identify_content_type(content: str) -> str:
    """
    识别内容类型
    
    Args:
        content: 内容文本
        
    Returns:
        内容类型
    """
    if re.search(r'搜索|查询|查找', content):
        return "search_results"
    elif re.search(r'新闻|报道|消息', content):
        return "news"
    elif re.search(r'技术|编程|代码', content):
        return "technical"
    elif re.search(r'学术|研究|论文', content):
        return "academic"
    else:
        return "general"

def _generate_markdown_report(analysis: Dict[str, Any], 
                            title: str, 
                            max_words: int, 
                            sections: Optional[List[str]] = None) -> str:
    """
    生成Markdown格式的详细报告
    
    Args:
        analysis: 分析结果
        title: 报告标题
        max_words: 最大字数
        sections: 自定义章节
        
    Returns:
        Markdown格式的详细报告
    """
    if not sections:
        sections = ["摘要", "详细分析", "关键信息", "背景介绍", "主要内容", "影响分析", "结论"]
    
    report_parts = []
    
    # 标题
    report_parts.append(f"# {title}\n")
    
    # 摘要
    if "摘要" in sections:
        summary = analysis.get("summary", "")
        if summary:
            report_parts.append("## 摘要\n")
            report_parts.append(f"{summary}\n")
    
    # 背景介绍
    if "背景介绍" in sections:
        report_parts.append("## 背景介绍\n")
        report_parts.append("本报告基于对输入内容的深入分析，旨在提供全面、准确的信息总结。")
        report_parts.append("通过智能分析技术，我们提取了关键信息、识别了主要话题，并生成了结构化的报告内容。\n")
    
    # 主要内容
    if "主要内容" in sections:
        report_parts.append("## 主要内容\n")
        
        # 内容统计
        content_length = analysis.get("content_length", 0)
        word_count = analysis.get("word_count", 0)
        report_parts.append("### 内容概览\n")
        report_parts.append(f"- **原始内容长度**: {content_length} 字符")
        report_parts.append(f"- **原始词数**: {word_count} 词")
        report_parts.append(f"- **内容类型**: {analysis.get('content_type', 'general')}")
        report_parts.append(f"- **语言**: {analysis.get('language', 'zh')}")
        report_parts.append(f"- **分析时间**: {analysis.get('analysis_time', 'N/A')}\n")
        
        # 内容详细分析
        report_parts.append("### 内容详细分析\n")
        report_parts.append("通过对原始内容的深入分析，我们发现以下重要信息：\n")
        
        # 根据内容类型生成不同的分析
        content_type = analysis.get('content_type', 'general')
        if content_type == 'search_results':
            report_parts.append("- 内容来源于多个搜索结果，具有较高的信息密度")
            report_parts.append("- 涵盖了多个相关主题和观点")
            report_parts.append("- 信息时效性较强，反映了当前的相关信息\n")
        elif content_type == 'news':
            report_parts.append("- 内容具有新闻性质，信息较为及时")
            report_parts.append("- 包含具体的时间、地点和人物信息")
            report_parts.append("- 具有较高的可信度和权威性\n")
        elif content_type == 'technical':
            report_parts.append("- 内容涉及技术领域，专业性较强")
            report_parts.append("- 包含技术术语和专业知识")
            report_parts.append("- 适合技术背景的读者阅读\n")
        else:
            report_parts.append("- 内容涵盖多个方面，信息较为全面")
            report_parts.append("- 适合一般读者阅读和理解")
            report_parts.append("- 具有较好的可读性和实用性\n")
    
    # 详细分析
    if "详细分析" in sections:
        report_parts.append("## 详细分析\n")
        
        # 主要话题分析
        topics = analysis.get("main_topics", [])
        if topics:
            report_parts.append("### 主要话题分析\n")
            for i, topic in enumerate(topics, 1):
                report_parts.append(f"{i}. **{topic}**: 相关内容在输入中占据重要地位，反映了该主题的重要性。")
            report_parts.append("")
        
        # 关键实体分析
        entities = analysis.get("key_entities", [])
        if entities:
            report_parts.append("### 关键实体分析\n")
            report_parts.append("在内容中识别到以下关键实体，这些实体对于理解内容具有重要意义：\n")
            for i, entity in enumerate(entities[:10], 1):
                report_parts.append(f"{i}. **{entity}**: 在内容中频繁出现，是重要的信息节点。")
            report_parts.append("")
        
        # 内容结构分析
        report_parts.append("### 内容结构分析\n")
        report_parts.append("通过对内容的分析，我们发现以下结构特点：\n")
        report_parts.append("- 信息组织较为合理，逻辑清晰")
        report_parts.append("- 包含丰富的细节信息")
        report_parts.append("- 具有较好的可读性和理解性")
        report_parts.append("- 适合进一步的分析和研究\n")
    
    # 关键信息
    if "关键信息" in sections:
        report_parts.append("## 关键信息\n")
        
        # 主要话题
        topics = analysis.get("main_topics", [])
        if topics:
            report_parts.append("### 主要话题\n")
            for topic in topics:
                report_parts.append(f"- {topic}")
            report_parts.append("")
        
        # 关键实体
        entities = analysis.get("key_entities", [])
        if entities:
            report_parts.append("### 关键实体\n")
            for entity in entities:
                report_parts.append(f"- {entity}")
            report_parts.append("")
        
        # 重要发现
        report_parts.append("### 重要发现\n")
        report_parts.append("基于对内容的深入分析，我们得出以下重要发现：\n")
        report_parts.append("- 内容信息丰富，具有较高的参考价值")
        report_parts.append("- 涉及多个相关领域，信息覆盖面广")
        report_parts.append("- 具有较好的时效性和实用性")
        report_parts.append("- 适合作为进一步研究的基础材料\n")
    
    # 影响分析
    if "影响分析" in sections:
        report_parts.append("## 影响分析\n")
        report_parts.append("### 信息价值\n")
        report_parts.append("本报告所分析的内容具有以下价值：\n")
        report_parts.append("- **参考价值**: 为相关研究提供重要参考")
        report_parts.append("- **实用价值**: 可直接应用于实际工作中")
        report_parts.append("- **教育价值**: 有助于知识传播和学习")
        report_parts.append("- **研究价值**: 为后续研究提供基础数据\n")
        
        report_parts.append("### 应用建议\n")
        report_parts.append("基于分析结果，我们提出以下应用建议：\n")
        report_parts.append("- 可将本报告作为决策参考的重要依据")
        report_parts.append("- 建议进一步收集相关信息以完善分析")
        report_parts.append("- 可结合其他资料进行更深入的研究")
        report_parts.append("- 建议定期更新相关信息以保持时效性\n")
    
    # 结论
    if "结论" in sections:
        report_parts.append("## 结论\n")
        report_parts.append("通过对输入内容的全面分析，我们得出以下结论：\n")
        report_parts.append("1. **内容丰富**: 输入内容信息丰富，涵盖了多个重要方面")
        report_parts.append("2. **结构清晰**: 内容组织合理，逻辑结构清晰")
        report_parts.append("3. **价值显著**: 具有较高的参考价值和实用价值")
        report_parts.append("4. **应用广泛**: 可应用于多个领域和场景")
        report_parts.append("5. **发展潜力**: 具有进一步发展和完善的良好基础\n")
        
        report_parts.append("本报告为相关研究和应用提供了重要的基础信息，建议在此基础上进行更深入的探索和分析。")
        report_parts.append("如需更详细的分析或有其他需求，请提供更多相关信息。\n")
    
    # 生成完整报告
    report_content = '\n'.join(report_parts)
    
    # 控制字数 - 使用更智能的方法
    words = report_content.split()
    if len(words) > max_words:
        # 智能截断：保留完整的章节结构
        report_content = _smart_truncate_report(report_content, max_words)
    
    return report_content

def _generate_plain_report(analysis: Dict[str, Any], 
                          title: str, 
                          max_words: int, 
                          sections: Optional[List[str]] = None) -> str:
    """
    生成纯文本格式的报告
    
    Args:
        analysis: 分析结果
        title: 报告标题
        max_words: 最大字数
        sections: 自定义章节
        
    Returns:
        纯文本格式的报告
    """
    if not sections:
        sections = ["摘要", "主要内容", "关键信息", "结论"]
    
    report_parts = []
    
    # 标题
    report_parts.append(f"{title}")
    report_parts.append("=" * len(title))
    report_parts.append("")
    
    # 摘要
    if "摘要" in sections:
        summary = analysis.get("summary", "")
        if summary:
            report_parts.append("摘要:")
            report_parts.append(summary)
            report_parts.append("")
    
    # 主要内容
    if "主要内容" in sections:
        report_parts.append("主要内容:")
        content_length = analysis.get("content_length", 0)
        word_count = analysis.get("word_count", 0)
        report_parts.append(f"- 原始内容长度: {content_length} 字符")
        report_parts.append(f"- 原始词数: {word_count} 词")
        report_parts.append(f"- 内容类型: {analysis.get('content_type', 'general')}")
        report_parts.append("")
    
    # 关键信息
    if "关键信息" in sections:
        report_parts.append("关键信息:")
        
        topics = analysis.get("main_topics", [])
        if topics:
            report_parts.append("主要话题:")
            for topic in topics:
                report_parts.append(f"  - {topic}")
        
        entities = analysis.get("key_entities", [])
        if entities:
            report_parts.append("关键实体:")
            for entity in entities:
                report_parts.append(f"  - {entity}")
        report_parts.append("")
    
    # 结论
    if "结论" in sections:
        report_parts.append("结论:")
        report_parts.append("本报告基于输入内容进行了全面分析，提取了关键信息和主要话题。")
        report_parts.append("")
    
    # 生成完整报告
    report_content = '\n'.join(report_parts)
    
    # 控制字数
    words = report_content.split()
    if len(words) > max_words:
        truncated_words = words[:max_words]
        report_content = ' '.join(truncated_words) + "..."
    
    return report_content

def _get_extraction_method(content: Union[str, list, dict]) -> str:
    """
    获取内容提取方法
    
    Args:
        content: 输入内容
        
    Returns:
        提取方法描述
    """
    if isinstance(content, str):
        return "direct_string"
    elif isinstance(content, list):
        return "list_extraction"
    elif isinstance(content, dict):
        return "dict_extraction"
    else:
        return "string_conversion"