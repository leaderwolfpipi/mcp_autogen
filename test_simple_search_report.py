#!/usr/bin/env python3
"""
简单测试搜索和报告生成功能
"""

import logging
import json
from tools.smart_search import smart_search
from tools.report_generator import report_generator

# 设置日志
logging.basicConfig(level=logging.INFO)

def test_search_and_report():
    """测试搜索和报告生成"""
    print("开始测试搜索和报告生成功能...")
    
    # 1. 执行搜索
    print("\n1. 执行智能搜索...")
    search_result = smart_search("李自成生平", max_results=3)
    
    if search_result.get('status') == 'success':
        results = search_result.get('data', {}).get('primary', [])
        print(f"搜索成功，找到 {len(results)} 个结果")
        
        # 显示搜索结果
        for i, result in enumerate(results):
            title = result.get('title', 'N/A')
            full_content = result.get('full_content', '')
            content_length = len(full_content) if full_content else 0
            
            print(f"  结果 {i+1}: {title}")
            print(f"    内容长度: {content_length} 字符")
            
            if full_content:
                # 检查内容质量
                nav_keywords = ['跳转到内容', '主菜单', '导航', '维基百科']
                has_nav = any(keyword in full_content for keyword in nav_keywords)
                print(f"    包含导航元素: {'是' if has_nav else '否'}")
                
                # 显示内容前200字符
                preview = full_content[:200].replace('\n', ' ')
                print(f"    内容预览: {preview}...")
        
        # 2. 生成报告
        print("\n2. 生成报告...")
        report = report_generator(results, format="structured")
        
        if isinstance(report, dict):
            print("报告生成成功")
            print(f"  内容长度: {report.get('content_length', 0)}")
            print(f"  词数: {report.get('word_count', 0)}")
            
            summary = report.get('summary', '')
            if summary:
                print(f"  摘要: {summary[:300]}...")
            
            key_entities = report.get('key_entities', [])
            if key_entities:
                print(f"  关键实体: {', '.join(key_entities[:5])}")
            
            # 保存报告
            with open("simple_test_report.json", 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print("  报告已保存到: simple_test_report.json")
        else:
            print(f"报告生成失败，返回类型: {type(report)}")
            print(f"报告内容: {report}")
    else:
        print(f"搜索失败: {search_result.get('message', '未知错误')}")

if __name__ == "__main__":
    test_search_and_report() 