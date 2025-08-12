#!/bin/bash

# 前端与MCP标准API完整系统启动脚本

echo "🚀 启动完整MCP聊天系统..."

# 检查是否在正确的目录
if [ ! -f "start_mcp_standard_api.py" ]; then
    echo "❌ 请在项目根目录下运行此脚本"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 加载环境变量
set -a  # 自动导出所有变量
source .env
set +a

# 激活虚拟环境
source venv/bin/activate

echo "📦 检查Python依赖..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 启动后端API服务
echo "🔧 启动MCP标准API服务（后台运行）..."
python3 start_mcp_standard_api.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 后端API已启动，PID: $BACKEND_PID"

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 3

# 检查后端是否正常启动
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "✅ 后端服务运行正常"
else
    echo "❌ 后端服务启动失败，请检查 logs/backend.log"
    exit 1
fi

# 检查前端目录和依赖
if [ ! -d "frontend/mcp_chat" ]; then
    echo "❌ 前端目录不存在: frontend/mcp_chat"
    kill $BACKEND_PID
    exit 1
fi

cd frontend/mcp_chat

echo "📦 检查前端依赖..."
if [ ! -d "node_modules" ]; then
    echo "🔧 安装前端依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 前端依赖安装失败"
        kill $BACKEND_PID
        exit 1
    fi
fi

# 启动前端开发服务器
echo "🎨 启动前端开发服务器..."
npm run dev > ../../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

cd ../..

echo ""
echo "🎉 系统启动完成！"
echo ""
echo "📍 服务地址："
echo "   🌐 后端API:        http://localhost:8000"
echo "   💬 聊天WebSocket:  ws://localhost:8000/ws/mcp/chat"
echo "   🎨 前端应用:       http://localhost:5173"
echo "   📺 API演示:        http://localhost:8000/demo/standard"
echo ""
echo "📊 进程信息："
echo "   🔧 后端PID: $BACKEND_PID"
echo "   🎨 前端PID: $FRONTEND_PID"
echo ""
echo "📝 日志文件："
echo "   📄 后端日志: logs/backend.log"
echo "   📄 前端日志: logs/frontend.log"
echo ""
echo "⭐ 使用说明："
echo "   1. 打开浏览器访问 http://localhost:5173"
echo "   2. 发送消息测试聊天功能"
echo "   3. 尝试发送任务查询观察流式输出"
echo ""
echo "🛑 停止服务："
echo "   执行: kill $BACKEND_PID $FRONTEND_PID"
echo "   或按 Ctrl+C 然后手动终止进程"

# 创建停止脚本
cat > stop_system.sh << EOF
#!/bin/bash
echo "🛑 停止MCP聊天系统..."
if kill -0 $BACKEND_PID 2>/dev/null; then
    kill $BACKEND_PID
    echo "✅ 后端服务已停止"
else
    echo "⚠️  后端服务已经停止"
fi

if kill -0 $FRONTEND_PID 2>/dev/null; then
    kill $FRONTEND_PID
    echo "✅ 前端服务已停止"
else
    echo "⚠️  前端服务已经停止"
fi
echo "🎉 系统已完全停止"
EOF

chmod +x stop_system.sh
echo "💡 提示: 运行 ./stop_system.sh 可以停止所有服务"

# 等待用户中断
echo ""
echo "系统正在运行中... 按 Ctrl+C 退出"
trap "echo ''; echo '🛑 收到退出信号...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '✅ 系统已停止'; exit 0" INT

# 保持脚本运行
while true; do
    # 检查服务是否还在运行
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ 后端服务意外停止"
        break
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ 前端服务意外停止"
        break
    fi
    sleep 5
done

echo "🛑 清理资源..."
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
echo "✅ 清理完成" 