#!/usr/bin/env python3
"""
测试改进后的搜索和报告生成功能
验证内容提取和清理是否正常工作
"""

import logging
import sys
import os
import asyncio
import json

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_improved_search_and_report():
    """测试改进后的搜索和报告生成功能"""
    logger = logging.getLogger("test_improved_search_and_report")
    
    try:
        # 导入智能Pipeline引擎
        from core.smart_pipeline_engine import SmartPipelineEngine
        
        logger.info("初始化智能Pipeline引擎...")
        engine = SmartPipelineEngine(use_llm=False)  # 不使用LLM，使用规则解析
        
        # 测试查询
        test_query = "请搜索李自成的生平经历和事迹，并生成详细报告"
        
        logger.info(f"执行测试查询: {test_query}")
        
        # 执行pipeline
        result = await engine.execute_from_natural_language(test_query)
        
        logger.info(f"执行结果:")
        logger.info(f"  成功: {result.get('success', False)}")
        logger.info(f"  执行时间: {result.get('execution_time', 0):.2f}秒")
        
        if result.get('success'):
            logger.info("  ✅ Pipeline执行成功")
            
            # 显示节点结果
            node_results = result.get('node_results', [])
            for node_result in node_results:
                tool_type = node_result.get('tool_type', 'unknown')
                status = node_result.get('status', 'unknown')
                
                logger.info(f"    节点: {node_result.get('node_id')}")
                logger.info(f"      工具: {tool_type}")
                logger.info(f"      状态: {status}")
                
                # 检查输出内容
                output = node_result.get('output', {})
                if output and tool_type == 'report_generator':
                    logger.info("      📄 报告生成器输出:")
                    
                    # 保存报告到文件
                    report_file = "improved_lizicheng_report.json"
                    with open(report_file, 'w', encoding='utf-8') as f:
                        json.dump(output, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"      报告已保存到: {report_file}")
                    
                    # 显示报告摘要
                    if isinstance(output, dict):
                        summary = output.get('summary', '')
                        if summary:
                            logger.info(f"      摘要: {summary[:200]}...")
                        
                        content_length = output.get('content_length', 0)
                        word_count = output.get('word_count', 0)
                        logger.info(f"      内容长度: {content_length} 字符")
                        logger.info(f"      词数: {word_count}")
                        
                        key_entities = output.get('key_entities', [])
                        if key_entities:
                            logger.info(f"      关键实体: {', '.join(key_entities[:5])}")
        else:
            errors = result.get('errors', [])
            logger.error(f"  ❌ Pipeline执行失败:")
            for error in errors:
                logger.error(f"    - {error}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_direct_tools():
    """直接测试工具功能"""
    logger = logging.getLogger("test_direct_tools")
    
    try:
        # 测试智能搜索
        from tools.smart_search import smart_search
        
        logger.info("测试智能搜索工具...")
        search_result = smart_search("李自成生平", max_results=3)
        
        if search_result.get('status') == 'success':
            results = search_result.get('data', {}).get('primary', [])
            logger.info(f"搜索成功，找到 {len(results)} 个结果")
            
            for i, result in enumerate(results):
                title = result.get('title', 'N/A')
                full_content = result.get('full_content', '')
                content_length = len(full_content) if full_content else 0
                
                logger.info(f"  结果 {i+1}: {title}")
                logger.info(f"    内容长度: {content_length} 字符")
                
                if full_content:
                    # 检查内容是否包含导航元素
                    nav_keywords = ['跳转到内容', '主菜单', '导航', '维基百科']
                    has_nav = any(keyword in full_content for keyword in nav_keywords)
                    logger.info(f"    包含导航元素: {'是' if has_nav else '否'}")
                    
                    # 显示内容前200字符
                    preview = full_content[:200].replace('\n', ' ')
                    logger.info(f"    内容预览: {preview}...")
        
        # 测试报告生成器
        from tools.report_generator import report_generator
        
        logger.info("\n测试报告生成器...")
        if search_result.get('status') == 'success':
            results = search_result.get('data', {}).get('primary', [])
            report = report_generator(results, format="structured")
            
            if isinstance(report, dict):
                logger.info("报告生成成功")
                logger.info(f"  内容长度: {report.get('content_length', 0)}")
                logger.info(f"  词数: {report.get('word_count', 0)}")
                
                summary = report.get('summary', '')
                if summary:
                    logger.info(f"  摘要: {summary[:300]}...")
                
                # 保存改进的报告
                improved_report_file = "improved_direct_report.json"
                with open(improved_report_file, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                
                logger.info(f"  报告已保存到: {improved_report_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"直接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    logger = logging.getLogger("main")
    
    logger.info("开始测试改进后的搜索和报告生成功能...")
    
    # 测试直接工具功能
    logger.info("\n=== 测试直接工具功能 ===")
    await test_direct_tools()
    
    # 测试完整pipeline
    logger.info("\n=== 测试完整Pipeline ===")
    await test_improved_search_and_report()
    
    logger.info("\n测试完成！")

if __name__ == "__main__":
    asyncio.run(main()) 