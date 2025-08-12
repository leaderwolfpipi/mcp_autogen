# 自动导入所有工具函数
# 使用动态发现机制，自动扫描tools目录下的所有工具文件

import os
import importlib
import logging
import inspect
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def _is_tool_function(obj: Any) -> bool:
    """
    判断一个对象是否为工具函数
    
    Args:
        obj: 要检查的对象
        
    Returns:
        是否为工具函数
    """
    # 必须是可调用的
    if not callable(obj):
        return False
    
    # 不能是内置函数或类型
    if obj.__name__ in ['Any', 'Dict', 'List', 'Optional', 'Union', 'Tuple', 'Callable']:
        return False
    
    # 不能是类
    if inspect.isclass(obj):
        return False
    
    # 不能是模块
    if inspect.ismodule(obj):
        return False
    
    # 必须来自tools包
    if not hasattr(obj, '__module__') or not obj.__module__.startswith('tools.'):
        return False
    
    # 不能以下划线开头
    if obj.__name__.startswith('_'):
        return False
    
    # 排除一些常见的非工具函数
    exclude_names = {
        'logger', 'logging', 'os', 'sys', 're', 'json', 'time', 'datetime',
        'requests', 'urllib', 'pathlib', 'shutil', 'subprocess', 'threading',
        'asyncio', 'concurrent', 'functools', 'itertools', 'collections'
    }
    if obj.__name__ in exclude_names:
        return False
    
    return True

def _discover_tool_functions() -> Dict[str, Any]:
    """
    自动发现tools目录下的所有工具函数
    
    Returns:
        工具函数字典，键为函数名，值为函数对象
    """
    tools = {}
    tools_dir = os.path.dirname(__file__)
    
    # 获取tools目录下的所有.py文件
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            module_name = filename[:-3]  # 移除.py后缀
            
            # 跳过__init__.py和__pycache__
            if module_name in ['__init__', '__pycache__']:
                continue
                
            try:
                # 动态导入模块
                module = importlib.import_module(f'.{module_name}', package='tools')
                
                # 查找模块中的工具函数
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    # 检查是否为工具函数
                    if _is_tool_function(attr):
                        tools[attr_name] = attr
                        logger.debug(f"发现工具函数: {attr_name} (来自 {module_name})")
                        
            except ImportError as e:
                logger.warning(f"导入模块 {module_name} 失败: {e}")
                continue
            except Exception as e:
                logger.warning(f"处理模块 {module_name} 时出错: {e}")
                continue
    
    return tools

# 自动发现并导入所有工具函数
_discovered_tools = _discover_tool_functions()

# 只将发现的工具函数添加到当前模块的命名空间，不包括typing导入
for tool_name, tool_func in _discovered_tools.items():
    globals()[tool_name] = tool_func

# 构建__all__列表
__all__ = list(_discovered_tools.keys())

# 记录发现的工具数量
logger.info(f"自动发现并导入了 {len(_discovered_tools)} 个工具函数: {', '.join(__all__)}")

# 为了向后兼容，保留一些常用的工具函数别名
# 这些别名可以帮助IDE提供更好的代码补全
if 'smart_search' in _discovered_tools:
    smart_search = _discovered_tools['smart_search']

if 'text_formatter' in _discovered_tools:
    text_formatter = _discovered_tools['text_formatter']

if 'file_writer' in _discovered_tools:
    file_writer = _discovered_tools['file_writer']

if 'search_tool' in _discovered_tools:
    search_tool = _discovered_tools['search_tool']

if 'baidu_search_tool' in _discovered_tools:
    baidu_search_tool = _discovered_tools['baidu_search_tool']
