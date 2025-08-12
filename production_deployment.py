 #!/usr/bin/env python3
"""
生产级别部署方案
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List
from pathlib import Path
from core.integrated_pipeline import IntegratedPipeline
from core.universal_adapter import UniversalAdapter
from core.mcp_wrapper import MCPWrapper

class ProductionDeployment:
    """
    生产级别部署管理器
    """
    
    def __init__(self, config_path: str = "config/production.json"):
        self.logger = logging.getLogger("ProductionDeployment")
        self.config_path = config_path
        self.pipeline = IntegratedPipeline()
        self.config = self._load_config()
        
        # 设置日志
        self._setup_logging()
        
        # 初始化系统
        self._initialize_system()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "logging": {
                "level": "INFO",
                "file": "logs/production.log",
                "max_size": "100MB",
                "backup_count": 5
            },
            "pipeline": {
                "max_concurrent": 10,
                "timeout": 300,
                "retry_count": 3,
                "error_handling": "continue"
            },
            "tools": {
                "auto_discovery": True,
                "validation": True,
                "caching": True
            },
            "monitoring": {
                "enabled": True,
                "metrics_interval": 60,
                "health_check_interval": 30
            },
            "security": {
                "api_key_required": True,
                "rate_limiting": True,
                "max_requests_per_minute": 100
            }
        }

    def _setup_logging(self):
        """设置日志"""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/production.log")
        
        # 创建日志目录
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def _initialize_system(self):
        """初始化系统"""
        self.logger.info("初始化生产系统...")
        
        # 创建必要的目录
        self._create_directories()
        
        # 加载预定义流水线
        self._load_predefined_pipelines()
        
        # 初始化监控
        if self.config.get("monitoring", {}).get("enabled", False):
            self._initialize_monitoring()
        
        self.logger.info("生产系统初始化完成")

    def _create_directories(self):
        """创建必要的目录"""
        directories = [
            "logs",
            "data",
            "cache", 
            "temp",
            "config",
            "backups"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def _load_predefined_pipelines(self):
        """加载预定义流水线"""
        pipeline_configs = self.config.get("pipelines", [])
        
        for pipeline_config in pipeline_configs:
            try:
                pipeline_name = pipeline_config["name"]
                pipeline_steps = pipeline_config["steps"]
                pipeline_desc = pipeline_config.get("description", "")
                
                pipeline = self.pipeline.create_pipeline_from_steps(
                    pipeline_name, pipeline_steps, pipeline_desc
                )
                
                self.logger.info(f"加载预定义流水线: {pipeline_name}")
                
            except Exception as e:
                self.logger.error(f"加载流水线失败 {pipeline_config.get('name', 'unknown')}: {e}")

    def _initialize_monitoring(self):
        """初始化监控"""
        self.logger.info("初始化监控系统...")
        # 这里可以集成Prometheus、Grafana等监控工具
        pass

    async def deploy_pipeline(self, pipeline_config: Dict[str, Any]) -> bool:
        """部署流水线"""
        try:
            pipeline_name = pipeline_config["name"]
            pipeline_steps = pipeline_config["steps"]
            pipeline_desc = pipeline_config.get("description", "")
            
            # 验证流水线配置
            if not self._validate_pipeline_config(pipeline_config):
                return False
            
            # 创建流水线
            pipeline = self.pipeline.create_pipeline_from_steps(
                pipeline_name, pipeline_steps, pipeline_desc
            )
            
            # 保存配置
            self._save_pipeline_config(pipeline_config)
            
            self.logger.info(f"流水线部署成功: {pipeline_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"流水线部署失败: {e}")
            return False

    def _validate_pipeline_config(self, config: Dict[str, Any]) -> bool:
        """验证流水线配置"""
        required_fields = ["name", "steps"]
        
        for field in required_fields:
            if field not in config:
                self.logger.error(f"流水线配置缺少必需字段: {field}")
                return False
        
        if not config["steps"]:
            self.logger.error("流水线步骤不能为空")
            return False
        
        # 验证每个步骤
        for i, step in enumerate(config["steps"]):
            if "tool" not in step:
                self.logger.error(f"步骤 {i} 缺少工具名称")
                return False
            
            # 检查工具是否存在
            tool_name = step["tool"]
            if tool_name not in self.pipeline.mcp_wrapper.tools:
                self.logger.warning(f"工具不存在: {tool_name}")
        
        return True

    def _save_pipeline_config(self, config: Dict[str, Any]):
        """保存流水线配置"""
        config_dir = "config/pipelines"
        os.makedirs(config_dir, exist_ok=True)
        
        config_file = os.path.join(config_dir, f"{config['name']}.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    async def execute_pipeline_safe(self, pipeline_name: str, input_data: Any = None,
                                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """安全执行流水线"""
        try:
            # 检查流水线是否存在
            if pipeline_name not in self.pipeline.pipelines:
                raise ValueError(f"流水线不存在: {pipeline_name}")
            
            # 执行流水线
            result = await self.pipeline.execute_pipeline(pipeline_name, input_data, context)
            
            # 记录执行结果
            self._log_execution_result(pipeline_name, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"流水线执行失败 {pipeline_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "pipeline_name": pipeline_name
            }

    def _log_execution_result(self, pipeline_name: str, result: Dict[str, Any]):
        """记录执行结果"""
        log_data = {
            "pipeline_name": pipeline_name,
            "timestamp": asyncio.get_event_loop().time(),
            "success": result.get("success", False),
            "step_count": len(result.get("step_results", [])),
            "error": result.get("error")
        }
        
        # 保存到日志文件
        log_file = "logs/pipeline_executions.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "status": "running",
            "pipelines_count": len(self.pipeline.pipelines),
            "tools_count": len(self.pipeline.mcp_wrapper.tools),
            "executions_count": len(self.pipeline.execution_history),
            "config": self.config
        }

    def backup_system(self) -> str:
        """备份系统"""
        try:
            import shutil
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"backups/system_backup_{timestamp}"
            
            # 创建备份目录
            os.makedirs(backup_dir, exist_ok=True)
            
            # 备份配置文件
            if os.path.exists(self.config_path):
                shutil.copy2(self.config_path, backup_dir)
            
            # 备份流水线配置
            pipeline_config_dir = "config/pipelines"
            if os.path.exists(pipeline_config_dir):
                shutil.copytree(pipeline_config_dir, os.path.join(backup_dir, "pipelines"))
            
            # 备份工具
            tools_dir = "tools"
            if os.path.exists(tools_dir):
                shutil.copytree(tools_dir, os.path.join(backup_dir, "tools"))
            
            # 导出系统状态
            system_state = {
                "pipelines": self.pipeline.export_pipeline_manifest(),
                "timestamp": timestamp
            }
            
            state_file = os.path.join(backup_dir, "system_state.json")
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(system_state, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"系统备份完成: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            self.logger.error(f"系统备份失败: {e}")
            raise

    def restore_system(self, backup_dir: str) -> bool:
        """恢复系统"""
        try:
            import shutil
            
            # 验证备份目录
            if not os.path.exists(backup_dir):
                raise ValueError(f"备份目录不存在: {backup_dir}")
            
            # 恢复配置文件
            config_backup = os.path.join(backup_dir, os.path.basename(self.config_path))
            if os.path.exists(config_backup):
                shutil.copy2(config_backup, self.config_path)
            
            # 恢复流水线配置
            pipeline_backup = os.path.join(backup_dir, "pipelines")
            if os.path.exists(pipeline_backup):
                pipeline_config_dir = "config/pipelines"
                if os.path.exists(pipeline_config_dir):
                    shutil.rmtree(pipeline_config_dir)
                shutil.copytree(pipeline_backup, pipeline_config_dir)
            
            # 恢复工具
            tools_backup = os.path.join(backup_dir, "tools")
            if os.path.exists(tools_backup):
                tools_dir = "tools"
                if os.path.exists(tools_dir):
                    shutil.rmtree(tools_dir)
                shutil.copytree(tools_backup, tools_dir)
            
            self.logger.info(f"系统恢复完成: {backup_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"系统恢复失败: {e}")
            return False

# 全局生产部署实例
production_deployment = ProductionDeployment()

# 便捷函数
async def deploy_pipeline(pipeline_config: Dict[str, Any]) -> bool:
    """部署流水线"""
    return await production_deployment.deploy_pipeline(pipeline_config)

async def execute_pipeline_safe(pipeline_name: str, input_data: Any = None,
                               context: Dict[str, Any] = None) -> Dict[str, Any]:
    """安全执行流水线"""
    return await production_deployment.execute_pipeline_safe(pipeline_name, input_data, context)

def get_system_status() -> Dict[str, Any]:
    """获取系统状态"""
    return production_deployment.get_system_status()

def backup_system() -> str:
    """备份系统"""
    return production_deployment.backup_system()

def restore_system(backup_dir: str) -> bool:
    """恢复系统"""
    return production_deployment.restore_system(backup_dir)