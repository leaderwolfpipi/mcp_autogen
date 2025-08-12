#!/usr/bin/env python3
"""
Google Custom Search API 配置助手
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
    
    # 提取Google API配置
    api_key_match = re.search(r'GOOGLE_API_KEY=(.+)', content)
    cse_id_match = re.search(r'GOOGLE_CSE_ID=(.+)', content)
    
    api_key = api_key_match.group(1) if api_key_match else None
    cse_id = cse_id_match.group(1) if cse_id_match else None
    
    return api_key, cse_id

def update_env_file(api_key, cse_id):
    """更新.env文件"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env文件不存在，请先创建.env文件")
        return False
    
    content = env_file.read_text()
    
    # 更新API密钥
    if re.search(r'GOOGLE_API_KEY=', content):
        content = re.sub(r'GOOGLE_API_KEY=.+', f'GOOGLE_API_KEY={api_key}', content)
    else:
        content += f'\nGOOGLE_API_KEY={api_key}'
    
    # 更新搜索引擎ID
    if re.search(r'GOOGLE_CSE_ID=', content):
        content = re.sub(r'GOOGLE_CSE_ID=.+', f'GOOGLE_CSE_ID={cse_id}', content)
    else:
        content += f'\nGOOGLE_CSE_ID={cse_id}'
    
    # 写入文件
    env_file.write_text(content)
    return True

def validate_api_key(api_key):
    """验证API密钥格式"""
    if not api_key or api_key == 'your-google-api-key-here':
        return False
    
    # Google API密钥通常是39个字符，以AIza开头
    if not re.match(r'^AIza[0-9A-Za-z_-]{35}$', api_key):
        return False
    
    return True

def validate_cse_id(cse_id):
    """验证搜索引擎ID格式"""
    if not cse_id or cse_id == 'your-custom-search-engine-id-here':
        return False
    
    # 搜索引擎ID通常是44个字符，包含数字和冒号
    if not re.match(r'^[0-9]{21}:[0-9A-Za-z_-]{22}$', cse_id):
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
    print("🔧 Google Custom Search API 配置助手")
    print("=" * 50)
    
    # 检查.env文件
    if not check_env_file():
        print("请先创建.env文件")
        return
    
    # 读取当前配置
    current_api_key, current_cse_id = read_current_config()
    
    print(f"当前配置:")
    print(f"  API密钥: {'已配置' if validate_api_key(current_api_key) else '未配置或无效'}")
    print(f"  搜索引擎ID: {'已配置' if validate_cse_id(current_cse_id) else '未配置或无效'}")
    print()
    
    # 如果配置有效，测试搜索
    if validate_api_key(current_api_key) and validate_cse_id(current_cse_id):
        print("🧪 测试当前配置...")
        if test_search_config():
            print("✅ 当前配置工作正常！")
            return
        else:
            print("❌ 当前配置有问题，需要重新配置")
            print()
    
    # 交互式配置
    print("📝 开始配置Google Custom Search API")
    print()
    print("请按照以下步骤获取API密钥和搜索引擎ID:")
    print("1. 访问 https://console.cloud.google.com/")
    print("2. 创建项目并启用Custom Search API")
    print("3. 创建API密钥")
    print("4. 访问 https://programmablesearchengine.google.com/")
    print("5. 创建自定义搜索引擎")
    print()
    
    # 获取API密钥
    while True:
        api_key = input("请输入Google API密钥 (格式: AIzaSyC...): ").strip()
        if validate_api_key(api_key):
            break
        print("❌ API密钥格式无效，请重新输入")
    
    # 获取搜索引擎ID
    while True:
        cse_id = input("请输入搜索引擎ID (格式: 012345678901234567890:abcdefghijk): ").strip()
        if validate_cse_id(cse_id):
            break
        print("❌ 搜索引擎ID格式无效，请重新输入")
    
    # 更新配置文件
    print()
    print("💾 更新配置文件...")
    if update_env_file(api_key, cse_id):
        print("✅ 配置文件更新成功")
    else:
        print("❌ 配置文件更新失败")
        return
    
    # 测试新配置
    print()
    print("🧪 测试新配置...")
    if test_search_config():
        print("✅ 配置成功！Google搜索功能已启用")
    else:
        print("❌ 配置测试失败，请检查API密钥和搜索引擎ID是否正确")

if __name__ == "__main__":
    main() 