import logging

def text_case_converter(conversion_type: str, file_path: str) -> None:
    """
    Converts the case of text in a file based on the specified conversion type.

    Parameters:
    conversion_type (str): The type of case conversion to perform. Supported types: 'swap_case'.
    file_path (str): The path to the text file to be processed.

    Raises:
    ValueError: If the conversion_type is not supported.
    FileNotFoundError: If the file_path does not exist.
    IOError: If there is an error reading or writing the file.
    """
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        # Validate conversion type
        if conversion_type != 'swap_case':
            raise ValueError(f"Unsupported conversion type: {conversion_type}")

        # Read the file
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            logging.debug(f"Original text: {text}")

        # Perform case conversion
        converted_text = text.swapcase()
        logging.debug(f"Converted text: {converted_text}")

        # Write the converted text back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(converted_text)
            logging.info(f"Text successfully converted and saved to {file_path}")

    except FileNotFoundError:
        logging.error(f"The file at {file_path} was not found.")
        raise
    except IOError as e:
        logging.error(f"An I/O error occurred: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise