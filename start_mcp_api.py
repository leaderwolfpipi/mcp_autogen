#!/usr/bin/env python3
"""
MCP协议API服务启动脚本
"""

import os
import sys
import logging
import asyncio
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
    """启动MCP API服务"""
    logger.info("🚀 启动MCP协议API服务...")
    
    # 检查环境变量
    required_env_vars = []
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"⚠️ 缺少环境变量: {', '.join(missing_vars)}")
        logger.info("💡 可以在.env文件中设置这些变量")
    
    # 设置默认端口
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🌐 服务将在 http://{host}:{port} 启动")
    logger.info(f"🔗 WebSocket端点: ws://{host}:{port}/ws/mcp/chat")
    logger.info(f"📺 演示页面: http://{host}:{port}/demo")
    
    try:
        # 导入并启动服务
        import uvicorn
        from api.mcp_api import app
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 收到中断信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 