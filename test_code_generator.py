#!/usr/bin/env python3
"""
测试优化后的代码生成器
"""

import os
import sys
from core.code_generator import CodeGenerator

def test_code_generation():
    """测试代码生成功能"""
    print("🧪 测试代码生成器")
    print("=" * 50)
    
    # 初始化代码生成器
    codegen = CodeGenerator(use_llm=True, llm_model="gpt-4o")
    
    # 测试用例
    test_cases = [
        {
            "name": "文本翻译工具",
            "tool": "text_translator",
            "params": {
                "text": "Hello, how are you?",
                "source_lang": "en",
                "target_lang": "zh"
            }
        },
        {
            "name": "图片处理工具",
            "tool": "image_processor",
            "params": {
                "image": "test.jpg",
                "scale_factor": 2
            }
        },
        {
            "name": "文本提取工具",
            "tool": "text_extractor",
            "params": {
                "image": "document.png"
            }
        },
        {
            "name": "通用工具",
            "tool": "custom_processor",
            "params": {
                "input_data": "some data",
                "output_format": "json"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试用例 {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            # 生成代码
            code = codegen.generate(test_case)
            print("✅ 代码生成成功")
            print("📝 生成的代码:")
            print("```python")
            print(code)
            print("```")
            
            # 保存到文件
            file_path = codegen.generate_and_save(test_case)
            print(f"💾 代码已保存到: {file_path}")
            
        except Exception as e:
            print(f"❌ 代码生成失败: {e}")
        
        print()

def test_template_generation():
    """测试模板生成功能"""
    print("\n🔧 测试模板生成")
    print("=" * 50)
    
    # 初始化代码生成器（使用模板模式）
    codegen = CodeGenerator(use_llm=False)
    
    # 测试用例
    test_cases = [
        {
            "name": "文本翻译模板",
            "tool": "text_translator",
            "params": {
                "text": "Hello",
                "source_lang": "en",
                "target_lang": "zh"
            }
        },
        {
            "name": "图片处理模板",
            "tool": "image_resizer",
            "params": {
                "image": "test.jpg",
                "scale_factor": 2
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 模板测试 {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            # 生成代码
            code = codegen.generate(test_case)
            print("✅ 模板生成成功")
            print("📝 生成的模板代码:")
            print("```python")
            print(code)
            print("```")
            
        except Exception as e:
            print(f"❌ 模板生成失败: {e}")
        
        print()

def main():
    """主测试函数"""
    print("🎯 代码生成器测试")
    print("=" * 60)
    
    # 测试模板生成
    test_template_generation()
    
    # 测试LLM生成（需要API密钥）
    if os.environ.get("OPENAI_API_KEY"):
        test_code_generation()
    else:
        print("\n⚠️  跳过LLM测试：未设置OPENAI_API_KEY环境变量")
        print("   请设置: export OPENAI_API_KEY=your_api_key")
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    main() 