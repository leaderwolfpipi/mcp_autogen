#!/usr/bin/env python3
"""
测试通用工具分类系统
"""

import json
from core.requirement_parser import RequirementParser
from core.tool_category_manager import ToolCategoryManager, CategoryRule

def test_basic_categorization():
    """测试基本分类功能"""
    
    # 创建分类管理器
    category_manager = ToolCategoryManager()
    
    # 测试工具
    test_tools = [
        {
            "name": "smart_search",
            "description": "智能搜索工具",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "results": {"type": "array", "description": "搜索结果"},
                    "status": {"type": "string", "description": "状态"},
                    "message": {"type": "string", "description": "消息"}
                }
            }
        },
        {
            "name": "image_rotator",
            "description": "图像旋转工具",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "temp_path": {"type": "string", "description": "临时路径"},
                    "rotated_image_path": {"type": "string", "description": "旋转后路径"},
                    "status": {"type": "string", "description": "状态"},
                    "message": {"type": "string", "description": "消息"}
                }
            }
        },
        {
            "name": "ai_code_generator",
            "description": "AI代码生成器",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "generated_code": {"type": "string", "description": "生成的代码"},
                    "language": {"type": "string", "description": "编程语言"},
                    "status": {"type": "string", "description": "状态"},
                    "message": {"type": "string", "description": "消息"}
                }
            }
        }
    ]
    
    # 分类工具
    categorized = category_manager.categorize_tools(test_tools)
    
    print("=== 基本分类测试 ===")
    for category_name, tools in categorized.items():
        if tools:
            emoji = category_manager.get_category_emoji(category_name)
            print(f"{emoji} {category_name}:")
            for tool_name, _ in tools:
                print(f"  - {tool_name}")
    print()

def test_custom_category():
    """测试自定义分类功能"""
    
    # 创建分类管理器
    category_manager = ToolCategoryManager()
    
    # 添加自定义分类
    blockchain_category = CategoryRule(
        name="区块链工具",
        keywords=["blockchain", "crypto", "ethereum", "bitcoin", "smart_contract"],
        output_patterns=["block_data", "transaction", "wallet", "contract"],
        emoji="⛓️",
        description="区块链和加密货币相关工具",
        priority=8
    )
    
    category_manager.add_category(blockchain_category)
    
    # 测试工具
    test_tools = [
        {
            "name": "blockchain_explorer",
            "description": "区块链浏览器",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "block_data": {"type": "object", "description": "区块数据"},
                    "transaction_count": {"type": "integer", "description": "交易数量"},
                    "status": {"type": "string", "description": "状态"},
                    "message": {"type": "string", "description": "消息"}
                }
            }
        },
        {
            "name": "crypto_wallet",
            "description": "加密货币钱包",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "wallet_address": {"type": "string", "description": "钱包地址"},
                    "balance": {"type": "number", "description": "余额"},
                    "status": {"type": "string", "description": "状态"},
                    "message": {"type": "string", "description": "消息"}
                }
            }
        }
    ]
    
    # 分类工具
    categorized = category_manager.categorize_tools(test_tools)
    
    print("=== 自定义分类测试 ===")
    for category_name, tools in categorized.items():
        if tools:
            emoji = category_manager.get_category_emoji(category_name)
            print(f"{emoji} {category_name}:")
            for tool_name, _ in tools:
                print(f"  - {tool_name}")
    print()

