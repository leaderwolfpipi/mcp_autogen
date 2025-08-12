import os
from PIL import Image
import logging
import tempfile
import time
from typing import Dict, Any, List, Union
import json
import ast

from tools.base_tool import create_standardized_output

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def image_rotator(image_path: Union[str, List[str], Image.Image, List[Image.Image]], 
                 angle: float = 90.0) -> Dict[str, Any]:
    """
    智能图像旋转工具 - 支持多种输入格式
    
    Parameters:
    - image_path: 支持以下格式：
        * 单个文件路径 (str)
        * 文件路径列表 (List[str])
        * 单个PIL Image对象
        * PIL Image对象列表
        * 包含文件路径的JSON字符串
    - angle (float): 旋转角度（度）
    
    Returns:
    - 标准化的输出字典，包含：
        {
            "status": "success" | "error",
            "data": {
                "primary": List[str],          # 主要输出：旋转后的图片路径列表
                "secondary": Dict,             # 次要输出：详细信息
                "counts": Dict                 # 统计信息
            },
            "metadata": {
                "tool_name": "image_rotator",
                "version": "1.0.0",
                "parameters": Dict,            # 输入参数
                "processing_time": float       # 处理时间
            },
            "paths": List[str],                # 文件路径列表
            "message": str                     # 处理消息
        }
    """
    logger = logging.getLogger(__name__)
    start_time = time.time()
    
    # 准备参数
    parameters = {
        "image_path": image_path,
        "angle": angle
    }
    
    try:
        # 标准化输入
        images_to_process = _normalize_input(image_path)
        
        if not images_to_process:
            raise ValueError("No valid images found in input")
        
        logger.info(f"Processing {len(images_to_process)} images with rotation angle {angle}")
        
        # 处理所有图片
        results = []
        temp_paths = []
        original_sizes = []
        rotated_sizes = []
        
        for i, img_input in enumerate(images_to_process):
            try:
                # 获取PIL Image对象
                if isinstance(img_input, str):
                    # 文件路径
                    img = Image.open(img_input)
                    original_path = img_input
                elif hasattr(img_input, 'save'):
                    # PIL Image对象
                    img = img_input
                    original_path = f"image_{i}"
                else:
                    logger.warning(f"Skipping invalid image input at index {i}: {type(img_input)}")
                    continue
                
                original_size = img.size
                original_sizes.append(original_size)
                
                # 旋转图片
                rotated_img = img.rotate(angle, expand=True)
                new_size = rotated_img.size
                rotated_sizes.append(new_size)
                
                # 保存到临时文件
                temp_dir = tempfile.mkdtemp()
                temp_path = os.path.join(temp_dir, f"rotated_image_{i}_{int(time.time())}.png")
                rotated_img.save(temp_path)
                temp_paths.append(temp_path)
                
                # 记录结果
                result = {
                    "index": i,
                    "original_path": original_path,
                    "original_size": original_size,
                    "rotated_size": new_size,
                    "angle": angle,
                    "temp_path": temp_path,
                    "status": "success"
                }
                results.append(result)
                
                logger.info(f"Rotated image {i+1}/{len(images_to_process)}: {original_size} -> {new_size}")
                
            except Exception as e:
                logger.error(f"Failed to process image {i}: {e}")
                results.append({
                    "index": i,
                    "status": "failed",
                    "error": str(e)
                })
        
        # 生成统计信息
        successful_count = len([r for r in results if r["status"] == "success"])
        failed_count = len(results) - successful_count
        
        if successful_count == 0:
            raise Exception("No images were successfully processed")
        
        # 创建标准化输出
        output = create_standardized_output(
            tool_name="image_rotator",
            status="success",
            primary_data=temp_paths,  # 主要输出：旋转后的图片路径列表
            secondary_data={
                "results": results,
                "original_sizes": original_sizes,
                "rotated_sizes": rotated_sizes,
                "angle": angle
            },
            counts={
                "total": len(images_to_process),
                "successful": successful_count,
                "failed": failed_count
            },
            paths=temp_paths,  # 文件路径列表
            message=f"Processed {successful_count}/{len(images_to_process)} images with rotation angle {angle}",
            parameters=parameters,
            start_time=start_time
        )
        
        return output

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return create_standardized_output(
            tool_name="image_rotator",
            status="error",
            error=str(e),
            parameters=parameters,
            start_time=start_time
        )

def _normalize_input(image_path: Union[str, List[str], Image.Image, List[Image.Image]]) -> List[Union[str, Image.Image]]:
    """
    标准化输入，支持多种格式
    
    Args:
        image_path: 输入图片，支持多种格式
        
    Returns:
        标准化的图片列表
    """
    if isinstance(image_path, str):
        # 检查是否是JSON字符串
        if image_path.strip().startswith('[') and image_path.strip().endswith(']'):
            try:
                # 尝试解析JSON
                parsed = json.loads(image_path)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        
        # 检查是否是Python列表的字符串表示
        if image_path.strip().startswith('[') and image_path.strip().endswith(']'):
            try:
                # 清理字符串
                cleaned = image_path.replace("\\'", "'").replace('\\"', '"')
                # 尝试eval（安全的方式）
                parsed = ast.literal_eval(cleaned)
                if isinstance(parsed, list):
                    return parsed
            except (ValueError, SyntaxError):
                pass
        
        # 单个文件路径
        return [image_path]
    
    elif isinstance(image_path, list):
        # 已经是列表
        return image_path
    
    elif hasattr(image_path, 'save'):
        # PIL Image对象
        return [image_path]
    
    else:
        # 其他类型，尝试转换为列表
        try:
            return list(image_path)
        except:
            return []

