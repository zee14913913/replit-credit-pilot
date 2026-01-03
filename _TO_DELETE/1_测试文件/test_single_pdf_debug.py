#!/usr/bin/env python3
"""调试单个PDF上传，查看完整响应"""
import requests

BASE_URL = "http://localhost:8000"

with open('test_pdfs/PDF-1-Normal-HongLeong-May2025.pdf', 'rb') as f:
    pdf_content = f.read()

files = {'file': ('test.pdf', pdf_content, 'application/pdf')}

response = requests.post(
    f"{BASE_URL}/api/v2/import/bank-statement?company_id=1",
    files=files,
    timeout=60
)

print("="*80)
print(f"HTTP Status: {response.status_code}")
print("="*80)
print(f"Headers: {dict(response.headers)}")
print("="*80)
print(f"Response Text:\n{response.text}")
print("="*80)
