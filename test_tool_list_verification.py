#!/usr/bin/env python3
"""
验证工具列表传递
测试工具列表是否正确传递给需求解析器
"""

import logging
import sys
import os

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_tool_list_passing():
    """测试工具列表传递"""
    logger = logging.getLogger("test_tool_list_passing")
    
    try:
        from core.requirement_parser import RequirementParser
        from core.unified_tool_manager import get_unified_tool_manager
        
        # 获取工具列表
        tool_manager = get_unified_tool_manager()
        available_tools = tool_manager.get_tool_list()
        
        logger.info(f"工具管理器发现的工具数量: {len(available_tools)}")
        
        # 显示搜索相关工具
        search_tools = [tool for tool in available_tools if 'search' in tool.get('name', '').lower()]
        logger.info(f"搜索相关工具数量: {len(search_tools)}")
        
        for tool in search_tools:
            name = tool.get('name', 'unknown')
            description = tool.get('description', 'N/A')
            logger.info(f"  🔍 {name}: {description[:100]}...")
        
        # 创建需求解析器
        parser = RequirementParser(available_tools=available_tools)
        
        # 验证工具列表是否正确传递
        tools_text = parser._build_available_tools_text()
        logger.info("需求解析器中的可用工具列表:")
        logger.info(tools_text)
        
        # 检查是否包含搜索工具
        if 'search_tool' in tools_text and 'baidu_search_tool' in tools_text:
            logger.info("✅ 搜索工具已正确传递给需求解析器")
            return True
        else:
            logger.error("❌ 搜索工具未正确传递给需求解析器")
            return False
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_smart_pipeline_initialization():
    """测试智能Pipeline引擎初始化"""
    logger = logging.getLogger("test_smart_pipeline_initialization")
    
    try:
        from core.smart_pipeline_engine import SmartPipelineEngine
        
        # 初始化引擎
        engine = SmartPipelineEngine(use_llm=False)  # 不使用LLM
        
        # 获取工具列表
        tools_info = engine.list_all_tools()
        
        logger.info(f"智能Pipeline引擎发现的工具数量: {len(tools_info)}")
        
        # 检查搜索工具
        search_tools = {name: info for name, info in tools_info.items() if 'search' in name.lower()}
        
        if search_tools:
            logger.info("✅ 智能Pipeline引擎正确发现了搜索工具:")
            for name, info in search_tools.items():
                description = info.get('description', 'N/A')
                logger.info(f"  🔍 {name}: {description[:100]}...")
            return True
        else:
            logger.error("❌ 智能Pipeline引擎未发现搜索工具")
            return False
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_requirement_parser_without_llm():
    """测试需求解析器（不使用LLM）"""
    logger = logging.getLogger("test_requirement_parser_without_llm")
    
    try:
        from core.requirement_parser import RequirementParser
        from core.unified_tool_manager import get_unified_tool_manager
        
        # 获取工具列表
        tool_manager = get_unified_tool_manager()
        available_tools = tool_manager.get_tool_list()
        
        # 创建需求解析器（不使用LLM）
        parser = RequirementParser(use_llm=False, available_tools=available_tools)
        
        # 测试解析
        test_query = "请搜索李自成的生平经历和事迹"
        logger.info(f"测试解析查询: {test_query}")
        
        result = parser.parse(test_query)
        
        logger.info("解析结果:")
        logger.info(f"  Pipeline ID: {result.get('pipeline_id')}")
        
        components = result.get('components', [])
        logger.info(f"  组件数量: {len(components)}")
        
        for i, comp in enumerate(components):
            tool_type = comp.get('tool_type', 'unknown')
            logger.info(f"    组件{i+1}: {tool_type}")
            
            # 检查是否使用了正确的搜索工具
            if 'search' in tool_type.lower():
                if tool_type in ['search_tool', 'baidu_search_tool']:
                    logger.info(f"    ✅ 正确使用了本地搜索工具: {tool_type}")
                else:
                    logger.warning(f"    ⚠️ 使用了非本地搜索工具: {tool_type}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger = logging.getLogger("main")
    logger.info("开始验证工具列表传递...")
    
    # 测试1: 工具列表传递
    success1 = test_tool_list_passing()
    
    # 测试2: 智能Pipeline引擎初始化
    success2 = test_smart_pipeline_initialization()
    
    # 测试3: 需求解析器（不使用LLM）
    success3 = test_requirement_parser_without_llm()
    
    if success1 and success2 and success3:
        logger.info("🎉 所有测试通过！工具列表传递正确！")
        logger.info("✅ 现在大模型应该能够使用本地的search_tool而不是生成web_searcher")
        sys.exit(0)
    else:
        logger.error("❌ 部分测试失败！")
        sys.exit(1) 