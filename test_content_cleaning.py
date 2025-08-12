#!/usr/bin/env python3
"""
测试内容净化效果
验证从搜索引擎结果到最终报告的完整净化流程
"""

import logging
from tools.smart_search import smart_search
from tools.report_generator import report_generator

# 设置日志
logging.basicConfig(level=logging.INFO)

def test_content_cleaning():
    """测试内容净化效果"""
    print("🧪 测试内容净化效果")
    print("=" * 50)
    
    # 模拟包含垃圾信息的搜索结果
    mock_search_results = [
        {
            'title': '张飞 - 维基百科',
            'link': 'https://example.com/zhangfei',
            'snippet': '张飞（？－221年），字益德，东汉末年幽州涿郡（今河北省保定市涿州市）人，三国时期蜀汉名将。',
            'full_content': '''
            张飞繁体字張飛简化字张飞标音官话(现代标准汉语)
            汉语拼音Zhāng Fēi
            威妥玛拼音Chang1 Fei1
            国际音标[tsán féi]闽语
            闽南语白话字Tiun Hui
            台语罗马字Tiunn Hui粤语
            粤拼Zoeng1 Fei1
            耶鲁拼音张飞 (2.—221年),字益德,东汉末年幽州涿郡(今河北省保定市涿州市)人,三国时期蜀汉名将。
            
            张飞（？－221年），字益德，东汉末年幽州涿郡（今河北省保定市涿州市）人，三国时期蜀汉名将。
            与关羽、刘备并称为"桃园三结义"的兄弟。
            
            跳转到内容 主菜单 移至侧栏 隐藏 导航 首页分类索引特色内容新闻动态最近更改随机条目
            帮助 帮助维基社群方针与指引互助客栈知识问答字词转换IRC即时聊天联络我们关于维基百科
            '''
        },
        {
            'title': '李自成生平',
            'link': 'https://example.com/lizicheng',
            'snippet': '李自成（1606年9月22日—1645年5月17日），原名鸿基，陕西米脂人，明末农民起义领袖。',
            'full_content': '''
            李自成（1606年9月22日—1645年5月17日），原名鸿基，陕西米脂人，世居米脂李继迁寨，明末民变领袖之一，大顺皇帝。
            
            李自成出生在米脂河西200里怀远堡李继迁寨（今横山县城关街道柴兴梁村）。
            崇祯帝采信大臣裁撤驿卒的建议，造成失业驿卒武夫起义，李自成参与起义军。
            
            高迎祥被明朝处决后，李自成称闯王，成为明末民变领袖之一，率起义军于河南歼灭明军主力。
            崇祯十七年（1644年）正月，李自成在西安称王，国号大顺，年号永昌。
            
            同年三月，李自成攻入北京，崇祯帝自缢于煤山，明朝灭亡。李自成在北京称帝，但不久后清军入关，李自成被迫撤离北京。
            
            1645年，李自成在湖北九宫山被当地地主武装杀害，一说在湖南归隐。
            李自成领导的农民起义虽然最终失败，但加速了明朝的灭亡，对中国历史产生了重要影响。
            
            收藏查看我的收藏0有用+10分享评论点赞
            相关推荐热门最新更多加载更多
            广告推广赞助商业合作
            '''
        }
    ]
    
    print("1. 原始搜索结果（包含垃圾信息）:")
    print("-" * 40)
    for i, result in enumerate(mock_search_results, 1):
        print(f"结果 {i}:")
        print(f"  标题: {result['title']}")
        print(f"  摘要: {result['snippet']}")
        print(f"  内容长度: {len(result['full_content'])} 字符")
        print(f"  内容预览: {result['full_content'][:100]}...")
        print()
    
    # 2. 测试内容净化
    print("2. 测试内容净化效果:")
    print("-" * 40)
    
    # 模拟净化后的内容
    from tools.smart_search import _clean_and_filter_content
    
    for i, result in enumerate(mock_search_results, 1):
        print(f"净化结果 {i}:")
        cleaned_content = _clean_and_filter_content(result['full_content'])
        print(f"  原始长度: {len(result['full_content'])} 字符")
        print(f"  净化后长度: {len(cleaned_content)} 字符")
        print(f"  净化率: {((len(result['full_content']) - len(cleaned_content)) / len(result['full_content']) * 100):.1f}%")
        print(f"  净化后内容: {cleaned_content[:200]}...")
        print()
    
    # 3. 测试报告生成
    print("3. 测试报告生成:")
    print("-" * 40)
    
    # 使用净化后的内容生成报告
    cleaned_results = []
    for result in mock_search_results:
        cleaned_content = _clean_and_filter_content(result['full_content'])
        if cleaned_content:
            cleaned_results.append({
                'title': result['title'],
                'snippet': result['snippet'],
                'full_content': cleaned_content
            })
    
    if cleaned_results:
        report_result = report_generator(
            content=cleaned_results,
            format="markdown",
            max_words=1000,
            title="历史人物研究报告",
            sections=["摘要", "详细分析", "关键信息", "结论"]
        )
        
        if report_result.get('status') == 'success':
            print("✅ 报告生成成功")
            
            output_data = report_result.get('data', {}).get('primary', {})
            report_content = output_data.get('report_content', '')
            
            print(f"报告字数: {len(report_content.split())}")
            print(f"报告长度: {len(report_content)} 字符")
            
            print("\n📄 生成的报告:")
            print("-" * 40)
            print(report_content)
            print("-" * 40)
            
            # 检查是否包含垃圾信息
            garbage_indicators = ['拼音', '音标', '威妥玛', '国际音标', '闽南语', '粤拼', '耶鲁拼音']
            found_garbage = []
            for indicator in garbage_indicators:
                if indicator in report_content:
                    found_garbage.append(indicator)
            
            if found_garbage:
                print(f"⚠️ 报告中仍包含垃圾信息: {', '.join(found_garbage)}")
            else:
                print("✅ 报告已成功清理垃圾信息")
        else:
            print(f"❌ 报告生成失败: {report_result.get('message', '未知错误')}")
    else:
        print("❌ 没有有效的净化后内容")