def image_rotator_directory(image_directory: Union[str, List[str]], angle: float = 90.0) -> Dict[str, Any]:
    """
    旋转目录中的所有图片或指定的图片列表
    
    Parameters:
    - image_directory (str | List[str]): 图片目录路径或图片路径列表
    - angle (float): 旋转角度（度）
    
    Returns:
    - 标准化的输出字典，包含：
        {
            "status": "success" | "error",
            "data": {
                "primary": List[str],          # 主要输出：旋转后的图片路径列表
                "secondary": Dict,              # 次要输出：详细信息
                "counts": Dict                  # 统计信息
            },
            "metadata": {
                "tool_name": "image_rotator_directory",
                "version": "1.0.0",
                "parameters": Dict,             # 输入参数
                "processing_time": float        # 处理时间
            },
            "paths": List[str],                 # 文件路径列表
            "message": str                      # 处理消息
        }
    """
    logger = logging.getLogger(__name__)
    start_time = time.time()
    
    parameters = {
        "image_directory": image_directory,
        "angle": angle
    }
    
    try:
        # 智能处理输入：支持目录路径或图片路径列表
        if isinstance(image_directory, list):
            # 如果输入是列表，直接使用作为图片路径列表
            image_files = image_directory
            input_type = "image_list"
            logger.info(f"Processing {len(image_files)} images from provided list")
        elif isinstance(image_directory, str):
            # 如果输入是字符串，检查是目录还是单个文件
            if os.path.isdir(image_directory):
                # 是目录，获取目录中的所有图片文件
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
                image_files = []
                
                for filename in os.listdir(image_directory):
                    if any(filename.lower().endswith(ext) for ext in image_extensions):
                        image_files.append(os.path.join(image_directory, filename))
                
                if not image_files:
                    raise ValueError(f"No image files found in directory {image_directory}")
                
                input_type = "directory"
                logger.info(f"Found {len(image_files)} images in directory {image_directory}")
            elif os.path.isfile(image_directory):
                # 是单个文件
                image_files = [image_directory]
                input_type = "single_file"
                logger.info(f"Processing single file: {image_directory}")
            else:
                raise ValueError(f"The path {image_directory} does not exist.")
        else:
            raise ValueError(f"Invalid input type: {type(image_directory)}. Expected str or List[str]")
        
        # 处理所有图片
        results = []
        temp_paths = []
        original_sizes = []
        rotated_sizes = []
        
        for i, img_path in enumerate(image_files):
            try:
                # 验证文件是否存在
                if not os.path.exists(img_path):
                    logger.warning(f"Image file does not exist: {img_path}")
                    results.append({
                        "index": i,
                        "original_path": img_path,
                        "status": "failed",
                        "error": f"File does not exist: {img_path}"
                    })
                    continue
                
                # 打开图片
                img = Image.open(img_path)
                original_size = img.size
                original_sizes.append(original_size)
                
                # 旋转图片
                rotated_img = img.rotate(angle, expand=True)
                new_size = rotated_img.size
                rotated_sizes.append(new_size)
                
                # 保存到临时文件
                temp_dir = tempfile.mkdtemp()
                temp_path = os.path.join(temp_dir, f"rotated_image_{i}_{int(time.time())}.png")
                rotated_img.save(temp_path)
                temp_paths.append(temp_path)
                
                # 记录结果
                result = {
                    "index": i,
                    "original_path": img_path,
            "original_size": original_size,
            "rotated_size": new_size,
            "angle": angle,
            "temp_path": temp_path,
                    "status": "success"
                }
                results.append(result)
                
                logger.info(f"Rotated image {i+1}/{len(image_files)}: {original_size} -> {new_size}")
                
            except Exception as e:
                logger.error(f"Failed to process image {i}: {e}")
                results.append({
                    "index": i,
                    "original_path": img_path,
                    "status": "failed",
                    "error": str(e)
                })
        
        # 生成统计信息
        successful_count = len([r for r in results if r["status"] == "success"])
        failed_count = len(results) - successful_count
        
        if successful_count == 0:
            raise Exception("No images were successfully processed")
        
        # 创建标准化输出
        output = create_standardized_output(
            tool_name="image_rotator_directory",
            status="success",
            primary_data=temp_paths,  # 主要输出：旋转后的图片路径列表
            secondary_data={
                "results": results,
                "original_sizes": original_sizes,
                "rotated_sizes": rotated_sizes,
                "angle": angle,
                "input_type": input_type,
                "input_path": image_directory
            },
            counts={
                "total": len(image_files),
                "successful": successful_count,
                "failed": failed_count
            },
            paths=temp_paths,  # 文件路径列表
            message=f"Processed {successful_count}/{len(image_files)} images with rotation angle {angle}",
            parameters=parameters,
            start_time=start_time
        )
        
        return output

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return create_standardized_output(
            tool_name="image_rotator_directory",
            status="error",
            error=str(e),
            parameters=parameters,
            start_time=start_time
        )