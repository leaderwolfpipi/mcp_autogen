import logging
import os
import re
import ast
from typing import Union, List, Dict, Any
from datetime import timedelta
from minio import Minio
from minio.error import S3Error
from tools.base_tool import create_standardized_output
import time

def _flatten_paths(value: Any) -> List[str]:
    """将输入递归拍平成字符串路径列表，支持字符串表示的列表格式。"""
    paths: List[str] = []
    if value is None:
        return paths
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return paths
        
        # 检查是否是字符串表示的列表格式 (如 "['/path1', '/path2']")
        if v.startswith('[') and v.endswith(']'):
            try:
                # 尝试安全解析字符串表示的列表
                parsed = ast.literal_eval(v)
                if isinstance(parsed, (list, tuple)):
                    for item in parsed:
                        paths.extend(_flatten_paths(item))
                    return paths
            except (ValueError, SyntaxError):
                # 如果解析失败，当作普通字符串处理
                pass
        
        # 检查是否是逗号分隔的路径字符串
        if ',' in v and not os.path.exists(v):
            # 如果包含逗号且文件不存在，尝试按逗号分割
            for part in v.split(','):
                part = part.strip().strip('\'"')  # 去除引号
                if part:
                    paths.append(part)
            return paths
        
        # 普通字符串路径
        paths.append(v)
        return paths
    
    if isinstance(value, (list, tuple)):
        for item in value:
            paths.extend(_flatten_paths(item))
        return paths
    
    if isinstance(value, dict):
        # 兼容可能的字典格式
        for key in ("path", "file_path", "filepath", "file", "paths", "file_paths"):
            if key in value and isinstance(value[key], (str, list, tuple)):
                paths.extend(_flatten_paths(value[key]))
        return paths
    
    # 其他类型转为字符串尝试处理
    try:
        str_value = str(value).strip()
        if str_value and str_value != 'None':
            paths.extend(_flatten_paths(str_value))
    except Exception:
        # 转换失败则忽略
        pass
    
    return paths


