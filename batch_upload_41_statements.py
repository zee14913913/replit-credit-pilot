#!/usr/bin/env python3
"""
批量上传 Cheok Jun Yoon 的 41 份信用卡账单
使用系统现有的 parse_statement_auto 函数（Google Document AI + 银行模板）
目标：解析率 90% 以上
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 导入现有系统的解析器
from ingest.statement_parser import parse_statement_auto
from db.database import get_db

# 配置
CUSTOMER_ID = 6  # Cheok Jun Yoon
CUSTOMER_CODE = "Be_rich_CJY"
BASE_DIR = Path("./static/uploads/customers/Be_rich_CJY/credit_cards")

# 7家银行列表（目录名 -> 数据库名, 卡号后四位）
BANKS = [
    ("AmBank", "AmBank", "6354"),
    ("AMBANK", "AmBank Islamic", "9902"),  # AmBank Islamic
    ("UOB", "UOB", "3530"),
    ("HONG_LEONG", "HONG LEONG", "3964"),
    ("OCBC", "OCBC", "3506"),
    ("HSBC", "HSBC", "0034"),
    ("STANDARD_CHARTERED", "STANDARD CHARTERED", "1237")
]

class BatchUploader:
    def __init__(self):
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'by_bank': {}
        }
        self.failed_files = []
    
    def get_card_id(self, bank_name, last4):
        """获取 card_id"""
        conn = sqlite3.connect('db/smart_loan_manager.db')
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id FROM credit_cards 
        WHERE customer_id = ? AND bank_name = ? AND card_number_last4 = ?
        """, (CUSTOMER_ID, bank_name, last4))
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None
    
    def check_existing_statement(self, card_id, statement_date):
        """检查账单是否已存在"""
        conn = sqlite3.connect('db/smart_loan_manager.db')
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, is_confirmed FROM statements 
        WHERE card_id = ? AND statement_date = ?
        """, (card_id, statement_date))
        
        row = cursor.fetchone()
        conn.close()
        
        return row
    
    def _to_float(self, value):
        """转换 Decimal 或其他数字类型为 float"""
        from decimal import Decimal
        if isinstance(value, Decimal):
            return float(value)
        elif value is None:
            return 0.0
        else:
            try:
                return float(value)
            except:
                return 0.0
    
    def save_statement(self, card_id, info, transactions, pdf_path):
        """保存账单到数据库"""
        try:
            conn = sqlite3.connect('db/smart_loan_manager.db')
            cursor = conn.cursor()
            
            # 提取字段并转换为 float
            statement_date = info.get('statement_date', '')
            total = self._to_float(info.get('total', 0))
            previous_balance = self._to_float(info.get('previous_balance', 0))
            minimum_payment = self._to_float(info.get('minimum_payment', 0))
            
            # 检查是否已存在
            existing = self.check_existing_statement(card_id, statement_date)
            
            if existing and existing[1] == 1:  # 已确认
                conn.close()
                return {'status': 'skipped', 'reason': 'already_confirmed'}
            
            if existing:
                # 更新现有记录
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
                    validation_score = 1.0,
                    file_path = ?
                WHERE id = ?
                """, (
                    total,
                    previous_balance,
                    info.get('due_date', ''),
                    total,
                    minimum_payment,
                    str(pdf_path),
                    existing[0]
                ))
                
                statement_id = existing[0]
                
                # 删除旧交易记录
                cursor.execute("DELETE FROM transactions WHERE statement_id = ?", (statement_id,))
                
            else:
                # 插入新记录
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
                    total,
                    str(pdf_path),
                    'pdf',
                    1.0,
                    1,
                    previous_balance,
                    info.get('due_date', ''),
                    total,
                    minimum_payment,
                    'success',
                    datetime.now().isoformat()
                ))
                
                statement_id = cursor.lastrowid
            
            # 保存交易记录
            for txn in transactions:
                amount = self._to_float(txn.get('amount', 0))
                cursor.execute("""
                INSERT INTO transactions (
                    statement_id,
                    transaction_date,
                    description,
                    amount,
                    category,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    statement_id,
                    txn.get('date', ''),
                    txn.get('description', ''),
                    amount,
                    'uncategorized',
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            return {'status': 'success', 'statement_id': statement_id, 'transactions': len(transactions)}
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def find_all_pdfs(self):
        """查找所有 PDF 账单"""
        pdfs = []
        
        for dir_name, db_bank_name, last4 in BANKS:
            bank_dir = BASE_DIR / dir_name
            if bank_dir.exists():
                for pdf_file in sorted(bank_dir.rglob("*.pdf")):
                    pdfs.append({
                        'path': pdf_file,
                        'dir_name': dir_name,
                        'bank': db_bank_name,
                        'last4': last4,
                        'filename': pdf_file.name
                    })
        
        return pdfs
    
    def process_all(self):
        """批量处理所有账单"""
        pdfs = self.find_all_pdfs()
        
        print("=" * 100)
        print(f"批量上传 Cheok Jun Yoon 的 {len(pdfs)} 份信用卡账单")
        print("=" * 100)
        print(f"使用系统现有解析器：Google Document AI + 银行专用模板")
        print(f"目标：解析率 90% 以上\n")
        
        for idx, pdf_info in enumerate(pdfs, 1):
            pdf_path = pdf_info['path']
            dir_name = pdf_info['dir_name']
            bank = pdf_info['bank']
            last4 = pdf_info['last4']
            filename = pdf_info['filename']
            
            print(f"\n[{idx}/{len(pdfs)}] {dir_name}/{filename}")
            print("-" * 80)
            
            # 初始化银行统计
            if bank not in self.stats['by_bank']:
                self.stats['by_bank'][bank] = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}
            
            self.stats['total'] += 1
            self.stats['by_bank'][bank]['total'] += 1
            
            # 获取 card_id
            card_id = self.get_card_id(bank, last4)
            if not card_id:
                print(f"  ❌ 找不到信用卡记录: {bank} - {last4}")
                self.stats['failed'] += 1
                self.stats['by_bank'][bank]['failed'] += 1
                self.failed_files.append({'file': str(pdf_path), 'error': f'No card found: {bank} - {last4}'})
                continue
            
            # 使用系统解析器
            print(f"  📄 解析中 (Google Document AI + 银行模板)...", end=" ", flush=True)
            
            try:
                info, transactions = parse_statement_auto(str(pdf_path))
                
                print(f"✅ 成功")
                print(f"     银行: {info.get('bank', 'N/A')}")
                print(f"     账单日期: {info.get('statement_date', 'N/A')}")
                print(f"     上期余额: RM{info.get('previous_balance', 0):.2f}")
                print(f"     本期余额: RM{info.get('total', 0):.2f}")
                print(f"     交易数量: {len(transactions)}")
                
                # 保存到数据库
                print(f"  💾 保存到数据库...", end=" ", flush=True)
                
                result = self.save_statement(card_id, info, transactions, pdf_path)
                
                if result['status'] == 'success':
                    print(f"✅ 成功 (账单ID: {result['statement_id']}, {result['transactions']} 笔交易)")
                    self.stats['success'] += 1
                    self.stats['by_bank'][bank]['success'] += 1
                    
                elif result['status'] == 'skipped':
                    print(f"⏭️  跳过 ({result['reason']})")
                    self.stats['skipped'] += 1
                    self.stats['by_bank'][bank]['skipped'] += 1
                    
                else:
                    print(f"❌ 失败 - {result.get('error', 'Unknown')}")
                    self.stats['failed'] += 1
                    self.stats['by_bank'][bank]['failed'] += 1
                    self.failed_files.append({'file': str(pdf_path), 'error': result.get('error', 'Unknown')})
                
            except Exception as e:
                print(f"❌ 解析失败 - {str(e)}")
                self.stats['failed'] += 1
                self.stats['by_bank'][bank]['failed'] += 1
                self.failed_files.append({'file': str(pdf_path), 'error': str(e)})
        
        # 生成报告
        self.print_report()
    
    def print_report(self):
        """打印最终报告"""
        print("\n" + "=" * 100)
        print("批量处理完成 - 最终报告")
        print("=" * 100)
        
        print(f"\n{'银行名称':<25} {'总账单':<10} {'成功':<10} {'失败':<10} {'跳过':<10} {'解析率':<12}")
        print("-" * 100)
        
        for _, bank, _ in BANKS:
            if bank in self.stats['by_bank']:
                stats = self.stats['by_bank'][bank]
                total = stats['total']
                success = stats['success']
                failed = stats['failed']
                skipped = stats['skipped']
                rate = (success * 100.0 / total) if total > 0 else 0.0
                
                print(f"{bank:<25} {total:<10} {success:<10} {failed:<10} {skipped:<10} {rate:>10.2f}%")
        
        print("=" * 100)
        
        total = self.stats['total']
        success = self.stats['success']
        failed = self.stats['failed']
        skipped = self.stats['skipped']
        overall_rate = (success * 100.0 / total) if total > 0 else 0.0
        
        print(f"{'总计':<25} {total:<10} {success:<10} {failed:<10} {skipped:<10} {overall_rate:>10.2f}%")
        print("=" * 100)
        
        if overall_rate >= 90:
            print("\n🎉 恭喜！解析率达到目标（>=90%）")
        elif overall_rate >= 70:
            print(f"\n⚠️  解析率 {overall_rate:.2f}% - 接近目标，建议检查失败账单")
        else:
            print(f"\n❌ 解析率 {overall_rate:.2f}% - 未达到目标，需要进一步优化")
        
        # 打印失败文件
        if self.failed_files:
            print("\n失败的文件：")
            for item in self.failed_files:
                print(f"  - {item['file']}")
                print(f"    错误: {item['error']}")

if __name__ == "__main__":
    uploader = BatchUploader()
    uploader.process_all()
