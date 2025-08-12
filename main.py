#!/usr/bin/env python3
"""
主程序入口
"""

import os
import logging
from core.smart_pipeline_engine import SmartPipelineEngine
from core.tool_registry import ToolRegistry

def import_tools():
    """导入工具模块"""
    try:
        import tools
        logging.info("✅ 工具模块导入成功")
    except ImportError as e:
        logging.warning(f"⚠️ 工具模块导入失败: {e}")

def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    import_tools()
    
    # 数据库连接配置
    PG_HOST = os.environ.get("PG_HOST", "106.14.24.138")
    PG_PORT = os.environ.get("PG_PORT", "5432")
    PG_USER = os.environ.get("PG_USER", "postgres")
    PG_PASSWORD = os.environ.get("PG_PASSWORD", "mypass123_lh007")
    PG_DB = os.environ.get("PG_DB", "mcp")
    db_url = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    
    # 初始化数据库工具注册表
    try:
        db_registry = ToolRegistry(db_url)
        logging.info("✅ 数据库工具注册表初始化成功")
    except Exception as e:
        logging.error(f"❌ 数据库工具注册表初始化失败: {e}")
        db_registry = None
    
    # 初始化智能Pipeline引擎（集成数据库工具）
    engine = SmartPipelineEngine(
        use_llm=True,  # 使用规则解析
        db_registry=db_registry
    )
    
    # 显示工具信息
    logging.info("🔧 可用工具列表:")
    tools_info = engine.list_all_tools()
    for tool_name, tool_info in tools_info.items():
        source = tool_info.get("source", "unknown")
        logging.info(f"  - {tool_name} (来源: {source})")
    
    logging.info(f"📊 总共发现 {len(tools_info)} 个工具")
    
    return engine

if __name__ == "__main__":
    main()