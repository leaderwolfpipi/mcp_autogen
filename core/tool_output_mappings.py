#!/usr/bin/env python3
"""
工具输出格式映射配置
用于管理工具的新旧输出格式兼容性
"""

# 搜索类工具的字段映射
SEARCH_TOOL_MAPPINGS = {
    "search_tool": {
        "legacy_fields": ["results"],
        "standard_fields": ["data.primary"],
        "field_mappings": {
            "results": "data.primary",
            "source": "data.secondary.source",
            "message": "message"
        }
    },
    "smart_search": {
        "legacy_fields": ["results"],
        "standard_fields": ["data.primary"],
        "field_mappings": {
            "results": "data.primary",
            "content_stats": "data.secondary.content_stats",
            "message": "message"
        }
    },
    "google_search_tool": {
        "legacy_fields": ["results"],
        "standard_fields": ["data.primary"],
        "field_mappings": {
            "results": "data.primary",
            "source": "data.secondary.source",
            "message": "message"
        }
    },
    "baidu_search_tool": {
        "legacy_fields": ["results"],
        "standard_fields": ["data.primary"],
        "field_mappings": {
            "results": "data.primary",
            "source": "data.secondary.source",
            "message": "message"
        }
    },
    "baidu_search_engine_tool": {
        "legacy_fields": ["results"],
        "standard_fields": ["data.primary"],
        "field_mappings": {
            "results": "data.primary",
            "source": "data.secondary.source",
            "message": "message"
        }
    }
}

# 图像处理类工具的字段映射
IMAGE_TOOL_MAPPINGS = {
    "image_rotator": {
        "legacy_fields": ["rotated_images", "temp_paths"],
        "standard_fields": ["data.primary", "paths"],
        "field_mappings": {
            "rotated_images": "data.primary",
            "temp_paths": "paths",
            "angle": "data.secondary.angle",
            "message": "message"
        }
    },
    "image_rotator_directory": {
        "legacy_fields": ["rotated_images", "temp_paths"],
        "standard_fields": ["data.primary", "paths"],
        "field_mappings": {
            "rotated_images": "data.primary",
            "temp_paths": "paths",
            "angle": "data.secondary.angle",
            "message": "message"
        }
    },
    "image_scaler": {
        "legacy_fields": ["scaled_images", "temp_paths"],
        "standard_fields": ["data.primary", "paths"],
        "field_mappings": {
            "scaled_images": "data.primary",
            "temp_paths": "paths",
            "scale_factor": "data.secondary.scale_factor",
            "message": "message"
        }
    },
    "image_scaler_directory": {
        "legacy_fields": ["scaled_images", "temp_paths"],
        "standard_fields": ["data.primary", "paths"],
        "field_mappings": {
            "scaled_images": "data.primary",
            "temp_paths": "paths",
            "scale_factor": "data.secondary.scale_factor",
            "message": "message"
        }
    }
}

# 文件上传类工具的字段映射
UPLOAD_TOOL_MAPPINGS = {
    "minio_uploader": {
        "legacy_fields": ["upload_url", "file_path"],
        "standard_fields": ["data.primary", "paths"],
        "field_mappings": {
            "upload_url": "data.primary",
            "file_path": "paths",
            "bucket_name": "data.secondary.bucket_name",
            "message": "message"
        }
    }
}

# 合并所有映射
ALL_TOOL_MAPPINGS = {
    **SEARCH_TOOL_MAPPINGS,
    **IMAGE_TOOL_MAPPINGS,
    **UPLOAD_TOOL_MAPPINGS
}

def get_tool_mapping(tool_name: str) -> dict:
    """
    获取工具的字段映射配置
    
    Args:
        tool_name: 工具名称
        
    Returns:
        工具的字段映射配置字典
    """
    return ALL_TOOL_MAPPINGS.get(tool_name, {})

def get_legacy_fields(tool_name: str) -> list:
    """
    获取工具的旧格式字段列表
    
    Args:
        tool_name: 工具名称
        
    Returns:
        旧格式字段列表
    """
    mapping = get_tool_mapping(tool_name)
    return mapping.get("legacy_fields", [])

def get_standard_fields(tool_name: str) -> list:
    """
    获取工具的标准格式字段列表
    
    Args:
        tool_name: 工具名称
        
    Returns:
        标准格式字段列表
    """
    mapping = get_tool_mapping(tool_name)
    return mapping.get("standard_fields", [])

def get_field_mappings(tool_name: str) -> dict:
    """
    获取工具的字段映射关系
    
    Args:
        tool_name: 工具名称
        
    Returns:
        字段映射关系字典
    """
    mapping = get_tool_mapping(tool_name)
    return mapping.get("field_mappings", {})

def is_search_tool(tool_name: str) -> bool:
    """
    判断是否为搜索类工具
    
    Args:
        tool_name: 工具名称
        
    Returns:
        是否为搜索类工具
    """
    return tool_name in SEARCH_TOOL_MAPPINGS

def is_image_tool(tool_name: str) -> bool:
    """
    判断是否为图像处理类工具
    
    Args:
        tool_name: 工具名称
        
    Returns:
        是否为图像处理类工具
    """
    return tool_name in IMAGE_TOOL_MAPPINGS

def is_upload_tool(tool_name: str) -> bool:
    """
    判断是否为文件上传类工具
    
    Args:
        tool_name: 工具名称
        
    Returns:
        是否为文件上传类工具
    """
    return tool_name in UPLOAD_TOOL_MAPPINGS 