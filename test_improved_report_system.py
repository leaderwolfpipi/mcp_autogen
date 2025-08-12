#!/usr/bin/env python3
"""
测试改进后的报告生成系统
验证通用报告生成器和PDF生成功能
"""

import logging
import asyncio
import json
from tools.smart_search import smart_search
from tools.report_generator import report_generator
from tools.file_writer import file_writer

# 设置日志
logging.basicConfig(level=logging.INFO)

def test_improved_report_system():
    """测试改进后的报告生成系统"""
    print("🧪 测试改进后的报告生成系统")
    print("=" * 50)
    
    try:
        # 1. 执行搜索
        print("1. 执行智能搜索...")
        search_result = smart_search("李自成生平", max_results=3)
        
        if search_result.get('status') == 'success':
            results = search_result.get('data', {}).get('primary', [])
            print(f"✅ 搜索成功，找到 {len(results)} 个结果")
            
            # 2. 生成Markdown格式报告
            print("\n2. 生成Markdown格式报告...")
            report_result = report_generator(
                content=results,
                format="markdown",
                max_words=800,
                title="李自成生平研究报告",
                sections=["摘要", "主要内容", "关键信息", "结论"]
            )
            
            if report_result.get('status') == 'success':
                print("✅ 报告生成成功")
                
                output_data = report_result.get('data', {}).get('primary', {})
                report_content = output_data.get('report_content', '')
                word_count = output_data.get('word_count', 0)
                
                print(f"   报告字数: {word_count}")
                print(f"   报告长度: {len(report_content)} 字符")
                
                # 显示报告预览
                print("\n   报告预览:")
                lines = report_content.split('\n')[:10]
                for line in lines:
                    print(f"   {line}")
                if len(report_content.split('\n')) > 10:
                    print("   ...")
                
                # 3. 保存为Markdown文件
                print("\n3. 保存为Markdown文件...")
                md_result = file_writer("lizicheng_report.md", report_result.get('data', {}).get('primary', {}))
                
                if md_result.get('status') == 'success':
                    print("✅ Markdown文件保存成功")
                    file_path = md_result.get('data', {}).get('primary', {}).get('file_path', '')
                    print(f"   文件路径: {file_path}")
                else:
                    print(f"❌ Markdown文件保存失败: {md_result.get('message', '未知错误')}")
                
                # 4. 生成PDF文件
                print("\n4. 生成PDF文件...")
                pdf_result = file_writer("lizicheng_report.pdf", report_result.get('data', {}).get('primary', {}))
                
                if pdf_result.get('status') == 'success':
                    print("✅ PDF文件生成成功")
                    file_path = pdf_result.get('data', {}).get('primary', {}).get('file_path', '')
                    file_size = pdf_result.get('data', {}).get('primary', {}).get('file_size', 0)
                    print(f"   文件路径: {file_path}")
                    print(f"   文件大小: {file_size} 字节")
                    
                    # 显示PDF生成方法
                    method = pdf_result.get('data', {}).get('secondary', {}).get('pdf_generator', 'unknown')
                    print(f"   生成方法: {method}")
                    
                elif pdf_result.get('status') == 'partial_success':
                    print("⚠️ PDF生成部分成功")
                    file_path = pdf_result.get('data', {}).get('primary', {}).get('file_path', '')
                    print(f"   已保存为Markdown文件: {file_path}")
                    print(f"   原因: {pdf_result.get('message', 'PDF生成失败')}")
                    
                else:
                    print(f"❌ PDF文件生成失败: {pdf_result.get('message', '未知错误')}")
                
                # 5. 测试不同格式的报告
                print("\n5. 测试不同格式的报告...")
                
                # 测试纯文本格式
                plain_result = report_generator(
                    content=results,
                    format="plain",
                    max_words=500,
                    title="李自成生平简析"
                )
                
                if plain_result.get('status') == 'success':
                    print("✅ 纯文本格式报告生成成功")
                    plain_content = plain_result.get('data', {}).get('primary', {}).get('report_content', '')
                    print(f"   字数: {len(plain_content.split())}")
                else:
                    print(f"❌ 纯文本格式报告生成失败: {plain_result.get('message', '未知错误')}")
                
                # 6. 测试不同内容类型
                print("\n6. 测试不同内容类型...")
                
                # 测试字符串输入
                string_result = report_generator(
                    content="这是一个测试内容，包含技术信息和商业数据。",
                    format="markdown",
                    max_words=200,
                    title="测试报告"
                )
                
                if string_result.get('status') == 'success':
                    print("✅ 字符串输入处理成功")
                else:
                    print(f"❌ 字符串输入处理失败: {string_result.get('message', '未知错误')}")
                
                # 测试字典输入
                dict_result = report_generator(
                    content={"content": "这是字典格式的测试内容", "type": "test"},
                    format="markdown",
                    max_words=150,
                    title="字典输入测试"
                )
                
                if dict_result.get('status') == 'success':
                    print("✅ 字典输入处理成功")
                else:
                    print(f"❌ 字典输入处理失败: {dict_result.get('message', '未知错误')}")
                
            else:
                print(f"❌ 报告生成失败: {report_result.get('message', '未知错误')}")
                
        else:
            print(f"❌ 搜索失败: {search_result.get('message', '未知错误')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_generation():
    """专门测试PDF生成功能"""
    print("\n🔧 专门测试PDF生成功能")
    print("=" * 30)
    
    try:
        # 创建测试Markdown内容
        test_markdown = """# 测试报告

## 摘要
这是一个测试报告，用于验证PDF生成功能是否正常工作。

## 主要内容
- 测试项目：PDF生成
- 测试内容：Markdown转PDF
- 测试目标：验证功能完整性

## 关键信息
### 技术要点
- 支持多种PDF生成方法
- 自动降级到Markdown格式
- 错误处理和日志记录

### 使用说明
1. 优先使用weasyprint
2. 备选markdown2+weasyprint
3. 最后尝试pandoc

## 结论
PDF生成功能设计合理，具备良好的容错性和可扩展性。
"""
        
        # 测试PDF生成
        test_content = {"report_content": test_markdown}
        pdf_result = file_writer("test_report.pdf", test_content)
        
        if pdf_result.get('status') == 'success':
            print("✅ PDF生成测试成功")
            file_path = pdf_result.get('data', {}).get('primary', {}).get('file_path', '')
            file_size = pdf_result.get('data', {}).get('primary', {}).get('file_size', 0)
            method = pdf_result.get('data', {}).get('secondary', {}).get('pdf_generator', 'unknown')
            
            print(f"   文件路径: {file_path}")
            print(f"   文件大小: {file_size} 字节")
            print(f"   生成方法: {method}")
            
        elif pdf_result.get('status') == 'partial_success':
            print("⚠️ PDF生成部分成功")
            file_path = pdf_result.get('data', {}).get('primary', {}).get('file_path', '')
            print(f"   已保存为Markdown文件: {file_path}")
            
        else:
            print(f"❌ PDF生成测试失败: {pdf_result.get('message', '未知错误')}")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始测试改进后的报告生成系统...\n")
    
    # 测试主要功能
    success1 = test_improved_report_system()
    
    # 测试PDF生成
    success2 = test_pdf_generation()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败，请检查日志")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main() 