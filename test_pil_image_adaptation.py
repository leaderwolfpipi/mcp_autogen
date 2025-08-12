#!/usr/bin/env python3
"""
测试PIL Image适配功能
专门测试image_loader到image_rotator的适配
"""

import asyncio
import logging
import tempfile
import os
from PIL import Image

from core.tool_adapter import get_tool_adapter
from core.placeholder_resolver import NodeOutput

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_test_images():
    """创建测试图片"""
    test_dir = "./test_pil_images"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建几个测试图片
    images = []
    for i in range(2):
        img = Image.new('RGB', (100, 100), color=f'rgb({i*100}, {i*50}, {i*25})')
        img_path = os.path.join(test_dir, f"test_image_{i}.png")
        img.save(img_path)
        images.append(img)
        print(f"创建测试图片: {img_path}")
    
    return images

async def test_pil_image_adaptation():
    """测试PIL Image适配功能"""
    print("🧪 测试PIL Image适配功能")
    print("=" * 60)
    
    adapter = get_tool_adapter()
    
    # 创建测试图片
    print("📁 创建测试图片...")
    test_images = create_test_images()
    
    # 模拟image_loader的输出（PIL Image列表）
    print("\n🔄 模拟image_loader输出...")
    source_output = NodeOutput(
        node_id="load_images_node",
        output_type="list",
        output_key="data",
        value=test_images,  # PIL Image列表
        description="加载的图片列表"
    )
    
    print(f"   输出类型: {type(test_images)}")
    print(f"   输出长度: {len(test_images)}")
    print(f"   元素类型: {type(test_images[0])}")
    print(f"   是否为PIL Image: {hasattr(test_images[0], 'save')}")
    
    # 模拟image_rotator的期望输入
    print("\n🎯 模拟image_rotator期望输入...")
    target_expectation = {
        "image_path": "$load_images_node.output.images",
        "angle": 45
    }
    
    # 分析兼容性
    print("\n🔍 分析兼容性...")
    analysis = adapter.analyze_compatibility(source_output, target_expectation)
    
    print(f"   兼容性: {'✓' if analysis['is_compatible'] else '✗'}")
    print(f"   缺失键: {analysis['missing_keys']}")
    print(f"   类型不匹配: {analysis['type_mismatches']}")
    print(f"   置信度: {analysis['confidence']:.2f}")
    
    # 显示结构分析结果
    if analysis['source_structure']:
        print(f"\n📊 源结构分析:")
        source_structure = analysis['source_structure']
        print(f"   类型: {source_structure.get('type')}")
        print(f"   长度: {source_structure.get('length')}")
        print(f"   元素类型: {source_structure.get('element_type')}")
        if 'element_analysis' in source_structure:
            element_info = source_structure['element_analysis']
            print(f"   元素信息: {element_info.get('type')}")
            if 'image_info' in element_info:
                print(f"   图片信息: {element_info['image_info']}")
    
    # 测试智能映射
    print("\n🔄 测试智能映射...")
    adapted_output = adapter.auto_adapt_output(source_output, target_expectation)
    
    print(f"   适配前类型: {type(source_output.value)}")
    print(f"   适配后类型: {type(adapted_output)}")
    
    if isinstance(adapted_output, dict):
        print(f"   适配后键: {list(adapted_output.keys())}")
        if "image_path" in adapted_output:
            image_path = adapted_output["image_path"]
            print(f"   ✅ 成功找到image_path: {type(image_path)}")
            if isinstance(image_path, list):
                print(f"      路径数量: {len(image_path)}")
                for i, path in enumerate(image_path):
                    print(f"      路径 {i}: {path}")
                    if os.path.exists(path):
                        print(f"        ✅ 文件存在")
                    else:
                        print(f"        ❌ 文件不存在")
            else:
                print(f"      路径: {image_path}")
                if os.path.exists(image_path):
                    print(f"      ✅ 文件存在")
                else:
                    print(f"      ❌ 文件不存在")
    
    # 测试适配器创建
    print("\n🔧 测试适配器创建...")
    adapter_def = adapter.create_adapter(
        "load_images_node", 
        "image_rotator", 
        source_output, 
        target_expectation
    )
    
    if adapter_def:
        print(f"   ✅ 适配器创建成功: {adapter_def.name}")
        print(f"   适配器类型: {adapter_def.adapter_type.value}")
        print(f"   映射规则数量: {len(adapter_def.mapping_rules)}")
        
        # 测试适配器应用
        print("\n⚡ 测试适配器应用...")
        result = adapter.apply_adapter(adapter_def.name, source_output.value)
        
        print(f"   应用结果类型: {type(result)}")
        if isinstance(result, dict):
            print(f"   结果键: {list(result.keys())}")
            if "image_path" in result:
                image_path = result["image_path"]
                print(f"   image_path: {type(image_path)}")
                if isinstance(image_path, list):
                    print(f"   路径数量: {len(image_path)}")
                else:
                    print(f"   路径: {image_path}")
    else:
        print("   ❌ 适配器创建失败")
    
    # 清理测试文件
    print("\n🧹 清理测试文件...")
    import shutil
    if os.path.exists("./test_pil_images"):
        shutil.rmtree("./test_pil_images")
        print("   ✅ 测试目录已清理")
    
    print("\n🎯 测试完成")

async def test_real_pipeline_simulation():
    """测试真实pipeline场景"""
    print("\n🚀 测试真实pipeline场景")
    print("=" * 60)
    
    adapter = get_tool_adapter()
    
    # 模拟真实的pipeline执行
    print("📋 模拟pipeline执行...")
    
    # 1. 模拟image_loader执行结果
    from tools.image_loader import image_loader
    
    try:
        # 使用现有的测试图片目录
        test_dir = "tests/images"
        if os.path.exists(test_dir):
            load_result = image_loader(test_dir)
            
            print(f"✅ image_loader执行成功")
            print(f"   加载图片数量: {len(load_result)}")
            print(f"   图片类型: {type(load_result[0])}")
            
            # 2. 创建NodeOutput
            load_node_output = NodeOutput(
                node_id="load_images_node",
                output_type="list",
                output_key="data",
                value=load_result,
                description="加载的图片列表"
            )
            
            # 3. 模拟image_rotator的参数解析
            from core.placeholder_resolver import PlaceholderResolver
            resolver = PlaceholderResolver()
            
            node_outputs = {"load_images_node": load_node_output}
            params = {
                "image_path": "$load_images_node.output.images",
                "angle": 45
            }
            
            print(f"\n🔍 解析参数: {params}")
            resolved_params = resolver.resolve_placeholders(params, node_outputs)
            print(f"📝 解析后参数: {resolved_params}")
            
            # 4. 检查是否成功适配
            if "image_path" in resolved_params:
                image_path = resolved_params["image_path"]
                if isinstance(image_path, str) and image_path != "$load_images_node.output.images":
                    print("✅ 参数自动适配成功")
                    print(f"   适配后image_path: {image_path}")
                else:
                    print("❌ 参数自动适配失败")
                    print(f"   原始image_path: {image_path}")
            
        else:
            print(f"❌ 测试目录不存在: {test_dir}")
            
    except Exception as e:
        print(f"❌ 执行失败: {e}")

async def main():
    """主测试函数"""
    print("🚀 PIL Image适配功能测试")
    print("=" * 80)
    
    await test_pil_image_adaptation()
    await test_real_pipeline_simulation()
    
    print("\n🎯 所有测试完成！")

if __name__ == "__main__":
    asyncio.run(main()) 