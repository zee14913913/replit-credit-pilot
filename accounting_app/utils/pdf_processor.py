"""
PDF Processing Utilities
使用 pypdfium2 + pytesseract 进行 PDF 文本提取（不依赖系统 poppler）
"""
import io
import pypdfium2 as pdfium
from PIL import Image
import pytesseract
from typing import Optional


def pdf_bytes_to_text(data: bytes, ocr_lang: str = "eng", dpi: int = 200) -> str:
    """
    将 PDF 字节数据转换为文本
    
    Args:
        data: PDF 文件的字节数据
        ocr_lang: OCR 语言（默认 "eng"，中文使用 "chi_sim"）
        dpi: 渲染 DPI（默认 200，更高的值提供更好的质量但更慢）
    
    Returns:
        提取的文本内容
    
    Example:
        >>> with open("statement.pdf", "rb") as f:
        ...     text = pdf_bytes_to_text(f.read())
    """
    try:
        pdf = pdfium.PdfDocument(io.BytesIO(data))
        extracted_pages = []
        
        for page_num in range(len(pdf)):
            page = pdf.get_page(page_num)
            
            # 渲染页面为图像（scale = dpi/72）
            scale = dpi / 72.0
            bitmap = page.render(scale=scale)
            pil_image = bitmap.to_pil()
            
            # 转换为灰度以提高 OCR 准确性
            grayscale_image = pil_image.convert("L")
            
            # 使用 pytesseract 进行 OCR
            page_text = pytesseract.image_to_string(grayscale_image, lang=ocr_lang)
            extracted_pages.append(page_text)
            
            # 清理资源
            page.close()
        
        pdf.close()
        
        # 合并所有页面的文本
        full_text = "\n\n".join(extracted_pages).strip()
        return full_text
        
    except Exception as e:
        raise RuntimeError(f"PDF processing failed: {str(e)}") from e


def pdf_file_to_text(file_path: str, ocr_lang: str = "eng", dpi: int = 200) -> str:
    """
    从文件路径读取 PDF 并转换为文本
    
    Args:
        file_path: PDF 文件路径
        ocr_lang: OCR 语言
        dpi: 渲染 DPI
    
    Returns:
        提取的文本内容
    """
    with open(file_path, "rb") as f:
        return pdf_bytes_to_text(f.read(), ocr_lang=ocr_lang, dpi=dpi)
