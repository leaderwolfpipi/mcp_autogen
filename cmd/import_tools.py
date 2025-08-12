import sys
import os
import yaml
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


def import_tools():
    """导入工具的主函数"""
    try:
        # 读取数据库连接信息
        PG_HOST = os.environ.get("PG_HOST", "106.14.24.138")
        PG_PORT = os.environ.get("PG_PORT", "5432")
        PG_USER = os.environ.get("PG_USER", "postgres")
        PG_PASSWORD = os.environ.get("PG_PASSWORD", "mypass123_lh007")
        PG_DB = os.environ.get("PG_DB", "mcp")
        db_url = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

        registry = ToolRegistry(db_url)
        yaml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "tools.yaml")
        
        if not os.path.exists(yaml_path):
            logger.warning(f"tools.yaml not found: {yaml_path}")
            return
            
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            count = 0
            for tool in data.get("tools", []):
                try:
                    registry.register_tool({
                        "tool_id": tool["id"],
                        "description": tool.get("description"),
                        "input_type": tool.get("input_type"),
                        "output_type": tool.get("output_type"),
                        "params": tool.get("params", {})
                    })
                    logger.info(f"导入工具: {tool['id']}")
                    count += 1
                except Exception as e:
                    logger.warning(f"跳过工具 {tool['id']}: {e}")
            logger.info(f"共导入 {count} 个工具.")
    except Exception as e:
        logger.error(f"导入工具失败: {e}")


def main():
    """命令行入口函数"""
    import_tools()


if __name__ == "__main__":
    main() 