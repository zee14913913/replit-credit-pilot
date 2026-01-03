#!/usr/bin/env python3
"""
批量处理 Cheok Jun Yoon 的 41 份信用卡账单
使用 Google Document AI + 后处理系统
目标：解析率 90% 以上
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from google.cloud import documentai_v1 as documentai
from google.oauth2 import service_account

# 导入后处理系统
from main import StatementProcessor

# 配置
CUSTOMER_ID = 6  # Cheok Jun Yoon
CUSTOMER_CODE = "Be_rich_CJY"
BASE_DIR = Path("./static/uploads/customers/Be_rich_CJY/credit_cards")

# Google Document AI 配置
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_LOCATION", "us")
PROCESSOR_ID = os.getenv("GOOGLE_PROCESSOR_ID")
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

# 7家银行列表
BANKS = [
    "AmBank",
    "AMBANK",  # AmBank Islamic
    "UOB",
    "HONG_LEONG",
    "OCBC",
    "HSBC",
    "STANDARD_CHARTERED"
]

class BatchStatementProcessor:
    def __init__(self):
        self.processor = StatementProcessor()
        self.doc_ai_client = self._init_document_ai()
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'by_bank': {}
        }
    
    def _init_document_ai(self):
        """初始化 Document AI 客户端"""
        try:
            credentials_dict = json.loads(SERVICE_ACCOUNT_JSON)
            credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            client = documentai.DocumentProcessorServiceClient(credentials=credentials)
            return client
        except Exception as e:
            print(f"❌ Document AI 初始化失败: {e}")
            return None
    
    def parse_pdf_with_document_ai(self, pdf_path):
        """使用 Document AI 解析 PDF"""
        if not self.doc_ai_client:
            return None
        
        try:
            # 读取 PDF
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # 构造请求
            name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"
            
            raw_document = documentai.RawDocument(
                content=pdf_content,
                mime_type="application/pdf"
            )
            
            request = documentai.ProcessRequest(
                name=name,
                raw_document=raw_document
            )
            
            # 调用 Document AI
            result = self.doc_ai_client.process_document(request=request)
            document = result.document
            
            # 转换为 JSON 格式
            doc_ai_json = {
                "text": document.text,
                "entities": []
            }
            
            for entity in document.entities:
                entity_dict = {
                    "type": entity.type_,
                    "mentionText": entity.mention_text,
                    "confidence": entity.confidence
                }
                
                # 处理嵌套属性
                if entity.properties:
                    entity_dict["properties"] = [
                        {
                            "type": prop.type_,
                            "mentionText": prop.mention_text
                        }
                        for prop in entity.properties
                    ]
                
                doc_ai_json["entities"].append(entity_dict)
            
            return doc_ai_json
            
        except Exception as e:
            print(f"  ❌ Document AI 解析失败: {e}")
            return None
    
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
        # 例如：AMBANK_9902_2025-05-28.pdf -> 9902
        parts = filename.split('_')
        if len(parts) >= 2:
            return parts[1]
        return None
    
    def save_to_database(self, result, card_id, pdf_path):
        """保存解析结果到数据库"""
        try:
            conn = sqlite3.connect('db/smart_loan_manager.db')
            cursor = conn.cursor()
            
            # 检查是否已存在
            statement_date = result.get('statement_date', '')
            
            cursor.execute("""
            SELECT id FROM statements 
            WHERE card_id = ? AND statement_date = ?
            """, (card_id, statement_date))
            
            existing = cursor.fetchone()
            
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
                    txn.get('transaction_description', ''),
                    txn.get('amount_DR', 0) - txn.get('amount_CR', 0),
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
        print(f"使用 Google Document AI + 后处理系统")
        print(f"目标：解析率 90% 以上\n")
        
        for idx, pdf_info in enumerate(pdfs, 1):
            pdf_path = pdf_info['path']
            bank = pdf_info['bank']
            filename = pdf_info['filename']
            
            print(f"\n[{idx}/{len(pdfs)}] 处理: {bank}/{filename}")
            print("-" * 80)
            
            # 初始化银行统计
            if bank not in self.stats['by_bank']:
                self.stats['by_bank'][bank] = {'total': 0, 'success': 0, 'failed': 0}
            
            self.stats['total'] += 1
            self.stats['by_bank'][bank]['total'] += 1
            
            # 步骤1：Document AI 解析
            print("  步骤1: Document AI 解析...", end=" ")
            doc_ai_json = self.parse_pdf_with_document_ai(pdf_path)
            
            if not doc_ai_json:
                print("失败 ❌")
                self.stats['failed'] += 1
                self.stats['by_bank'][bank]['failed'] += 1
                continue
            
            print(f"成功 ✅ (提取了 {len(doc_ai_json.get('entities', []))} 个实体)")
            
            # 步骤2：后处理系统
            print("  步骤2: 后处理 (16字段提取 + CR/DR修正 + 余额验证)...", end=" ")
            
            try:
                result = self.processor.process(doc_ai_json)
                
                # 显示提取结果
                print("成功 ✅")
                print(f"    - 银行: {result.get('bank_name', 'N/A')}")
                print(f"    - 客户: {result.get('customer_name', 'N/A')}")
                print(f"    - 账单日期: {result.get('statement_date', 'N/A')}")
                print(f"    - 上期余额: RM{result.get('previous_balance', 0):.2f}")
                print(f"    - 本期余额: RM{result.get('current_balance', 0):.2f}")
                print(f"    - 交易数量: {len(result.get('transactions', []))}")
                print(f"    - 余额验证: {result.get('balance_verification', {}).get('status', 'N/A')}")
                
            except Exception as e:
                print(f"失败 ❌ - {e}")
                self.stats['failed'] += 1
                self.stats['by_bank'][bank]['failed'] += 1
                continue
            
            # 步骤3：保存到数据库
            print("  步骤3: 保存到数据库...", end=" ")
            
            # 获取 card_id
            last4 = self.extract_last4_from_filename(filename)
            card_id = self.get_card_id(bank, last4)
            
            if not card_id:
                print(f"失败 ❌ (找不到卡片: {bank} - {last4})")
                self.stats['failed'] += 1
                self.stats['by_bank'][bank]['failed'] += 1
                continue
            
            if self.save_to_database(result, card_id, pdf_path):
                print("成功 ✅")
                self.stats['success'] += 1
                self.stats['by_bank'][bank]['success'] += 1
            else:
                print("失败 ❌")
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
        
        if overall_rate >= 90:
            print("\n🎉 恭喜！解析率达到目标（>=90%）")
        elif overall_rate >= 70:
            print(f"\n⚠️ 解析率 {overall_rate:.2f}% - 接近目标，建议检查失败账单")
        else:
            print(f"\n❌ 解析率 {overall_rate:.2f}% - 未达到目标，需要进一步优化")

if __name__ == "__main__":
    processor = BatchStatementProcessor()
    processor.process_all()
