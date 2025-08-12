#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试报告生成器
直接测试报告生成器函数
"""

import json
from tools.report_generator import report_generator
from tools.enhanced_report_generator import enhanced_report_generator

def debug_report_generator():
    """调试报告生成器"""
    print("🔍 调试报告生成器")
    print("=" * 60)
    
    # 简单的测试内容
    test_content = "诸葛亮（181年－234年），字孔明，号卧龙，琅琊阳都（今山东临沂）人，三国时期蜀汉丞相，杰出的政治家、军事家、发明家、文学家。"
    
    print("📋 测试内容:")
    print(test_content)
    print()
    
    # 测试旧版报告生成器
    print("🔴 测试旧版报告生成器:")
    print("-" * 40)
    
    try:
        old_result = report_generator(
            content=test_content,
            format="markdown",
            max_words=300,
            title="诸葛亮简介"
        )
        
        print("返回结果结构:")
        print(f"状态: {old_result.get('status')}")
        print(f"消息: {old_result.get('message')}")
        print(f"数据键: {list(old_result.get('data', {}).keys())}")
        
        if old_result.get("status") == "success":
            # 修复：正确获取报告内容
            old_report = old_result.get("data", {}).get("primary", {}).get("report_content", "")
            print(f"报告内容长度: {len(old_report)}")
            print("报告内容:")
            print(old_report)
        else:
            print("错误信息:", old_result.get("error"))
            
    except Exception as e:
        print(f"❌ 旧版报告生成器异常: {e}")
    
    print("\n" + "=" * 60)
    
    # 测试新版报告生成器
    print("🟢 测试新版报告生成器:")
    print("-" * 40)
    
    try:
        new_result = enhanced_report_generator(
            content=test_content,
            format="markdown",
            max_words=300,
            title="诸葛亮简介",
            topic="诸葛亮",
            style="professional"
        )
        
        print("返回结果结构:")
        print(f"状态: {new_result.get('status')}")
        print(f"消息: {new_result.get('message')}")
        print(f"数据键: {list(new_result.get('data', {}).keys())}")
        
        if new_result.get("status") == "success":
            # 修复：正确获取报告内容
            new_report = new_result.get("data", {}).get("primary", {}).get("report_content", "")
            print(f"报告内容长度: {len(new_report)}")
            print("报告内容:")
            print(new_report)
        else:
            print("错误信息:", new_result.get("error"))
            
    except Exception as e:
        print(f"❌ 新版报告生成器异常: {e}")

def test_content_extraction():
    """测试内容提取功能"""
    print("\n🔍 测试内容提取功能")
    print("=" * 60)
    
    from tools.enhanced_report_generator import _extract_content, _smart_analyze_content
    
    # 测试不同格式的内容
    test_cases = [
        {
            "name": "字符串内容",
            "content": "诸葛亮是三国时期著名的政治家、军事家。"
        },
        {
            "name": "字典内容",
            "content": {
                "title": "诸葛亮",
                "description": "三国时期蜀汉丞相",
                "details": "杰出的政治家、军事家"
            }
        },
        {
            "name": "列表内容",
            "content": [
                {"title": "诸葛亮", "snippet": "三国时期蜀汉丞相"},
                {"title": "孔明", "snippet": "字孔明，号卧龙"}
            ]
        }
    ]
    
    for case in test_cases:
        print(f"\n📋 {case['name']}:")
        print(f"原始内容: {case['content']}")
        
        try:
            extracted = _extract_content(case['content'])
            print(f"提取结果: {extracted}")
            
            if extracted:
                analysis = _smart_analyze_content(extracted, "诸葛亮")
                print(f"分析结果: {analysis}")
            
        except Exception as e:
            print(f"❌ 提取失败: {e}")

if __name__ == "__main__":
    debug_report_generator()
    test_content_extraction() 