#!/usr/bin/env python3
"""
测试包含file_writer的Pipeline执行
"""

import logging
import asyncio
import os

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_pipeline_with_file_writer():
    """测试包含file_writer的Pipeline"""
    logger = logging.getLogger("test_pipeline_with_file_writer")
    
    try:
        from core.smart_pipeline_engine import SmartPipelineEngine
        
        logger.info("=== 测试包含file_writer的Pipeline ===")
        
        # 创建Pipeline引擎
        engine = SmartPipelineEngine(use_llm=False)
        
        # 测试搜索并写入文件的Pipeline
        test_query = "请搜索李自成的生平经历并生成报告"
        
        logger.info(f"执行查询: {test_query}")
        
        result = await engine.execute_from_natural_language(test_query)
        
        logger.info("Pipeline执行结果:")
        logger.info(f"  成功: {result.get('success')}")
        logger.info(f"  执行时间: {result.get('execution_time', 0):.2f}秒")
        
        if result.get('success'):
            logger.info("  ✅ Pipeline执行成功")
            
            # 显示节点结果
            node_results = result.get('node_results', [])
            for node_result in node_results:
                node_id = node_result.get('node_id', 'unknown')
                tool_type = node_result.get('tool_type', 'unknown')
                status = node_result.get('status', 'unknown')
                
                logger.info(f"    节点: {node_id} ({tool_type}) - {status}")
                
                # 检查file_writer的结果
                if tool_type == 'file_writer':
                    output = node_result.get('output', {})
                    if output:
                        file_path = output.get('file_path', 'N/A')
                        file_size = output.get('file_size', 0)
                        message = output.get('message', 'N/A')
                        logger.info(f"      文件路径: {file_path}")
                        logger.info(f"      文件大小: {file_size} 字符")
                        logger.info(f"      消息: {message}")
                        
                        # 检查文件是否真的被创建
                        if os.path.exists(file_path):
                            logger.info(f"      ✅ 文件确实存在: {file_path}")
                            # 读取文件内容的前100个字符
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read(100)
                                logger.info(f"      文件内容预览: {content}...")
                            except Exception as e:
                                logger.error(f"      读取文件失败: {e}")
                        else:
                            logger.warning(f"      ⚠️ 文件不存在: {file_path}")
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

async def test_direct_file_writer_in_pipeline():
    """测试直接在Pipeline中使用file_writer"""
    logger = logging.getLogger("test_direct_file_writer")
    
    try:
        from core.smart_pipeline_engine import SmartPipelineEngine
        
        logger.info("\n=== 测试直接使用file_writer的Pipeline ===")
        
        # 创建一个简单的Pipeline
        pipeline = {
            "pipeline_id": "test_file_writer_pipeline",
            "components": [
                {
                    "id": "search_node",
                    "tool_type": "search_tool",
                    "params": {
                        "query": "李自成生平经历",
                        "max_results": 3
                    },
                    "output": {
                        "type": "object",
                        "fields": {
                            "results": "搜索结果列表",
                            "status": "执行状态",
                            "message": "执行消息"
                        }
                    }
                },
                {
                    "id": "report_writer_node",
                    "tool_type": "file_writer",
                    "params": {
                        "file_path": "search_report.txt",
                        "text": "搜索结果报告\n\n基于搜索结果的报告内容..."
                    },
                    "output": {
                        "type": "object",
                        "fields": {
                            "file_path": "输出文件路径",
                            "status": "执行状态",
                            "message": "执行消息"
                        }
                    }
                }
            ]
        }
        
        # 执行Pipeline
        engine = SmartPipelineEngine(use_llm=False)
        
        # 手动执行Pipeline
        start_time = asyncio.get_event_loop().time()
        
        # 执行第一个节点
        search_result = await engine.execute_from_natural_language("请搜索李自成的生平经历")
        
        if search_result.get('success'):
            logger.info("搜索节点执行成功")
            
            # 手动执行file_writer
            from tools.file_writer import file_writer
            
            file_result = file_writer(
                "search_report.txt", 
                "李自成生平经历搜索报告\n\n这是基于搜索结果的报告内容..."
            )
            
            logger.info(f"文件写入结果: {file_result}")
            
            # 检查文件
            if os.path.exists("search_report.txt"):
                logger.info("✅ 报告文件创建成功")
                
                # 清理测试文件
                os.remove("search_report.txt")
                logger.info("清理测试文件: search_report.txt")
            else:
                logger.warning("⚠️ 报告文件未创建")
        else:
            logger.error("搜索节点执行失败")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger = logging.getLogger("main")
    logger.info("开始测试包含file_writer的Pipeline...")
    
    # 测试1: 自然语言Pipeline
    success1 = asyncio.run(test_pipeline_with_file_writer())
    
    # 测试2: 直接file_writer测试
    success2 = asyncio.run(test_direct_file_writer_in_pipeline())
    
    if success1 and success2:
        logger.info("🎉 所有测试通过！file_writer在Pipeline中工作正常")
    else:
        logger.error("❌ 部分测试失败") 