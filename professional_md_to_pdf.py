#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业Markdown到PDF转换工具
使用pandoc + LaTeX引擎，确保最高质量的PDF输出
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import tempfile
import shutil

class ProfessionalMarkdownToPDF:
    """专业的Markdown到PDF转换器"""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent / "pdf_templates"
        self.template_dir.mkdir(exist_ok=True)
        self._setup_templates()
    
    def _setup_templates(self):
        """设置专业的LaTeX模板"""
        # 创建专业的LaTeX模板
        template_content = r"""\documentclass[12pt,a4paper]{article}
\usepackage[UTF8]{ctex}
\usepackage{geometry}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{hyperref}
\usepackage{listings}
\usepackage{xcolor}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{multirow}
\usepackage{wrapfig}
\usepackage{float}
\usepackage{colortbl}
\usepackage{pdflscape}
\usepackage{tabu}
\usepackage{threeparttable}
\usepackage{threeparttablex}
\usepackage{makecell}
\usepackage{xltabular}
\usepackage{fontspec}
\usepackage{setspace}

% 页面设置
\geometry{
    left=2.5cm,
    right=2.5cm,
    top=2.5cm,
    bottom=2.5cm,
    headheight=15pt
}

% 字体设置
\setmainfont{Times New Roman}
\setsansfont{Arial}
\setmonofont{Courier New}

% 行间距
\onehalfspacing

% 页眉页脚
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\leftmark}
\fancyhead[R]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}

% 标题格式
\titleformat{\section}{\Large\bfseries}{\thesection}{1em}{}
\titleformat{\subsection}{\large\bfseries}{\thesubsection}{1em}{}
\titleformat{\subsubsection}{\normalsize\bfseries}{\thesubsubsection}{1em}{}

% 代码块样式
\lstset{
    basicstyle=\ttfamily\small,
    breaklines=true,
    frame=single,
    numbers=left,
    numberstyle=\tiny,
    keywordstyle=\color{blue},
    commentstyle=\color{green!60!black},
    stringstyle=\color{red},
    backgroundcolor=\color{gray!10},
    showspaces=false,
    showstringspaces=false,
    showtabs=false,
    tabsize=2
}

% 超链接样式
\hypersetup{
    colorlinks=true,
    linkcolor=black,
    filecolor=magenta,
    urlcolor=blue,
    citecolor=green,
    pdftitle={$title$},
    pdfauthor={$author$},
    pdfsubject={$subject$},
    pdfkeywords={$keywords$}
}

% 表格样式
\renewcommand{\arraystretch}{1.2}

\begin{document}

% 标题页
\begin{titlepage}
    \centering
    \vspace*{2cm}
    
    {\Huge\bfseries $title$}
    
    \vspace{1cm}
    
    {\Large $subtitle$}
    
    \vspace{2cm}
    
    {\large $author$}
    
    \vspace{1cm}
    
    {\large $date$}
    
    \vfill
    
    {\large $institute$}
\end{titlepage}

% 目录
\tableofcontents
\newpage

% 正文内容
$body$

\end{document}
"""
        
        template_file = self.template_dir / "professional_template.tex"
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
    
    def check_dependencies(self):
        """检查必要的依赖是否安装"""
        dependencies = ['pandoc', 'xelatex']
        missing = []
        
        for dep in dependencies:
            try:
                subprocess.run([dep, '--version'], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing.append(dep)
        
        if missing:
            print("❌ 缺少必要的依赖:")
            for dep in missing:
                print(f"   - {dep}")
            print("\n请安装以下依赖:")
            print("1. Pandoc: https://pandoc.org/installing.html")
            print("2. LaTeX发行版 (如TeX Live或MiKTeX)")
            return False
        
        print("✅ 所有依赖已安装")
        return True
    
    def convert_md_to_pdf(self, input_file, output_file=None, 
                         title=None, author=None, subject=None, 
                         keywords=None, institute=None):
        """转换Markdown文件为PDF"""
        
        if not self.check_dependencies():
            return False
        
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"❌ 输入文件不存在: {input_file}")
            return False
        
        if output_file is None:
            output_file = input_path.with_suffix('.pdf')
        
        # 读取Markdown内容
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取元数据
        metadata = self._extract_metadata(content)
        
        # 设置默认值
        title = title or metadata.get('title', input_path.stem)
        author = author or metadata.get('author', '')
        subject = subject or metadata.get('subject', '')
        keywords = keywords or metadata.get('keywords', '')
        institute = institute or metadata.get('institute', '')
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 写入处理后的Markdown文件
            processed_md = temp_path / "processed.md"
            with open(processed_md, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 构建pandoc命令
            template_file = self.template_dir / "professional_template.tex"
            cmd = [
                'pandoc',
                str(processed_md),
                '-o', str(output_file),
                '--template', str(template_file),
                '--pdf-engine', 'xelatex',
                '--variable', f'title={title}',
                '--variable', f'author={author}',
                '--variable', f'subject={subject}',
                '--variable', f'keywords={keywords}',
                '--variable', f'institute={institute}',
                '--variable', f'date={self._get_current_date()}',
                '--variable', f'subtitle=',
                '--toc',
                '--number-sections',
                '--highlight-style', 'tango',
                '--pdf-engine-opt=-shell-escape'
            ]
            
            try:
                print(f"🔄 正在转换: {input_file} -> {output_file}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ 转换成功: {output_file}")
                    return True
                else:
                    print(f"❌ 转换失败:")
                    print(result.stderr)
                    return False
                    
            except Exception as e:
                print(f"❌ 转换过程中出现错误: {e}")
                return False
    
    def _extract_metadata(self, content):
        """从Markdown内容中提取元数据"""
        metadata = {}
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith('---'):
                break
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                metadata[key.lower()] = value
        
        return metadata
    
    def _get_current_date(self):
        """获取当前日期"""
        from datetime import datetime
        return datetime.now().strftime("%Y年%m月%d日")
    
    def batch_convert(self, input_dir, output_dir=None):
        """批量转换目录中的所有Markdown文件"""
        input_path = Path(input_dir)
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
        else:
            output_path = input_path
        
        md_files = list(input_path.glob('*.md'))
        
        if not md_files:
            print(f"❌ 在目录 {input_dir} 中未找到Markdown文件")
            return
        
        print(f"📁 找到 {len(md_files)} 个Markdown文件")
        
        success_count = 0
        for md_file in md_files:
            if output_dir:
                output_file = output_path / f"{md_file.stem}.pdf"
            else:
                output_file = md_file.with_suffix('.pdf')
            
            if self.convert_md_to_pdf(str(md_file), str(output_file)):
                success_count += 1
        
        print(f"\n📊 转换完成: {success_count}/{len(md_files)} 个文件成功转换")

def main():
    parser = argparse.ArgumentParser(description='专业Markdown到PDF转换工具')
    parser.add_argument('input', help='输入的Markdown文件或目录')
    parser.add_argument('-o', '--output', help='输出PDF文件路径')
    parser.add_argument('--title', help='文档标题')
    parser.add_argument('--author', help='作者')
    parser.add_argument('--subject', help='主题')
    parser.add_argument('--keywords', help='关键词')
    parser.add_argument('--institute', help='机构')
    parser.add_argument('--batch', action='store_true', help='批量转换模式')
    
    args = parser.parse_args()
    
    converter = ProfessionalMarkdownToPDF()
    
    if args.batch or Path(args.input).is_dir():
        converter.batch_convert(args.input, args.output)
    else:
        converter.convert_md_to_pdf(
            args.input, args.output,
            args.title, args.author, args.subject,
            args.keywords, args.institute
        )

if __name__ == '__main__':
    main() 