#!/usr/bin/env python3
"""
MCP Stdio 服务器
支持stdio传输协议的MCP服务器入口
"""

import asyncio
import os
import sys
import argparse
import json
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.protocol_adapter import ProtocolAdapter
from core.mcp_adapter import MCPAdapter


# 配置日志
def setup_logging(log_level: str = "INFO", log_file: str = None):
    """设置日志配置"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # 如果指定了日志文件，写入文件
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        # 否则写入stderr（避免与stdio通信冲突）
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(formatter)
        logger.addHandler(stderr_handler)


def load_config(config_file: str = None) -> dict:
    """加载配置文件"""
    default_config = {
        "llm": {
            "type": "openai",
            "model": "gpt-4-turbo",
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "base_url": os.getenv("OPENAI_BASE_URL", "")
        },
        "tool_registry": {
            "auto_discover": True,
            "tool_paths": ["./tools"]
        },
        "server": {
            "max_sessions": 1000,
            "execution_timeout": 300,
            "max_iterations": 10
        }
    }
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # 合并配置
                for key, value in user_config.items():
                    if isinstance(value, dict) and key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
        except Exception as e:
            logging.error(f"配置文件加载失败: {e}")
    
    return default_config


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MCP Stdio 服务器")
    parser.add_argument("--config", "-c", type=str, help="配置文件路径")
    parser.add_argument("--log-level", "-l", type=str, default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="日志级别")
    parser.add_argument("--log-file", type=str, help="日志文件路径")
    parser.add_argument("--version", "-v", action="store_true", help="显示版本信息")
    
    args = parser.parse_args()
    
    if args.version:
        print("MCP AutoGen Stdio Server v2.0")
        print("支持的传输协议: stdio")
        print("符合MCP 1.0标准")
        return
    
    # 设置日志
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    try:
        # 加载配置
        config = load_config(args.config)
        logger.info(f"配置加载完成: {config.get('server', {})}")
        
        # 初始化MCP适配器
        mcp_adapter = MCPAdapter(
            max_sessions=config["server"]["max_sessions"]
        )
        
        # 初始化协议适配器
        protocol_adapter = ProtocolAdapter(mcp_adapter)
        
        # 显示启动信息
        logger.info("🚀 MCP Stdio 服务器启动")
        logger.info("📋 等待stdin输入...")
        logger.info("🔄 请使用JSON-RPC 2.0格式发送请求")
        
        # 显示使用示例到stderr
        example = {
            "mcp_version": "1.0",
            "session_id": "session_123",
            "request_id": "req_456", 
            "user_query": "帮我搜索Python教程",
            "context": {}
        }
        
        sys.stderr.write("📖 请求示例:\n")
        sys.stderr.write(json.dumps(example, indent=2, ensure_ascii=False) + "\n")
        sys.stderr.write("=" * 50 + "\n")
        sys.stderr.flush()
        
        # 启动stdio服务器
        await protocol_adapter.start_stdio_server()
        
    except KeyboardInterrupt:
        logger.info("📋 接收到停止信号")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)
    finally:
        logger.info("🛑 MCP Stdio 服务器关闭")


if __name__ == "__main__":
    # 确保在事件循环中运行
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n📋 服务器已停止", file=sys.stderr)
        sys.exit(0) 