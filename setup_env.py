#!/usr/bin/env python3
"""
MCP AutoGen 环境配置脚本
帮助用户快速设置所需的环境变量以启用完整功能
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """创建 .env 配置文件"""
    
    env_content = """# MCP AutoGen 环境变量配置
# =============================================================================
# OpenAI 配置 (推荐，用于智能模式检测和LLM功能)
# =============================================================================

# OpenAI API Key - 必须设置才能启用完整的LLM功能
# 获取方式：https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# OpenAI API Base URL (可选，默认使用官方API)
# 如果使用代理或其他兼容的API端点，可以设置此项
# OPENAI_API_BASE=https://api.openai.com/v1

# OpenAI 模型选择 (可选，默认: gpt-4-turbo)
# 可选值: gpt-4o, gpt-4-turbo, gpt-4, gpt-3.5-turbo
OPENAI_MODEL=gpt-4-turbo

# =============================================================================
# 数据库配置
# =============================================================================

# 数据库连接字符串 (可选，默认使用SQLite)
# DATABASE_URL=sqlite:///./mcp_autogen.db

# =============================================================================
# 服务器配置
# =============================================================================

# API服务器端口 (可选，默认: 8000)
PORT=8000

# 日志级别 (可选，默认: INFO)
# 可选值: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# =============================================================================
# 功能开关
# =============================================================================

# 是否启用调试模式 (可选，默认: false)
DEBUG=false

# 最大并发任务数 (可选，默认: 10)
MAX_CONCURRENT_TASKS=10

# =============================================================================
# 重要提示
# =============================================================================

# 1. 如果不设置 OPENAI_API_KEY，系统将使用简化的模式检测逻辑
# 2. 建议设置 API Key 以获得最佳的智能体验
# 3. 请确保 API Key 有足够的配额
# 4. 不要将包含真实 API Key 的 .env 文件提交到版本控制系统
"""
    
    env_path = Path(".env")
    
    if env_path.exists():
        print(f"⚠️  .env 文件已存在")
        response = input("是否覆盖现有配置？(y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ 操作取消")
            return False
    
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"✅ .env 配置文件创建成功: {env_path.absolute()}")
        return True
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
        return False

def check_current_config():
    """检查当前环境配置"""
    print("🔍 当前环境配置检查:")
    
    # 检查关键环境变量
    important_vars = [
        ("OPENAI_API_KEY", "OpenAI API密钥"),
        ("OPENAI_API_BASE", "OpenAI API基础URL"),
        ("OPENAI_MODEL", "OpenAI模型"),
        ("PORT", "服务器端口"),
        ("LOG_LEVEL", "日志级别")
    ]
    
    for var_name, var_desc in important_vars:
        value = os.getenv(var_name)
        if value:
            # 对于API Key，只显示前4个和后4个字符
            if "KEY" in var_name and len(value) > 8:
                display_value = f"{value[:4]}...{value[-4:]}"
            else:
                display_value = value
            print(f"  ✅ {var_desc}: {display_value}")
        else:
            print(f"  ❌ {var_desc}: 未设置")
    
    print()

def setup_interactive():
    """交互式设置环境变量"""
    print("🛠️  交互式环境配置")
    
    # 获取用户输入
    api_key = input("请输入您的 OpenAI API Key (留空跳过): ").strip()
    
    if api_key:
        # 验证API Key格式
        if not api_key.startswith(('sk-', 'sk-proj-')):
            print("⚠️  API Key格式可能不正确，OpenAI API Key通常以 'sk-' 开头")
        
        # 询问其他配置
        model = input("请选择模型 (默认: gpt-4-turbo): ").strip() or "gpt-4-turbo"
        port = input("请输入服务器端口 (默认: 8000): ").strip() or "8000"
        
        # 生成配置内容
        config_lines = [
            f"OPENAI_API_KEY={api_key}",
            f"OPENAI_MODEL={model}",
            f"PORT={port}",
            "LOG_LEVEL=INFO"
        ]
        
        # 写入文件
        env_path = Path(".env")
        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                for line in config_lines:
                    f.write(line + '\n')
            print(f"✅ 配置已保存到: {env_path.absolute()}")
            print("🚀 请重启服务以应用新配置")
            return True
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            return False
    else:
        print("⚠️  跳过API Key配置，将使用简化的模式检测")
        return False

def load_env_file():
    """加载.env文件到环境变量"""
    env_path = Path(".env")
    
    if not env_path.exists():
        return False
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        return True
    except Exception as e:
        print(f"❌ 加载.env文件失败: {e}")
        return False

def main():
    print("🚀 MCP AutoGen 环境配置工具")
    print("=" * 50)
    
    # 检查当前配置
    check_current_config()
    
    print("请选择操作:")
    print("1. 创建示例配置文件 (.env)")
    print("2. 交互式配置环境变量")
    print("3. 加载现有.env文件到当前会话")
    print("4. 退出")
    
    choice = input("\n请输入选项 (1-4): ").strip()
    
    if choice == '1':
        create_env_file()
        print("\n📝 请编辑 .env 文件，填写您的 API Key 和其他配置")
        
    elif choice == '2':
        setup_interactive()
        
    elif choice == '3':
        if load_env_file():
            print("✅ .env 文件已加载到当前会话")
            check_current_config()
        else:
            print("❌ 未找到 .env 文件或加载失败")
            
    elif choice == '4':
        print("👋 再见!")
        
    else:
        print("❌ 无效选项")

if __name__ == "__main__":
    main() 