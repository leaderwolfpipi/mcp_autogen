import logging
import os
from minio import Minio
from minio.error import S3Error

def file_uploader(destination: str, file_path: str) -> bool:
    """
    Uploads a file to the specified destination.

    Parameters:
    - destination (str): The destination where the file should be uploaded. 
                        Supports 'minio' or 'minio/bucket_name' format.
    - file_path (str): The path to the file that needs to be uploaded.

    Returns:
    - bool: True if the upload is successful, False otherwise.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # 解析destination参数
    if destination.startswith("minio/"):
        # 格式: minio/bucket_name
        bucket_name = destination.split("/", 1)[1]
        storage_type = "minio"
    elif destination == "minio":
        # 格式: minio (使用默认bucket)
        bucket_name = "kb-dev"
        storage_type = "minio"
    else:
        logger.error("Unsupported destination: %s", destination)
        logger.error("Supported formats: 'minio' or 'minio/bucket_name'")
        return False

    logger.info(f"Storage type: {storage_type}, Bucket: {bucket_name}")

    # MinIO client configuration
    minio_client = Minio(
        "minio.originhub.tech",  # Example endpoint, replace with actual endpoint
        access_key="myscalekb",
        secret_key="passwd_sfzASAXazd",
        secure=True
    )

    try:
        # Check if the bucket exists, create if not
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info("Bucket '%s' created.", bucket_name)

        # Upload the file
        file_name = os.path.basename(file_path)
        minio_client.fput_object(bucket_name, file_name, file_path)
        logger.info("File '%s' uploaded to bucket '%s'.", file_name, bucket_name)
        return True

    except S3Error as e:
        logger.error("Failed to upload file: %s", e)
        return False
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)
        return False