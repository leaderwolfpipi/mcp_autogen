import logging
import os
from minio import Minio
from minio.error import S3Error
from PIL import Image

def image_uploader(destination: str, image_path: str, bucket_name: str = None, object_name: str = None) -> bool:
    """
    [LEGACY] 图像上传工具 - 推荐使用 minio_uploader 替代。
    
    此工具专门用于单个图像文件上传到MinIO存储。
    
    注意：对于新项目建议使用 minio_uploader，它提供更强大的功能：
    - 支持批量上传
    - 标准化输出格式  
    - 更好的错误处理
    - 自动生成下载链接

    :param destination: The destination where the image will be uploaded. 
                       Supports 'minio' or 'minio/bucket_name' format.
    :param image_path: The local path to the image file.
    :param bucket_name: The name of the bucket in the MinIO server (optional if specified in destination).
    :param object_name: The name of the object in the bucket (optional, defaults to filename).
    :return: True if the upload is successful, False otherwise.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # 解析destination参数
    if destination.startswith("minio/"):
        # 格式: minio/bucket_name
        parsed_bucket_name = destination.split("/", 1)[1]
        storage_type = "minio"
    elif destination == "minio":
        # 格式: minio (使用默认bucket)
        parsed_bucket_name = "kb-dev"
        storage_type = "minio"
    else:
        logger.error("Unsupported destination: %s", destination)
        logger.error("Supported formats: 'minio' or 'minio/bucket_name'")
        return False

    # 使用解析的bucket_name或传入的bucket_name
    final_bucket_name = bucket_name or parsed_bucket_name
    final_object_name = object_name or os.path.basename(image_path)
    
    logger.info(f"Storage type: {storage_type}, Bucket: {final_bucket_name}, Object: {final_object_name}")

    try:
        # Initialize MinIO client with environment variables
        import os
        endpoint = os.getenv("MINIO_ENDPOINT", "minio.originhub.tech")
        access_key = os.getenv("MINIO_ACCESS_KEY", "myscalekb")
        secret_key = os.getenv("MINIO_SECRET_KEY", "passwd_sfzASAXazd")
        
        if not all([endpoint, access_key, secret_key]):
            logger.error("MinIO配置不完整，请检查环境变量")
            return False
            
        minio_client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=True
        )

        # Check if the bucket exists
        if not minio_client.bucket_exists(final_bucket_name):
            logger.info("Bucket %s does not exist. Creating bucket.", final_bucket_name)
            minio_client.make_bucket(final_bucket_name)

        # Open the image file
        with Image.open(image_path) as img:
            img_format = img.format.lower()
            temp_path = f"/tmp/{final_object_name}.{img_format}"
            img.save(temp_path)

        # Upload the image
        minio_client.fput_object(final_bucket_name, final_object_name, temp_path)
        logger.info("Image uploaded successfully to %s/%s", final_bucket_name, final_object_name)

        # Clean up temporary file
        os.remove(temp_path)

        return True

    except S3Error as e:
        logger.error("Failed to upload image: %s", e)
        return False
    except FileNotFoundError:
        logger.error("Image file not found: %s", image_path)
        return False
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)
        return False