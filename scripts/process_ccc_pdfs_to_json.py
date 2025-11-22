"""
从PDF原件生成VBA格式JSON文件，然后用vba_json_processor.py处理
模拟VBA工作流程：PDF → JSON → 数据库
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

def extract_card_info_from_path(file_path):
    """从文件路径提取银行和月份信息"""
    parts = file_path.split('/')
    
    # 路径格式: .../credit_cards/Bank_Name/Month/file.pdf
    bank_name = None
    month = None
    
    for i, part in enumerate(parts):
        if part == 'credit_cards' and i + 2 < len(parts):
            bank_name = parts[i + 1].replace('_', ' ')
            month = parts[i + 2]
            break
    
    return bank_name, month

def parse_pdf_to_vba_json(pdf_path):
    """
    解析PDF文件，生成VBA标准格式的JSON
    """
    try:
        bank_name, month = extract_card_info_from_path(pdf_path)
        
        if not bank_name or not month:
            print(f"  ⚠️  无法从路径提取银行/月份: {pdf_path}")
            return None
        
        with pdfplumber.open(pdf_path) as pdf:
            # 提取所有文本
            all_text = ""
            for page in pdf.pages:
                all_text += page.extract_text() or ""
            
            # 提取表格数据
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
                        
                        # 尝试解析交易行
                        try:
                            # 查找日期模式
                            date_match = None
                            description = ""
                            amount = Decimal('0')
                            
                            for cell in row:
                                if not cell:
                                    continue
                                
                                # 日期匹配
                                if not date_match:
                                    date_patterns = [
                                        r'\d{2}[-/]\d{2}[-/]\d{4}',
                                        r'\d{2}[-/]\d{2}',
                                    ]
                                    for pattern in date_patterns:
                                        match = re.search(pattern, str(cell))
                                        if match:
                                            date_match = match.group()
                                            break
                                
                                # 金额匹配
                                amount_match = re.search(r'[\d,]+\.\d{2}', str(cell))
                                if amount_match:
                                    amount_str = amount_match.group().replace(',', '')
                                    amount = Decimal(amount_str)
                                
                                # 描述提取
                                if len(str(cell)) > 5 and not re.match(r'^[\d,\.]+$', str(cell)):
                                    description = str(cell).strip()
                            
                            if date_match and description and amount > 0:
                                # 判断是消费还是付款
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
                        
                        except Exception as e:
                            continue
            
            # 如果没有提取到交易，返回None
            if not transactions:
                print(f"  ⚠️  未提取到交易数据: {pdf_path}")
                return None
            
            # 生成VBA标准格式JSON
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
                    'statement_date': f'01-{month}',
                    'due_date': f'01-{month}',
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
                }
            }
            
            return vba_json
    
    except Exception as e:
        print(f"  ❌ 解析失败: {pdf_path} - {str(e)}")
        return None

def process_all_ccc_pdfs():
    """处理所有Chang Choon Chow的PDF文件"""
    base_dir = 'static/uploads/customers/Be_rich_CCC/credit_cards'
    
    # 查找所有PDF文件
    pdf_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    print("=" * 100)
    print(f"🔍 找到 {len(pdf_files)} 个PDF文件")
    print("=" * 100)
    
    # 创建VBA JSON处理器
    processor = VBAJSONProcessor()
    
    # 统计
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    # 处理每个PDF
    for idx, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{idx}/{len(pdf_files)}] 处理: {os.path.basename(pdf_path)}")
        
        # 解析PDF生成JSON
        vba_json = parse_pdf_to_vba_json(pdf_path)
        
        if not vba_json:
            skipped_count += 1
            continue
        
        # 使用VBA JSON处理器处理
        result = processor.process_json(vba_json, user_id=1, filename=os.path.basename(pdf_path))
        
        if result['success']:
            print(f"  ✅ 成功入库: {result.get('bank')} {result.get('month')} - {result.get('transaction_count')}笔交易")
            success_count += 1
        else:
            print(f"  ❌ 入库失败: {result['message']}")
            failed_count += 1
    
    print("\n" + "=" * 100)
    print("📊 处理完成统计")
    print("=" * 100)
    print(f"✅ 成功: {success_count}个文件")
    print(f"❌ 失败: {failed_count}个文件")
    print(f"⚠️  跳过: {skipped_count}个文件")
    print(f"📁 总计: {len(pdf_files)}个文件")
    print("=" * 100)

if __name__ == '__main__':
    print("🚀 开始处理Chang Choon Chow的PDF文件...")
    print("📋 流程: PDF → VBA格式JSON → vba_json_processor.py → 数据库")
    print("")
    process_all_ccc_pdfs()
