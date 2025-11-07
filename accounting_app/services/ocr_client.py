import os, io, pytesseract
from PIL import Image
from typing import List, Dict

class OCRClient:
    def __init__(self):
        self.provider = os.getenv("OCR_PROVIDER", "demo").lower()

    def ocr_image(self, content: bytes) -> Dict:
        if self.provider == "demo":
            return {"merchant_name":"DEMO MERCHANT","amount": 12.34, "date":"2025-11-05","confidence":0.76}
        if self.provider == "tesseract":
            img = Image.open(io.BytesIO(content))
            text = pytesseract.image_to_string(img)
            return {
                "raw_text": text,
                "merchant_name": text.splitlines()[0][:32] if text.strip() else "UNKNOWN",
                "amount": None, "date": None, "confidence": 0.55
            }
        return {"merchant_name":"UNKNOWN","amount": None, "date": None, "confidence": 0.0}

    def batch_ocr(self, files: List[bytes]) -> List[Dict]:
        return [self.ocr_image(b) for b in files]
