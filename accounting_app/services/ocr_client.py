import os

class OCRClient:
    """
    统一 OCR 接口占位：
    - 若 PERPLEXITY/第三方 OCR Key 未配置，则返回示例
    - 未来可接 Google Vision / Azure / Tesseract Server 等
    """
    def __init__(self):
        self.provider = os.getenv("OCR_PROVIDER", "demo")
        self.api_key = os.getenv("OCR_API_KEY", "")

    def parse(self, image_bytes: bytes) -> dict:
        if self.provider == "demo" or not self.api_key:
            return {
                "merchant_name": "DEMO MERCHANT",
                "amount": 12.34,
                "date": "2025-11-05",
                "confidence_score": 0.80
            }
        # TODO: 实接供应商
        raise NotImplementedError("OCR provider not implemented yet")
