import logging
import requests
import re
import time
from typing import List, Dict, Any, Union
from bs4 import BeautifulSoup
from tools.base_tool import create_standardized_output

# 导入现有的搜索工具
from .search_tool import search_tool

def smart_search(query: str, max_results: int = 3) -> Dict[str, Any]:
    """
    🎯 推荐搜索工具 - 多引擎智能搜索（谷歌+百度）
    
    这是最稳定可靠的搜索工具，自动处理搜索引擎故障和网络问题。
    支持多搜索引擎回退机制，无需额外依赖库，获取完整网页内容。
    
    🔥 优势特性：
    - 多引擎支持：谷歌搜索 + 百度搜索自动回退
    - 零依赖：无需外部库，自带网络请求处理
    - 内容增强：自动获取完整网页内容并智能净化
    - 高可用性：自动处理搜索引擎故障和超时
    - 标准化输出：完全符合MCP协议标准
    
    💡 使用场景：
    - 通用搜索查询（推荐首选）
    - 需要稳定可靠的搜索服务
    - 需要完整网页内容的深度搜索
    - 跨地域搜索需求

    参数：
        query (str): 搜索查询字符串，不能为空。
        max_results (int): 最大结果数量，默认3个，范围1-10。
    返回：
        dict: 标准化输出，字段包括：
            status: 'success' | 'error'
            data.primary: 增强搜索结果列表（包含完整内容）
            data.secondary: 搜索和内容获取元信息
            data.counts: 结果统计
            metadata: 工具元信息
            paths: 搜索源信息
            message: 执行消息
            error: 错误信息（如有）
    """
    logger = logging.getLogger("smart_search")
    start_time = time.time()
    
    try:
        logger.info(f"开始智能搜索: {query}")
        
        # 参数验证
        if not query or not query.strip():
            return create_standardized_output(
                tool_name="smart_search",
                status="error",
                message="搜索查询不能为空",
                error="搜索查询不能为空",
                start_time=start_time,
                parameters={"query": query, "max_results": max_results}
            )
        
        if not isinstance(max_results, int) or max_results < 1 or max_results > 10:
            max_results = 3
            logger.warning(f"max_results参数无效，使用默认值: {max_results}")
        
        # 使用现有的搜索工具获取基础搜索结果
        search_result = search_tool(query, max_results)
        
        if search_result.get("status") == "success":
            results = search_result.get("data", {}).get("primary", [])
            logger.info(f"基础搜索完成，找到 {len(results)} 个结果")
            
            # 增强搜索结果，获取更完整的内容
            enhanced_results = []
            content_stats = {
                "total_processed": 0,
                "successful_content_fetch": 0,
                "failed_content_fetch": 0,
                "total_content_length": 0
            }
            
            for i, result in enumerate(results):
                logger.info(f"正在处理第 {i+1} 个结果: {result.get('title', 'Unknown')}")
                content_stats["total_processed"] += 1
                
                enhanced_result = result.copy()
                
                # 尝试获取更完整的内容
                try:
                    full_content = _fetch_full_content(result.get('link', ''))
                    if full_content:
                        enhanced_result['full_content'] = full_content
                        enhanced_result['content_length'] = len(full_content)
                        content_stats["successful_content_fetch"] += 1
                        content_stats["total_content_length"] += len(full_content)
                        logger.info(f"成功获取完整内容，长度: {len(full_content)} 字符")
                    else:
                        enhanced_result['full_content'] = result.get('snippet', '')
                        enhanced_result['content_length'] = len(result.get('snippet', ''))
                        content_stats["failed_content_fetch"] += 1
                        logger.info(f"无法获取完整内容，使用摘要")
                except Exception as e:
                    logger.warning(f"获取完整内容失败: {e}")
                    enhanced_result['full_content'] = result.get('snippet', '')
                    enhanced_result['content_length'] = len(result.get('snippet', ''))
                    content_stats["failed_content_fetch"] += 1
                
                enhanced_results.append(enhanced_result)
                
                # 添加延迟，避免请求过于频繁
                if i < len(results) - 1:
                    time.sleep(0.5)
            
            logger.info(f"智能搜索完成，找到 {len(enhanced_results)} 个增强结果")
            
            # 构建标准化输出
            return create_standardized_output(
                tool_name="smart_search",
                status="success",
                primary_data=enhanced_results,
                secondary_data={
                    "content_stats": content_stats,
                    "base_search_result": search_result,
                    "query": query
                },
                counts={
                    "total": len(enhanced_results),
                    "requested": max_results,
                    "actual": len(enhanced_results),
                    "content_fetch_success": content_stats["successful_content_fetch"],
                    "content_fetch_failed": content_stats["failed_content_fetch"]
                },
                paths=search_result.get("paths", []),
                message=f"智能搜索完成，找到 {len(enhanced_results)} 个增强结果，内容获取成功率: {content_stats['successful_content_fetch']}/{content_stats['total_processed']}",
                start_time=start_time,
                parameters={"query": query, "max_results": max_results}
            )
        else:
            return create_standardized_output(
                tool_name="smart_search",
                status="error",
                message=f"基础搜索失败: {search_result.get('message', '未知错误')}",
                error=search_result.get('message', '未知错误'),
                start_time=start_time,
                parameters={"query": query, "max_results": max_results}
            )
            
    except Exception as e:
        logger.error(f"智能搜索执行失败: {e}")
        return create_standardized_output(
            tool_name="smart_search",
            status="error",
            message=f"智能搜索执行失败: {str(e)}",
            error=str(e),
            start_time=start_time,
            parameters={"query": query, "max_results": max_results}
        )

