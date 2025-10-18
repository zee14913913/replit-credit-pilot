"""
CTOS报告解析器
自动提取月度负债承诺（Monthly Commitment）
"""

import re
try:
    from PyPDF2 import PdfReader
except ImportError:
    import pdfplumber
    PdfReader = None

def extract_commitment_from_ctos(pdf_path):
    """
    从CTOS PDF报告中提取月度负债总额
    
    Args:
        pdf_path: CTOS PDF文件路径
        
    Returns:
        (amount, notes) - 金额和提取说明
    """
    try:
        # 尝试使用PyPDF2
        if PdfReader:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        else:
            # Fallback到pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
        
        # 多种模式匹配CTOS中的commitment字段
        patterns = [
            r"Total\s*Monthly\s*(Commitment|Installment)\s*[:：]?\s*RM?\s*([\d,]+\.?\d*)",
            r"Monthly\s*Commitment\s*[:：]?\s*RM?\s*([\d,]+\.?\d*)",
            r"Total\s*Commitments?\s*[:：]?\s*RM?\s*([\d,]+\.?\d*)",
            r"Total\s*Debt\s*Service\s*[:：]?\s*RM?\s*([\d,]+\.?\d*)",
        ]
        
        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                amt = m.groups()[-1]
                amt = float(amt.replace(",", ""))
                return amt, "✅ CTOS自动解析成功"
        
        return 0.0, "⚠️ 未在CTOS中找到commitment字段，已默认0，请人工覆盖"
    
    except Exception as e:
        return 0.0, f"❌ CTOS解析异常：{str(e)}"
