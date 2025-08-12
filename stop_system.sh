#!/bin/bash
echo "🛑 停止MCP聊天系统..."
if kill -0 8204 2>/dev/null; then
    kill 8204
    echo "✅ 后端服务已停止"
else
    echo "⚠️  后端服务已经停止"
fi

if kill -0 8407 2>/dev/null; then
    kill 8407
    echo "✅ 前端服务已停止"
else
    echo "⚠️  前端服务已经停止"
fi
echo "🎉 系统已完全停止"
