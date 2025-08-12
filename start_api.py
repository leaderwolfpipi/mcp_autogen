#!/usr/bin/env python3
"""
启动MCP AutoGen API服务
"""

import uvicorn
import os
import sys
from pathlib import Path

def main():
    """启动API服务"""
    # 确保在正确的目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # 检查环境变量
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  警告: 未设置OPENAI_API_KEY环境变量")
        print("   请设置: export OPENAI_API_KEY=your_api_key")
    
    # 启动服务
    print("🚀 启动MCP AutoGen API服务...")
    print("📖 API文档: http://localhost:8000/docs")
    print("🌍 演示页面: http://localhost:8000/")
    print("🔌 WebSocket: ws://localhost:8000/ws/execute_task")
    print("=" * 50)
    
    uvicorn.run(
        "api.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 