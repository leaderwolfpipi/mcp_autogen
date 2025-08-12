#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版报告生成器
对比新旧报告生成器的效果
"""

import json
from tools.report_generator import report_generator
from tools.enhanced_report_generator import enhanced_report_generator

def test_report_generators():
    """测试新旧报告生成器"""
    print("🧪 测试报告生成器对比")
    print("=" * 60)
    
    # 模拟搜索诸葛亮的结果
    search_results = [
        {
            "title": "诸葛亮 - 维基百科",
            "snippet": "诸葛亮（181年－234年），字孔明，号卧龙，琅琊阳都（今山东临沂）人，三国时期蜀汉丞相，杰出的政治家、军事家、发明家、文学家。",
            "url": "https://zh.wikipedia.org/wiki/诸葛亮"
        },
        {
            "title": "诸葛亮生平事迹",
            "snippet": "诸葛亮早年隐居隆中，后经徐庶推荐，刘备三顾茅庐请其出山。辅佐刘备建立蜀汉政权，任丞相，主持朝政。",
            "url": "https://example.com/zhuge-liang"
        },
        {
            "title": "诸葛亮的军事才能",
            "snippet": "诸葛亮精通兵法，善于用兵，曾多次北伐曹魏，虽然未能成功，但展现了卓越的军事才能和战略眼光。",
            "url": "https://example.com/military"
        }
    ]
    
    # 转换为字符串格式
    content = json.dumps(search_results, ensure_ascii=False, indent=2)
    
    print("📋 输入内容:")
    print(content[:200] + "...")
    print()
    
    # 测试旧版报告生成器
    print("🔴 旧版报告生成器结果:")
    print("-" * 40)
    old_result = report_generator(
        content=content,
        format="markdown",
        max_words=500,
        title="诸葛亮背景报告"
    )
    
    if old_result.get("status") == "success":
        # 修复：正确获取报告内容
        old_report = old_result.get("data", {}).get("primary", {}).get("report_content", "")
        print("✅ 生成成功")
        print(f"字数: {len(old_report.split())}")
        print("内容预览:")
        print(old_report[:500] + "..." if len(old_report) > 500 else old_report)
    else:
        print("❌ 生成失败:", old_result.get("message"))
    
    print("\n" + "=" * 60)
    
    # 测试新版报告生成器
    print("🟢 新版报告生成器结果:")
    print("-" * 40)
    new_result = enhanced_report_generator(
        content=content,
        format="markdown",
        max_words=500,
        title="诸葛亮背景报告",
        topic="诸葛亮",
        style="professional"
    )
    
    if new_result.get("status") == "success":
        # 修复：正确获取报告内容
        new_report = new_result.get("data", {}).get("primary", {}).get("report_content", "")
        print("✅ 生成成功")
        print(f"字数: {len(new_report.split())}")
        print("内容预览:")
        print(new_report[:500] + "..." if len(new_report) > 500 else new_report)
    else:
        print("❌ 生成失败:", new_result.get("message"))
    
    print("\n" + "=" * 60)
    
    # 对比分析
    print("📊 对比分析:")
    print("-" * 40)
    
    if old_result.get("status") == "success" and new_result.get("status") == "success":
        old_report = old_result.get("data", {}).get("primary", {}).get("report_content", "")
        new_report = new_result.get("data", {}).get("primary", {}).get("report_content", "")
        
        print("1. 内容相关性:")
        old_zhuge_count = old_report.count("诸葛亮")
        new_zhuge_count = new_report.count("诸葛亮")
        print(f"   旧版中'诸葛亮'出现次数: {old_zhuge_count}")
        print(f"   新版中'诸葛亮'出现次数: {new_zhuge_count}")
        
        print("\n2. 模板化程度:")
        template_phrases = [
            "本报告基于对输入内容的深入分析",
            "通过智能分析技术",
            "内容涵盖多个方面",
            "适合一般读者阅读",
            "具有较好的可读性"
        ]
        
        old_template_count = sum(1 for phrase in template_phrases if phrase in old_report)
        new_template_count = sum(1 for phrase in template_phrases if phrase in new_report)
        print(f"   旧版模板化短语数量: {old_template_count}")
        print(f"   新版模板化短语数量: {new_template_count}")
        
        print("\n3. 信息密度:")
        old_words = len(old_report.split())
        new_words = len(new_report.split())
        old_info_ratio = old_zhuge_count / max(old_words, 1)
        new_info_ratio = new_zhuge_count / max(new_words, 1)
        print(f"   旧版信息密度: {old_info_ratio:.4f}")
        print(f"   新版信息密度: {new_info_ratio:.4f}")
        
        print("\n4. 质量评估:")
        if new_zhuge_count > old_zhuge_count and new_template_count < old_template_count:
            print("   ✅ 新版报告质量明显优于旧版")
        elif new_zhuge_count > old_zhuge_count:
            print("   ⚠️ 新版相关性更好，但模板化程度相似")
        elif new_template_count < old_template_count:
            print("   ⚠️ 新版模板化程度更低，但相关性相似")
        else:
            print("   ❌ 新版改进不明显")
    
    print("\n" + "=" * 60)
    print("🎯 改进建议:")
    print("-" * 40)
    print("1. 集成真正的LLM API（如OpenAI GPT、百度文心一言等）")
    print("2. 添加更多主题相关的关键词提取")
    print("3. 实现更智能的内容筛选和排序")
    print("4. 支持多种报告风格和模板")
    print("5. 添加内容质量评估机制")

def test_with_real_llm():
    """测试集成真实LLM的效果"""
    print("\n🚀 测试集成真实LLM")
    print("=" * 60)
    
    # 这里可以添加真实的LLM API调用测试
    # 需要配置相应的API密钥
    
    print("📝 要集成真实LLM，请:")
    print("1. 在 enhanced_report_generator.py 中配置API密钥")
    print("2. 取消注释 _call_llm_api 函数中的API调用代码")
    print("3. 选择合适的模型（如GPT-4、文心一言等）")
    print("4. 调整提示词以获得最佳效果")

if __name__ == "__main__":
    test_report_generators()
    test_with_real_llm() 