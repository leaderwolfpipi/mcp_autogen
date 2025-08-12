#!/usr/bin/env python3
"""
智能Pipeline系统演示
展示从自然语言到pipeline执行的完整流程
"""

import asyncio
import json
import logging
from core.smart_pipeline_engine import SmartPipelineEngine
from core.requirement_parser import RequirementParser
from core.placeholder_resolver import PlaceholderResolver

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def demo_requirement_parsing():
    """演示需求解析功能"""
    print("🔍 需求解析演示")
    print("=" * 60)
    
    parser = RequirementParser(use_llm=False)  # 使用规则解析进行演示
    
    test_cases = [
        "请将图片旋转45度，然后放大3倍，最后上传到云存储",
        "请将这段文字翻译成英文，然后提取关键词",
        "请将文档转换为PDF格式，然后压缩文件"
    ]
    
    for i, user_input in enumerate(test_cases, 1):
        print(f"\n📝 测试用例 {i}: {user_input}")
        try:
            result = parser.parse(user_input)
            print(f"✅ 解析成功:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"❌ 解析失败: {e}")

def demo_placeholder_resolution():
    """演示占位符解析功能"""
    print("\n🔗 占位符解析演示")
    print("=" * 60)
    
    resolver = PlaceholderResolver()
    
    # 模拟pipeline组件
    components = [
        {
            "id": "rotate_node",
            "tool_type": "image_rotator",
            "params": {
                "image_path": "input.jpg",
                "angle": 45
            },
            "output": {
                "type": "image_path",
                "key": "rotated_image",
                "description": "旋转后的图片路径"
            }
        },
        {
            "id": "scale_node",
            "tool_type": "image_scaler",
            "params": {
                "image_path": "$rotate_node.output",
                "scale_factor": 3
            },
            "output": {
                "type": "image_path",
                "key": "scaled_image",
                "description": "放大后的图片路径"
            }
        },
        {
            "id": "upload_node",
            "tool_type": "file_uploader",
            "params": {
                "file_path": "$scale_node.output",
                "destination": "cloud_storage"
            },
            "output": {
                "type": "json",
                "key": "upload_result",
                "description": "上传结果信息"
            }
        }
    ]
    
    print("📋 Pipeline组件定义:")
    print(json.dumps(components, indent=2, ensure_ascii=False))
    
    # 验证依赖关系
    print("\n🔍 验证依赖关系:")
    errors = resolver.validate_pipeline_dependencies(components)
    if errors:
        print("❌ 验证失败:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ 验证通过")
    
    # 构建执行顺序
    print("\n📋 构建执行顺序:")
    execution_order = resolver.build_execution_order(components)
    print(f"执行顺序: {' -> '.join(execution_order)}")
    
    # 演示占位符解析
    print("\n🔄 占位符解析演示:")
    
    # 模拟节点输出
    node_outputs = {
        "rotate_node": resolver.create_node_output(
            "rotate_node",
            components[0]["output"],
            "/path/to/rotated.jpg"
        ),
        "scale_node": resolver.create_node_output(
            "scale_node", 
            components[1]["output"],
            "/path/to/scaled.jpg"
        )
    }
    
    # 解析第三个节点的参数
    test_params = components[2]["params"]
    resolved_params = resolver.resolve_placeholders(test_params, node_outputs)
    
    print(f"原始参数: {test_params}")
    print(f"解析后参数: {resolved_params}")

async def demo_smart_pipeline_execution():
    """演示智能pipeline执行"""
    print("\n🚀 智能Pipeline执行演示")
    print("=" * 60)
    
    engine = SmartPipelineEngine(use_llm=False)  # 使用规则解析进行演示
    
    test_cases = [
        {
            "name": "图像处理Pipeline",
            "input": "请将图片旋转45度，然后放大3倍，最后上传到云存储"
        },
        {
            "name": "文本处理Pipeline", 
            "input": "请将这段文字翻译成英文，然后提取关键词"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🎯 {test_case['name']}")
        print(f"输入: {test_case['input']}")
        
        try:
            result = await engine.execute_from_natural_language(test_case['input'])
            
            print(f"执行结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
            print(f"执行时间: {result['execution_time']:.2f}秒")
            
            if result['errors']:
                print("错误信息:")
                for error in result['errors']:
                    print(f"  - {error}")
            else:
                print("节点执行详情:")
                for node_result in result['node_results']:
                    status_icon = "✅" if node_result['status'] == 'success' else "❌"
                    print(f"  {status_icon} {node_result['node_id']} ({node_result['tool_type']})")
                    if node_result['status'] == 'success':
                        print(f"    输入: {node_result['input_params']}")
                        print(f"    输出: {node_result['output']}")
                
                print(f"最终输出: {result['final_output']}")
                
        except Exception as e:
            print(f"❌ 执行失败: {e}")

def demo_advanced_features():
    """演示高级功能"""
    print("\n🌟 高级功能演示")
    print("=" * 60)
    
    # 演示复杂的占位符引用
    resolver = PlaceholderResolver()
    
    # 模拟复杂的输出结构
    complex_output = {
        "status": "success",
        "data": {
            "file_path": "/path/to/processed/file.jpg",
            "metadata": {
                "size": 1024000,
                "format": "JPEG"
            }
        },
        "timestamp": "2024-01-01T10:00:00Z"
    }
    
    node_outputs = {
        "process_node": resolver.create_node_output(
            "process_node",
            {"type": "json", "key": "result", "description": "处理结果"},
            complex_output
        )
    }
    
    # 测试不同的占位符引用方式
    test_cases = [
        {
            "name": "完整输出引用",
            "params": {"input": "$process_node.output"}
        },
        {
            "name": "嵌套字段引用",
            "params": {"file_path": "$process_node.output.data.file_path"}
        },
        {
            "name": "混合引用",
            "params": {
                "input_file": "$process_node.output.data.file_path",
                "file_size": "$process_node.output.data.metadata.size",
                "static_param": "fixed_value"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 {test_case['name']}:")
        print(f"原始参数: {test_case['params']}")
        
        resolved = resolver.resolve_placeholders(test_case['params'], node_outputs)
        print(f"解析后参数: {resolved}")

async def main():
    """主函数"""
    print("🎯 智能Pipeline系统完整演示")
    print("=" * 80)
    
    # 1. 需求解析演示
    demo_requirement_parsing()
    
    # 2. 占位符解析演示
    demo_placeholder_resolution()
    
    # 3. 智能pipeline执行演示
    await demo_smart_pipeline_execution()
    
    # 4. 高级功能演示
    demo_advanced_features()
    
    print("\n" + "=" * 80)
    print("🎉 演示完成！")
    print("\n系统特点总结:")
    print("✅ 基于LLM的智能意图识别")
    print("✅ 自动占位符解析和依赖管理")
    print("✅ 拓扑排序确保正确执行顺序")
    print("✅ 支持复杂的数据结构引用")
    print("✅ 自动工具发现和注册")
    print("✅ 完善的错误处理和日志记录")

if __name__ == "__main__":
    asyncio.run(main()) 