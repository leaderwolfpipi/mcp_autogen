import os
import logging
import json
from typing import Union, Dict, Any
from tools.base_tool import create_standardized_output

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def file_writer(file_path: str, text: Union[str, Dict[str, Any]]) -> dict:
    """
    通用文件写入工具，支持文本和字典格式的内容
    
    :param file_path: 文件路径，支持.txt, .json, .md, .pdf等格式
    :param text: 要写入的内容，可以是字符串或字典
    :return: 标准化的输出字典
    """
    import time
    start_time = time.time()
    
    try:
        # 验证参数
        if not file_path or not file_path.strip():
            return create_standardized_output(
                tool_name="file_writer",
                status="error",
                message="文件路径不能为空",
                error="文件路径不能为空",
                start_time=start_time,
                parameters={"file_path": file_path, "text": text}
            )
        
        if not text:
            logging.warning("文本内容为空，将写入空文件")
        
        # 清理文件路径
        file_path = file_path.strip()
        
        # 确保目录存在
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
            logging.info(f"目录已创建或已存在: {directory}")
        
        # 根据文件扩展名和内容类型决定写入方式
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if isinstance(text, dict):
            # 处理字典格式的内容
            if file_ext == '.json':
                # 写入JSON文件
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(text, file, ensure_ascii=False, indent=2)
                content_to_write = json.dumps(text, ensure_ascii=False, indent=2)
            elif file_ext == '.md' or file_ext == '.markdown':
                # 从字典中提取Markdown内容
                if 'report_content' in text:
                    content_to_write = text['report_content']
                else:
                    content_to_write = str(text)
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content_to_write)
            elif file_ext == '.pdf':
                # 生成PDF文件
                return _generate_pdf_from_content(file_path, text)
            else:
                # 默认写入JSON格式
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(text, file, ensure_ascii=False, indent=2)
                content_to_write = json.dumps(text, ensure_ascii=False, indent=2)
        else:
            # 处理字符串格式的内容
            content_to_write = str(text)
            if file_ext == '.pdf':
                # 生成PDF文件
                return _generate_pdf_from_content(file_path, {"content": content_to_write})
            else:
                # 写入文本文件
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content_to_write)
        
        success_msg = f"内容已成功写入文件: {file_path}"
        logging.info(success_msg)
        
        return create_standardized_output(
            tool_name="file_writer",
            status="success",
            primary_data={"file_path": file_path, "file_size": len(content_to_write)},
            secondary_data={"file_extension": file_ext, "content_type": type(text).__name__},
            counts={"file_size_bytes": len(content_to_write)},
            paths=[file_path],
            message=success_msg,
            start_time=start_time,
            parameters={"file_path": file_path, "text": text}
        )

    except Exception as e:
        error_msg = f"写入文件时发生错误: {e}"
        logging.error(error_msg)
        return create_standardized_output(
            tool_name="file_writer",
            status="error",
            message=error_msg,
            error=str(e),
            start_time=start_time,
            parameters={"file_path": file_path, "text": text}
        )

def _generate_pdf_from_content(file_path: str, content: Dict[str, Any]) -> dict:
    """
    从内容生成PDF文件
    
    Args:
        file_path: PDF文件路径
        content: 内容字典
        
    Returns:
        标准化的输出字典
    """
    import time
    start_time = time.time()
    
    try:
        # 提取Markdown内容
        if 'report_content' in content:
            markdown_content = content['report_content']
        elif 'content' in content:
            markdown_content = content['content']
        else:
            markdown_content = str(content)
        
        # 尝试使用不同的PDF生成方法
        pdf_result = _try_pdf_generation(file_path, markdown_content)
        
        if pdf_result['success']:
            return create_standardized_output(
                tool_name="file_writer",
                status="success",
                primary_data={"file_path": file_path, "file_size": pdf_result.get('file_size', 0)},
                secondary_data={"pdf_generator": pdf_result.get('method', 'unknown')},
                counts={"file_size_bytes": pdf_result.get('file_size', 0)},
                paths=[file_path],
                message=f"PDF文件已成功生成: {file_path}",
                start_time=start_time,
                parameters={"file_path": file_path, "content": content}
            )
        else:
            # 如果PDF生成失败，保存为Markdown文件
            md_path = file_path.replace('.pdf', '.md')
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            return create_standardized_output(
                tool_name="file_writer",
                status="partial_success",
                primary_data={"file_path": md_path, "file_size": len(markdown_content)},
                secondary_data={"pdf_generation_failed": True, "fallback_to_md": True},
                counts={"file_size_bytes": len(markdown_content)},
                paths=[md_path],
                message=f"PDF生成失败，已保存为Markdown文件: {md_path}",
                start_time=start_time,
                parameters={"file_path": file_path, "content": content}
            )
            
    except Exception as e:
        error_msg = f"PDF生成失败: {e}"
        logging.error(error_msg)
        return create_standardized_output(
            tool_name="file_writer",
            status="error",
            message=error_msg,
            error=str(e),
            start_time=start_time,
            parameters={"file_path": file_path, "content": content}
        )

