#!/usr/bin/env python3
"""
测试通用性修复
"""

import asyncio
import logging
import json
from core.smart_pipeline_engine import SmartPipelineEngine
from core.requirement_parser import RequirementParser

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FixedRequirementParser(RequirementParser):
    """修复后的LLM解析器"""
    
    def parse(self, user_input: str) -> dict:
        """生成修复后的pipeline定义"""
        self.logger.info(f"===修复后LLM解析: {user_input}")
        
        # 根据输入生成不同的pipeline
        if "旋转" in user_input and "放大" in user_input:
            return {
                "pipeline_id": "test_pipeline_001",
                "components": [
                    {
                        "id": "rotate_node",
                        "tool_type": "image_rotator",
                        "params": {
                            "image_path": "tests/images/test.png",
                            "angle": 45
                        },
                        "output": {
                            "type": "any",
                            "key": "rotated_image_path",
                            "description": "旋转后的图片"
                        }
                    },
                    {
                        "id": "scale_node",
                        "tool_type": "image_scaler",
                        "params": {
                            "image_path": "$rotate_node.output.temp_path",  # 使用temp_path
                            "scale_factor": 3
                        },
                        "output": {
                            "type": "any",
                            "key": "scaled_image_path",
                            "description": "放大后的图片"
                        }
                    }
                ]
            }
        else:
            return {
                "pipeline_id": "test_pipeline_default",
                "components": []
            }

class FixedSmartPipelineEngine(SmartPipelineEngine):
    """修复后的智能Pipeline引擎"""
    
    def __init__(self):
        super().__init__(use_llm=False)
        self.requirement_parser = FixedRequirementParser(use_llm=False)

async def test_universal_fixes():
    """测试通用性修复"""
    print("🔧 测试通用性修复")
    print("=" * 60)
    
    engine = FixedSmartPipelineEngine()
    
    # 测试用例
    test_cases = [
        {
            "input": "请将图片旋转45度，然后放大3倍",
            "description": "复合图像处理pipeline",
            "expected_tools": ["image_rotator", "image_scaler"]
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
                            print(f"    输出字段: {list(output.keys())}")
                            # 验证输出是否JSON可序列化
                            try:
                                json.dumps(output)
                                print(f"    ✅ 输出JSON可序列化")
                            except Exception as e:
                                print(f"    ❌ 输出JSON序列化失败: {e}")
                        else:
                            print(f"    输出: {output}")
        else:
            print(f"错误: {result['errors']}")

def test_json_serialization():
    """测试JSON序列化"""
    print(f"\n📄 测试JSON序列化")
    print("=" * 60)
    
    # 测试工具输出是否JSON可序列化
    test_outputs = [
        {
            "status": "success",
            "original_size": (1280, 888),
            "rotated_size": (1534, 1534),
            "angle": 45,
            "rotated_image_path": "/tmp/rotated_image.png",
            "temp_path": "/tmp/rotated_image.png",
            "message": "Image rotated by 45 degrees"
        },
        {
            "status": "success",
            "original_size": (1534, 1534),
            "scaled_size": (4602, 4602),
            "scale_factor": 3,
            "scaled_image_path": "/tmp/scaled_image.png",
            "temp_path": "/tmp/scaled_image.png",
            "message": "Image scaled from (1534, 1534) to (4602, 4602)"
        }
    ]
    
    for i, output in enumerate(test_outputs, 1):
        print(f"\n📝 测试输出 {i}:")
        print(f"输出: {output}")
        
        try:
            json_str = json.dumps(output, indent=2)
            print(f"✅ JSON序列化成功")
            print(f"JSON: {json_str}")
        except Exception as e:
            print(f"❌ JSON序列化失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_universal_fixes())
    test_json_serialization() 