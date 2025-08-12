#!/usr/bin/env python3
"""
增强版工具自适应功能测试
演示统计信息、配置管理、导出导入、性能基准测试等功能
"""

import asyncio
import logging
import tempfile
import os
import json
import time
from PIL import Image

from core.tool_adapter import get_tool_adapter, MappingRule
from core.placeholder_resolver import NodeOutput

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_test_data():
    """创建测试数据"""
    return {
        "simple_list": ["item1", "item2", "item3"],
        "nested_dict": {
            "images": ["img1.png", "img2.png"],
            "metadata": {"count": 2, "format": "png"}
        },
        "mixed_data": {
            "data": [1, 2, 3, 4, 5],
            "info": {"type": "numbers", "count": 5}
        }
    }

async def test_statistics_and_monitoring():
    """测试统计信息和监控功能"""
    print("📊 测试统计信息和监控功能")
    print("=" * 60)
    
    adapter = get_tool_adapter()
    
    # 创建测试适配器
    test_adapter_name = "test_statistics_adapter"
    test_code = """
def test_statistics_adapter(source_data):
    import logging
    logger = logging.getLogger("test_statistics_adapter")
    
    if isinstance(source_data, dict):
        result = source_data.copy()
        if "data" in result:
            result["processed_data"] = [x * 2 for x in result["data"]]
        return result
    return source_data
"""
    
    # 模拟创建适配器
    adapter_def = adapter.adapters.get(test_adapter_name)
    if not adapter_def:
        adapter_def = type('AdapterDefinition', (), {
            'name': test_adapter_name,
            'adapter_type': type('AdapterType', (), {'value': 'test'})(),
            'source_tool': 'test_source',
            'target_tool': 'test_target',
            'mapping_rules': [],
            'code': test_code,
            'is_active': True,
            'created_at': time.time(),
            'metadata': {}
        })()
        adapter.adapters[test_adapter_name] = adapter_def
    
    # 编译适配器
    adapter_func = adapter._compile_adapter(test_adapter_name, test_code)
    if adapter_func:
        adapter.adapter_cache[test_adapter_name] = adapter_func
    
    # 执行多次适配操作
    test_data = {"data": [1, 2, 3], "info": "test"}
    
    print("🔄 执行多次适配操作...")
    for i in range(10):
        result = adapter.apply_adapter(test_adapter_name, test_data)
        time.sleep(0.01)  # 模拟处理时间
    
    # 获取统计信息
    stats = adapter.get_adapter_statistics()
    
    print(f"📈 统计信息:")
    print(f"   总适配次数: {stats['total_adaptations']}")
    print(f"   成功次数: {stats['successful_adaptations']}")
    print(f"   失败次数: {stats['failed_adaptations']}")
    print(f"   成功率: {stats['success_rate']:.2%}")
    print(f"   平均耗时: {stats['average_time']:.4f}秒")
    print(f"   缓存命中率: {stats['cache_hit_rate']:.2%}")
    print(f"   总适配器数: {stats['total_adapters']}")
    
    # 显示适配器使用情况
    if test_adapter_name in stats['adapter_usage']:
        usage = stats['adapter_usage'][test_adapter_name]
        print(f"   适配器 {test_adapter_name} 使用情况:")
        print(f"     成功: {usage['success']}")
        print(f"     失败: {usage['failed']}")
        print(f"     总耗时: {usage['total_time']:.4f}秒")