def _try_pdf_generation(file_path: str, markdown_content: str) -> dict:
    """
    尝试使用不同的方法生成PDF
    
    Args:
        file_path: PDF文件路径
        markdown_content: Markdown内容
        
    Returns:
        生成结果字典
    """
    # 方法1: 使用weasyprint (推荐)
    try:
        import weasyprint
        from weasyprint import HTML, CSS
        
        # 将Markdown转换为HTML
        html_content = _markdown_to_html(markdown_content)
        
        # 生成PDF
        html = HTML(string=html_content)
        html.write_pdf(file_path)
        
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        return {
            "success": True,
            "method": "weasyprint",
            "file_size": file_size
        }
    except ImportError:
        logging.warning("weasyprint未安装，尝试其他方法")
    except Exception as e:
        logging.warning(f"weasyprint生成PDF失败: {e}")
    
    # 方法2: 使用markdown2 + weasyprint
    try:
        import markdown2
        
        # 转换Markdown为HTML
        html_content = markdown2.markdown(markdown_content)
        
        # 添加CSS样式
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #333; border-bottom: 2px solid #333; }}
                h2 {{ color: #666; margin-top: 30px; }}
                h3 {{ color: #888; }}
                ul, ol {{ margin-left: 20px; }}
                li {{ margin-bottom: 5px; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # 生成PDF
        html = HTML(string=styled_html)
        html.write_pdf(file_path)
        
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        return {
            "success": True,
            "method": "markdown2+weasyprint",
            "file_size": file_size
        }
    except ImportError:
        logging.warning("markdown2未安装")
    except Exception as e:
        logging.warning(f"markdown2+weasyprint生成PDF失败: {e}")
    
    # 方法3: 使用pandoc (如果系统安装了pandoc)
    try:
        import subprocess
        
        # 先保存Markdown文件
        temp_md = file_path.replace('.pdf', '_temp.md')
        with open(temp_md, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # 使用pandoc转换
        result = subprocess.run([
            'pandoc', temp_md, '-o', file_path, 
            '--pdf-engine=xelatex', '--variable=mainfont:SimSun'
        ], capture_output=True, text=True)
        
        # 清理临时文件
        if os.path.exists(temp_md):
            os.remove(temp_md)
        
        if result.returncode == 0 and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            return {
                "success": True,
                "method": "pandoc",
                "file_size": file_size
            }
    except Exception as e:
        logging.warning(f"pandoc生成PDF失败: {e}")
    
    return {
        "success": False,
        "method": "none",
        "file_size": 0
    }

def _markdown_to_html(markdown_content: str) -> str:
    """
    将Markdown转换为HTML
    
    Args:
        markdown_content: Markdown内容
        
    Returns:
        HTML内容
    """
    try:
        import markdown
        
        # 使用markdown库转换
        html_content = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])
        
        # 添加CSS样式
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>报告</title>
            <style>
                body {{
                    font-family: 'Microsoft YaHei', 'SimSun', Arial, sans-serif;
                    margin: 40px;
                    line-height: 1.8;
                    color: #333;
                    font-size: 14px;
                    text-align: justify;
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                    font-size: 24px;
                    font-weight: bold;
                    margin-top: 30px;
                    margin-bottom: 20px;
                }}
                h2 {{
                    color: #34495e;
                    margin-top: 25px;
                    margin-bottom: 15px;
                    font-size: 20px;
                    font-weight: bold;
                }}
                h3 {{
                    color: #7f8c8d;
                    margin-top: 20px;
                    margin-bottom: 10px;
                    font-size: 16px;
                    font-weight: bold;
                }}
                ul, ol {{
                    margin-left: 20px;
                    margin-bottom: 15px;
                    padding-left: 0;
                }}
                li {{
                    margin-bottom: 8px;
                    line-height: 1.6;
                }}
                p {{
                    margin-bottom: 12px;
                    text-align: justify;
                    line-height: 1.8;
                }}
                strong, b {{
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .summary {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-left: 4px solid #3498db;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                .key-info {{
                    background-color: #e8f4fd;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                /* 统一所有文本元素的字体大小 */
                * {{
                    font-size: 14px;
                }}
                h1 {{
                    font-size: 24px !important;
                }}
                h2 {{
                    font-size: 20px !important;
                }}
                h3 {{
                    font-size: 16px !important;
                }}
                /* 确保列表项字体大小一致 */
                ul li, ol li {{
                    font-size: 14px !important;
                }}
                /* 确保段落字体大小一致 */
                p {{
                    font-size: 14px !important;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        return styled_html
        
    except ImportError:
        # 如果没有markdown库，使用简单的转换
        html_content = markdown_content.replace('\n', '<br>')
        html_content = html_content.replace('# ', '<h1>').replace('\n', '</h1>')
        html_content = html_content.replace('## ', '<h2>').replace('\n', '</h2>')
        html_content = html_content.replace('### ', '<h3>').replace('\n', '</h3>')
        html_content = html_content.replace('- ', '<li>').replace('\n', '</li>')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #333; border-bottom: 2px solid #333; }}
                h2 {{ color: #666; margin-top: 30px; }}
                h3 {{ color: #888; }}
                ul, ol {{ margin-left: 20px; }}
                li {{ margin-bottom: 5px; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

# Example usage
# file_writer("tests/lou.txt", "I LOVE YOU, and want to fuck you")