def minio_uploader(bucket_name: str, file_path: Union[str, List[str]], generate_download_urls: bool = True) -> Dict[str, Any]:
    """
    通用MinIO上传工具。
    支持单文件或文件路径列表上传，输出结构标准化。
    支持多种输入格式：字符串、列表、字符串表示的列表等。
    自动生成临时下载链接。

    参数：
        bucket_name (str): 目标bucket名称。
        file_path (str | List[str]): 待上传文件路径或路径列表。
                                   支持格式：
                                   - 单个路径字符串: "/path/to/file.txt"
                                   - 路径列表: ["/path1", "/path2"]
                                   - 字符串表示的列表: "['/path1', '/path2']"
                                   - 逗号分隔的路径: "/path1,/path2"
        generate_download_urls (bool): 是否生成临时下载链接，默认True
    返回：
        dict: 标准化输出，字段包括：
            status: 'success' | 'error'
            data.primary: 上传后的下载链接或链接列表
            data.secondary: 详细上传结果
            data.counts: 上传统计
            metadata: 工具元信息
            paths: 上传文件路径列表
            message: 执行消息
            error: 错误信息（如有）
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    start_time = time.time()
    
    # 记录原始输入用于调试
    logger.info(f"原始输入 - bucket_name: {bucket_name}, file_path: {file_path}, type: {type(file_path)}")
    
    # 统一处理输入（file_path为必填），支持嵌套列表/字典，自动拍平、去重、清洗
    try:
        file_paths = _flatten_paths(file_path)
        logger.info(f"解析后的路径列表: {file_paths}")
    except Exception as e:
        logger.error(f"路径解析失败: {e}")
        return create_standardized_output(
            tool_name="minio_uploader",
            status="error",
            message=f"路径解析失败: {str(e)}",
            error=f"路径解析失败: {str(e)}",
            start_time=start_time,
            parameters={"bucket_name": bucket_name, "file_path": file_path}
        )
    
    # 去重并保持顺序
    seen = set()
    deduped: List[str] = []
    for p in file_paths:
        if p not in seen:
            seen.add(p)
            deduped.append(p)
    file_paths = deduped
    
    if not file_paths:
        return create_standardized_output(
            tool_name="minio_uploader",
            status="error",
            message="file_path参数不能为空或无法解析有效路径",
            error="file_path为空",
            start_time=start_time,
            parameters={"bucket_name": bucket_name, "file_path": file_path}
        )
    
    # 验证bucket名称
    if not bucket_name or not isinstance(bucket_name, str):
        logger.error(f"bucket名称必须是非空字符串: {bucket_name}")
        return create_standardized_output(
            tool_name="minio_uploader",
            status="error",
            message=f"bucket名称必须是非空字符串: {bucket_name}",
            error=f"无效的bucket名称: {bucket_name}",
            start_time=start_time,
            parameters={"bucket_name": bucket_name, "file_path": file_path}
        )
    
    if not re.match(r'^[a-z0-9][a-z0-9.-]*[a-z0-9]$', bucket_name):
        logger.error(f"无效的bucket名称: {bucket_name}，必须符合S3命名规则")
        return create_standardized_output(
            tool_name="minio_uploader",
            status="error",
            message=f"无效的bucket名称: {bucket_name}，必须符合S3命名规则",
            error=f"无效的bucket名称: {bucket_name}",
            start_time=start_time,
            parameters={"bucket_name": bucket_name, "file_path": file_path}
        )
    
    # 获取下载链接过期时间配置
    download_expires_seconds = int(os.getenv("MINIO_DOWNLOAD_EXPIRED", "3600"))  # 默认1小时
    download_expires = timedelta(seconds=download_expires_seconds)
    logger.info(f"下载链接过期时间: {download_expires_seconds}秒")
    
    # 初始化MinIO客户端
    try:
        # 获取MinIO配置，提供默认值以确保向后兼容
        endpoint = os.getenv("MINIO_ENDPOINT", "minio.originhub.tech")
        access_key = os.getenv("MINIO_ACCESS_KEY", "myscalekb")
        secret_key = os.getenv("MINIO_SECRET_KEY", "passwd_sfzASAXazd")
        
        if not all([endpoint, access_key, secret_key]):
            raise ValueError("MinIO配置不完整，请检查环境变量")
        
        minio_client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=True
        )
        
        # 测试连接
        logger.info("正在测试MinIO连接...")
        minio_client.list_buckets()
        logger.info("MinIO连接测试成功")
        
    except Exception as e:
        logger.error(f"MinIO客户端初始化失败: {e}")
        return create_standardized_output(
            tool_name="minio_uploader",
            status="error",
            message="MinIO客户端初始化失败",
            error=str(e),
            start_time=start_time,
            parameters={"bucket_name": bucket_name, "file_path": file_path}
        )
    
    results = []
    download_links = []
    success_count = 0
    fail_count = 0
    
    for idx, path in enumerate(file_paths):
        logger.info(f"处理文件 {idx+1}/{len(file_paths)}: {path}")
        
        # 验证路径
        if not path or not isinstance(path, str):
            logger.error(f"无效的文件路径: {path}")
            results.append({"index": idx, "file_path": path, "status": "error", "error": "无效的文件路径"})
            fail_count += 1
            continue
            
        # 展开用户目录
        expanded_path = os.path.expanduser(path)
        
        # 转换为绝对路径
        abs_path = os.path.abspath(expanded_path)
        
        if not os.path.exists(abs_path):
            logger.error(f"文件不存在: {abs_path} (原路径: {path})")
            results.append({"index": idx, "file_path": path, "status": "error", "error": f"文件不存在: {abs_path}"})
            fail_count += 1
            continue
            
        if not os.path.isfile(abs_path):
            logger.error(f"路径不是文件: {abs_path}")
            results.append({"index": idx, "file_path": path, "status": "error", "error": f"路径不是文件: {abs_path}"})
            fail_count += 1
            continue
            
        try:
            # 检查bucket
            if not minio_client.bucket_exists(bucket_name):
                logger.info(f"Bucket '{bucket_name}' does not exist. Creating bucket.")
                minio_client.make_bucket(bucket_name)
            else:
                logger.info(f"Bucket '{bucket_name}' exists.")
                
            file_name = os.path.basename(abs_path)
            
            # 确保文件名唯一性
            object_name = file_name
            counter = 1
            while True:
                try:
                    minio_client.stat_object(bucket_name, object_name)
                    # 文件存在，生成新名称
                    name, ext = os.path.splitext(file_name)
                    object_name = f"{name}_{counter}{ext}"
                    counter += 1
                except S3Error as e:
                    if e.code == 'NoSuchKey':
                        # 文件不存在，可以使用这个名称
                        break
                    else:
                        raise
            
            logger.info(f"Uploading '{file_name}' as '{object_name}' to bucket '{bucket_name}'.")
            
            # 执行上传
            result = minio_client.fput_object(bucket_name, object_name, abs_path)
            logger.info(f"Upload completed: {result.etag}")
            
            # 生成临时下载链接
            download_url = None
            if generate_download_urls:
                try:
                    logger.info(f"Generating presigned URL with expires={download_expires} ({download_expires_seconds} seconds)")
                    download_url = minio_client.presigned_get_object(
                        bucket_name, 
                        object_name, 
                        expires=download_expires
                    )
                    logger.info(f"Generated download URL for {object_name}, expires in {download_expires_seconds}s")
                    logger.info(f"Download URL: {download_url[:100]}...")
                except Exception as e:
                    logger.warning(f"Failed to generate download URL for {object_name}: {e}")
                    # 如果生成签名URL失败，尝试生成永久URL
                    logger.info("Trying to use permanent URL as fallback")
                    download_url = f"https://{endpoint}/{bucket_name}/{object_name}"
            
            # 构建永久URL（用于备用）
            permanent_url = f"https://{endpoint}/{bucket_name}/{object_name}"
            
            if download_url:
                download_links.append({
                    "name": file_name,
                    "original_name": file_name,
                    "object_name": object_name,
                    "download_url": download_url,
                    "permanent_url": permanent_url,
                    "expires_in_seconds": download_expires_seconds
                })
            
            results.append({
                "index": idx, 
                "file_path": path, 
                "abs_path": abs_path,
                "file_name": file_name,
                "object_name": object_name,
                "status": "success", 
                "download_url": download_url,
                "permanent_url": permanent_url,
                "expires_in_seconds": download_expires_seconds if download_url else None,
                "etag": result.etag
            })
            success_count += 1
            logger.info(f"Successfully uploaded {file_name}, download URL: {download_url}")
            
        except S3Error as e:
            logger.error(f"Failed to upload file '{abs_path}' to bucket '{bucket_name}': {e}")
            results.append({"index": idx, "file_path": path, "abs_path": abs_path, "status": "error", "error": str(e)})
            fail_count += 1
        except Exception as e:
            logger.error(f"An unexpected error occurred while uploading '{abs_path}': {e}")
            results.append({"index": idx, "file_path": path, "abs_path": abs_path, "status": "error", "error": str(e)})
            fail_count += 1
    
    status = "success" if success_count > 0 else "error"
    
    # 简洁的状态消息
    message = f"成功上传{success_count}个文件，失败{fail_count}个。"
    if download_links:
        message += f" 生成了{len(download_links)}个临时下载链接。"
    
    # 根据返回数量决定primary_data格式
    primary_data = None
    if download_links:
        if len(download_links) == 1:
            primary_data = download_links[0]
        else:
            primary_data = download_links
    
    return create_standardized_output(
        tool_name="minio_uploader",
        status=status,
        primary_data=primary_data,
        secondary_data={
            "results": results,
            "download_config": {
                "expires_in_seconds": download_expires_seconds,
                "generate_download_urls": generate_download_urls
            }
        },
        counts={"total": len(file_paths), "successful": success_count, "failed": fail_count},
        paths=file_paths,
        message=message,
        error=None if status == "success" else message,
        start_time=start_time,
        parameters={"bucket_name": bucket_name, "file_path": file_path, "generate_download_urls": generate_download_urls}
    )