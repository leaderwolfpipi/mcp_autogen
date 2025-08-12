#!/usr/bin/env python3
"""
启动脚本 - 自动加载.env文件并启动MCP AutoGen API服务
"""

import os
import sys
from pathlib import Path

def load_env_file():
    """加载.env文件到环境变量"""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("❌ 未找到.env文件")
        print("💡 请先编辑.env文件，设置您的OpenAI API Key")
        return False
    
    print("📁 加载.env文件...")
    loaded_count = 0
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 跳过占位符值
                        if value == 'your_openai_api_key_here':
                            print(f"⚠️  第{line_num}行: {key} 仍为占位符，请设置真实值")
                            continue
                            
                        os.environ[key] = value
                        loaded_count += 1
                        
                        # 对API Key进行脱敏显示
                        if 'KEY' in key and len(value) > 8:
                            display_value = f"{value[:4]}...{value[-4:]}"
                        else:
                            display_value = value
                        
                        print(f"✅ {key}={display_value}")
                        
                    except ValueError:
                        print(f"⚠️  第{line_num}行格式错误: {line}")
                        
        print(f"📊 成功加载 {loaded_count} 个环境变量")
        return loaded_count > 0
        
    except Exception as e:
        print(f"❌ 加载.env文件失败: {e}")
        return False

def check_api_key():
    """检查API Key是否已正确设置"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY 未设置")
        return False
    
    if api_key == "your_openai_api_key_here":
        print("❌ OPENAI_API_KEY 仍为占位符，请设置真实的API Key")
        return False
    
    if not api_key.startswith(('sk-', 'sk-proj-')):
        print("⚠️  API Key格式可能不正确，OpenAI API Key通常以 'sk-' 开头")
        return False
    
    print(f"✅ API Key已设置: {api_key[:4]}...{api_key[-4:]}")
    return True

def start_api_server():
    """启动API服务器"""
    print("\n🚀 启动MCP AutoGen API服务...")
    
    try:
        # 导入并启动API服务
        from api.mcp_standard_api import app
        import uvicorn
        
        port = int(os.getenv("PORT", 8000))
        
        print(f"🌐 服务将在端口 {port} 启动")
        print(f"📖 演示页面: http://localhost:{port}/demo/standard")
        print("🛑 按 Ctrl+C 停止服务")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            reload=False,
            log_level=os.getenv("LOG_LEVEL", "info").lower()
        )
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("💡 请确保在项目根目录运行此脚本")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def main():
    print("🚀 MCP AutoGen 启动器")
    print("=" * 50)
    
    # 1. 加载环境变量
    if not load_env_file():
        print("\n❌ 环境变量加载失败")
        print("\n💡 解决方案:")
        print("1. 确保.env文件存在于当前目录")
        print("2. 编辑.env文件，设置您的OpenAI API Key:")
        print("   OPENAI_API_KEY=sk-your-actual-api-key-here")
        print("3. 重新运行此脚本")
        return
    
    # 2. 检查关键配置
    print("\n🔍 检查关键配置...")
    has_api_key = check_api_key()
    
    if not has_api_key:
        print("\n⚠️  没有有效的OpenAI API Key")
        print("🔧 系统将使用简化的模式检测逻辑")
        print("💡 建议设置API Key以获得最佳体验")
        
        choice = input("\n是否继续启动服务？(y/N): ").strip().lower()
        if choice not in ['y', 'yes']:
            print("❌ 启动取消")
            return
    
    # 3. 启动服务
    start_api_server()

if __name__ == "__main__":
    main() 