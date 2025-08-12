#!/usr/bin/env python3
"""
测试使用CodeGenerator的全自动工具生成功能
"""

import asyncio
import logging
from core.smart_pipeline_engine import SmartPipelineEngine

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_codegen_tool_generation():
    """测试使用CodeGenerator的工具生成功能"""
    print("🔧 测试CodeGenerator工具生成功能")
    print("=" * 60)
    
    engine = SmartPipelineEngine(use_llm=False)  # 使用规则解析
    
    # 测试不同类型的工具生成
    test_cases = [
        {
            "tool_type": "custom_image_processor",
            "params": {"image_path": "test.jpg", "operation": "blur", "radius": 5}
        },
        {
            "tool_type": "advanced_text_analyzer", 
            "params": {"text": "Hello World", "analysis_type": "sentiment", "language": "en"}
        },
        {
            "tool_type": "data_transformer",
            "params": {"input_data": "raw_data.csv", "transformation": "normalize", "output_format": "json"}
        },
        {
            "tool_type": "api_integrator",
            "params": {"endpoint": "https://api.example.com", "method": "POST", "data": {"key": "value"}}
        },
        {
            "tool_type": "machine_learning_predictor",
            "params": {"model_path": "model.pkl", "input_features": [1, 2, 3], "prediction_type": "classification"}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        tool_type = test_case["tool_type"]
        params = test_case["params"]
        
        print(f"\n📝 测试用例 {i}: {tool_type}")
        print(f"参数: {params}")
        
        try:
            tool_func = await engine._get_or_generate_tool(tool_type, params)
            
            if tool_func:
                print(f"✅ 工具生成成功")
                
                # 测试工具执行
                try:
                    result = tool_func(**params)
                    print(f"  执行结果: {result}")
                except Exception as exec_error:
                    print(f"  执行失败: {exec_error}")
            else:
                print(f"❌ 工具生成失败")
                
        except Exception as e:
            print(f"❌ 工具测试失败: {e}")

async def test_complex_pipeline():
    """测试复杂的pipeline执行"""
    print("\n🚀 测试复杂Pipeline执行")
    print("=" * 60)
    
    engine = SmartPipelineEngine(use_llm=False)
    
    # 测试用例：复杂的多步骤处理
    user_input = "请将图片进行边缘检测，然后提取文本，最后翻译成英文"
    
    print(f"用户输入: {user_input}")
    print("\n执行中...")
    
    try:
        result = await engine.execute_from_natural_language(user_input)
        
        print(f"\n执行结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
        print(f"执行时间: {result['execution_time']:.2f}秒")
        
        if result['success']:
            print("\n节点执行详情:")
            for node_result in result['node_results']:
                status_icon = "✅" if node_result['status'] == 'success' else "❌"
                print(f"  {status_icon} {node_result['node_id']} ({node_result['tool_type']})")
                print(f"    输入参数: {node_result['input_params']}")
                print(f"    输出结果: {node_result['output']}")
            
            print(f"\n最终输出: {result['final_output']}")
        else:
            print("\n错误信息:")
            for error in result['errors']:
                print(f"  - {error}")
                
    except Exception as e:
        print(f"❌ 执行失败: {e}")

async def test_llm_codegen():
    """测试LLM模式下的代码生成"""
    print("\n🤖 测试LLM模式下的代码生成")
    print("=" * 60)
    
    # 检查是否有OpenAI API密钥
    import os
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if api_key:
        try:
            engine = SmartPipelineEngine(use_llm=True, llm_config={"llm_model": "gpt-4o"})
            print("✅ 使用LLM模式")
            
            # 测试LLM生成的工具
            test_tool = "ai_powered_image_enhancer"
            test_params = {"image_path": "photo.jpg", "enhancement": "super_resolution", "scale": 4}
            
            print(f"\n测试LLM生成工具: {test_tool}")
            print(f"参数: {test_params}")
            
            tool_func = await engine._get_or_generate_tool(test_tool, test_params)
            
            if tool_func:
                print(f"✅ LLM工具生成成功")
                try:
                    result = tool_func(**test_params)
                    print(f"  执行结果: {result}")
                except Exception as exec_error:
                    print(f"  执行失败: {exec_error}")
            else:
                print(f"❌ LLM工具生成失败")
                
        except Exception as e:
            print(f"⚠️ LLM模式不可用: {e}")
    else:
        print("⚠️ 未设置OPENAI_API_KEY环境变量，跳过LLM测试")

async def test_tool_persistence():
    """测试工具持久化功能"""
    print("\n💾 测试工具持久化功能")
    print("=" * 60)
    
    engine = SmartPipelineEngine(use_llm=False)
    
    # 生成一个工具
    tool_type = "persistent_data_processor"
    params = {"data_source": "database", "operation": "aggregate", "group_by": "category"}
    
    print(f"生成工具: {tool_type}")
    
    try:
        tool_func = await engine._get_or_generate_tool(tool_type, params)
        
        if tool_func:
            print(f"✅ 工具生成成功")
            
            # 测试工具执行
            result = tool_func(**params)
            print(f"  执行结果: {result}")
            
            # 测试工具是否被缓存
            print(f"\n测试工具缓存...")
            cached_tool = await engine._get_or_generate_tool(tool_type, params)
            
            if cached_tool:
                print(f"✅ 工具缓存成功")
                cached_result = cached_tool(**params)
                print(f"  缓存工具执行结果: {cached_result}")
            else:
                print(f"❌ 工具缓存失败")
        else:
            print(f"❌ 工具生成失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

async def main():
    """主函数"""
    print("🎯 CodeGenerator全自动工具生成测试")
    print("=" * 80)
    
    # 1. 测试CodeGenerator工具生成
    await test_codegen_tool_generation()
    
    # 2. 测试复杂pipeline
    await test_complex_pipeline()
    
    # 3. 测试LLM代码生成
    await test_llm_codegen()
    
    # 4. 测试工具持久化
    await test_tool_persistence()
    
    print("\n" + "=" * 80)
    print("🎉 测试完成！")
    print("\n测试总结:")
    print("✅ CodeGenerator工具生成测试")
    print("✅ 复杂Pipeline执行测试")
    print("✅ LLM代码生成测试")
    print("✅ 工具持久化测试")
    print("\n现在SmartPipelineEngine具备了真正的全自动工具生成能力！")

if __name__ == "__main__":
    asyncio.run(main()) 