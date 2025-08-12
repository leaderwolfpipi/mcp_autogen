#!/usr/bin/env python3
"""
测试SmartPipelineEngine的通用占位符解析
"""

import asyncio
import logging
from core.smart_pipeline_engine import SmartPipelineEngine
from core.requirement_parser import RequirementParser

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TestRequirementParser(RequirementParser):
    """测试用的LLM解析器"""
    
    def parse(self, user_input: str) -> dict:
        """生成测试用的pipeline定义"""
        self.logger.info(f"===测试LLM解析: {user_input}")
        
        # 根据输入生成不同的pipeline
        if "旋转" in user_input and "放大" in user_input:
            return {
                "pipeline_id": "test_pipeline_001",
                "components": [
                    {
                        "id": "rotate_node",
                        "tool_type": "image_rotator",
                        "params": {
                            "image_path": "input_image.jpg",
                            "angle": 45
                        },
                        "output": {
                            "type": "any",
                            "key": "rotated_image",
                            "description": "旋转后的图片"
                        }
                    },
                    {
                        "id": "scale_node",
                        "tool_type": "image_scaler",
                        "params": {
                            "image_path": "$rotate_node.output.temp_path",  # 精确指定使用temp_path
                            "scale_factor": 3
                        },
                        "output": {
                            "type": "any",
                            "key": "scaled_image",
                            "description": "放大后的图片"
                        }
                    }
                ]
            }
        elif "翻译" in user_input:
            return {
                "pipeline_id": "test_pipeline_002",
                "components": [
                    {
                        "id": "translate_node",
                        "tool_type": "text_translator",
                        "params": {
                            "text": "Hello World",
                            "source_lang": "en",
                            "target_lang": "zh"
                        },
                        "output": {
                            "type": "any",
                            "key": "translated_text",
                            "description": "翻译后的文本"
                        }
                    }
                ]
            }
        else:
            return {
                "pipeline_id": "test_pipeline_default",
                "components": []
            }

class TestSmartPipelineEngine(SmartPipelineEngine):
    """测试用的智能Pipeline引擎"""
    
    def __init__(self):
        super().__init__(use_llm=False)
        self.requirement_parser = TestRequirementParser(use_llm=False)

async def test_smart_pipeline_universal():
    """测试SmartPipelineEngine的通用占位符解析"""
    print("🚀 测试SmartPipelineEngine的通用占位符解析")
    print("=" * 60)
    
    engine = TestSmartPipelineEngine()
    
    # 测试用例
    test_cases = [
        {
            "input": "请将图片旋转45度，然后放大3倍",
            "description": "复合图像处理pipeline",
            "expected_tools": ["image_rotator", "image_scaler"],
            "expected_final_output_type": "str"  # 应该返回文件路径字符串
        },
        {
            "input": "请将这段文字翻译成中文",
            "description": "文本翻译pipeline",
            "expected_tools": ["text_translator"],
            "expected_final_output_type": "str"  # 应该返回翻译后的文本
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 测试 {i}: {test_case['description']}")
        print(f"输入: {test_case['input']}")
        
        # 执行pipeline
        result = await engine.execute_from_natural_language(test_case['input'])
        
        print(f"执行结果: {'成功' if result['success'] else '失败'}")
        print(f"执行时间: {result['execution_time']:.3f}秒")
        
        if result['success']:
            print(f"最终输出: {result['final_output']}")
            print(f"最终输出类型: {type(result['final_output']).__name__}")
            
            # 验证工具类型
            if result['node_results']:
                actual_tools = [node['tool_type'] for node in result['node_results']]
                expected_tools = test_case['expected_tools']
                
                if actual_tools == expected_tools:
                    print(f"✅ 工具类型匹配: {actual_tools}")
                else:
                    print(f"❌ 工具类型不匹配: 期望 {expected_tools}, 实际 {actual_tools}")
                
                # 显示节点执行详情
                print(f"节点执行详情:")
                for node in result['node_results']:
                    print(f"  - {node['node_id']}: {node['status']}")
                    if 'output' in node:
                        output = node['output']
                        if isinstance(output, dict):
                            print(f"    输出结构: {list(output.keys())}")
                        else:
                            print(f"    输出: {output}")
            
            # 验证最终输出类型
            actual_output_type = type(result['final_output']).__name__
            expected_output_type = test_case['expected_final_output_type']
            
            if actual_output_type == expected_output_type:
                print(f"✅ 最终输出类型正确: {actual_output_type}")
            else:
                print(f"❌ 最终输出类型错误: 期望 {expected_output_type}, 实际 {actual_output_type}")
        else:
            print(f"错误: {result['errors']}")

def test_placeholder_resolution_in_pipeline():
    """测试pipeline中的占位符解析"""
    print(f"\n🔗 测试pipeline中的占位符解析")
    print("=" * 60)
    
    from core.placeholder_resolver import PlaceholderResolver, NodeOutput
    
    resolver = PlaceholderResolver()
    
    # 模拟第一个节点的输出
    rotate_output = {
        'status': 'success',
        'original_size': (1280, 888),
        'rotated_size': (1534, 1534),
        'angle': 45,
        'rotated_image': '<PIL.Image.Image object>',
        'temp_path': '/tmp/rotated_image.png',
        'metadata': {
            'format': 'PNG',
            'mode': 'RGB'
        }
    }
    
    # 创建第一个节点的输出
    rotate_node_output = NodeOutput(
        node_id="rotate_node",
        output_type="any",
        output_key="rotated_image",
        value=rotate_output,
        description="旋转后的图片"
    )
    
    node_outputs = {"rotate_node": rotate_node_output}
    
    # 模拟第二个节点的参数（使用占位符）
    scale_params = {
        "image_path": "$rotate_node.output.temp_path",  # 精确指定使用temp_path
        "scale_factor": 3
    }
    
    print("第二个节点的原始参数:", scale_params)
    print("第一个节点的输出:", rotate_output)
    
    # 解析占位符
    resolved_params = resolver.resolve_placeholders(scale_params, node_outputs)
    
    print("解析后的参数:", resolved_params)
    
    # 验证结果
    expected_path = '/tmp/rotated_image.png'
    actual_path = resolved_params["image_path"]
    
    if actual_path == expected_path:
        print("✅ 占位符解析成功！")
        print(f"  期望: {expected_path}")
        print(f"  实际: {actual_path}")
    else:
        print("❌ 占位符解析失败！")
        print(f"  期望: {expected_path}")
        print(f"  实际: {actual_path}")

if __name__ == "__main__":
    asyncio.run(test_smart_pipeline_universal())
    test_placeholder_resolution_in_pipeline() 