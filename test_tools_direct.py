#!/usr/bin/env python3
"""
直接测试工具链，不使用LLM
"""

import json
import time
from tools.smart_search import smart_search
from tools.report_generator import report_generator
from tools.file_writer import file_writer

def test_tools_chain():
    """直接测试工具链"""
    print("=== 直接测试工具链 ===")
    
    try:
        # 1. 搜索
        print("1. 执行搜索...")
        search_start = time.time()
        search_result = smart_search('李自成', 2)
        search_time = time.time() - search_start
        
        print(f"   搜索状态: {search_result.get('status')}")
        print(f"   搜索耗时: {search_time:.2f}秒")
        
        if search_result.get('status') != 'success':
            print("❌ 搜索失败")
            return
        
        # 提取搜索结果
        search_data = search_result.get('data', {})
        primary_data = search_data.get('primary', [])
        print(f"   搜索结果数量: {len(primary_data)}")
        
        # 2. 生成报告
        print("\n2. 生成报告...")
        report_start = time.time()
        report_result = report_generator(primary_data, 'structured')
        report_time = time.time() - report_start
        
        print(f"   报告生成耗时: {report_time:.2f}秒")
        print(f"   报告长度: {len(report_result)} 字符")
        print(f"   报告前200字符: {report_result[:200]}...")
        
        # 3. 保存文件
        print("\n3. 保存文件...")
        file_start = time.time()
        file_result = file_writer('lizicheng_report.json', report_result)
        file_time = time.time() - file_start
        
        print(f"   文件保存耗时: {file_time:.2f}秒")
        print(f"   文件保存状态: {file_result.get('status')}")
        
        if file_result.get('status') == 'success':
            print(f"   文件路径: {file_result.get('paths', [])}")
        
        # 4. 总结
        total_time = search_time + report_time + file_time
        print(f"\n=== 总结 ===")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"搜索: {search_time:.2f}秒 ({search_time/total_time*100:.1f}%)")
        print(f"报告: {report_time:.2f}秒 ({report_time/total_time*100:.1f}%)")
        print(f"保存: {file_time:.2f}秒 ({file_time/total_time*100:.1f}%)")
        
        # 5. 验证生成的文件
        try:
            with open('lizicheng_report.json', 'r', encoding='utf-8') as f:
                saved_content = f.read()
            print(f"\n✅ 文件验证成功，保存内容长度: {len(saved_content)} 字符")
            
            # 解析JSON验证格式
            parsed = json.loads(saved_content)
            print(f"✅ JSON格式验证成功，包含字段: {list(parsed.keys())}")
            
        except Exception as e:
            print(f"❌ 文件验证失败: {e}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tools_chain() 