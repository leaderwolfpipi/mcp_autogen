#!/bin/bash

echo "🚀 开始部署前端应用..."

# 进入前端目录
cd frontend/mcp_chat

# 安装依赖
echo "📦 安装依赖..."
npm install

# 构建生产版本
echo "🔨 构建生产版本..."
npm run build

# 检查构建结果
if [ $? -eq 0 ]; then
    echo "✅ 构建成功！"
    echo "📁 构建文件位于: dist/"
    
    # 启动开发服务器进行测试
    echo "🌐 启动开发服务器进行测试..."
    echo "📖 访问地址: http://localhost:5173"
    echo "🔌 WebSocket地址: ws://localhost:8000/ws/execute_task"
    echo ""
    echo "💡 提示:"
    echo "1. 确保后端API服务器已启动 (python start_api.py)"
    echo "2. 在浏览器中访问 http://localhost:5173"
    echo "3. 测试WebSocket连接和消息流式输出"
    echo ""
    
    # 启动开发服务器
    npm run dev
else
    echo "❌ 构建失败！"
    exit 1
fi