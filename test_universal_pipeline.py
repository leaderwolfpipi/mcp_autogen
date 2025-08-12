#!/usr/bin/env python3
"""
通用Pipeline测试 - 展示系统的通用性设计
"""

import asyncio
import logging
import json
from core.smart_pipeline_engine import SmartPipelineEngine
from core.requirement_parser import RequirementParser

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class UniversalRequirementParser(RequirementParser):
    """通用LLM解析器 - 展示系统的通用性"""
    
    def parse(self, user_input: str) -> dict:
        """模拟LLM解析结果 - 支持多种工具类型"""
        self.logger.info(f"===通用LLM解析开始: {user_input}")
        
        # 根据输入生成模拟的LLM响应
        mock_response = self._generate_universal_response(user_input)
        
        # 替换pipeline_id
        import uuid
        mock_response["pipeline_id"] = str(uuid.uuid4())
        self.logger.info(f"===通用LLM解析结果: {json.dumps(mock_response, ensure_ascii=False)}")
        
        return mock_response
    
    def _generate_universal_response(self, user_input: str) -> dict:
        """生成通用的LLM响应 - 支持多种工具类型"""
        
        # 图像处理类
        if "图片" in user_input and "放大" in user_input:
            return {
                "pipeline_id": "auto_generated_uuid",
                "components": [
                    {
                        "id": "scale_node",
                        "tool_type": "image_scaler",
                        "params": {
                            "image_path": "input_image.jpg",
                            "scale_factor": 3
                        },
                        "output": {
                            "type": "image_path",
                            "key": "scaled_image",
                            "description": "放大后的图片"
                        }
                    }
                ]
            }
        
        elif "图片" in user_input and "旋转" in user_input:
            return {
                "pipeline_id": "auto_generated_uuid",
                "components": [
                    {
                        "id": "rotate_node",
                        "tool_type": "image_rotator",
                        "params": {
                            "image_path": "input_image.jpg",
                            "angle": 90
                        },
                        "output": {
                            "type": "image_path",
                            "key": "rotated_image",
                            "description": "旋转后的图片"
                        }
                    }
                ]
            }
        
        # 文本处理类
        elif "文字" in user_input and "翻译" in user_input:
            return {
                "pipeline_id": "auto_generated_uuid",
                "components": [
                    {
                        "id": "translate_node",
                        "tool_type": "text_translator",
                        "params": {
                            "text": "示例文本",
                            "source_lang": "zh",
                            "target_lang": "en"
                        },
                        "output": {
                            "type": "string",
                            "key": "translated_text",
                            "description": "翻译后的文本"
                        }
                    }
                ]
            }
        
        elif "文字" in user_input and "提取" in user_input:
            return {
                "pipeline_id": "auto_generated_uuid",
                "components": [
                    {
                        "id": "extract_node",
                        "tool_type": "text_extractor",
                        "params": {
                            "image_path": "input_image.jpg",
                            "language": "eng+chi_sim"
                        },
                        "output": {
                            "type": "string",
                            "key": "extracted_text",
                            "description": "提取的文字"
                        }
                    }
                ]
            }
        
        # 文件处理类
        elif "文件" in user_input and "上传" in user_input:
            return {
                "pipeline_id": "auto_generated_uuid",
                "components": [
                    {
                        "id": "upload_node",
                        "tool_type": "file_uploader",
                        "params": {
                            "file_path": "input_file.txt",
                            "destination": "cloud_storage"
                        },
                        "output": {
                            "type": "string",
                            "key": "upload_url",
                            "description": "上传后的URL"
                        }
                    }
                ]
            }
        
        # 数据分析类
        elif "数据" in user_input and "分析" in user_input:
            return {
                "pipeline_id": "auto_generated_uuid",
                "components": [
                    {
                        "id": "analyze_node",
                        "tool_type": "data_analyzer",
                        "params": {
                            "data_file": "input_data.csv",
                            "analysis_type": "statistical"
                        },
                        "output": {
                            "type": "json",
                            "key": "analysis_result",
                            "description": "分析结果"
                        }
                    }
                ]
            }
        
        # 复合操作 - 展示pipeline的通用性
        elif "图片" in user_input and "然后" in user_input:
            return {
                "pipeline_id": "auto_generated_uuid",
                "components": [
                    {
                        "id": "process_node",
                        "tool_type": "image_processor",
                        "params": {
                            "image_path": "input_image.jpg",
                            "operation": "enhance"
                        },
                        "output": {
                            "type": "image_path",
                            "key": "processed_image",
                            "description": "处理后的图片"
                        }
                    },
                    {
                        "id": "upload_node",
                        "tool_type": "file_uploader",
                        "params": {
                            "file_path": "$process_node.output",
                            "destination": "cloud_storage"
                        },
                        "output": {
                            "type": "string",
                            "key": "upload_url",
                            "description": "上传后的URL"
                        }
                    }
                ]
            }
        
        # 默认返回空组件
        else:
            return {
                "pipeline_id": "auto_generated_uuid",
                "components": []
            }

