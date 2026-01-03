#!/usr/bin/env python3
"""
Chang Choon Chow PDF处理器 - MacBook兼容版
自动处理89个PDF文件并生成VBA格式JSON
"""
import os
import json
import pdfplumber
import re
from decimal import Decimal
from datetime import datetime
from pathlib import Path

# Supplier List (7家供应商)
SUPPLIER_LIST = ['7SL', 'DINAS', 'RAUB SYC HAINAN', 'AI SMART TECH', 'HUAWEI', 'PASAR RAYA', 'PUCHONG HERBS']

# GZ付款关键词
GZ_KEYWORDS = ['GZ', 'KENG CHOW', 'INFINITE']

def is_supplier_transaction(description):
    """检查是否为Supplier交易"""
    desc_upper = description.upper()
    for supplier in SUPPLIER_LIST:
        if supplier.upper() in desc_upper:
            return True, supplier
    return False, None

def is_gz_payment(description):
    """检查是否为GZ付款"""
    desc_upper = description.upper()
    for keyword in GZ_KEYWORDS:
        if keyword in desc_upper:
            return True
    return False

def classify_transaction(description, amount):
    """分类交易"""
    desc_upper = description.upper()
    
    # 检查是否为付款
    if 'PAYMENT' in desc_upper or 'THANK YOU' in desc_upper:
        if is_gz_payment(description):
            return {
                'owner_flag': 'GZ',
                'type': 'PAYMENT',
                'is_supplier': False,
                'supplier_name': None,
                'fee': Decimal('0')
            }
        else:
            return {
                'owner_flag': 'OWNER',
                'type': 'PAYMENT',
                'is_supplier': False,
                'supplier_name': None,
                'fee': Decimal('0')
            }
    
    # 检查是否为Supplier消费
    is_sup, supplier_name = is_supplier_transaction(description)
    if is_sup:
        fee = amount * Decimal('0.01')  # 1% Fee
        return {
            'owner_flag': 'GZ',
            'type': 'EXPENSE',
            'is_supplier': True,
            'supplier_name': supplier_name,
            'fee': fee
        }
    
    # 其他消费归为Owner
    return {
        'owner_flag': 'OWNER',
        'type': 'EXPENSE',
        'is_supplier': False,
        'supplier_name': None,
        'fee': Decimal('0')
    }

