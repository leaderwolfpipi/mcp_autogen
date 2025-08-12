#!/usr/bin/env python3
"""
测试工具自适应功能
演示如何自动解决pipeline输出结构与工具输入期望不匹配的问题
"""

import asyncio
import logging
import tempfile
import os
from PIL import Image
import numpy as np

from core.smart_pipeline_engine import SmartPipelineEngine
from core.tool_adapter import get_tool_adapter, ToolAdapter
from core.placeholder_resolver import NodeOutput

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_test_image():
    """创建测试图片"""
    # 创建一个简单的测试图片
    img = Image.new('RGB', (100, 100), color='red')
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "test_image.png")
    img.save(temp_path)
    return temp_path

def create_test_pipeline():
    """创建测试pipeline配置"""
    return {
        "components": [
            {
                "id": "load_images_node",
                "tool_type": "image_loader",
                "params": {
                    "directory": "./test_images"
                },
                "output": {
                    "type": "list",
                    "key": "data",
                    "description": "加载的图片列表"
                }
            },
            {
                "id": "rotate_images_node",
                "tool_type": "image_rotator",
                "params": {
                    "image_path": "$load_images_node.output.images",
                    "angle": 45
                },
                "output": {
                    "type": "dict",
                    "key": "result",
                    "description": "旋转后的图片信息"
                }
            }
        ]
    }

async def test_tool_adaptation():
    """测试工具自适应功能"""
    print("🧪 测试工具自适应功能")
    print("=" * 60)
    
    # 1. 初始化工具适配器
    adapter = get_tool_adapter()
    print("✅ 工具适配器初始化成功")
    
    # 2. 创建测试数据
    print("\n📁 创建测试数据...")
    
    # 创建测试目录和图片
    test_dir = "./test_images"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建几个测试图片
    for i in range(3):
        img = Image.new('RGB', (100, 100), color=f'rgb({i*100}, {i*50}, {i*25})')
        img_path = os.path.join(test_dir, f"test_image_{i}.png")
        img.save(img_path)
        print(f"   创建测试图片: {img_path}")
    
    # 3. 模拟load_images_node的输出
    print("\n🔄 模拟load_images_node输出...")
    
    # 模拟image_loader的输出（没有images键）
    load_result = [
        Image.open(os.path.join(test_dir, f"test_image_{i}.png"))
        for i in range(3)
    ]
    
    source_output = NodeOutput(
        node_id="load_images_node",
        output_type="list",
        output_key="data",
        value=load_result,
        description="加载的图片列表"
    )
    
    print(f"   输出类型: {type(load_result)}")
    print(f"   输出长度: {len(load_result)}")
    print(f"   输出键: data (没有images键)")
    
    # 4. 模拟rotate_images_node的期望输入
    print("\n🎯 模拟rotate_images_node期望输入...")
    target_expectation = {
        "image_path": "$load_images_node.output.images",  # 期望有images键
        "angle": 45
    }
    
    # 5. 分析兼容性
    print("\n🔍 分析兼容性...")
    analysis = adapter.analyze_compatibility(source_output, target_expectation)
    
    print(f"   兼容性: {'✓' if analysis['is_compatible'] else '✗'}")
    print(f"   缺失键: {analysis['missing_keys']}")
    print(f"   类型不匹配: {analysis['type_mismatches']}")
    print(f"   置信度: {analysis['confidence']:.2f}")
    
    # 6. 创建适配器
    if not analysis['is_compatible']:
        print("\n🔧 创建适配器...")
        adapter_def = adapter.create_adapter(
            "load_images_node", 
            "image_rotator", 
            source_output, 
            target_expectation
        )
        
        if adapter_def:
            print(f"   ✅ 适配器创建成功: {adapter_def.name}")
            print(f"   适配器类型: {adapter_def.adapter_type.value}")
            print(f"   映射规则: {adapter_def.mapping_rules}")
        else:
            print("   ❌ 适配器创建失败")
    
    # 7. 测试自动适配
    print("\n🔄 测试自动适配...")
    adapted_output = adapter.auto_adapt_output(source_output, target_expectation)
    
    print(f"   适配前类型: {type(source_output.value)}")
    print(f"   适配后类型: {type(adapted_output)}")
    
    if isinstance(adapted_output, dict):
        print(f"   适配后键: {list(adapted_output.keys())}")
        if "images" in adapted_output:
            print(f"   ✅ 成功找到images键，包含 {len(adapted_output['images'])} 个图片")
    
    # 8. 测试完整的pipeline执行
    print("\n🚀 测试完整pipeline执行...")
    
    # 初始化智能pipeline引擎
    engine = SmartPipelineEngine(use_llm=False)
    
    # 创建测试pipeline
    pipeline_config = create_test_pipeline()
    
    # 模拟执行第一个节点
    print("   执行load_images_node...")
    from tools.image_loader import image_loader
    
    try:
        load_result = image_loader(test_dir)
        load_node_output = NodeOutput(
            node_id="load_images_node",
            output_type="list",
            output_key="data",
            value=load_result,
            description="加载的图片列表"
        )
        
        print(f"   ✅ 加载成功，获得 {len(load_result)} 个图片")
        
        # 模拟执行第二个节点（这里会触发适配）
        print("   执行rotate_images_node...")
        
        # 解析参数
        from core.placeholder_resolver import PlaceholderResolver
        resolver = PlaceholderResolver()
        
        node_outputs = {"load_images_node": load_node_output}
        params = pipeline_config["components"][1]["params"]
        
        print(f"   原始参数: {params}")
        resolved_params = resolver.resolve_placeholders(params, node_outputs)
        print(f"   解析后参数: {resolved_params}")
        
        # 检查是否成功适配
        if "image_path" in resolved_params and resolved_params["image_path"] != "$load_images_node.output.images":
            print("   ✅ 参数自动适配成功")
        else:
            print("   ❌ 参数自动适配失败")
            
    except Exception as e:
        print(f"   ❌ 执行失败: {e}")
    
    # 9. 清理测试文件
    print("\n🧹 清理测试文件...")
    import shutil
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print("   ✅ 测试目录已清理")
    
    print("\n🎯 测试完成")

