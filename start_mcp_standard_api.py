#!/usr/bin/env python3
"""
标准MCP协议API服务启动脚本
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """启动标准MCP API服务"""
    logger.info("🚀 启动标准MCP协议API服务...")
    
    # 设置默认端口
    port = int(os.getenv("PORT", 8000))  # 改为8000以匹配前端配置
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🌐 标准MCP服务将在 http://{host}:{port} 启动")
    logger.info(f"🔗 标准MCP WebSocket端点: ws://{host}:{port}/ws/mcp/standard")
    logger.info(f"💬 聊天WebSocket端点: ws://{host}:{port}/ws/mcp/chat")  # 新增聊天端点
    logger.info(f"📺 标准MCP演示页面: http://{host}:{port}/demo/standard")
    logger.info(f"📋 MCP协议信息: http://{host}:{port}/mcp/info")
    logger.info(f"🔧 可用工具: http://{host}:{port}/mcp/tools")
    
    try:
        # 导入并启动服务
        import uvicorn
        from api.mcp_standard_api import app
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            ws_max_size=16 * 1024 * 1024,  # 16MB WebSocket消息大小限制
            ws_ping_interval=None,  # 禁用ping
            ws_ping_timeout=None   # 禁用ping超时
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 收到中断信号，正在关闭标准MCP服务...")
    except Exception as e:
        logger.error(f"❌ 标准MCP服务启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 