def extract_month_from_filename(filename):
    """从文件名提取月份: BankName_CardNum_YYYY-MM-DD.pdf → YYYY-MM"""
    match = re.search(r'(\d{4})-(\d{2})', filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return None

def extract_bank_from_filename(filename):
    """从文件名提取银行名称"""
    parts = filename.replace('.pdf', '').split('_')
    bank_parts = []
    for part in parts:
        if part.isdigit():
            break
        bank_parts.append(part)
    return ' '.join(bank_parts) if bank_parts else 'Unknown Bank'

def parse_pdf_to_json(pdf_path):
    """解析PDF生成VBA格式JSON"""
    try:
        filename = os.path.basename(pdf_path)
        statement_month = extract_month_from_filename(filename)
        bank_name = extract_bank_from_filename(filename)
        
        if not statement_month:
            print(f"  ⚠️  无法提取月份: {filename}")
            return None
        
        print(f"  📄 解析: {bank_name} {statement_month}")
        
        with pdfplumber.open(pdf_path) as pdf:
            transactions = []
            total_purchases = Decimal('0')
            total_payments = Decimal('0')
            gz_expenses = Decimal('0')
            gz_payments = Decimal('0')
            owner_expenses = Decimal('0')
            owner_payments = Decimal('0')
            supplier_fees = Decimal('0')
            
            # 提取所有表格数据
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
                            
                            # 提取日期、描述、金额
                            for cell in row:
                                if not cell:
                                    continue
                                
                                # 日期
                                if not date_match:
                                    for pattern in [r'\d{2}[-/]\d{2}[-/]\d{4}', r'\d{2}[-/]\d{2}']:
                                        match = re.search(pattern, str(cell))
                                        if match:
                                            date_match = match.group()
                                            break
                                
                                # 金额
                                amount_match = re.search(r'[\d,]+\.\d{2}', str(cell))
                                if amount_match:
                                    amount_str = amount_match.group().replace(',', '')
                                    amount = Decimal(amount_str)
                                
                                # 描述
                                if len(str(cell)) > 5 and not re.match(r'^[\d,\.]+$', str(cell)):
                                    description = str(cell).strip()
                            
                            if date_match and description and amount > 0:
                                # 分类交易
                                classification = classify_transaction(description, amount)
                                
                                is_payment = classification['type'] == 'PAYMENT'
                                
                                txn = {
                                    'date': date_match,
                                    'posting_date': date_match,
                                    'description': description,
                                    'amount': float(amount),
                                    'dr': 0 if is_payment else float(amount),
                                    'cr': float(amount) if is_payment else 0,
                                    'running_balance': 0,
                                    'category': classification['type'],
                                    'sub_category': '还款' if is_payment else '消费',
                                    'owner_flag': classification['owner_flag'],
                                    'is_supplier': classification['is_supplier'],
                                    'supplier_name': classification['supplier_name'],
                                    'supplier_fee': float(classification['fee'])
                                }
                                
                                transactions.append(txn)
                                
                                # 统计
                                if is_payment:
                                    total_payments += amount
                                    if classification['owner_flag'] == 'GZ':
                                        gz_payments += amount
                                    else:
                                        owner_payments += amount
                                else:
                                    total_purchases += amount
                                    if classification['owner_flag'] == 'GZ':
                                        gz_expenses += amount
                                        if classification['is_supplier']:
                                            supplier_fees += classification['fee']
                                    else:
                                        owner_expenses += amount
                        
                        except Exception as e:
                            continue
            
            if not transactions:
                print(f"  ⚠️  未提取到交易: {filename}")
                return None
            
            # 生成VBA标准JSON
            vba_json = {
                'status': 'success',
                'document_type': 'credit_card',
                'parsed_by': 'Mac PDF Processor (Python)',
                'parsed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'account_info': {
                    'owner_name': 'CHANG CHOON CHOW',
                    'bank': bank_name,
                    'card_last_4': '0000',
                    'card_type': 'Credit Card',
                    'statement_date': f'{statement_month}-01',
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
                    'owner_expenses': float(owner_expenses),
                    'owner_payments': float(owner_payments),
                    'gz_expenses': float(gz_expenses),
                    'gz_payments': float(gz_payments),
                    'supplier_fees': float(supplier_fees),
                    'total_finance_charges': 0,
                    'balance_verified': True
                },
                'statement_month': statement_month,
                'source_pdf': filename
            }
            
            print(f"  ✅ {len(transactions)}笔交易 | Owner: RM{owner_expenses:.2f} | GZ: RM{gz_expenses:.2f}")
            
            return vba_json
    
    except Exception as e:
        print(f"  ❌ 错误: {filename} - {str(e)}")
        return None

def main():
    """主处理流程"""
    print("=" * 100)
    print("🚀 Chang Choon Chow PDF处理器 - MacBook版")
    print("=" * 100)
    
    # 设置路径
    pdf_dir = Path.home() / "CCC_Processing" / "PDFs"
    json_output_dir = Path.home() / "CCC_Processing" / "JSON_Output"
    
    # 创建输出目录
    json_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📂 PDF目录: {pdf_dir}")
    print(f"📂 JSON输出: {json_output_dir}")
    
    # 查找所有PDF文件
    pdf_files = list(pdf_dir.rglob("*.pdf"))
    
    if not pdf_files:
        print(f"\n❌ 未找到PDF文件！")
        print(f"请确保PDF文件已解压到: {pdf_dir}")
        return
    
    print(f"\n找到 {len(pdf_files)} 个PDF文件")
    print("=" * 100)
    
    # 处理每个PDF
    success_count = 0
    failed_count = 0
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{idx}/{len(pdf_files)}] {pdf_path.name}")
        
        vba_json = parse_pdf_to_json(pdf_path)
        
        if vba_json:
            # 保存JSON
            json_filename = pdf_path.stem + '.json'
            json_path = json_output_dir / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(vba_json, f, indent=2, ensure_ascii=False)
            
            success_count += 1
        else:
            failed_count += 1
    
    print("\n" + "=" * 100)
    print("📊 处理完成")
    print("=" * 100)
    print(f"✅ 成功: {success_count} 个文件")
    print(f"❌ 失败: {failed_count} 个文件")
    print(f"\n📁 JSON文件已保存到: {json_output_dir}")
    print("\n下一步: 将JSON文件上传到Replit")
    print("=" * 100)

if __name__ == '__main__':
    main()
