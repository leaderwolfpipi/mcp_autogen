from PIL import Image
import os

def image_resizer(scale_factor: int, image: str) -> str:
    """
    Resize the input image by a given scale factor using PIL.

    Args:
    scale_factor (int): The factor by which the image should be scaled.
    image (str): The path to the input image file.

    Returns:
    str: The path to the resized image file.

    Raises:
    FileNotFoundError: If the input image file is not found.
    ValueError: If the scale factor is not a positive integer.
    Exception: For any other unexpected errors.
    """
    try:
        if not os.path.exists(image):
            raise FileNotFoundError(f"Input image file '{image}' not found.")

        if not isinstance(scale_factor, int) or scale_factor <= 0:
            raise ValueError("Scale factor must be a positive integer.")

        img = Image.open(image)
        new_size = (img.size[0] * scale_factor, img.size[1] * scale_factor)
        resized_img = img.resize(new_size)
        
        resized_image_path = os.path.splitext(image)[0] + f"_resized_{scale_factor}x.png"
        resized_img.save(resized_image_path)
        
        return resized_image_path
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example of usage
resized_image_path = image_resizer(2, "tests/images/test.png")
print(f"Resized image saved at: {resized_image_path}")