async def test_configuration_management():
    """测试配置管理功能"""
    print("\n⚙️ 测试配置管理功能")
    print("=" * 60)
    
    adapter = get_tool_adapter()
    
    # 显示当前配置
    print("📋 当前配置:")
    for key, value in adapter.config.config.items():
        print(f"   {key}: {value}")
    
    # 更新配置
    print("\n🔄 更新配置...")
    adapter.config.update_config(
        similarity_threshold=0.5,
        enable_caching=False,
        cache_size=500
    )
    
    print("📋 更新后的配置:")
    for key, value in adapter.config.config.items():
        print(f"   {key}: {value}")
    
    # 测试配置获取
    threshold = adapter.config.get_config("similarity_threshold")
    print(f"\n🔍 获取相似度阈值: {threshold}")
    
    # 创建临时配置文件
    temp_config_file = "temp_adapter_config.yaml"
    try:
        adapter.config.save_to_file(temp_config_file)
        print(f"✅ 配置已保存到: {temp_config_file}")
        
        # 重新加载配置
        adapter.config.load_from_file(temp_config_file)
        print("✅ 配置已重新加载")
        
    except Exception as e:
        print(f"❌ 配置文件操作失败: {e}")
    finally:
        if os.path.exists(temp_config_file):
            os.remove(temp_config_file)

