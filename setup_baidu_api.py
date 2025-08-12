#!/usr/bin/env python3
"""
百度搜索API配置助手
"""

import os
import re
from pathlib import Path

def check_env_file():
    """检查.env文件是否存在"""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env文件不存在")
        return False
    return True

def read_current_config():
    """读取当前配置"""
    env_file = Path('.env')
    if not env_file.exists():
        return None, None
    
    content = env_file.read_text()
    
    # 提取百度API配置
    api_key_match = re.search(r'BAIDU_API_KEY=(.+)', content)
    secret_key_match = re.search(r'BAIDU_SECRET_KEY=(.+)', content)
    
    api_key = api_key_match.group(1) if api_key_match else None
    secret_key = secret_key_match.group(1) if secret_key_match else None
    
    return api_key, secret_key

def update_env_file(api_key, secret_key):
    """更新.env文件"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env文件不存在，请先创建.env文件")
        return False
    
    content = env_file.read_text()
    
    # 更新API密钥
    if re.search(r'BAIDU_API_KEY=', content):
        content = re.sub(r'BAIDU_API_KEY=.+', f'BAIDU_API_KEY={api_key}', content)
    else:
        content += f'\nBAIDU_API_KEY={api_key}'
    
    # 更新Secret密钥
    if re.search(r'BAIDU_SECRET_KEY=', content):
        content = re.sub(r'BAIDU_SECRET_KEY=.+', f'BAIDU_SECRET_KEY={secret_key}', content)
    else:
        content += f'\nBAIDU_SECRET_KEY={secret_key}'
    
    # 写入文件
    env_file.write_text(content)
    return True

def validate_api_key(api_key):
    """验证API密钥格式"""
    if not api_key or api_key == 'your-baidu-api-key-here':
        return False
    
    # 百度API密钥通常是24个字符
    if len(api_key) < 20:
        return False
    
    return True

def validate_secret_key(secret_key):
    """验证Secret密钥格式"""
    if not secret_key or secret_key == 'your-baidu-secret-key-here':
        return False
    
    # 百度Secret密钥通常是32个字符
    if len(secret_key) < 20:
        return False
    
    return True

def test_search_config():
    """测试搜索配置"""
    try:
        from tools.search_tool import search_tool
        result = search_tool('测试搜索')
        
        if result['status'] == 'success':
            print(f"✅ 搜索测试成功！")
            print(f"   搜索源: {result['source']}")
            print(f"   结果数量: {len(result['results'])}")
            return True
        else:
            print(f"❌ 搜索测试失败: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ 搜索测试出错: {e}")
        return False

def main():
    """主函数"""
    print("🔧 百度搜索API配置助手")
    print("=" * 50)
    
    # 检查.env文件
    if not check_env_file():
        print("请先创建.env文件")
        return
    
    # 读取当前配置
    current_api_key, current_secret_key = read_current_config()
    
    print(f"当前配置:")
    print(f"  API密钥: {'已配置' if validate_api_key(current_api_key) else '未配置或无效'}")
    print(f"  Secret密钥: {'已配置' if validate_secret_key(current_secret_key) else '未配置或无效'}")
    print()
    
    # 如果配置有效，测试搜索
    if validate_api_key(current_api_key) and validate_secret_key(current_secret_key):
        print("🧪 测试当前配置...")
        if test_search_config():
            print("✅ 当前配置工作正常！")
            return
        else:
            print("❌ 当前配置有问题，需要重新配置")
            print()
    
    # 交互式配置
    print("📝 开始配置百度搜索API")
    print()
    print("请按照以下步骤获取百度API密钥:")
    print("1. 访问 https://developer.baidu.com/")
    print("2. 使用百度账户登录")
    print("3. 点击'控制台' → '创建应用'")
    print("4. 应用名称: MCP搜索工具")
    print("5. 应用类型: 选择'服务端'")
    print("6. 创建后复制API Key和Secret Key")
    print()
    
    # 获取API密钥
    while True:
        api_key = input("请输入百度API密钥: ").strip()
        if validate_api_key(api_key):
            break
        print("❌ API密钥格式无效，请重新输入")
    
    # 获取Secret密钥
    while True:
        secret_key = input("请输入百度Secret密钥: ").strip()
        if validate_secret_key(secret_key):
            break
        print("❌ Secret密钥格式无效，请重新输入")
    
    # 更新配置文件
    print()
    print("💾 更新配置文件...")
    if update_env_file(api_key, secret_key):
        print("✅ 配置文件更新成功")
    else:
        print("❌ 配置文件更新失败")
        return
    
    # 测试新配置
    print()
    print("🧪 测试新配置...")
    if test_search_config():
        print("✅ 配置成功！百度搜索功能已启用")
    else:
        print("❌ 配置测试失败，请检查API密钥和Secret密钥是否正确")

if __name__ == "__main__":
    main() 