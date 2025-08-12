#!/usr/bin/env python3
"""
演示pipeline_id的唯一性
"""

import asyncio
import json
from core.requirement_parser import RequirementParser

async def demo_pipeline_id_uniqueness():
    """演示pipeline_id的唯一性"""
    print("🎯 Pipeline ID唯一性演示")
    print("=" * 60)
    
    parser = RequirementParser(use_llm=False)  # 使用规则解析进行演示
    
    # 多次解析相同的用户输入，验证pipeline_id的唯一性
    user_input = "请将图片旋转45度，然后放大3倍"
    
    print(f"用户输入: {user_input}")
    print("\n多次解析结果:")
    
    pipeline_ids = set()
    
    for i in range(5):
        result = parser.parse(user_input)
        pipeline_id = result["pipeline_id"]
        pipeline_ids.add(pipeline_id)
        
        print(f"第{i+1}次解析:")
        print(f"  Pipeline ID: {pipeline_id}")
        print(f"  组件数量: {len(result['components'])}")
        print()
    
    # 验证唯一性
    if len(pipeline_ids) == 5:
        print("✅ 验证通过: 所有pipeline_id都是唯一的!")
    else:
        print(f"❌ 验证失败: 发现重复的pipeline_id")
        print(f"   生成了 {len(pipeline_ids)} 个唯一ID，期望 5 个")
    
    print(f"\n生成的唯一ID列表:")
    for i, pid in enumerate(sorted(pipeline_ids), 1):
        print(f"  {i}. {pid}")

def demo_pipeline_structure():
    """演示新的pipeline结构"""
    print("\n📋 Pipeline结构演示")
    print("=" * 60)
    
    parser = RequirementParser(use_llm=False)
    
    test_cases = [
        "请将这段文字翻译成英文",
        "请将图片旋转90度，然后压缩",
        "请将文档转换为PDF，然后上传到云存储"
    ]
    
    for i, user_input in enumerate(test_cases, 1):
        print(f"\n📝 测试用例 {i}: {user_input}")
        
        result = parser.parse(user_input)
        
        print(f"Pipeline ID: {result['pipeline_id']}")
        print(f"组件数量: {len(result['components'])}")
        
        # 显示组件详情
        for j, component in enumerate(result['components'], 1):
            print(f"  组件 {j}: {component['id']} ({component['tool_type']})")
            if component.get('params'):
                print(f"    参数: {component['params']}")
            print(f"    输出: {component['output']['type']} - {component['output']['key']}")

if __name__ == "__main__":
    asyncio.run(demo_pipeline_id_uniqueness())
    demo_pipeline_structure() 