def test_real_search():
    """测试真实搜索的内容净化"""
    print("\n🔍 测试真实搜索的内容净化:")
    print("=" * 50)
    
    try:
        # 执行真实搜索
        search_result = smart_search("张飞生平", max_results=2)
        
        if search_result.get('status') == 'success':
            results = search_result.get('data', {}).get('primary', [])
            print(f"✅ 搜索成功，找到 {len(results)} 个结果")
            
            for i, result in enumerate(results, 1):
                print(f"\n结果 {i}: {result.get('title', 'N/A')}")
                
                full_content = result.get('full_content', '')
                if full_content:
                    print(f"  内容长度: {len(full_content)} 字符")
                    
                    # 检查是否包含垃圾信息
                    garbage_indicators = ['拼音', '音标', '威妥玛', '国际音标', '闽南语', '粤拼', '耶鲁拼音']
                    found_garbage = []
                    for indicator in garbage_indicators:
                        if indicator in full_content:
                            found_garbage.append(indicator)
                    
                    if found_garbage:
                        print(f"  ⚠️ 包含垃圾信息: {', '.join(found_garbage)}")
                    else:
                        print("  ✅ 内容已净化")
                    
                    print(f"  内容预览: {full_content[:200]}...")
                else:
                    print("  ⚠️ 无完整内容")
            
            # 生成报告
            print(f"\n📄 生成报告:")
            report_result = report_generator(
                content=results,
                format="markdown",
                max_words=800,
                title="张飞生平研究报告"
            )
            
            if report_result.get('status') == 'success':
                print("✅ 报告生成成功")
                
                output_data = report_result.get('data', {}).get('primary', {})
                report_content = output_data.get('report_content', '')
                
                print(f"报告字数: {len(report_content.split())}")
                print(f"报告长度: {len(report_content)} 字符")
                
                # 检查报告质量
                garbage_indicators = ['拼音', '音标', '威妥玛', '国际音标', '闽南语', '粤拼', '耶鲁拼音']
                found_garbage = []
                for indicator in garbage_indicators:
                    if indicator in report_content:
                        found_garbage.append(indicator)
                
                if found_garbage:
                    print(f"⚠️ 报告中仍包含垃圾信息: {', '.join(found_garbage)}")
                else:
                    print("✅ 报告质量良好，无垃圾信息")
                
                print(f"\n报告预览:")
                lines = report_content.split('\n')[:15]
                for line in lines:
                    print(f"  {line}")
                if len(report_content.split('\n')) > 15:
                    print("  ...")
                    
            else:
                print(f"❌ 报告生成失败: {report_result.get('message', '未知错误')}")
        else:
            print(f"❌ 搜索失败: {search_result.get('message', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("开始测试内容净化效果...\n")
    
    # 测试模拟数据
    test_content_cleaning()
    
    # 测试真实搜索
    test_real_search()
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main() 