import os
from PIL import Image
import logging

def image_processor(operation: str, scale_factor: int = 1, image_directory: str = '.', image_path: str = None) -> None:
    """
    Process images in the specified directory based on the given operation.

    Parameters:
    - operation (str): The type of operation to perform on images. Supported operations: 'scale'.
    - scale_factor (int): The factor by which to scale images. Default is 1 (no scaling).
    - image_directory (str): The directory containing images to process. Default is current directory.
    - image_path (str): The path to a specific image file to process. If provided, overrides image_directory.

    Raises:
    - ValueError: If the operation is not supported.
    - FileNotFoundError: If the image directory does not exist.
    """
    logging.basicConfig(level=logging.INFO)
    
    if operation not in ['scale', 'enhance']:
        raise ValueError(f"Unsupported operation: {operation}. Supported operations: 'scale', 'enhance'.")
    
    # If image_path is provided, process only that file
    if image_path:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"The image file {image_path} does not exist.")
        
        try:
            with Image.open(image_path) as img:
                if operation == 'scale':
                    new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
                    img = img.resize(new_size, Image.ANTIALIAS)
                    img.save(image_path)
                    logging.info(f"Scaled image {image_path} to {new_size}.")
                elif operation == 'enhance':
                    # Simple enhancement - increase contrast and brightness
                    from PIL import ImageEnhance
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.2)
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(1.1)
                    img.save(image_path)
                    logging.info(f"Enhanced image {image_path}.")
            return
        except Exception as e:
            logging.error(f"Failed to process image {image_path}: {e}")
            raise
    
    # Process all images in directory
    if not os.path.isdir(image_directory):
        raise FileNotFoundError(f"The directory {image_directory} does not exist.")
    
    for filename in os.listdir(image_directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            try:
                image_path = os.path.join(image_directory, filename)
                with Image.open(image_path) as img:
                    if operation == 'scale':
                        new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
                        img = img.resize(new_size, Image.ANTIALIAS)
                        img.save(image_path)
                        logging.info(f"Scaled image {filename} to {new_size}.")
                    elif operation == 'enhance':
                        # Simple enhancement - increase contrast and brightness
                        from PIL import ImageEnhance
                        enhancer = ImageEnhance.Contrast(img)
                        img = enhancer.enhance(1.2)
                        enhancer = ImageEnhance.Brightness(img)
                        img = enhancer.enhance(1.1)
                        img.save(image_path)
                        logging.info(f"Enhanced image {filename}.")
            except Exception as e:
                logging.error(f"Failed to process image {filename}: {e}")

# Example usage:
# image_processor(operation="scale", scale_factor=2, image_directory="tests/images")
# image_processor(operation="enhance", image_path="input_image.jpg")