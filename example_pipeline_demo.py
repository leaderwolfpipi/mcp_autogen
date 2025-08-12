#!/usr/bin/env python3
"""
MCP Pipeline无缝衔接示例
演示图像处理流程：上传 → 缩放 → OCR → 翻译
"""

import asyncio
import os
import sys
from typing import Dict, Any, List
from dataclasses import dataclass

# 模拟MCP工具函数
def image_uploader(image_path: str, bucket_name: str = "default") -> Dict[str, Any]:
    """图像上传工具"""
    print(f"📤 上传图像: {image_path} 到桶: {bucket_name}")
    # 模拟上传成功，返回云端路径
    cloud_path = f"https://storage.example.com/{bucket_name}/{os.path.basename(image_path)}"
    return {
        "status": "success",
        "cloud_path": cloud_path,
        "file_size": 1024000,
        "upload_time": "2024-01-01T10:00:00Z"
    }

def image_scaler(image_path: str, scale_factor: float = 1.0) -> Dict[str, Any]:
    """图像缩放工具"""
    print(f"🔄 缩放图像: {image_path}, 缩放因子: {scale_factor}")
    # 模拟缩放处理
    scaled_path = f"scaled_{os.path.basename(image_path)}"
    return {
        "status": "success",
        "original_path": image_path,
        "scaled_path": scaled_path,
        "new_dimensions": (800, 600),
        "scale_factor": scale_factor
    }

def ocr_processor(image_path: str, language: str = "eng+chi_sim") -> Dict[str, Any]:
    """OCR文字识别工具"""
    print(f"🔍 OCR识别: {image_path}, 语言: {language}")
    # 模拟OCR结果
    extracted_text = "这是一个测试图像，包含中英文混合内容。This is a test image with mixed content."
    return {
        "status": "success",
        "image_path": image_path,
        "extracted_text": extracted_text,
        "confidence": 0.95,
        "language": language
    }

def text_translator(text: str, source_lang: str = "auto", target_lang: str = "en") -> Dict[str, Any]:
    """文本翻译工具"""
    print(f"🌐 翻译文本: {text[:50]}..., {source_lang} -> {target_lang}")
    # 模拟翻译结果
    translated_text = "This is a test image with mixed content."
    return {
        "status": "success",
        "original_text": text,
        "translated_text": translated_text,
        "source_language": source_lang,
        "target_language": target_lang
    }

# MCP工具包装器
class MCPToolWrapper:
    """MCP工具包装器 - 实现标准化接口"""
    
    def __init__(self):
        self.tools = {
            "image_uploader": image_uploader,
            "image_scaler": image_scaler,
            "ocr_processor": ocr_processor,
            "text_translator": text_translator
        }
        
        # 参数映射规则 - 关键：实现无缝衔接
        self.parameter_mappings = {
            # 图像上传器输出 → 图像缩放器输入
            ("image_uploader", "image_scaler"): {
                "cloud_path": "image_path"  # 云端路径映射到本地路径
            },
            # 图像缩放器输出 → OCR处理器输入
            ("image_scaler", "ocr_processor"): {
                "scaled_path": "image_path"  # 缩放后路径映射到OCR输入
            },
            # OCR处理器输出 → 文本翻译器输入
            ("ocr_processor", "text_translator"): {
                "extracted_text": "text"  # 提取的文本映射到翻译输入
            }
        }
    
    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """获取工具的参数schema"""
        tool_func = self.tools[tool_name]
        import inspect
        sig = inspect.signature(tool_func)
        
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for name, param in sig.parameters.items():
            param_type = "string" if param.annotation == str else "object"
            schema["properties"][name] = {
                "type": param_type,
                "description": f"Parameter: {name}"
            }
            if param.default == inspect.Parameter.empty:
                schema["required"].append(name)
        
        return schema
    
    def adapt_parameters(self, source_tool: str, target_tool: str, 
                        source_output: Dict[str, Any], **additional_params) -> Dict[str, Any]:
        """参数适配 - 核心衔接机制"""
        mapping_key = (source_tool, target_tool)
        if mapping_key not in self.parameter_mappings:
            return additional_params
        
        mapping = self.parameter_mappings[mapping_key]
        adapted_params = {}
        
        # 应用映射规则
        for source_key, target_key in mapping.items():
            if source_key in source_output:
                adapted_params[target_key] = source_output[source_key]
        
        # 合并额外参数
        adapted_params.update(additional_params)
        return adapted_params
    
    async def execute_tool(self, tool_name: str, **params) -> Dict[str, Any]:
        """执行工具"""
        if tool_name not in self.tools:
            raise ValueError(f"工具不存在: {tool_name}")
        
        tool_func = self.tools[tool_name]
        result = tool_func(**params)
        return result

