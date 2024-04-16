import os
import sys
import pytesseract
from pytesseract import Output
from pdf2image import convert_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError,
)
from .logger import build_logger

# Get the current directory
path = os.path.dirname(os.path.abspath(__file__))
# Set the logger
logger = build_logger('proc_pdf', path + '/logs')

def correct_image_orientation(image):
    gray_image = image.convert('L')
    
    osd = pytesseract.image_to_osd(gray_image, output_type=Output.DICT)
    rotation_angle = osd['rotate']
    corrected_image = gray_image.rotate(-rotation_angle, expand=True)
    return corrected_image

def convert_pdf_to_images(pdf_path, destination_directory):
    logger.info(f"PDF UPLOAD Directory: {pdf_path}")
    try:
        pdf_path = os.path.abspath(pdf_path)
        pdf_name_no_ext = os.path.splitext(os.path.basename(pdf_path))[0]
        final_destination_directory = os.path.join(destination_directory, pdf_name_no_ext)
        # Verifica si el directorio de destino existe, si no, lo crea
        if not os.path.exists(final_destination_directory):
            os.makedirs(final_destination_directory)
           
        images = convert_from_path(pdf_path, dpi=600)
        for i, image in enumerate(images):
            image = correct_image_orientation(image)
            fname = os.path.join(final_destination_directory, f'{pdf_name_no_ext}{i}.png')
            image.save(fname, 'PNG')  
            logger.info(f"Images Directory {final_destination_directory}")
    except PDFInfoNotInstalledError:
        logger.error('Error: Unable to get document information')
        sys.exit(1)
    except PDFPageCountError:
        logger.error('Error: Unable to get page count')
        sys.exit(1)
    except PDFSyntaxError:
        logger.error('Error: Unable to get document information')
        sys.exit(1)
    
    return pdf_name_no_ext
