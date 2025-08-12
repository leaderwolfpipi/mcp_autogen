import logging
import os

def ocr(image) -> str:
    """
    Perform Optical Character Recognition (OCR) on the given image.

    Args:
        image: The image path (str) or PIL Image object.

    Returns:
        str: The extracted text from the image.
    """
    try:
        # 检查PIL依赖
        try:
            from PIL import Image
        except ImportError:
            logging.error("PIL/Pillow未安装，请运行: pip install Pillow")
            return "错误: PIL/Pillow未安装"
        
        # 检查pytesseract依赖
        try:
            import pytesseract
        except ImportError:
            logging.error("pytesseract未安装，请运行: pip install pytesseract")
            return "错误: pytesseract未安装"
        
        # 处理输入：如果是字符串（文件路径），则打开图片
        if isinstance(image, str):
            if not os.path.exists(image):
                logging.error(f"图片文件不存在: {image}")
                return f"错误: 图片文件不存在 - {image}"
            img = Image.open(image)
        elif hasattr(image, 'size'):  # 检查是否为PIL Image对象
            img = image
        else:
            logging.error(f"无效的图片输入: {type(image)}")
            return f"错误: 无效的图片输入类型 - {type(image)}"

        logging.info("开始OCR处理...")
        
        # 执行OCR
        extracted_text = pytesseract.image_to_string(img, lang='eng+chi_sim')
        
        if not extracted_text.strip():
            extracted_text = "未检测到文字内容"
        
        logging.info("OCR处理完成")
        return extracted_text.strip()

    except Exception as e:
        logging.error(f"OCR处理失败: {e}")
        return f"OCR处理失败: {str(e)}"