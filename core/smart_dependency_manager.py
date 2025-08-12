#!/usr/bin/env python3
"""
智能依赖管理器
能够自动检测依赖问题并与用户交互解决
"""

import logging
import asyncio
import importlib
import subprocess
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import re


class DependencyStatus(Enum):
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    MISSING = "missing"
    INSTALLING = "installing"
    FAILED = "failed"


@dataclass
class DependencyIssue:
    package_name: str
    display_name: str
    description: str
    install_command: str
    status: DependencyStatus
    error_message: Optional[str] = None
    alternative_packages: Optional[List[str]] = None
    manual_steps: Optional[List[str]] = None


class SmartDependencyManager:
    def __init__(self, user_interaction_callback: Optional[Callable] = None):
        self.logger = logging.getLogger("SmartDependencyManager")
        self.user_interaction_callback = user_interaction_callback
        
        # 预定义的依赖配置
        self.dependency_configs = {
            "baidusearch": {
                "display_name": "百度搜索库",
                "description": "用于执行百度搜索的Python库",
                "install_command": "pip install baidusearch",
                "alternative_packages": ["requests", "beautifulsoup4"],
                "manual_steps": [
                    "1. 打开终端或命令提示符",
                    "2. 运行: pip install baidusearch",
                    "3. 如果失败，可以尝试: pip install --user baidusearch"
                ]
            },
            "googlesearch-python": {
                "display_name": "谷歌搜索库",
                "description": "用于执行谷歌搜索的Python库",
                "install_command": "pip install googlesearch-python",
                "alternative_packages": ["requests", "beautifulsoup4"],
                "manual_steps": [
                    "1. 打开终端或命令提示符",
                    "2. 运行: pip install googlesearch-python",
                    "3. 如果失败，可以尝试: pip install --user googlesearch-python"
                ]
            }
        }
        
        self._package_cache: Dict[str, DependencyStatus] = {}
    
    def check_package_availability(self, package_name: str) -> DependencyStatus:
        if package_name in self._package_cache:
            return self._package_cache[package_name]
        
        try:
            importlib.import_module(package_name)
            self._package_cache[package_name] = DependencyStatus.AVAILABLE
            return DependencyStatus.AVAILABLE
        except ImportError:
            self._package_cache[package_name] = DependencyStatus.MISSING
            return DependencyStatus.MISSING
    
    def analyze_error_message(self, error_message: str) -> List[DependencyIssue]:
        issues = []
        
        import_patterns = {
            r"ModuleNotFoundError: No module named '([^']+)'": "missing_module",
            r"ImportError: No module named '([^']+)'": "missing_module",
            r"([a-zA-Z_][a-zA-Z0-9_]*)库未安装": "missing_library",
            r"([a-zA-Z_][a-zA-Z0-9_]*)未安装": "missing_library"
        }
        
        for pattern, error_type in import_patterns.items():
            matches = re.findall(pattern, error_message)
            for match in matches:
                package_name = match.strip()
                if package_name in self.dependency_configs:
                    config = self.dependency_configs[package_name]
                    issues.append(DependencyIssue(
                        package_name=package_name,
                        display_name=config["display_name"],
                        description=config["description"],
                        install_command=config["install_command"],
                        status=DependencyStatus.MISSING,
                        error_message=error_message,
                        alternative_packages=config.get("alternative_packages"),
                        manual_steps=config.get("manual_steps")
                    ))
        
        return issues
    
    def format_issue_message(self, issues: List[DependencyIssue]) -> str:
        if not issues:
            return ""
        
        message = "🔧 **依赖问题检测**\n\n"
        message += "系统检测到以下依赖包缺失，这可能导致功能无法正常使用：\n\n"
        
        for i, issue in enumerate(issues, 1):
            message += f"**{i}. {issue.display_name}**\n"
            message += f"   📝 {issue.description}\n"
            message += f"   💻 安装命令: `{issue.install_command}`\n"
            
            if issue.alternative_packages:
                message += f"   🔄 替代方案: {', '.join(issue.alternative_packages)}\n"
            
            message += "\n"
        
        message += "**解决方案选择：**\n\n"
        message += "🤖 **自动安装** - 我将帮您自动安装所有缺失的依赖包\n"
        message += "📋 **手动安装** - 显示详细的安装步骤，您手动执行\n"
        message += "❌ **跳过** - 暂时跳过，稍后手动处理\n\n"
        message += "请选择操作方式：\n"
        message += "- 回复 `auto` 或 `自动` 进行自动安装\n"
        message += "- 回复 `manual` 或 `手动` 查看手动安装步骤\n"
        message += "- 回复 `skip` 或 `跳过` 暂时跳过\n"
        
        return message
    
    def parse_user_response(self, response: str) -> str:
        if not response:
            return "skip"
        
        response_lower = response.lower().strip()
        
        if response_lower in ["auto", "自动", "yes", "y", "是", "确认"]:
            return "auto"
        elif response_lower in ["manual", "手动", "manual_install", "步骤"]:
            return "manual"
        elif response_lower in ["skip", "跳过", "no", "n", "否", "取消"]:
            return "skip"
        else:
            return "skip"
    
    async def install_package(self, package_name: str, install_command: str) -> bool:
        try:
            self.logger.info(f"开始安装 {package_name}...")
            
            process = await asyncio.create_subprocess_shell(
                install_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(f"✅ {package_name} 安装成功")
                self._package_cache[package_name] = DependencyStatus.AVAILABLE
                return True
            else:
                error_msg = stderr.decode() if stderr else "未知错误"
                self.logger.error(f"❌ {package_name} 安装失败: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ {package_name} 安装异常: {e}")
            return False
    
    async def handle_dependency_issues(self, issues: List[DependencyIssue]) -> bool:
        if not issues:
            return True
        
        self.logger.info(f"检测到 {len(issues)} 个依赖问题")
        
        message = self.format_issue_message(issues)
        
        if self.user_interaction_callback:
            try:
                user_response = await self.user_interaction_callback(message)
                action = self.parse_user_response(user_response)
            except Exception as e:
                self.logger.error(f"用户交互失败: {e}")
                action = "skip"
        else:
            action = "skip"
        
        if action == "auto":
            self.logger.info("用户选择自动安装依赖")
            success_count = 0
            
            for issue in issues:
                success = await self.install_package(issue.package_name, issue.install_command)
                if success:
                    success_count += 1
            
            if success_count == len(issues):
                self.logger.info("✅ 所有依赖安装成功")
                return True
            else:
                self.logger.warning(f"⚠️ 部分依赖安装失败 ({success_count}/{len(issues)})")
                return False
                
        else:
            self.logger.info("用户选择跳过依赖安装")
            return False


# 全局智能依赖管理器实例
smart_dependency_manager = SmartDependencyManager() 