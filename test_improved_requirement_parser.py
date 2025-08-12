#!/usr/bin/env python3
"""
测试改进后的需求解析器的通用性
"""

import json
from core.requirement_parser import RequirementParser

def test_dynamic_tool_output_schema():
    """测试动态工具输出schema生成"""
    
    # 模拟一些工具定义
    mock_tools = [
        {
            "name": "smart_search",
            "description": "智能搜索工具",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "results": {"type": "array", "description": "搜索结果列表"},
                    "status": {"type": "string", "description": "执行状态"},
                    "message": {"type": "string", "description": "执行消息"},
                    "total_count": {"type": "integer", "description": "结果总数"}
                }
            }
        },
        {
            "name": "image_rotator",
            "description": "图像旋转工具",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "temp_path": {"type": "string", "description": "临时文件路径"},
                    "rotated_image_path": {"type": "string", "description": "旋转后的图片路径"},
                    "status": {"type": "string", "description": "执行状态"},
                    "message": {"type": "string", "description": "执行消息"}
                }
            }
        },
        {
            "name": "text_translator",
            "description": "文本翻译工具",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "translated_text": {"type": "string", "description": "翻译后的文本"},
                    "status": {"type": "string", "description": "执行状态"},
                    "message": {"type": "string", "description": "执行消息"}
                }
            }
        },
        {
            "name": "file_uploader",
            "description": "文件上传工具",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "upload_url": {"type": "string", "description": "上传后的URL"},
                    "status": {"type": "string", "description": "执行状态"},
                    "message": {"type": "string", "description": "执行消息"}
                }
            }
        },
        {
            "name": "data_analyzer",
            "description": "数据分析工具",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "analysis_result": {"type": "object", "description": "分析结果"},
                    "charts": {"type": "array", "description": "生成的图表"},
                    "status": {"type": "string", "description": "执行状态"},
                    "message": {"type": "string", "description": "执行消息"}
                }
            }
        }
    ]
    
    # 创建解析器实例
    parser = RequirementParser(use_llm=False, available_tools=mock_tools)
    
    # 测试动态生成工具输出字段说明
    tool_output_guide = parser._generate_tool_output_schema_guide()
    print("=== 动态生成的工具输出字段说明 ===")
    print(tool_output_guide)
    print()
    
    # 测试可用工具文本生成
    available_tools_text = parser._build_available_tools_text()
    print("=== 可用工具列表 ===")
    print(available_tools_text)
    print()
    
    # 测试字段提取
    for tool in mock_tools:
        fields = parser._extract_output_fields(tool.get('outputSchema', {}))
        print(f"{tool['name']}: {fields}")

def test_scalability():
    """测试可扩展性 - 模拟大量工具"""
    
    # 生成大量模拟工具
    large_tool_set = []
    
    # 搜索工具
    for i in range(10):
        large_tool_set.append({
            "name": f"search_engine_{i}",
            "description": f"搜索引擎{i}",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "results": {"type": "array", "description": "搜索结果"},
                    "status": {"type": "string", "description": "状态"},
                    "message": {"type": "string", "description": "消息"}
                }
            }
        })
    
    # 图像处理工具
    for i in range(20):
        large_tool_set.append({
            "name": f"image_processor_{i}",
            "description": f"图像处理器{i}",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "temp_path": {"type": "string", "description": "临时路径"},
                    "processed_path": {"type": "string", "description": "处理后路径"},
                    "status": {"type": "string", "description": "状态"},
                    "message": {"type": "string", "description": "消息"}
                }
            }
        })
    
    # 文本处理工具
    for i in range(15):
        large_tool_set.append({
            "name": f"text_processor_{i}",
            "description": f"文本处理器{i}",
            "outputSchema": {
                "type": "object",
                "properties": {
                    "processed_text": {"type": "string", "description": "处理后的文本"},
                    "status": {"type": "string", "description": "状态"},
                    "message": {"type": "string", "description": "消息"}
                }
            }
        })
    
    print(f"=== 测试可扩展性 - {len(large_tool_set)}个工具 ===")
    
    # 创建解析器实例
    parser = RequirementParser(use_llm=False, available_tools=large_tool_set)
    
    # 测试性能
    import time
    start_time = time.time()
    
    tool_output_guide = parser._generate_tool_output_schema_guide()
    
    end_time = time.time()
    print(f"生成工具输出字段说明耗时: {end_time - start_time:.4f}秒")
    print(f"生成的说明长度: {len(tool_output_guide)}字符")
    print()
    
    # 显示分类结果
    print("=== 工具分类结果 ===")
    print(tool_output_guide)

def test_new_tool_addition():
    """测试新工具添加的便利性"""
    
    # 初始工具集
    initial_tools = [
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
        }
    ]
    
    parser = RequirementParser(use_llm=False, available_tools=initial_tools)
    
    print("=== 初始工具集 ===")
    print(parser._generate_tool_output_schema_guide())
    print()
    
    # 添加新工具
    new_tools = [
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
    
    # 更新工具集
    updated_tools = initial_tools + new_tools
    parser.update_available_tools(updated_tools)
    
    print("=== 添加新工具后 ===")
    print(parser._generate_tool_output_schema_guide())

if __name__ == "__main__":
    print("🧪 测试改进后的需求解析器通用性")
    print("=" * 50)
    
    test_dynamic_tool_output_schema()
    print("\n" + "=" * 50)
    
    test_scalability()
    print("\n" + "=" * 50)
    
    test_new_tool_addition()
    print("\n" + "=" * 50)
    
    print("✅ 所有测试完成！") 