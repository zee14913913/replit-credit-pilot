"""
从PDF原件生成VBA格式JSON文件（修复版）
修复：正确从文件名提取月份信息
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
    """
    从文件名提取月份
    格式: Bank_Name_CardNum_YYYY-MM-DD.pdf
    例如: Hong_Leong_Bank_2033_2025-01-07.pdf → 2025-01
    """
    # 匹配 YYYY-MM-DD 或 YYYY-MM
    match = re.search(r'(\d{4})-(\d{2})', filename)
    if match:
        year = match.group(1)
        month = match.group(2)
        return f"{year}-{month}"
    return None

def parse_pdf_to_vba_json(pdf_path):
    """
    解析PDF文件，生成VBA标准格式的JSON
    """
    try:
        filename = os.path.basename(pdf_path)
        
        # 从文件名提取月份
        statement_month = extract_month_from_filename(filename)
        if not statement_month:
            print(f"  ⚠️  无法从文件名提取月份: {filename}")
            return None
        
        # 从文件名提取银行名称
        # 格式: BankName_CardNum_Date.pdf
        parts = filename.replace('.pdf', '').split('_')
        
        # 银行名称通常是前面几部分（排除纯数字部分）
        bank_parts = []
        for part in parts:
            if part.isdigit():
                break
            bank_parts.append(part)
        
        bank_name = ' '.join(bank_parts) if bank_parts else 'Unknown Bank'
        
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
                print(f"  ⚠️  未提取到交易数据: {filename}")
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
                    'statement_date': f'01-{statement_month}',
                    'due_date': f'01-{statement_month}',
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
                'statement_month': statement_month
            }
            
            return vba_json
    
    except Exception as e:
        print(f"  ❌ 解析失败: {filename} - {str(e)}")
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
    
    processed_files = []
    
    # 处理每个PDF
    for idx, pdf_path in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        print(f"\n[{idx}/{len(pdf_files)}] 处理: {filename}")
        
        # 解析PDF生成JSON
        vba_json = parse_pdf_to_vba_json(pdf_path)
        
        if not vba_json:
            skipped_count += 1
            continue
        
        # 使用VBA JSON处理器处理
        result = processor.process_json(vba_json, user_id=1, filename=filename)
        
        if result['success']:
            bank = vba_json.get('account_info', {}).get('bank', 'Unknown')
            month = vba_json.get('statement_month', 'Unknown')
            txn_count = vba_json.get('summary', {}).get('total_transactions', 0)
            
            print(f"  ✅ 成功入库: {bank} {month} - {txn_count}笔交易")
            success_count += 1
            
            processed_files.append({
                'file': filename,
                'bank': bank,
                'month': month,
                'transactions': txn_count
            })
        else:
            print(f"  ❌ 入库失败: {result['message']}")
            failed_count += 1
        
        # 每10个文件报告一次进度
        if idx % 10 == 0:
            progress = (idx / len(pdf_files)) * 100
            print(f"\n  📊 进度: {progress:.1f}% ({idx}/{len(pdf_files)})")
            print(f"  ✅ 成功: {success_count} | ❌ 失败: {failed_count} | ⚠️  跳过: {skipped_count}")
    
    print("\n" + "=" * 100)
    print("📊 处理完成统计")
    print("=" * 100)
    print(f"✅ 成功: {success_count}个文件")
    print(f"❌ 失败: {failed_count}个文件")
    print(f"⚠️  跳过: {skipped_count}个文件")
    print(f"📁 总计: {len(pdf_files)}个文件")
    print("=" * 100)
    
    # 保存处理记录
    if processed_files:
        print("\n成功处理的文件列表:")
        for pf in processed_files[:10]:  # 显示前10个
            print(f"  • {pf['file']} → {pf['bank']} {pf['month']} ({pf['transactions']}笔)")
        if len(processed_files) > 10:
            print(f"  ... 及其他 {len(processed_files) - 10} 个文件")

if __name__ == '__main__':
    print("🚀 开始处理Chang Choon Chow的PDF文件...")
    print("📋 流程: PDF → VBA格式JSON → vba_json_processor.py → 数据库")
    print("")
    process_all_ccc_pdfs()
