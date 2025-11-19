import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_document_ai_service import GoogleDocumentAIService

# 找到STANDARD_CHARTERED的PDF
files = []
for root, dirs, filenames in os.walk('static/uploads/customers'):
    for f in filenames:
        if 'STANDARD' in f.upper() and f.endswith('.pdf'):
            files.append(os.path.join(root, f))
            break
    if files:
        break

if files:
    print(f"\n=== STANDARD_CHARTERED PDF: {files[0]} ===")
    service = GoogleDocumentAIService()
    result = service.parse_pdf(files[0])
    text = result['text']
    lines = text.split('\n')
    print(f"\n总行数: {len(lines)}")
    print("\n前200行:")
    for i, line in enumerate(lines[:200], 1):
        print(f"{i:3d}: {line}")
else:
    print("找不到STANDARD_CHARTERED的PDF")
