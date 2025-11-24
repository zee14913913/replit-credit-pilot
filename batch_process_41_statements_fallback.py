
#!/usr/bin/env python3
"""
批量处理 Cheok Jun Yoon 的 41 份信用卡账单
使用免费 Fallback Parser（无需 Google Document AI）
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# 导入 Fallback Parser
from services.fallback_parser import parse_statement_fallback

# 配置
CUSTOMER_ID = 6  # Cheok Jun Yoon
CUSTOMER_CODE = "Be_rich_CJY"
BASE_DIR = Path("./static/uploads/customers/Be_rich_CJY/credit_cards")

# 7家银行列表
BANKS = [
    "AMBANK",
    "AmBank",  # AmBank Islamic
    "UOB",
    "HONG_LEONG",
    "OCBC",
    "HSBC",
    "STANDARD_CHARTERED"
]


class BatchStatementProcessor:
    def __init__(self):
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'by_bank': {}
        }
    
    def find_all_pdfs(self):
        """查找所有 PDF 账单"""
        pdfs = []
        
        for bank in BANKS:
            bank_dir = BASE_DIR / bank
            if bank_dir.exists():
                for pdf_file in bank_dir.rglob("*.pdf"):
                    pdfs.append({
                        'path': pdf_file,
                        'bank': bank,
                        'filename': pdf_file.name
                    })
        
        return sorted(pdfs, key=lambda x: (x['bank'], x['filename']))
    
    def get_card_id(self, bank_name, last4):
        """根据银行和卡号后四位获取 card_id"""
        conn = sqlite3.connect('db/smart_loan_manager.db')
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id FROM credit_cards 
        WHERE customer_id = ? AND bank_name = ? AND card_number_last4 = ?
        """, (CUSTOMER_ID, bank_name, last4))
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None
    
    def extract_last4_from_filename(self, filename):
        """从文件名提取卡号后四位"""
        parts = filename.split('_')
        if len(parts) >= 2:
            return parts[1]
        return None
    
    def save_to_database(self, result, card_id, pdf_path):
        """保存解析结果到数据库"""
        try:
            conn = sqlite3.connect('db/smart_loan_manager.db')
            cursor = conn.cursor()
            
            statement_date = result.get('statement_date', '')
            
            cursor.execute("""
            SELECT id FROM statements 
            WHERE card_id = ? AND statement_date = ?
            """, (card_id, statement_date))
            
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                UPDATE statements 
                SET 
                    statement_total = ?,
                    previous_balance = ?,
                    due_date = ?,
                    due_amount = ?,
                    minimum_payment = ?,
                    is_confirmed = 1,
                    upload_status = 'success',
                    validation_score = 1.0
                WHERE id = ?
                """, (
                    result.get('current_balance', 0),
                    result.get('previous_balance', 0),
                    result.get('payment_due_date', ''),
                    result.get('current_balance', 0),
                    result.get('minimum_payment', 0),
                    existing[0]
                ))
                
                statement_id = existing[0]
            else:
                cursor.execute("""
                INSERT INTO statements (
                    card_id,
                    statement_date,
                    statement_total,
                    file_path,
                    file_type,
                    validation_score,
                    is_confirmed,
                    previous_balance,
                    due_date,
                    due_amount,
                    minimum_payment,
                    upload_status,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    card_id,
                    statement_date,
                    result.get('current_balance', 0),
                    str(pdf_path),
                    'pdf',
                    1.0,
                    1,
                    result.get('previous_balance', 0),
                    result.get('payment_due_date', ''),
                    result.get('current_balance', 0),
                    result.get('minimum_payment', 0),
                    'success',
                    datetime.now().isoformat()
                ))
                
                statement_id = cursor.lastrowid
            
            # 保存交易记录
            for txn in result.get('transactions', []):
                cursor.execute("""
                INSERT OR REPLACE INTO transactions (
                    statement_id,
                    transaction_date,
                    description,
                    amount,
                    category,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    statement_id,
                    txn.get('transaction_date', ''),
                    txn.get('description', ''),
                    txn.get('amount', 0),
                    'uncategorized',
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"  ❌ 数据库保存失败: {e}")
            return False
    
    def process_all(self):
        """批量处理所有账单"""
        pdfs = self.find_all_pdfs()
        
        print("=" * 100)
        print(f"批量处理 Cheok Jun Yoon 的 {len(pdfs)} 份信用卡账单")
        print("=" * 100)
        print(f"使用免费 Fallback Parser（无需 Google Document AI）\n")
        
        for idx, pdf_info in enumerate(pdfs, 1):
            pdf_path = pdf_info['path']
            bank = pdf_info['bank']
            filename = pdf_info['filename']
            
            print(f"\n[{idx}/{len(pdfs)}] 处理: {bank}/{filename}")
            print("-" * 80)
            
            if bank not in self.stats['by_bank']:
                self.stats['by_bank'][bank] = {'total': 0, 'success': 0, 'failed': 0}
            
            self.stats['total'] += 1
            self.stats['by_bank'][bank]['total'] += 1
            
            # 使用 Fallback Parser 解析
            print("  步骤1: Fallback Parser 解析...", end=" ")
            
            try:
                info, transactions = parse_statement_fallback(str(pdf_path))
                
                print(f"成功 ✅ (提取了 {len(transactions)} 笔交易)")
                
                # 显示提取结果
                print(f"    - 银行: {info.get('bank_name', 'N/A')}")
                print(f"    - 客户: {info.get('customer_name', 'N/A')}")
                print(f"    - 账单日期: {info.get('statement_date', 'N/A')}")
                print(f"    - 本期余额: RM{info.get('current_balance', 0):.2f}")
                print(f"    - 交易数量: {len(transactions)}")
                
                # 保存到数据库
                print("  步骤2: 保存到数据库...", end=" ")
                
                last4 = self.extract_last4_from_filename(filename)
                card_id = self.get_card_id(bank, last4)
                
                if not card_id:
                    print(f"失败 ❌ (找不到卡片: {bank} - {last4})")
                    self.stats['failed'] += 1
                    self.stats['by_bank'][bank]['failed'] += 1
                    continue
                
                # 准备结果数据
                result = {
                    'statement_date': info.get('statement_date', ''),
                    'current_balance': info.get('current_balance', 0),
                    'previous_balance': info.get('previous_balance', 0),
                    'payment_due_date': info.get('payment_due_date', ''),
                    'minimum_payment': info.get('minimum_payment', 0),
                    'transactions': transactions
                }
                
                if self.save_to_database(result, card_id, pdf_path):
                    print("成功 ✅")
                    self.stats['success'] += 1
                    self.stats['by_bank'][bank]['success'] += 1
                else:
                    print("失败 ❌")
                    self.stats['failed'] += 1
                    self.stats['by_bank'][bank]['failed'] += 1
                
            except Exception as e:
                print(f"失败 ❌ - {e}")
                self.stats['failed'] += 1
                self.stats['by_bank'][bank]['failed'] += 1
        
        # 生成报告
        self.print_report()
    
    def print_report(self):
        """打印最终报告"""
        print("\n" + "=" * 100)
        print("批量处理完成 - 最终报告")
        print("=" * 100)
        
        print(f"\n{'银行名称':<25} {'总账单':<10} {'成功':<10} {'失败':<10} {'解析率':<12}")
        print("-" * 100)
        
        for bank in BANKS:
            if bank in self.stats['by_bank']:
                stats = self.stats['by_bank'][bank]
                total = stats['total']
                success = stats['success']
                failed = stats['failed']
                rate = (success * 100.0 / total) if total > 0 else 0.0
                
                print(f"{bank:<25} {total:<10} {success:<10} {failed:<10} {rate:>10.2f}%")
        
        print("=" * 100)
        
        total = self.stats['total']
        success = self.stats['success']
        failed = self.stats['failed']
        overall_rate = (success * 100.0 / total) if total > 0 else 0.0
        
        print(f"{'总计':<25} {total:<10} {success:<10} {failed:<10} {overall_rate:>10.2f}%")
        print("=" * 100)
        
        # 保存报告
        report_path = 'reports/fallback_parser_report.json'
        os.makedirs('reports', exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'parser': 'Fallback Parser (Free)',
                'google_ai_used': False,
                'total_statements': total,
                'success': success,
                'failed': failed,
                'success_rate': overall_rate,
                'by_bank': self.stats['by_bank']
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 详细报告已保存: {report_path}")
        
        if overall_rate >= 90:
            print("\n🎉 恭喜！解析率达到目标（>=90%）")
        elif overall_rate >= 70:
            print(f"\n⚠️ 解析率 {overall_rate:.2f}% - 接近目标")
        else:
            print(f"\n❌ 解析率 {overall_rate:.2f}% - 需要手动校对")


if __name__ == "__main__":
    print("🆓 使用免费 Fallback Parser（完全停用 Google Document AI）\n")
    processor = BatchStatementProcessor()
    processor.process_all()