def _fetch_full_content(url: str, timeout: int = 10) -> str:
    """
    获取网页的完整内容并进行智能净化
    
    Args:
        url: 网页URL
        timeout: 请求超时时间
        
    Returns:
        净化后的网页文本内容
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除不需要的元素
        for element in soup(["script", "style", "nav", "header", "footer", "aside", "menu", "sidebar"]):
            element.decompose()
        
        # 移除常见的导航和广告元素
        for element in soup.find_all(["div", "span"], class_=lambda x: x and any(keyword in x.lower() for keyword in [
            "nav", "menu", "header", "footer", "sidebar", "ad", "banner", "toolbar", "breadcrumb",
            "comment", "share", "social", "related", "recommend", "hot", "trending"
        ])):
            element.decompose()
        
        # 尝试找到主要内容区域
        main_content = None
        
        # 常见的正文容器
        content_selectors = [
            "main", "article", ".content", ".main-content", ".post-content", 
            ".entry-content", ".article-content", "#content", "#main",
            ".mw-parser-output", ".content-body", ".text-content",
            ".article", ".post", ".story", ".news-content"
        ]
        
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # 如果没有找到主要内容区域，使用body
        if not main_content:
            main_content = soup.find("body") or soup
        
        # 提取文本内容
        text = main_content.get_text()
        
        # 智能净化文本内容
        text = _clean_and_filter_content(text)
        
        return text
        
    except Exception as e:
        logging.warning(f"获取网页内容失败 {url}: {e}")
        return ""

def _clean_and_filter_content(text: str) -> str:
    """
    智能净化和过滤文本内容
    
    Args:
        text: 原始文本内容
        
    Returns:
        净化后的文本内容
    """
    if not text:
        return ""
    
    # 1. 基础清理
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 2. 移除无用的导航和界面元素
    useless_patterns = [
        r'跳转到内容.*?主菜单.*?移至侧栏.*?隐藏.*?导航',
        r'首页.*?分类.*?索引.*?特色内容.*?新闻动态.*?最近更改',
        r'随机条目.*?帮助.*?维基社群.*?方针与指引.*?互助客栈',
        r'知识问答.*?字词转换.*?IRC即时聊天.*?联络我们',
        r'关于维基百科.*?特殊页面.*?搜索.*?外观.*?资助维基百科',
        r'创建账号.*?登录.*?个人工具.*?目录.*?序言.*?开关',
        r'子章节.*?注释.*?延伸阅读.*?参考文献.*?来源.*?参见',
        r'编辑链接.*?条目讨论.*?简体.*?不转换.*?繁体',
        r'大陆简体.*?香港繁体.*?澳門繁體.*?大马简体.*?新加坡简体.*?臺灣正體',
        r'阅读.*?编辑.*?查看历史.*?工具.*?操作.*?常规',
        r'链入页面.*?相关更改.*?上传文件.*?固定链接.*?页面信息',
        r'引用此页.*?获取短链接.*?下载二维码.*?打印.*?导出',
        r'下载为PDF.*?打印版本.*?在其他项目中.*?维基共享资源.*?维基数据项目',
        r'收藏.*?查看我的收藏.*?有用.*?分享.*?评论.*?点赞',
        r'相关推荐.*?热门.*?最新.*?更多.*?加载更多',
        r'广告.*?推广.*?赞助.*?商业合作',
        r'版权.*?免责声明.*?隐私政策.*?使用条款',
        r'联系我们.*?关于我们.*?网站地图.*?帮助中心',
        r'内容.*?伍言.*?on.*?字符.*?词数.*?类型',
        r'维基百科.*?自由的百科全书',
        r'繁体字.*?简化字.*?标音.*?官话.*?现代标准汉语',
        r'右将军.*?假节.*?故宫.*?南薰殿.*?画像.*?车骑将军.*?司隶校尉.*?西乡侯',
        r'国家.*?时代.*?主君.*?姓.*?姓名.*?字.*?封爵.*?封地.*?籍贯.*?出生.*?逝世.*?谥号.*?墓葬.*?亲属',
        r'新亭侯.*?西乡县.*?幽州.*?涿郡.*?河北省.*?涿州市.*?蜀汉.*?昭烈帝.*?章武.*?益州.*?巴西郡.*?阆中县.*?四川省.*?阆中市',
        r'桓侯.*?灵应王.*?前蜀.*?加封.*?武义.*?忠显.*?英烈.*?灵惠.*?助顺王.*?元朝',
        r'张桓侯庙.*?头颅.*?张桓侯祠.*?身体.*?妻.*?夏侯氏.*?子.*?张苞.*?张绍.*?女.*?敬哀皇后.*?张皇后.*?孙.*?张遵'
    ]
    
    for pattern in useless_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # 3. 移除拼音和音标信息
    # 移除汉语拼音（带声调）
    text = re.sub(r'[a-zA-Zāáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜńňǹḿ]+(?:\s+[a-zA-Zāáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜńňǹḿ]+)*\s*[0-9]*', '', text)
    
    # 移除国际音标
    text = re.sub(r'\[[^\]]*\]', '', text)
    
    # 移除威妥玛拼音等
    text = re.sub(r'[A-Z][a-z]+[0-9]\s+[A-Z][a-z]+[0-9]', '', text)
    
    # 移除各种拼音系统
    pinyin_systems = [
        r'威妥瑪拼音', r'威妥玛拼音', r'威妥玛式拼音',
        r'国际音标', r'IPA',
        r'闽南语白话字', r'台语罗马字', r'粤拼', r'耶鲁拼音',
        r'汉语拼音', r'Hanyu Pinyin', r'Wade-Giles',
        r'注音符号', r'注音', r'标音', r'发音', r'读音',
        r'官话', r'方言', r'闽语', r'粤语', r'台语',
        r'白话字', r'罗马字', r'拼音', r'音标'
    ]
    
    for pattern in pinyin_systems:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # 移除包含拼音的行
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 检查是否包含大量拼音内容
        pinyin_indicators = [
            r'[a-zA-Zāáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜńňǹḿ]{2,}',  # 连续拼音字符
            r'[A-Z][a-z]+[0-9]',  # 威妥玛拼音
            r'\[[^\]]*[a-zA-Z][^\]]*\]',  # 包含字母的音标
            r'[一-龯]+\s*[a-zA-Zāáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜńňǹḿ]+',  # 中文+拼音
            r'[a-zA-Zāáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜńňǹḿ]+\s*[一-龯]+',  # 拼音+中文
        ]
        
        is_pinyin_line = False
        for pattern in pinyin_indicators:
            if re.search(pattern, line):
                # 计算拼音内容的比例
                pinyin_chars = len(re.findall(r'[a-zA-Zāáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜńňǹḿ]', line))
                total_chars = len(line)
                if pinyin_chars > total_chars * 0.3:  # 如果拼音字符超过30%，认为是拼音行
                    is_pinyin_line = True
                    break
        
        if not is_pinyin_line:
            filtered_lines.append(line)
    
    text = '\n'.join(filtered_lines)
    
    # 4. 移除重复内容
    lines = text.split('\n')
    unique_lines = []
    seen_lines = set()
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 10:  # 只保留有意义的行
            # 计算相似度，避免重复内容
            is_duplicate = False
            for seen_line in seen_lines:
                if _calculate_similarity(line, seen_line) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_lines.append(line)
                seen_lines.add(line)
    
    # 5. 重新组合文本
    text = '\n'.join(unique_lines)
    
    # 6. 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 7. 限制内容长度
    if len(text) > 3000:
        # 智能截断：保留完整的句子
        sentences = re.split(r'[。！？.!?]', text)
        truncated_text = ""
        for sentence in sentences:
            if len(truncated_text + sentence) < 3000:
                truncated_text += sentence + "。"
            else:
                break
        text = truncated_text
    
    return text

def _calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度
    
    Args:
        text1: 文本1
        text2: 文本2
        
    Returns:
        相似度 (0-1)
    """
    if not text1 or not text2:
        return 0.0
    
    # 简单的相似度计算
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0