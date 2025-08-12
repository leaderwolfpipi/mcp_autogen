from PIL import Image
import pytesseract

def text_extractor(image: str) -> str:
    """
    Extract text from the given image using OCR (Optical Character Recognition).
    
    Args:
    image (str): The path to the image file from which text needs to be extracted.
    
    Returns:
    str: Extracted text from the image.
    """
    
    try:
        # Open the image file
        img = Image.open(image)
        
        # Use pytesseract to extract text from the image
        extracted_text = pytesseract.image_to_string(img)
        
        return extracted_text
    
    except Exception as e:
        # Log any errors that occur during text extraction
        print(f"Error occurred during text extraction: {e}")
        return ""