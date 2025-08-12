#!/usr/bin/env python3
"""
基础依赖管理器
提供简单的依赖检查和安装功能
"""

import logging
import asyncio
import importlib
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import re


class DependencyIssueType(Enum):
    """依赖问题类型"""
    MISSING_PACKAGE = "missing_package"
    VERSION_CONFLICT = "version_conflict"
    PERMISSION_ERROR = "permission_error"
    NETWORK_ERROR = "network_error"
    COMPATIBILITY_ISSUE = "compatibility_issue"
    UNKNOWN = "unknown"


@dataclass
class DependencyIssue:
    """依赖问题"""
    package_name: str
    issue_type: DependencyIssueType
    error_message: str
    suggested_solutions: List[str]
    install_commands: List[str]


class DependencyManager:
    """基础依赖管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger("DependencyManager")
        
        # 常见错误模式
        self.error_patterns = {
            r"ModuleNotFoundError: No module named '([^']+)'": "missing_package",
            r"ImportError: No module named '([^']+)'": "missing_package",
            r"([a-zA-Z_][a-zA-Z0-9_]*)库未安装": "missing_package",
            r"([a-zA-Z_][a-zA-Z0-9_]*)未安装": "missing_package",
            r"Permission denied": "permission_error",
            r"pip install.*failed": "network_error",
            r"version.*conflict": "version_conflict",
            r"incompatible.*version": "compatibility_issue"
        }
    
    def analyze_error(self, error_message: str) -> List[DependencyIssue]:
        """分析错误信息"""
        issues = []
        
        for pattern, issue_type in self.error_patterns.items():
            matches = re.findall(pattern, error_message, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    package_name = match[0]
                else:
                    package_name = match
                
                # 清理包名
                package_name = package_name.strip()
                if "库未安装" in package_name:
                    package_name = package_name.replace("库未安装", "").strip()
                if "未安装" in package_name:
                    package_name = package_name.replace("未安装", "").strip()
                
                # 跳过无效的包名
                if not package_name or len(package_name) < 2:
                    continue
                
                issue = DependencyIssue(
                    package_name=package_name,
                    issue_type=DependencyIssueType(issue_type),
                    error_message=error_message,
                    suggested_solutions=self._get_suggested_solutions(package_name, issue_type),
                    install_commands=self._get_install_commands(package_name, issue_type)
                )
                issues.append(issue)
        
        return issues
    
    def _get_suggested_solutions(self, package_name: str, issue_type: str) -> List[str]:
        """获取建议的解决方案"""
        solutions = {
            "missing_package": [
                f"安装 {package_name} 包",
                f"使用 pip install {package_name}",
                f"如果失败，尝试 pip install --user {package_name}"
            ],
            "permission_error": [
                "使用管理员权限运行",
                "使用 --user 参数安装到用户目录",
                "检查Python环境权限"
            ],
            "version_conflict": [
                "检查包版本兼容性",
                "使用虚拟环境隔离依赖",
                "升级或降级相关包"
            ],
            "network_error": [
                "检查网络连接",
                "使用国内镜像源",
                "重试安装命令"
            ]
        }
        return solutions.get(issue_type, [f"解决 {package_name} 相关问题"])
    
    def _get_install_commands(self, package_name: str, issue_type: str) -> List[str]:
        """获取安装命令"""
        if issue_type == "missing_package":
            return [f"pip install {package_name}"]
        elif issue_type == "permission_error":
            return ["使用管理员权限运行", "使用 --user 参数安装到用户目录"]
        elif issue_type == "version_conflict":
            return ["检查包版本兼容性", "使用虚拟环境隔离依赖", "升级或降级相关包"]
        elif issue_type == "network_error":
            return ["检查网络连接", "使用国内镜像源", "重试安装命令"]
        return []
    
    async def install_package(self, package_name: str) -> bool:
        """安装包"""
        try:
            self.logger.info(f"安装包: {package_name}")
            
            process = await asyncio.create_subprocess_shell(
                f"pip install {package_name}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(f"✅ 安装成功: {package_name}")
                return True
            else:
                error_msg = stderr.decode() if stderr else "未知错误"
                self.logger.error(f"❌ 安装失败: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 执行安装命令异常: {e}")
            return False
    
    def check_package_installed(self, package_name: str) -> bool:
        """检查包是否已安装"""
        try:
            importlib.import_module(package_name)
            return True
        except ImportError:
            return False
    
    async def ensure_dependencies_for_tool(self, tool_name: str, error_message: str) -> bool:
        """确保工具所需的依赖已安装"""
        try:
            issues = self.analyze_error(error_message)
            
            if not issues:
                self.logger.info("未检测到依赖问题")
                return True
            
            self.logger.info(f"检测到 {len(issues)} 个依赖问题")
            
            success_count = 0
            for issue in issues:
                if issue.issue_type == DependencyIssueType.MISSING_PACKAGE:
                    success = await self.install_package(issue.package_name)
                    if success:
                        success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"依赖管理失败: {e}")
            return False


# 全局依赖管理器实例
dependency_manager = DependencyManager()
