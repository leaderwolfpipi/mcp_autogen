#!/bin/bash

# MCP双协议支持设置脚本
# 用于安装依赖、配置环境和测试功能

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "🚀 MCP双协议支持设置脚本"
    echo "支持stdio和SSE传输协议的MCP服务器"
    echo "=================================================="
    echo -e "${NC}"
}

# 检查Python版本
check_python() {
    print_info "检查Python版本..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3未安装，请先安装Python3.8+"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    major_version=$(echo $python_version | cut -d. -f1)
    minor_version=$(echo $python_version | cut -d. -f2)
    
    if [[ $major_version -lt 3 ]] || [[ $major_version -eq 3 && $minor_version -lt 8 ]]; then
        print_error "Python版本过低 ($python_version)，需要Python 3.8+"
        exit 1
    fi
    
    print_success "Python版本: $python_version"
}

# 检查虚拟环境
check_venv() {
    print_info "检查虚拟环境..."
    
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_warning "未激活虚拟环境"
        
        if [[ -d "venv" ]]; then
            print_info "发现现有虚拟环境，激活中..."
            source venv/bin/activate
            print_success "虚拟环境已激活"
        else
            print_info "创建新虚拟环境..."
            python3 -m venv venv
            source venv/bin/activate
            print_success "虚拟环境已创建并激活"
        fi
    else
        print_success "虚拟环境已激活: $VIRTUAL_ENV"
    fi
}

# 安装依赖
install_dependencies() {
    print_info "安装MCP协议依赖..."
    
    # 升级pip
    python3 -m pip install --upgrade pip
    
    # 安装基础依赖
    if [[ -f "requirements_mcp_protocols.txt" ]]; then
        python3 -m pip install -r requirements_mcp_protocols.txt
        print_success "MCP协议依赖安装完成"
    else
        print_warning "requirements_mcp_protocols.txt 未找到，安装基础依赖..."
        python3 -m pip install fastapi uvicorn sse-starlette aiohttp pydantic
    fi
    
    # 安装现有依赖（如果存在）
    if [[ -f "requirements.txt" ]]; then
        print_info "安装现有项目依赖..."
        python3 -m pip install -r requirements.txt
        print_success "现有依赖安装完成"
    fi
}

# 运行测试
run_tests() {
    print_info "运行MCP双协议功能测试..."
    
    if [[ -f "test_mcp_protocols.py" ]]; then
        python3 test_mcp_protocols.py
    else
        print_error "测试文件 test_mcp_protocols.py 未找到"
        return 1
    fi
}

# 创建启动脚本
create_startup_scripts() {
    print_info "创建启动脚本..."
    
    # Stdio服务器启动脚本
    cat > start_stdio_server.sh << 'EOF'
#!/bin/bash
# Stdio服务器启动脚本

echo "🚀 启动MCP Stdio服务器..."
python3 mcp_stdio_server.py --log-level INFO

EOF
    chmod +x start_stdio_server.sh
    
    # SSE服务器启动脚本  
    cat > start_sse_server.sh << 'EOF'
#!/bin/bash
# SSE服务器启动脚本

echo "🚀 启动MCP SSE服务器..."
echo "访问演示页面: http://localhost:8000/mcp/sse/demo"
python3 -m uvicorn api.mcp_standard_api:app --host 0.0.0.0 --port 8000

EOF
    chmod +x start_sse_server.sh
    
    # 协议网关启动脚本
    cat > start_protocol_gateway.sh << 'EOF'
#!/bin/bash
# 协议网关启动脚本

echo "🚀 启动MCP协议转换网关..."
echo "将stdio服务转换为SSE端点: http://localhost:8001/sse"
python3 mcp_protocol_gateway.py --stdio "python3 mcp_stdio_server.py" --port 8001

EOF
    chmod +x start_protocol_gateway.sh
    
    print_success "启动脚本已创建:"
    echo "  - start_stdio_server.sh     (Stdio服务器)"
    echo "  - start_sse_server.sh       (SSE服务器)"
    echo "  - start_protocol_gateway.sh (协议网关)"
}

# 显示使用指南
show_usage_guide() {
    print_info "MCP双协议使用指南:"
    echo ""
    echo "1. 📋 Stdio模式 (标准输入输出):"
    echo "   ./start_stdio_server.sh"
    echo "   echo '{\"user_query\":\"测试请求\"}' | python3 mcp_stdio_server.py"
    echo ""
    echo "2. 🌐 SSE模式 (服务器推送事件):"
    echo "   ./start_sse_server.sh"
    echo "   访问: http://localhost:8000/mcp/sse/demo"
    echo ""
    echo "3. 🔄 协议转换网关:"
    echo "   ./start_protocol_gateway.sh"
    echo "   访问: http://localhost:8001/sse"
    echo ""
    echo "4. 📊 监控和管理:"
    echo "   curl http://localhost:8000/protocol/stats"
    echo "   curl http://localhost:8000/protocol/connections"
    echo ""
    echo "详细文档: 查看 MCP_PROTOCOL_GUIDE.md"
}

# 主函数
main() {
    print_header
    
    # 检查环境
    check_python
    
    # 处理命令行参数
    case "${1:-setup}" in
        "setup")
            check_venv
            install_dependencies
            create_startup_scripts
            run_tests
            show_usage_guide
            ;;
        "test")
            run_tests
            ;;
        "deps")
            install_dependencies
            ;;
        "clean")
            print_info "清理环境..."
            rm -rf venv __pycache__ *.pyc
            rm -f start_*.sh demo_config.json
            print_success "环境已清理"
            ;;
        "help")
            echo "用法: $0 [command]"
            echo ""
            echo "命令:"
            echo "  setup  - 完整设置 (默认)"
            echo "  test   - 仅运行测试"
            echo "  deps   - 仅安装依赖"
            echo "  clean  - 清理环境"
            echo "  help   - 显示帮助"
            ;;
        *)
            print_error "未知命令: $1"
            print_info "使用 '$0 help' 查看可用命令"
            exit 1
            ;;
    esac
}

# 错误处理
trap 'print_error "设置过程中发生错误，退出码: $?"' ERR

# 运行主函数
main "$@" 