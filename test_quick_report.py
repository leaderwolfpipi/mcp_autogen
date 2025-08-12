#!/usr/bin/env python3
"""
快速测试改进后的报告生成功能
"""

from tools.report_generator import report_generator

def test_quick_report():
    """快速测试报告生成"""
    print("🧪 快速测试改进后的报告生成功能")
    print("=" * 40)
    
    # 测试内容
    test_content = """
    李自成（1606年9月22日—1645年5月17日），原名鸿基，陕西米脂人，世居米脂李继迁寨，明末民变领袖之一，大顺皇帝。
    
    李自成出生在米脂河西200里怀远堡李继迁寨（今横山县城关街道柴兴梁村）。崇祯帝采信大臣裁撤驿卒的建议，造成失业驿卒武夫起义，李自成参与起义军。
    
    高迎祥被明朝处决后，李自成称闯王，成为明末民变领袖之一，率起义军于河南歼灭明军主力。崇祯十七年（1644年）正月，李自成在西安称王，国号大顺，年号永昌。
    
    同年三月，李自成攻入北京，崇祯帝自缢于煤山，明朝灭亡。李自成在北京称帝，但不久后清军入关，李自成被迫撤离北京。
    
    1645年，李自成在湖北九宫山被当地地主武装杀害，一说在湖南归隐。李自成领导的农民起义虽然最终失败，但加速了明朝的灭亡，对中国历史产生了重要影响。
    """
    
    # 生成报告
    result = report_generator(
        content=test_content,
        format="markdown",
        max_words=500,
        title="李自成生平简析",
        sections=["摘要", "主要内容", "关键信息", "结论"]
    )
    
    if result.get('status') == 'success':
        print("✅ 报告生成成功")
        
        output_data = result.get('data', {}).get('primary', {})
        report_content = output_data.get('report_content', '')
        
        print("\n📄 生成的报告:")
        print("-" * 40)
        print(report_content)
        print("-" * 40)
        
        # 显示统计信息
        analysis = output_data.get('analysis', {})
        print(f"\n📊 统计信息:")
        print(f"   内容长度: {analysis.get('content_length', 0)} 字符")
        print(f"   词数: {analysis.get('word_count', 0)} 词")
        print(f"   语言: {analysis.get('language', 'zh')}")
        print(f"   内容类型: {analysis.get('content_type', 'general')}")
        
        # 显示关键信息
        entities = analysis.get('key_entities', [])
        topics = analysis.get('main_topics', [])
        
        print(f"\n🔍 关键实体: {', '.join(entities[:5])}")
        print(f"📋 主要话题: {', '.join(topics[:3])}")
        
    else:
        print(f"❌ 报告生成失败: {result.get('message', '未知错误')}")

if __name__ == "__main__":
    test_quick_report() 