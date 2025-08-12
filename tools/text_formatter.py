import logging
import re
from typing import Union, List, Dict, Any

def text_formatter(text: Union[str, List[Dict[str, Any]]]) -> str:
    """
    Formats the given text or search results by performing several operations:
    - If input is a string: formats the text directly
    - If input is a list of search results: converts search results to formatted text
    - Strips leading and trailing whitespace
    - Converts multiple spaces into a single space
    - Capitalizes the first letter of each sentence

    Args:
        text (Union[str, List[Dict[str, Any]]]): The text to be formatted or search results list.

    Returns:
        str: The formatted text string.
    """
    logger = logging.getLogger("text_formatter")
    
    try:
        logger.info("Starting text formatting")

        # Handle different input types
        if isinstance(text, str):
            # Direct text formatting
            formatted_text = text.strip()
        elif isinstance(text, list):
            # Convert search results to text
            formatted_text = _convert_search_results_to_text(text)
        else:
            raise ValueError("Input must be a string or list of search results")

        # Convert multiple spaces into a single space
        formatted_text = re.sub(r'\s+', ' ', formatted_text)

        # Capitalize the first letter of each sentence
        formatted_text = '. '.join(sentence.capitalize() for sentence in formatted_text.split('. '))

        logger.info("Text formatting completed successfully")
        return formatted_text

    except Exception as e:
        logger.error(f"An error occurred during text formatting: {e}")
        raise

def _convert_search_results_to_text(search_results: List[Dict[str, Any]]) -> str:
    """
    Convert search results to formatted text
    
    Args:
        search_results: List of search result dictionaries
        
    Returns:
        Formatted text string
    """
    if not search_results:
        return "未找到相关搜索结果。"
    
    text_parts = []
    for i, result in enumerate(search_results, 1):
        title = result.get('title', '无标题')
        link = result.get('link', '无链接')
        
        # 优先使用完整内容，如果没有则使用摘要
        content = result.get('full_content', result.get('snippet', '无内容'))
        content_length = result.get('content_length', len(content))
        
        # 格式化每个结果
        result_text = f"【{i}. {title}】\n"
        result_text += f"链接: {link}\n"
        result_text += f"内容长度: {content_length} 字符\n"
        result_text += f"内容摘要: {content[:500]}{'...' if len(content) > 500 else ''}\n"
        
        text_parts.append(result_text)
    
    return "\n\n".join(text_parts)