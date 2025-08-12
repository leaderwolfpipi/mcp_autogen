#!/usr/bin/env python3
"""
工具分类管理器
提供可配置、可扩展的工具分类功能
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class CategoryRule:
    """分类规则定义"""
    name: str
    keywords: List[str] = field(default_factory=list)
    output_patterns: List[str] = field(default_factory=list)
    emoji: str = "🔧"
    description: str = ""
    priority: int = 0  # 优先级，数字越大优先级越高

class ToolCategoryManager:
    """工具分类管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config/tool_categories.json"
        self.categories: Dict[str, CategoryRule] = {}
        self._load_default_categories()
        self._load_custom_categories()
    
    def _load_default_categories(self):
        """加载默认分类规则"""
        default_categories = [
            CategoryRule(
                name="搜索工具",
                keywords=["search", "baidu", "google", "bing", "query", "find", "lookup"],
                output_patterns=["data.primary", "search_results", "query_results", "total_count"],
                emoji="🔍",
                description="用于信息搜索和查询的工具",
                priority=10
            ),
            CategoryRule(
                name="图像处理工具",
                keywords=["image", "rotator", "scaler", "processor", "filter", "transform", "resize", "crop", "enhance"],
                output_patterns=["paths", "processed_image", "image_path", "rotated", "scaled", "enhanced"],
                emoji="🖼️",
                description="处理图像文件的工具",
                priority=10
            ),
            CategoryRule(
                name="文本处理工具",
                keywords=["text", "translator", "formatter", "parser", "analyzer", "summarizer", "extractor"],
                output_patterns=["translated_text", "formatted_text", "processed_text", "summary", "extracted_text"],
                emoji="📝",
                description="处理文本内容的工具",
                priority=10
            ),
            CategoryRule(
                name="文件处理工具",
                keywords=["file", "writer", "reader", "converter", "compressor", "extractor"],
                output_patterns=["file_path", "output_path", "converted_file", "compressed_file"],
                emoji="📁",
                description="处理文件操作的工具",
                priority=8
            ),
            CategoryRule(
                name="上传工具",
                keywords=["upload", "uploader", "minio", "s3", "cloud", "storage", "cdn"],
                output_patterns=["upload_url", "download_url", "file_url", "cdn_url"],
                emoji="☁️",
                description="文件上传和存储工具",
                priority=8
            ),
            CategoryRule(
                name="数据分析工具",
                keywords=["analyzer", "analyzer", "statistics", "metrics", "chart", "graph", "dashboard"],
                output_patterns=["analysis_result", "statistics", "charts", "metrics", "dashboard_data"],
                emoji="📊",
                description="数据分析和可视化工具",
                priority=7
            ),
            CategoryRule(
                name="代码处理工具",
                keywords=["code", "generator", "compiler", "linter", "formatter", "debugger"],
                output_patterns=["generated_code", "compiled_code", "formatted_code", "debug_info"],
                emoji="💻",
                description="代码生成和处理工具",
                priority=7
            ),
            CategoryRule(
                name="AI模型工具",
                keywords=["ai", "model", "llm", "gpt", "bert", "neural", "ml"],
                output_patterns=["model_output", "prediction", "embedding", "classification"],
                emoji="🤖",
                description="AI模型和机器学习工具",
                priority=9
            ),
            CategoryRule(
                name="数据库工具",
                keywords=["database", "db", "sql", "nosql", "query", "migration"],
                output_patterns=["query_result", "db_connection", "migration_status"],
                emoji="🗄️",
                description="数据库操作工具",
                priority=6
            ),
            CategoryRule(
                name="网络工具",
                keywords=["network", "http", "api", "rest", "websocket", "proxy"],
                output_patterns=["response", "status_code", "headers", "connection_status"],
                emoji="🌐",
                description="网络和API工具",
                priority=6
            ),
            CategoryRule(
                name="其他工具",
                keywords=[],
                output_patterns=[],
                emoji="🔧",
                description="未分类的工具",
                priority=0
            )
        ]
        
        for category in default_categories:
            self.categories[category.name] = category
    
    def _load_custom_categories(self):
        """加载自定义分类规则"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    custom_data = json.load(f)
                
                for category_data in custom_data.get('categories', []):
                    category = CategoryRule(
                        name=category_data['name'],
                        keywords=category_data.get('keywords', []),
                        output_patterns=category_data.get('output_patterns', []),
                        emoji=category_data.get('emoji', '🔧'),
                        description=category_data.get('description', ''),
                        priority=category_data.get('priority', 5)
                    )
                    self.categories[category.name] = category
                    
        except Exception as e:
            print(f"加载自定义分类规则失败: {e}")
    
    def save_custom_categories(self):
        """保存自定义分类规则"""
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            custom_categories = []
            for category in self.categories.values():
                # 跳过默认分类
                if category.priority < 5:
                    continue
                    
                custom_categories.append({
                    'name': category.name,
                    'keywords': category.keywords,
                    'output_patterns': category.output_patterns,
                    'emoji': category.emoji,
                    'description': category.description,
                    'priority': category.priority
                })
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({'categories': custom_categories}, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存自定义分类规则失败: {e}")
    
    def add_category(self, category: CategoryRule):
        """添加新的分类规则"""
        self.categories[category.name] = category
        self.save_custom_categories()
    
    def remove_category(self, category_name: str):
        """删除分类规则"""
        if category_name in self.categories and self.categories[category_name].priority >= 5:
            del self.categories[category_name]
            self.save_custom_categories()
    
    def update_category(self, category_name: str, **kwargs):
        """更新分类规则"""
        if category_name in self.categories:
            category = self.categories[category_name]
            for key, value in kwargs.items():
                if hasattr(category, key):
                    setattr(category, key, value)
            self.save_custom_categories()
    
    def categorize_tool(self, tool_name: str, output_schema: Dict[str, Any]) -> str:
        """对单个工具进行分类"""
        tool_name_lower = tool_name.lower()
        output_fields = list(output_schema.get('properties', {}).keys())
        
        # 计算每个分类的匹配分数
        category_scores = {}
        
        for category_name, category in self.categories.items():
            if category_name == "其他工具":
                continue
                
            score = 0
            
            # 关键词匹配
            for keyword in category.keywords:
                if keyword.lower() in tool_name_lower:
                    score += 2  # 关键词匹配权重更高
            
            # 输出字段模式匹配
            for pattern in category.output_patterns:
                for field in output_fields:
                    if pattern.lower() in field.lower():
                        score += 1
            
            # 考虑优先级
            score += category.priority * 0.1
            
            category_scores[category_name] = score
        
        # 找到最高分数的分类
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            if best_category[1] > 0:
                return best_category[0]
        
        # 如果没有匹配，返回"其他工具"
        return "其他工具"
    
    def categorize_tools(self, tools: List[Dict[str, Any]]) -> Dict[str, List[tuple]]:
        """对工具列表进行分类"""
        categorized = {category.name: [] for category in self.categories.values()}
        
        for tool in tools:
            tool_name = tool.get('name', '')
            output_schema = tool.get('outputSchema', {})
            
            category_name = self.categorize_tool(tool_name, output_schema)
            categorized[category_name].append((tool_name, output_schema))
        
        return categorized
    
    def get_category_emoji(self, category_name: str) -> str:
        """获取分类对应的emoji"""
        category = self.categories.get(category_name)
        return category.emoji if category else "🔧"
    
    def get_all_categories(self) -> List[CategoryRule]:
        """获取所有分类规则"""
        return list(self.categories.values())
    
    def export_categories(self) -> Dict[str, Any]:
        """导出分类规则"""
        return {
            'categories': [
                {
                    'name': category.name,
                    'keywords': category.keywords,
                    'output_patterns': category.output_patterns,
                    'emoji': category.emoji,
                    'description': category.description,
                    'priority': category.priority
                }
                for category in self.categories.values()
            ]
        } 