#!/usr/bin/env python3
"""
测试智能参数适配功能
"""

import logging
from core.placeholder_resolver import PlaceholderResolver

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_smart_parameter_adaptation():
    """测试智能参数适配功能"""
    print("🧪 测试智能参数适配功能")
    print("=" * 50)
    
    # 初始化解析器
    resolver = PlaceholderResolver()
    
    # 测试用例：模拟数据流语义不匹配问题
    test_cases = [
        {
            "name": "测试用例1: 文件内容 -> 文件路径适配",
            "params": {
                "file_path": "娄建学资料报告\n=======\n\n摘要:\n本报告主要涉及文化、教育、历史等领域的内容...",
                "bucket_name": "kb-dev"
            },
            "tool_type": "minio_uploader",
            "expected_adaptation": "file_path should be adapted to actual file path"
        },
        {
            "name": "测试用例2: 文件路径 -> 文件内容适配",
            "params": {
                "content": "tianmu_lake_tour.md",
                "format": "markdown"
            },
            "tool_type": "enhanced_report_generator",
            "expected_adaptation": "content should be adapted to actual file content"
        },
        {
            "name": "测试用例3: 正常参数（无需适配）",
            "params": {
                "query": "常州天目湖景区旅游信息",
                "max_results": 3
            },
            "tool_type": "smart_search",
            "expected_adaptation": "no adaptation needed"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 {test_case['name']}")
        print("-" * 40)
        
        params = test_case["params"]
        tool_type = test_case["tool_type"]
        
        print(f"原始参数: {params}")
        print(f"工具类型: {tool_type}")
        
        # 分析参数不匹配
        mismatches = resolver.parameter_adapter.analyze_parameter_mismatch(params, tool_type)
        
        if mismatches:
            print(f"发现 {len(mismatches)} 个参数不匹配:")
            for mismatch in mismatches:
                print(f"  - {mismatch['param_name']}: {mismatch['issue']}")
                print(f"    当前语义: {mismatch['param_semantic']}")
                print(f"    期望语义: {mismatch['expected_semantics']}")
        
        # 建议修复方案
        suggestions = resolver.parameter_adapter.suggest_parameter_fixes(mismatches, tool_type)
        
        if suggestions:
            print(f"建议的修复方案:")
            for suggestion in suggestions:
                print(f"  - {suggestion['param_name']}: {suggestion['description']}")
                print(f"    置信度: {suggestion['confidence']:.2f}")
        
        # 执行智能参数适配
        adapted_params = resolver.parameter_adapter.adapt_parameters(params, tool_type, {})
        
        print(f"适配后参数: {adapted_params}")
        
        # 检查是否有变化
        if adapted_params != params:
            print("✅ 参数适配成功")
        else:
            print("ℹ️ 无需参数适配")
        
        print()

def test_integration_with_placeholder_resolution():
    """测试与占位符解析的集成"""
    print("\n🔗 测试与占位符解析的集成")
    print("=" * 50)
    
    resolver = PlaceholderResolver()
    
    # 模拟节点输出
    node_outputs = {
        "report_node": resolver.create_node_output(
            "report_node",
            {"type": "object", "fields": {"data.primary": "报告内容"}},
            "娄建学资料报告\n=======\n\n摘要:\n本报告主要涉及文化、教育、历史等领域的内容..."
        )
    }
    
    # 测试参数（包含占位符和语义不匹配）
    params = {
        "file_path": "$report_node.output.data.primary",  # 占位符引用
        "bucket_name": "kb-dev"
    }
    
    print(f"原始参数: {params}")
    
    # 解析占位符并适配参数
    resolved_params = resolver.resolve_placeholders(params, node_outputs)
    
    print(f"解析和适配后参数: {resolved_params}")
    
    # 检查结果
    if "file_path" in resolved_params and resolved_params["file_path"] != params["file_path"]:
        print("✅ 占位符解析和参数适配集成成功")
    else:
        print("❌ 集成测试失败")

if __name__ == "__main__":
    test_smart_parameter_adaptation()
    test_integration_with_placeholder_resolution() 