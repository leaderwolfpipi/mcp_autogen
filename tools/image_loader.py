import os
from PIL import Image
import logging

def image_loader(directory: str) -> list:
    """
    Loads all images from the specified directory.

    Args:
        directory (str): The path to the directory containing images.

    Returns:
        list: A list of PIL Image objects loaded from the directory.

    Raises:
        FileNotFoundError: If the directory does not exist.
        ValueError: If no images are found in the directory.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    if not os.path.exists(directory):
        logger.error(f"Directory not found: {directory}")
        raise FileNotFoundError(f"Directory not found: {directory}")

    image_files = [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    
    if not image_files:
        logger.error(f"No images found in directory: {directory}")
        raise ValueError(f"No images found in directory: {directory}")

    images = []
    for image_file in image_files:
        try:
            image_path = os.path.join(directory, image_file)
            image = Image.open(image_path)
            images.append(image)
            logger.info(f"Loaded image: {image_file}")
        except Exception as e:
            logger.error(f"Failed to load image {image_file}: {e}")

    return images