async def test_advanced_adaptation():
    """测试高级适配功能"""
    print("\n🧪 测试高级适配功能")
    print("=" * 60)
    
    adapter = get_tool_adapter()
    
    # 测试不同的数据格式适配
    test_cases = [
        {
            "name": "列表到字典适配",
            "source_data": ["image1.png", "image2.png"],
            "target_expectation": {"images": "$source.output.images"},
            "expected_keys": ["images"]
        },
        {
            "name": "字典键重命名",
            "source_data": {"data": ["image1.png"], "count": 1},
            "target_expectation": {"images": "$source.output.images"},
            "expected_keys": ["images"]
        },
        {
            "name": "类型转换",
            "source_data": {"angle": "45"},
            "target_expectation": {"angle": "$source.output.angle"},
            "expected_keys": ["angle"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        
        source_output = NodeOutput(
            node_id=f"test_node_{i}",
            output_type="dict",
            output_key="data",
            value=test_case["source_data"],
            description=f"测试数据 {i}"
        )
        
        # 分析兼容性
        analysis = adapter.analyze_compatibility(source_output, test_case["target_expectation"])
        
        print(f"   兼容性: {'✓' if analysis['is_compatible'] else '✗'}")
        print(f"   缺失键: {analysis['missing_keys']}")
        print(f"   类型不匹配: {analysis['type_mismatches']}")
        
        # 自动适配
        adapted_output = adapter.auto_adapt_output(source_output, test_case["target_expectation"])
        
        if isinstance(adapted_output, dict):
            found_keys = [key for key in test_case["expected_keys"] if key in adapted_output]
            print(f"   适配结果: {'✓' if found_keys else '✗'} 找到键: {found_keys}")
        else:
            print(f"   适配结果: {'✓' if adapted_output == test_case['source_data'] else '✗'}")

if __name__ == "__main__":
    asyncio.run(test_tool_adaptation())
    asyncio.run(test_advanced_adaptation()) 