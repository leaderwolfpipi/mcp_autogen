#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖安装脚本
用于安装专业Markdown到PDF转换所需的依赖
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_command(command):
    """检查命令是否可用"""
    try:
        subprocess.run([command, '--version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_on_macos():
    """在macOS上安装依赖"""
    print("🍎 检测到macOS系统")
    
    # 检查是否安装了Homebrew
    if not check_command('brew'):
        print("📦 正在安装Homebrew...")
        install_script = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        os.system(install_script)
    
    # 安装pandoc
    if not check_command('pandoc'):
        print("📄 正在安装Pandoc...")
        os.system('brew install pandoc')
    else:
        print("✅ Pandoc已安装")
    
    # 安装LaTeX (BasicTeX)
    if not check_command('xelatex'):
        print("📚 正在安装LaTeX...")
        os.system('brew install --cask basictex')
        
        # 添加到PATH
        tex_path = '/Library/TeX/texbin'
        if tex_path not in os.environ.get('PATH', ''):
            print(f"🔧 请将 {tex_path} 添加到您的PATH环境变量中")
            print("在 ~/.zshrc 或 ~/.bash_profile 中添加:")
            print(f"export PATH=$PATH:{tex_path}")
    else:
        print("✅ LaTeX已安装")

def install_on_ubuntu():
    """在Ubuntu/Debian上安装依赖"""
    print("🐧 检测到Ubuntu/Debian系统")
    
    # 更新包列表
    os.system('sudo apt update')
    
    # 安装pandoc
    if not check_command('pandoc'):
        print("📄 正在安装Pandoc...")
        os.system('sudo apt install -y pandoc')
    else:
        print("✅ Pandoc已安装")
    
    # 安装LaTeX
    if not check_command('xelatex'):
        print("📚 正在安装LaTeX...")
        os.system('sudo apt install -y texlive-xetex texlive-lang-chinese')
    else:
        print("✅ LaTeX已安装")

def install_on_centos():
    """在CentOS/RHEL上安装依赖"""
    print("🐧 检测到CentOS/RHEL系统")
    
    # 安装pandoc
    if not check_command('pandoc'):
        print("📄 正在安装Pandoc...")
        os.system('sudo yum install -y pandoc')
    else:
        print("✅ Pandoc已安装")
    
    # 安装LaTeX
    if not check_command('xelatex'):
        print("📚 正在安装LaTeX...")
        os.system('sudo yum install -y texlive-xetex texlive-lang-chinese')
    else:
        print("✅ LaTeX已安装")

def install_on_windows():
    """在Windows上安装依赖"""
    print("🪟 检测到Windows系统")
    
    print("📦 请手动安装以下软件:")
    print("1. Pandoc: https://pandoc.org/installing.html")
    print("2. MiKTeX: https://miktex.org/download")
    print("3. 或者使用Chocolatey:")
    print("   choco install pandoc miktex")
    
    # 检查是否已安装
    if check_command('pandoc'):
        print("✅ Pandoc已安装")
    else:
        print("❌ Pandoc未安装")
    
    if check_command('xelatex'):
        print("✅ LaTeX已安装")
    else:
        print("❌ LaTeX未安装")

def main():
    """主函数"""
    print("🔧 专业Markdown到PDF转换工具 - 依赖安装")
    print("=" * 50)
    
    system = platform.system().lower()
    
    if system == 'darwin':
        install_on_macos()
    elif system == 'linux':
        # 检测Linux发行版
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                if 'ubuntu' in content or 'debian' in content:
                    install_on_ubuntu()
                elif 'centos' in content or 'redhat' in content:
                    install_on_centos()
                else:
                    print("❌ 不支持的Linux发行版")
                    print("请手动安装pandoc和LaTeX")
        except FileNotFoundError:
            print("❌ 无法检测Linux发行版")
            print("请手动安装pandoc和LaTeX")
    elif system == 'windows':
        install_on_windows()
    else:
        print(f"❌ 不支持的操作系统: {system}")
        return
    
    print("\n" + "=" * 50)
    print("📋 安装完成！")
    print("\n使用方法:")
    print("1. 单个文件转换:")
    print("   python professional_md_to_pdf.py input.md")
    print("\n2. 批量转换:")
    print("   python professional_md_to_pdf.py input_directory --batch")
    print("\n3. 自定义参数:")
    print("   python professional_md_to_pdf.py input.md --title '文档标题' --author '作者名'")

if __name__ == '__main__':
    main() 