async def test_export_import_functionality():
    """测试导出导入功能"""
    print("\n📤 测试导出导入功能")
    print("=" * 60)
    
    adapter = get_tool_adapter()
    
    # 创建一些测试适配器
    test_adapters = [
        {
            "name": "export_test_adapter_1",
            "code": """
def export_test_adapter_1(source_data):
    return {"processed": source_data, "timestamp": time.time()}
"""
        },
        {
            "name": "export_test_adapter_2", 
            "code": """
def export_test_adapter_2(source_data):
    if isinstance(source_data, list):
        return {"items": source_data, "count": len(source_data)}
    return source_data
"""
        }
    ]
    
    # 添加测试适配器
    for test_adapter in test_adapters:
        adapter_def = type('AdapterDefinition', (), {
            'name': test_adapter["name"],
            'adapter_type': type('AdapterType', (), {'value': 'export_test'})(),
            'source_tool': 'export_source',
            'target_tool': 'export_target',
            'mapping_rules': [MappingRule("*", "*", "identity", priority=1)],
            'code': test_adapter["code"],
            'is_active': True,
            'created_at': time.time(),
            'metadata': {"test": True}
        })()
        adapter.adapters[test_adapter["name"]] = adapter_def
    
    # 导出适配器
    export_file = "test_adapters_export.json"
    try:
        adapter.export_adapters(export_file)
        print(f"✅ 适配器已导出到: {export_file}")
        
        # 检查导出文件
        with open(export_file, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        print(f"📊 导出统计:")
        print(f"   适配器数量: {len(export_data['adapters'])}")
        print(f"   配置项数量: {len(export_data['config'])}")
        print(f"   统计信息: {len(export_data['statistics'])} 项")
        
        # 清空当前适配器
        original_count = len(adapter.adapters)
        adapter.adapters.clear()
        adapter.adapter_cache.clear()
        print(f"🗑️ 已清空 {original_count} 个适配器")
        
        # 导入适配器
        adapter.import_adapters(export_file)
        print(f"✅ 已导入 {len(adapter.adapters)} 个适配器")
        
        # 验证导入的适配器
        for name in export_data['adapters']:
            adapter_info = adapter.get_adapter_info(name)
            if adapter_info:
                print(f"   ✅ {name}: {adapter_info['adapter_type']}")
            else:
                print(f"   ❌ {name}: 导入失败")
        
    except Exception as e:
        print(f"❌ 导出导入操作失败: {e}")
    finally:
        if os.path.exists(export_file):
            os.remove(export_file)

async def test_adapter_management():
    """测试适配器管理功能"""
    print("\n🔧 测试适配器管理功能")
    print("=" * 60)
    
    adapter = get_tool_adapter()
    
    # 创建测试适配器
    test_adapter_name = "management_test_adapter"
    test_code = """
def management_test_adapter(source_data):
    return {"managed": source_data, "status": "active"}
"""
    
    adapter_def = type('AdapterDefinition', (), {
        'name': test_adapter_name,
        'adapter_type': type('AdapterType', (), {'value': 'management_test'})(),
        'source_tool': 'management_source',
        'target_tool': 'management_target',
        'mapping_rules': [],
        'code': test_code,
        'is_active': True,
        'created_at': time.time(),
        'metadata': {}
    })()
    adapter.adapters[test_adapter_name] = adapter_def
    
    # 编译适配器
    adapter_func = adapter._compile_adapter(test_adapter_name, test_code)
    if adapter_func:
        adapter.adapter_cache[test_adapter_name] = adapter_func
    
    # 获取适配器信息
    adapter_info = adapter.get_adapter_info(test_adapter_name)
    print(f"📋 适配器信息:")
    print(f"   名称: {adapter_info['name']}")
    print(f"   类型: {adapter_info['adapter_type']}")
    print(f"   状态: {'启用' if adapter_info['is_active'] else '禁用'}")
    print(f"   使用次数: {adapter_info['usage_count']}")
    print(f"   成功率: {adapter_info['success_rate']:.2%}")
    
    # 验证适配器
    validation = adapter.validate_adapter(test_adapter_name)
    print(f"\n🔍 验证结果:")
    print(f"   有效: {'✅' if validation['valid'] else '❌'}")
    if validation['warnings']:
        print(f"   警告: {validation['warnings']}")
    if validation['errors']:
        print(f"   错误: {validation['errors']}")
    
    # 禁用适配器
    adapter.disable_adapter(test_adapter_name)
    adapter_info = adapter.get_adapter_info(test_adapter_name)
    print(f"🔒 禁用后状态: {'启用' if adapter_info['is_active'] else '禁用'}")
    
    # 启用适配器
    adapter.enable_adapter(test_adapter_name)
    adapter_info = adapter.get_adapter_info(test_adapter_name)
    print(f"🔓 启用后状态: {'启用' if adapter_info['is_active'] else '禁用'}")
    
    # 列出适配器
    adapters = adapter.list_adapters()
    print(f"\n📝 所有适配器 ({len(adapters)} 个):")
    for adapter_info in adapters:
        print(f"   - {adapter_info['name']} ({adapter_info['adapter_type']})")
    
    # 删除适配器
    adapter.delete_adapter(test_adapter_name)
    print(f"🗑️ 已删除适配器: {test_adapter_name}")

async def test_performance_benchmarking():
    """测试性能基准测试功能"""
    print("\n⚡ 测试性能基准测试功能")
    print("=" * 60)
    
    adapter = get_tool_adapter()
    
    # 创建性能测试适配器
    benchmark_adapter_name = "benchmark_test_adapter"
    benchmark_code = """
def benchmark_test_adapter(source_data):
    import time
    # 模拟一些处理时间
    time.sleep(0.001)
    
    if isinstance(source_data, dict):
        result = {}
        for key, value in source_data.items():
            if isinstance(value, list):
                result[key] = [x * 2 for x in value]
            else:
                result[key] = value
        return result
    return source_data
"""
    
    adapter_def = type('AdapterDefinition', (), {
        'name': benchmark_adapter_name,
        'adapter_type': type('AdapterType', (), {'value': 'benchmark_test'})(),
        'source_tool': 'benchmark_source',
        'target_tool': 'benchmark_target',
        'mapping_rules': [],
        'code': benchmark_code,
        'is_active': True,
        'created_at': time.time(),
        'metadata': {}
    })()
    adapter.adapters[benchmark_adapter_name] = adapter_def
    
    # 编译适配器
    adapter_func = adapter._compile_adapter(benchmark_adapter_name, benchmark_code)
    if adapter_func:
        adapter.adapter_cache[benchmark_adapter_name] = adapter_func
    
    # 准备测试数据
    test_data = {
        "numbers": [1, 2, 3, 4, 5],
        "strings": ["a", "b", "c"],
        "nested": {"x": [10, 20], "y": [30, 40]}
    }
    
    # 执行基准测试
    print("🔄 执行性能基准测试...")
    benchmark_result = adapter.benchmark_adapter(benchmark_adapter_name, test_data, iterations=50)
    
    if "error" not in benchmark_result:
        print(f"📊 基准测试结果:")
        print(f"   迭代次数: {benchmark_result['iterations']}")
        print(f"   总耗时: {benchmark_result['total_time']:.4f}秒")
        print(f"   平均耗时: {benchmark_result['average_time']:.6f}秒")
        print(f"   最小耗时: {benchmark_result['min_time']:.6f}秒")
        print(f"   最大耗时: {benchmark_result['max_time']:.6f}秒")
        print(f"   标准差: {benchmark_result['std_deviation']:.6f}秒")
        
        # 计算吞吐量
        throughput = benchmark_result['iterations'] / benchmark_result['total_time']
        print(f"   吞吐量: {throughput:.2f} 操作/秒")
    else:
        print(f"❌ 基准测试失败: {benchmark_result['error']}")

async def test_cache_management():
    """测试缓存管理功能"""
    print("\n💾 测试缓存管理功能")
    print("=" * 60)
    
    adapter = get_tool_adapter()
    
    # 启用缓存
    adapter.config.update_config(enable_caching=True, cache_size=10)
    
    # 创建缓存测试适配器
    cache_adapter_name = "cache_test_adapter"
    cache_code = """
def cache_test_adapter(source_data):
    import time
    time.sleep(0.01)  # 模拟处理时间
    return {"cached": source_data, "processed": True}
"""
    
    adapter_def = type('AdapterDefinition', (), {
        'name': cache_adapter_name,
        'adapter_type': type('AdapterType', (), {'value': 'cache_test'})(),
        'source_tool': 'cache_source',
        'target_tool': 'cache_target',
        'mapping_rules': [],
        'code': cache_code,
        'is_active': True,
        'created_at': time.time(),
        'metadata': {}
    })()
    adapter.adapters[cache_adapter_name] = adapter_def
    
    # 编译适配器
    adapter_func = adapter._compile_adapter(cache_adapter_name, cache_code)
    if adapter_func:
        adapter.adapter_cache[cache_adapter_name] = adapter_func
    
    # 测试缓存效果
    test_data = {"test": "cache_data"}
    
    print("🔄 测试缓存效果...")
    
    # 第一次调用（缓存未命中）
    start_time = time.time()
    result1 = adapter.apply_adapter(cache_adapter_name, test_data)
    first_call_time = time.time() - start_time
    
    # 第二次调用（缓存命中）
    start_time = time.time()
    result2 = adapter.apply_adapter(cache_adapter_name, test_data)
    second_call_time = time.time() - start_time
    
    print(f"📊 缓存测试结果:")
    print(f"   第一次调用耗时: {first_call_time:.4f}秒")
    print(f"   第二次调用耗时: {second_call_time:.4f}秒")
    print(f"   加速比: {first_call_time / second_call_time:.2f}x")
    
    # 获取缓存统计
    stats = adapter.get_adapter_statistics()
    print(f"   缓存命中: {stats['cache_hits']}")
    print(f"   缓存未命中: {stats['cache_misses']}")
    print(f"   缓存命中率: {stats['cache_hit_rate']:.2%}")
    
    # 清空缓存
    adapter.clear_cache()
    print("🗑️ 缓存已清空")
    
    # 验证缓存已清空
    stats_after_clear = adapter.get_adapter_statistics()
    print(f"   清空后缓存大小: {len(adapter._cache)}")

async def main():
    """主测试函数"""
    print("🚀 增强版工具自适应系统测试")
    print("=" * 80)
    
    # 运行所有测试
    await test_statistics_and_monitoring()
    await test_configuration_management()
    await test_export_import_functionality()
    await test_adapter_management()
    await test_performance_benchmarking()
    await test_cache_management()
    
    print("\n🎯 所有测试完成！")
    
    # 显示最终统计
    adapter = get_tool_adapter()
    final_stats = adapter.get_adapter_statistics()
    print(f"\n📈 最终统计:")
    print(f"   总适配次数: {final_stats['total_adaptations']}")
    print(f"   成功率: {final_stats['success_rate']:.2%}")
    print(f"   平均耗时: {final_stats['average_time']:.4f}秒")
    print(f"   缓存命中率: {final_stats['cache_hit_rate']:.2%}")

if __name__ == "__main__":
    asyncio.run(main()) 