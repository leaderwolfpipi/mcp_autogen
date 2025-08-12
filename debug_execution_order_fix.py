#!/usr/bin/env python3
"""
调试pipeline执行顺序问题
"""

import re
from typing import Dict, List, Set, Any

def analyze_pipeline_dependencies():
    """分析pipeline依赖关系问题"""
    print("🔍 分析Pipeline执行顺序问题")
    print("=" * 60)
    
    # 从日志中提取的pipeline组件
    components = [
        {
            "id": "search_node",
            "tool_type": "smart_search",
            "params": {
                "query": "常州天目湖景区旅游信息",
                "max_results": 3
            }
        },
        {
            "id": "report_node",
            "tool_type": "enhanced_report_generator",
            "params": {
                "content": "$search_node.output.data.primary",
                "format": "markdown",
                "title": "常州天目湖景区旅游路线",
                "topic": "常州天目湖旅游",
                "style": "professional"
            }
        },
        {
            "id": "file_writer_node",
            "tool_type": "file_writer",
            "params": {
                "file_path": "tianmu_lake_tour_guide.md",
                "text": "$enhanced_report_node.output.data.primary"
            }
        },
        {
            "id": "upload_node",
            "tool_type": "minio_uploader",
            "params": {
                "bucket_name": "kb-dev",
                "file_path": "$file_writer_node.output.data.primary"
            }
        }
    ]
    
    print("📋 Pipeline组件分析:")
    for i, comp in enumerate(components):
        print(f"\n组件 {i+1}: {comp['id']}")
        print(f"  工具类型: {comp['tool_type']}")
        print(f"  参数: {comp['params']}")
    
    # 分析依赖关系
    print(f"\n🔗 依赖关系分析:")
    dependencies = {}
    node_ids = {comp["id"] for comp in components}
    
    for component in components:
        node_id = component["id"]
        dependencies[node_id] = set()
        
        # 检查该节点依赖的其他节点
        params = component.get("params", {})
        placeholder_refs = extract_placeholder_references(params)
        
        print(f"\n{node_id} 的占位符引用:")
        for ref in placeholder_refs:
            print(f"  - 引用节点: {ref['node_id']}")
            print(f"    输出键: {ref['output_key']}")
            if ref["node_id"] in node_ids:
                dependencies[node_id].add(ref["node_id"])
                print(f"    ✓ 依赖关系建立")
            else:
                print(f"    ✗ 引用的节点不存在")
    
    print(f"\n📊 依赖关系图:")
    for node_id, deps in dependencies.items():
        if deps:
            print(f"  {node_id} 依赖: {list(deps)}")
        else:
            print(f"  {node_id} 无依赖")
    
    # 构建执行顺序
    print(f"\n📋 构建执行顺序:")
    execution_order = build_execution_order(components)
    print(f"当前执行顺序: {' -> '.join(execution_order)}")
    
    # 分析问题
    print(f"\n🔍 问题分析:")
    print("从依赖关系图可以看出:")
    print("1. search_node: 无依赖")
    print("2. report_node: 依赖 search_node")
    print("3. file_writer_node: 依赖 enhanced_report_node (但应该是 report_node)")
    print("4. upload_node: 依赖 file_writer_node")
    
    print(f"\n❌ 发现的问题:")
    print("1. file_writer_node 引用了 'enhanced_report_node' 但实际节点ID是 'report_node'")
    print("2. 这导致 file_writer_node 被认为没有依赖，可以最先执行")
    
    # 修复建议
    print(f"\n🔧 修复方案:")
    print("1. 修正节点ID引用:")
    print("   - file_writer_node.params.text: '$report_node.output.data.primary'")
    
    print(f"\n✅ 正确的执行顺序应该是:")
    print("1. search_node (搜索信息)")
    print("2. report_node (生成报告)")
    print("3. file_writer_node (写入文件)")
    print("4. upload_node (上传文件)")

def extract_placeholder_references(params: Dict[str, Any]) -> List[Dict[str, str]]:
    """提取参数中的所有占位符引用"""
    references = []
    placeholder_pattern = r'\$([^.]+)\.output(?:\.([^.]+))?'
    
    def extract_from_value(value):
        if isinstance(value, str):
            matches = re.finditer(placeholder_pattern, value)
            for match in matches:
                references.append({
                    "node_id": match.group(1),
                    "output_key": match.group(2)
                })
        elif isinstance(value, dict):
            for v in value.values():
                extract_from_value(v)
        elif isinstance(value, list):
            for v in value:
                extract_from_value(v)
    
    extract_from_value(params)
    return references

def build_execution_order(components: List[Dict[str, Any]]) -> List[str]:
    """构建pipeline的执行顺序（拓扑排序）"""
    # 构建依赖图
    dependencies = {}
    node_ids = {comp["id"] for comp in components}
    
    for component in components:
        node_id = component["id"]
        dependencies[node_id] = set()
        
        # 检查该节点依赖的其他节点
        params = component.get("params", {})
        placeholder_refs = extract_placeholder_references(params)
        
        for ref in placeholder_refs:
            if ref["node_id"] in node_ids:
                dependencies[node_id].add(ref["node_id"])
    
    # 拓扑排序
    execution_order = []
    visited = set()
    temp_visited = set()
    
    def visit(node_id):
        if node_id in temp_visited:
            raise ValueError(f"检测到循环依赖: {node_id}")
        if node_id in visited:
            return
            
        temp_visited.add(node_id)
        
        for dep in dependencies.get(node_id, []):
            visit(dep)
            
        temp_visited.remove(node_id)
        visited.add(node_id)
        execution_order.append(node_id)
    
    for node_id in node_ids:
        if node_id not in visited:
            visit(node_id)
            
    return execution_order

if __name__ == "__main__":
    analyze_pipeline_dependencies() 