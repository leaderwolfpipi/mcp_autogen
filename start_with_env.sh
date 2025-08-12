#!/bin/bash

# 加载环境变量
set -a  # 自动导出所有变量
source .env
set +a

# 激活虚拟环境
source venv/bin/activate

# 启动服务
python3 start_mcp_standard_api.py 