class UniversalSmartPipelineEngine(SmartPipelineEngine):
    """通用智能Pipeline引擎"""
    
    def __init__(self):
        # 调用父类的__init__方法
        super().__init__(use_llm=False)
        # 替换为通用解析器
        self.requirement_parser = UniversalRequirementParser(use_llm=False)

async def test_universal_pipeline():
    """测试通用pipeline系统"""
    print("🌐 通用Pipeline系统测试")
    print("=" * 60)
    
    # 初始化通用引擎
    engine = UniversalSmartPipelineEngine()
    
    # 测试不同类型的pipeline
    test_cases = [
        {
            "input": "请将图片放大3倍",
            "description": "图像处理",
            "expected_tools": ["image_scaler"]
        },
        {
            "input": "请将这段文字翻译成英文",
            "description": "文本处理",
            "expected_tools": ["text_translator"]
        },
        {
            "input": "请将文件上传到云存储",
            "description": "文件处理",
            "expected_tools": ["file_uploader"]
        },
        {
            "input": "请分析这个数据文件",
            "description": "数据分析",
            "expected_tools": ["data_analyzer"]
        },
        {
            "input": "请处理图片然后上传",
            "description": "复合操作",
            "expected_tools": ["image_processor", "file_uploader"]
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
            
            # 验证工具类型
            if result['node_results']:
                actual_tools = [node['tool_type'] for node in result['node_results']]
                expected_tools = test_case.get('expected_tools', [])
                
                if actual_tools == expected_tools:
                    print(f"✅ 工具类型匹配: {actual_tools}")
                else:
                    print(f"❌ 工具类型不匹配: 期望 {expected_tools}, 实际 {actual_tools}")
                
                # 显示节点执行详情
                print(f"节点执行详情:")
                for node in result['node_results']:
                    print(f"  - {node['node_id']}: {node['status']}")
                    if 'output' in node:
                        print(f"    输出: {node['output']}")
        else:
            print(f"错误: {result['errors']}")

def test_universal_design_principles():
    """测试通用性设计原则"""
    print(f"\n🎯 通用性设计原则验证")
    print("=" * 60)
    
    # 测试占位符机制
    print("1. 占位符机制测试")
    from core.placeholder_resolver import PlaceholderResolver
    
    resolver = PlaceholderResolver()
    
    # 模拟不同类型的节点输出
    node_outputs = {
        "image_node": resolver.create_node_output(
            "image_node",
            {"type": "image_path", "key": "processed_image", "description": "处理后的图片"},
            "/path/to/processed.jpg"
        ),
        "text_node": resolver.create_node_output(
            "text_node",
            {"type": "string", "key": "extracted_text", "description": "提取的文本"},
            "Hello World"
        ),
        "data_node": resolver.create_node_output(
            "data_node",
            {"type": "json", "key": "analysis_result", "description": "分析结果"},
            {"mean": 10.5, "std": 2.1}
        )
    }
    
    # 测试不同类型的占位符解析
    test_placeholders = [
        {
            "params": {"file_path": "$image_node.output", "destination": "cloud"},
            "description": "图像文件上传"
        },
        {
            "params": {"text": "$text_node.output", "target_lang": "en"},
            "description": "文本翻译"
        },
        {
            "params": {"data": "$data_node.output", "visualization": "chart"},
            "description": "数据可视化"
        }
    ]
    
    for test in test_placeholders:
        resolved = resolver.resolve_placeholders(test["params"], node_outputs)
        print(f"  {test['description']}: {test['params']} -> {resolved}")
    
    # 测试工具生成的通用性
    print("\n2. 工具生成通用性测试")
    from core.code_generator import CodeGenerator
    
    generator = CodeGenerator(use_llm=False)
    
    test_tools = [
        {"tool": "image_processor", "params": {"image_path": "input.jpg", "operation": "enhance"}},
        {"tool": "text_analyzer", "params": {"text": "sample text", "analysis_type": "sentiment"}},
        {"tool": "data_visualizer", "params": {"data_file": "data.csv", "chart_type": "bar"}},
        {"tool": "file_compressor", "params": {"file_path": "input.txt", "compression": "zip"}}
    ]
    
    for tool_spec in test_tools:
        try:
            code = generator.generate(tool_spec)
            print(f"  ✅ {tool_spec['tool']}: 代码生成成功 ({len(code)} 字符)")
        except Exception as e:
            print(f"  ❌ {tool_spec['tool']}: 代码生成失败 - {e}")

if __name__ == "__main__":
    asyncio.run(test_universal_pipeline())
    test_universal_design_principles() 