def test_requirement_parser_integration():
    """测试与RequirementParser的集成"""
    
    # 创建解析器
    parser = RequirementParser(use_llm=False)
    
    # 添加自定义分类
    parser.add_custom_category(
        category_name="机器学习工具",
        keywords=["ml", "machine_learning", "neural", "tensorflow", "pytorch"],
        output_patterns=["model", "prediction", "training", "accuracy"],
        emoji="🧠"
    )
    
    # 测试工具
    test_tools = [
        {
            "name": "smart_search",
            "description": "智能搜索工具",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "results": {"type": "array", "description": "搜索结果"},
                    "status": {"type": "string", "description": "状态"},
                    "message": {"type": "string", "description": "消息"}
                }
            }
        },
        {
            "name": "ml_model_trainer",
            "description": "机器学习模型训练器",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "model_path": {"type": "string", "description": "模型路径"},
                    "accuracy": {"type": "number", "description": "准确率"},
                    "training_time": {"type": "number", "description": "训练时间"},
                    "status": {"type": "string", "description": "状态"},
                    "message": {"type": "string", "description": "消息"}
                }
            }
        },
        {
            "name": "blockchain_explorer",
            "description": "区块链浏览器",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "block_data": {"type": "object", "description": "区块数据"},
                    "transaction_count": {"type": "integer", "description": "交易数量"},
                    "status": {"type": "string", "description": "状态"},
                    "message": {"type": "string", "description": "消息"}
                }
            }
        }
    ]
    
    # 更新工具列表
    parser.update_available_tools(test_tools)
    
    # 生成工具输出字段说明
    tool_output_guide = parser._generate_tool_output_schema_guide()
    
    print("=== RequirementParser集成测试 ===")
    print(tool_output_guide)
    print()

def test_scalability_with_many_tools():
    """测试大量工具的可扩展性"""
    
    # 生成大量测试工具
    large_tool_set = []
    
    # 不同类型的工具
    tool_types = [
        ("search_engine", "搜索", ["results", "query_results"]),
        ("image_processor", "图像", ["temp_path", "processed_image"]),
        ("text_analyzer", "文本", ["analyzed_text", "sentiment"]),
        ("ml_predictor", "机器学习", ["prediction", "confidence"]),
        ("blockchain_tool", "区块链", ["block_data", "transaction"]),
        ("api_client", "网络", ["response", "status_code"]),
        ("database_query", "数据库", ["query_result", "rows"]),
        ("file_converter", "文件", ["converted_file", "output_path"])
    ]
    
    for i, (base_name, category, output_fields) in enumerate(tool_types):
        for j in range(5):  # 每种类型5个工具
            tool_name = f"{base_name}_{i}_{j}"
            large_tool_set.append({
                "name": tool_name,
                "description": f"{category}工具{i}_{j}",
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        field: {"type": "string", "description": f"{field}描述"}
                        for field in output_fields
                    }
                }
            })
    
    print(f"=== 可扩展性测试 - {len(large_tool_set)}个工具 ===")
    
    # 创建分类管理器
    category_manager = ToolCategoryManager()
    
    # 测试性能
    import time
    start_time = time.time()
    
    categorized = category_manager.categorize_tools(large_tool_set)
    
    end_time = time.time()
    print(f"分类耗时: {end_time - start_time:.4f}秒")
    
    # 显示分类结果
    for category_name, tools in categorized.items():
        if tools:
            emoji = category_manager.get_category_emoji(category_name)
            print(f"{emoji} {category_name}: {len(tools)}个工具")
    
    print()

def test_configuration_persistence():
    """测试配置持久化"""
    
    # 创建分类管理器
    category_manager = ToolCategoryManager("test_categories.json")
    
    # 添加自定义分类
    custom_category = CategoryRule(
        name="测试分类",
        keywords=["test", "demo", "example"],
        output_patterns=["test_result", "demo_output"],
        emoji="🧪",
        description="测试用分类",
        priority=9
    )
    
    category_manager.add_category(custom_category)
    
    # 创建新的分类管理器实例，测试配置是否持久化
    new_category_manager = ToolCategoryManager("test_categories.json")
    
    # 检查自定义分类是否存在
    categories = new_category_manager.get_all_categories()
    test_category = next((cat for cat in categories if cat.name == "测试分类"), None)
    
    print("=== 配置持久化测试 ===")
    if test_category:
        print(f"✅ 自定义分类持久化成功: {test_category.name}")
        print(f"   关键词: {test_category.keywords}")
        print(f"   输出模式: {test_category.output_patterns}")
        print(f"   Emoji: {test_category.emoji}")
    else:
        print("❌ 自定义分类持久化失败")
    
    # 清理测试文件
    import os
    if os.path.exists("test_categories.json"):
        os.remove("test_categories.json")
    
    print()

if __name__ == "__main__":
    print("🧪 测试通用工具分类系统")
    print("=" * 60)
    
    test_basic_categorization()
    test_custom_category()
    test_requirement_parser_integration()
    test_scalability_with_many_tools()
    test_configuration_persistence()
    
    print("✅ 所有测试完成！") 