# Pipeline执行引擎
class MCPPipelineEngine:
    """MCP Pipeline执行引擎 - 实现无缝衔接"""
    
    def __init__(self):
        self.mcp_wrapper = MCPToolWrapper()
        self.execution_context = {}
    
    async def execute_pipeline(self, steps: List[Dict[str, Any]], 
                             initial_input: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行pipeline - 核心衔接逻辑"""
        print("🚀 开始执行MCP Pipeline")
        print("=" * 60)
        
        current_output = initial_input or {}
        pipeline_results = []
        
        for i, step in enumerate(steps):
            tool_name = step["tool"]
            additional_params = step.get("params", {})
            
            print(f"\n📋 步骤 {i+1}: {tool_name}")
            print(f"   输入参数: {additional_params}")
            
            try:
                # 关键：参数适配和衔接
                if i > 0:  # 不是第一步，需要适配参数
                    previous_tool = steps[i-1]["tool"]
                    adapted_params = self.mcp_wrapper.adapt_parameters(
                        previous_tool, tool_name, current_output, **additional_params
                    )
                    print(f"   🔗 参数适配: {previous_tool} -> {tool_name}")
                    print(f"   适配后参数: {adapted_params}")
                else:
                    adapted_params = additional_params
                
                # 执行工具
                result = await self.mcp_wrapper.execute_tool(tool_name, **adapted_params)
                current_output = result
                pipeline_results.append({
                    "step": i + 1,
                    "tool": tool_name,
                    "input": adapted_params,
                    "output": result,
                    "status": "success"
                })
                
                print(f"   ✅ 执行成功")
                print(f"   输出: {result}")
                
            except Exception as e:
                print(f"   ❌ 执行失败: {e}")
                pipeline_results.append({
                    "step": i + 1,
                    "tool": tool_name,
                    "error": str(e),
                    "status": "failed"
                })
                break
        
        return {
            "pipeline_results": pipeline_results,
            "final_output": current_output,
            "success": all(r["status"] == "success" for r in pipeline_results)
        }

# 示例：图像处理Pipeline
async def demo_image_processing_pipeline():
    """演示图像处理Pipeline的无缝衔接"""
    print("🎯 图像处理Pipeline演示")
    print("流程: 图像上传 → 图像缩放 → OCR识别 → 文本翻译")
    print("=" * 80)
    
    # 定义pipeline步骤
    pipeline_steps = [
        {
            "tool": "image_uploader",
            "params": {
                "image_path": "sample_image.jpg",
                "bucket_name": "image-processing"
            }
        },
        {
            "tool": "image_scaler",
            "params": {
                "scale_factor": 0.8
            }
        },
        {
            "tool": "ocr_processor",
            "params": {
                "language": "eng+chi_sim"
            }
        },
        {
            "tool": "text_translator",
            "params": {
                "target_lang": "en"
            }
        }
    ]
    
    # 执行pipeline
    engine = MCPPipelineEngine()
    result = await engine.execute_pipeline(pipeline_steps)
    
    print("\n" + "=" * 80)
    print("📊 Pipeline执行结果")
    print("=" * 80)
    
    if result["success"]:
        print("✅ Pipeline执行成功!")
        print(f"最终输出: {result['final_output']}")
    else:
        print("❌ Pipeline执行失败!")
        for step_result in result["pipeline_results"]:
            if step_result["status"] == "failed":
                print(f"失败步骤: {step_result['step']} - {step_result['tool']}")
                print(f"错误信息: {step_result['error']}")

# 示例：文档处理Pipeline
async def demo_document_processing_pipeline():
    """演示文档处理Pipeline的无缝衔接"""
    print("\n📄 文档处理Pipeline演示")
    print("流程: 文档上传 → 文本提取 → 文本格式化 → 内容分析")
    print("=" * 80)
    
    # 这里可以添加文档处理的工具和pipeline
    # 为了演示，我们复用图像处理的工具
    pipeline_steps = [
        {
            "tool": "image_uploader",
            "params": {
                "image_path": "document.pdf",
                "bucket_name": "documents"
            }
        },
        {
            "tool": "ocr_processor",
            "params": {
                "language": "eng"
            }
        },
        {
            "tool": "text_translator",
            "params": {
                "target_lang": "zh"
            }
        }
    ]
    
    engine = MCPPipelineEngine()
    result = await engine.execute_pipeline(pipeline_steps)
    
    print("\n" + "=" * 80)
    print("📊 文档处理Pipeline执行结果")
    print("=" * 80)
    
    if result["success"]:
        print("✅ 文档处理Pipeline执行成功!")
        print(f"最终输出: {result['final_output']}")

if __name__ == "__main__":
    asyncio.run(demo_image_processing_pipeline())
    asyncio.run(demo_document_processing_pipeline()) 