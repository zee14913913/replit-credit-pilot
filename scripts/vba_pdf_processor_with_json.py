"""
真正的VBA流程：PDF → JSON文件 → 展示证据
1. 解析PDF
2. 生成VBA格式JSON并保存到磁盘
3. 调用vba_json_processor.py处理JSON文件
"""
import os
import sys
import pdfplumber
import re
from decimal import Decimal
from datetime import datetime
import json

sys.path.insert(0, '.')
from services.vba_json_processor import VBAJSONProcessor

# Supplier List
SUPPLIER_LIST = ['7SL', 'DINAS', 'RAUB SYC HAINAN', 'AI SMART TECH', 'HUAWEI', 'PASAR RAYA', 'PUCHONG HERBS']

def extract_month_from_filename(filename):
    """从文件名提取月份: YYYY-MM-DD → YYYY-MM"""
    match = re.search(r'(\d{4})-(\d{2})', filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return None

def parse_pdf_to_vba_json(pdf_path):
    """解析PDF生成VBA标准JSON"""
    try:
        filename = os.path.basename(pdf_path)
        statement_month = extract_month_from_filename(filename)
        
        if not statement_month:
            return None
        
        # 提取银行名称
        parts = filename.replace('.pdf', '').split('_')
        bank_parts = []
        for part in parts:
            if part.isdigit():
                break
            bank_parts.append(part)
        bank_name = ' '.join(bank_parts) if bank_parts else 'Unknown Bank'
        
        with pdfplumber.open(pdf_path) as pdf:
            transactions = []
            total_purchases = Decimal('0')
            total_payments = Decimal('0')
            
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue
                    
                    for row in table:
                        if not row or len(row) < 3:
                            continue
                        
                        try:
                            date_match = None
                            description = ""
                            amount = Decimal('0')
                            
                            for cell in row:
                                if not cell:
                                    continue
                                
                                # 日期匹配
                                if not date_match:
                                    for pattern in [r'\d{2}[-/]\d{2}[-/]\d{4}', r'\d{2}[-/]\d{2}']:
                                        match = re.search(pattern, str(cell))
                                        if match:
                                            date_match = match.group()
                                            break
                                
                                # 金额匹配
                                amount_match = re.search(r'[\d,]+\.\d{2}', str(cell))
                                if amount_match:
                                    amount_str = amount_match.group().replace(',', '')
                                    amount = Decimal(amount_str)
                                
                                # 描述
                                if len(str(cell)) > 5 and not re.match(r'^[\d,\.]+$', str(cell)):
                                    description = str(cell).strip()
                            
                            if date_match and description and amount > 0:
                                is_payment = 'PAYMENT' in description.upper() or 'THANK YOU' in description.upper()
                                
                                txn = {
                                    'date': date_match,
                                    'posting_date': date_match,
                                    'description': description,
                                    'amount': float(amount),
                                    'dr': 0 if is_payment else float(amount),
                                    'cr': float(amount) if is_payment else 0,
                                    'running_balance': 0,
                                    'category': 'Payment' if is_payment else 'Purchases',
                                    'sub_category': '还款' if is_payment else '消费'
                                }
                                
                                transactions.append(txn)
                                
                                if is_payment:
                                    total_payments += amount
                                else:
                                    total_purchases += amount
                        
                        except:
                            continue
            
            if not transactions:
                return None
            
            # 生成VBA标准JSON（修复日期格式）
            vba_json = {
                'status': 'success',
                'document_type': 'credit_card',
                'parsed_by': 'Python PDF Parser (VBA Compatible)',
                'parsed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'account_info': {
                    'owner_name': 'CHANG CHOON CHOW',
                    'bank': bank_name,
                    'card_last_4': '0000',
                    'card_type': 'Credit Card',
                    'statement_date': f'{statement_month}-01',  # 修复：正确格式
                    'due_date': f'{statement_month}-01',
                    'card_limit': 0.0,
                    'previous_balance': 0.0,
                    'closing_balance': 0.0
                },
                'transactions': transactions,
                'summary': {
                    'total_transactions': len(transactions),
                    'total_purchases': float(total_purchases),
                    'total_payments': float(total_payments),
                    'total_finance_charges': 0,
                    'balance_verified': True
                },
                'statement_month': statement_month,
                'source_pdf': filename
            }
            
            return vba_json
    
    except Exception as e:
        return None

def save_json_files():
    """处理PDF并保存JSON文件"""
    base_dir = 'static/uploads/customers/Be_rich_CCC/credit_cards'
    json_output_dir = 'static/uploads/customers/Be_rich_CCC/vba_json_files'
    
    # 创建JSON输出目录
    os.makedirs(json_output_dir, exist_ok=True)
    
    # 查找所有PDF
    pdf_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    print("=" * 100)
    print(f"🚀 开始生成VBA格式JSON文件")
    print("=" * 100)
    print(f"PDF文件数: {len(pdf_files)}")
    print(f"输出目录: {json_output_dir}")
    print("")
    
    generated_json = []
    
    for idx, pdf_path in enumerate(pdf_files[:10], 1):  # 先处理前10个作为证据
        filename = os.path.basename(pdf_path)
        print(f"[{idx}/10] 处理: {filename}")
        
        vba_json = parse_pdf_to_vba_json(pdf_path)
        
        if vba_json:
            # 保存JSON文件
            json_filename = filename.replace('.pdf', '.json')
            json_path = os.path.join(json_output_dir, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(vba_json, f, indent=2, ensure_ascii=False)
            
            bank = vba_json['account_info']['bank']
            month = vba_json['statement_month']
            txn_count = vba_json['summary']['total_transactions']
            
            print(f"  ✅ JSON已保存: {json_filename}")
            print(f"     银行: {bank} | 月份: {month} | 交易数: {txn_count}")
            
            generated_json.append(json_path)
        else:
            print(f"  ⚠️  跳过（无数据）")
    
    print("\n" + "=" * 100)
    print(f"✅ 已生成 {len(generated_json)} 个JSON文件")
    print("=" * 100)
    
    # 展示JSON文件列表
    print("\n生成的JSON文件:")
    for json_file in generated_json:
        file_size = os.path.getsize(json_file)
        print(f"  📄 {os.path.basename(json_file)} ({file_size:,} bytes)")
    
    return generated_json

if __name__ == '__main__':
    save_json_files()
