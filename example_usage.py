#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业Markdown到PDF转换工具使用示例
"""

from professional_md_to_pdf import ProfessionalMarkdownToPDF
from pathlib import Path

def example_single_file():
    """单个文件转换示例"""
    print("📄 单个文件转换示例")
    print("-" * 30)
    
    converter = ProfessionalMarkdownToPDF()
    
    # 转换README.md
    if Path("README.md").exists():
        success = converter.convert_md_to_pdf(
            input_file="README.md",
            output_file="README_专业版.pdf",
            title="项目说明文档",
            author="开发团队",
            subject="技术文档",
            keywords="Markdown, PDF, 转换",
            institute="技术部门"
        )
        
        if success:
            print("✅ README.md转换成功")
        else:
            print("❌ README.md转换失败")
    else:
        print("⚠️ README.md文件不存在")

def example_batch_convert():
    """批量转换示例"""
    print("\n📁 批量转换示例")
    print("-" * 30)
    
    converter = ProfessionalMarkdownToPDF()
    
    # 创建输出目录
    output_dir = Path("pdf_output")
    output_dir.mkdir(exist_ok=True)
    
    # 批量转换当前目录下的所有Markdown文件
    converter.batch_convert(".", str(output_dir))

def example_with_metadata():
    """带元数据的转换示例"""
    print("\n📋 带元数据的转换示例")
    print("-" * 30)
    
    # 创建一个示例Markdown文件
    sample_md = """---
title: 技术报告
author: 张三
subject: 系统架构设计
keywords: 架构, 设计, 技术
institute: 技术部
date: 2024-01-15
---

# 系统架构设计报告

## 概述

本文档描述了系统的整体架构设计。

## 架构组件

### 前端层
- React.js
- TypeScript
- Material-UI

### 后端层
- Python Flask
- PostgreSQL
- Redis

### 部署层
- Docker
- Kubernetes
- Nginx

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | React | 18.x |
| 后端 | Python | 3.9+ |
| 数据库 | PostgreSQL | 14.x |

## 代码示例

```python
def hello_world():
    print("Hello, World!")
    return "success"
```

## 总结

这是一个完整的系统架构设计。
"""
    
    # 写入示例文件
    with open("sample_report.md", "w", encoding="utf-8") as f:
        f.write(sample_md)
    
    # 转换
    converter = ProfessionalMarkdownToPDF()
    success = converter.convert_md_to_pdf(
        input_file="sample_report.md",
        output_file="sample_report_专业版.pdf"
    )
    
    if success:
        print("✅ 示例报告转换成功")
    else:
        print("❌ 示例报告转换失败")

def main():
    """主函数"""
    print("🎯 专业Markdown到PDF转换工具 - 使用示例")
    print("=" * 50)
    
    # 检查依赖
    converter = ProfessionalMarkdownToPDF()
    if not converter.check_dependencies():
        print("❌ 请先安装必要的依赖")
        print("运行: python install_dependencies.py")
        return
    
    # 运行示例
    example_single_file()
    example_batch_convert()
    example_with_metadata()
    
    print("\n" + "=" * 50)
    print("🎉 所有示例执行完成！")
    print("\n生成的PDF文件具有以下专业特性:")
    print("✅ 专业的LaTeX排版")
    print("✅ 中文字体支持")
    print("✅ 自动生成目录")
    print("✅ 代码高亮显示")
    print("✅ 页眉页脚")
    print("✅ 超链接支持")
    print("✅ 表格美化")
    print("✅ 数学公式支持")

if __name__ == '__main__':
    main() 