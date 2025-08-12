#!/usr/bin/env python3
"""
简化的通用性测试
"""

import logging
from core.placeholder_resolver import PlaceholderResolver

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_universal_solution():
    """测试通用性解决方案"""
    print("🧪 测试通用性依赖解析解决方案")
    print("=" * 50)
    
    # 初始化解析器
    resolver = PlaceholderResolver()
    
    # 测试用例：模拟LLM生成的不一致节点ID
    components = [
        {
            "id": "search_node",
            "tool_type": "smart_search",
            "params": {"query": "常州天目湖景区旅游信息", "max_results": 3},
            "output": {"type": "object", "fields": {"data.primary": "搜索结果列表"}}
        },
        {
            "id": "report_node",
            "tool_type": "enhanced_report_generator",
            "params": {"content": "$search_node.output.data.primary", "format": "markdown"},
            "output": {"type": "object", "fields": {"data.primary": "生成的报告内容"}}
        },
        {
            "id": "file_node",
            "tool_type": "file_writer",
            "params": {"file_path": "tianmu_lake_tour.md", "text": "$enhanced_report_node.output.data.primary"},
            "output": {"type": "object", "fields": {"data.primary": "文件写入结果"}}
        },
        {
            "id": "upload_node",
            "tool_type": "minio_uploader",
            "params": {"bucket_name": "kb-dev", "file_path": "tianmu_lake_tour.md"},
            "output": {"type": "object", "fields": {"data.primary": "上传后的URL"}}
        }
    ]
    
    print("组件列表:")
    for comp in components:
        print(f"  - {comp['id']} ({comp['tool_type']})")
    
    # 构建执行顺序
    print(f"\n🔍 构建执行顺序...")
    execution_order = resolver.build_execution_order(components)
    print(f"✅ 执行顺序: {' -> '.join(execution_order)}")
    
    # 验证执行顺序
    print(f"\n🔍 验证执行顺序...")
    validation_errors = resolver.validate_execution_order(components, execution_order)
    if validation_errors:
        print("❌ 验证失败:")
        for error in validation_errors:
            print(f"  - {error}")
    else:
        print("✅ 执行顺序验证通过")
    
    # 检查期望的执行顺序
    expected_order = ['search_node', 'report_node', 'file_node', 'upload_node']
    if execution_order == expected_order:
        print("🎉 执行顺序完全正确！")
    else:
        print(f"⚠️ 执行顺序与期望不同:")
        print(f"  期望: {' -> '.join(expected_order)}")
        print(f"  实际: {' -> '.join(execution_order)}")

if __name__ == "__main__":
    test_universal_solution() 