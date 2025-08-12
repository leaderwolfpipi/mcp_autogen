#!/usr/bin/env python3
"""
调试pipeline解析和执行
"""

import asyncio
import logging
from core.requirement_parser import RequirementParser
from core.placeholder_resolver import PlaceholderResolver

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def debug_pipeline():
    """调试pipeline解析"""
    print("🔍 调试Pipeline解析")
    print("=" * 60)
    
    # 初始化解析器
    parser = RequirementParser(use_llm=False)
    resolver = PlaceholderResolver()
    
    # 测试复合pipeline
    user_input = "请将图片旋转90度，然后放大2倍"
    print(f"用户输入: {user_input}")
    
    # 解析需求
    parsed = parser.parse(user_input)
    print(f"\n解析结果:")
    print(f"Pipeline ID: {parsed['pipeline_id']}")
    print(f"组件数量: {len(parsed['components'])}")
    
    for i, comp in enumerate(parsed['components']):
        print(f"\n组件 {i+1}:")
        print(f"  ID: {comp['id']}")
        print(f"  工具类型: {comp['tool_type']}")
        print(f"  参数: {comp['params']}")
        print(f"  输出: {comp['output']}")
    
    # 验证依赖关系
    print(f"\n🔗 验证依赖关系...")
    validation_errors = resolver.validate_pipeline_dependencies(parsed['components'])
    if validation_errors:
        print(f"验证错误: {validation_errors}")
    else:
        print("✅ 依赖关系验证通过")
    
    # 构建执行顺序
    print(f"\n📋 构建执行顺序...")
    execution_order = resolver.build_execution_order(parsed['components'])
    print(f"执行顺序: {execution_order}")
    
    # 检查占位符引用
    print(f"\n🔍 检查占位符引用...")
    for comp in parsed['components']:
        params = comp.get('params', {})
        placeholder_refs = resolver._extract_placeholder_references(params)
        if placeholder_refs:
            print(f"  {comp['id']} 的占位符引用: {placeholder_refs}")

if __name__ == "__main__":
    asyncio.run(debug_pipeline()) 