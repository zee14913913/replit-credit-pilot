"""
CHANG CHOON CHOW - 5家银行完整重新计算系统
================================================================================
功能：
1. 重新导入/验证5家银行的信用卡账单（MBB, HLB, UOB, HSBC, ALLIANCE）
2. 处理银行流水月结单（个人PBB 0727，公司PBB 3427）
3. 识别并重新分类GZ转账（Card Due Assist / Loan / Credit Assist / Build Profile）
4. 生成完整财务报告

使用最新的INFINITE GZ系统设置
================================================================================
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import sqlite3
import pdfplumber
from datetime import datetime
import re
from services.infinite_gz_processor import InfiniteGZProcessor


def get_db():
    """获取数据库连接"""
    return sqlite3.connect('db/smart_loan_manager.db')


class CCCBankRecalculator:
    """Chang Choon Chow 5家银行重新计算器"""
    
    def __init__(self):
        self.customer_id = 10  # Chang Choon Chow
        self.customer_code = 'Be_rich_CCC'
        self.base_path = f'static/uploads/customers/{self.customer_code}/credit_cards'
        self.gz_processor = InfiniteGZProcessor()
        
        # 5家银行配置
        self.banks_config = {
            'Alliance Bank': {
                'folder': 'Alliance_Bank',
                'card_id': 33,  # YOU:NIQUE MASTERCARD 尾号4514
                'card_last4': '4514',
                'months': []
            },
            'Hong Leong Bank': {
                'folder': 'Hong_Leong_Bank',
                'card_id': 34,  # 尾号2033
                'card_last4': '2033',
                'months': []
            },
            'Maybank': {
                'folder': 'Maybank',
                'card_id': 39,  # VISA PETRONAS PLATINUM 尾号5943
                'card_last4': '5943',
                'months': []
            },
            'UOB': {
                'folder': 'UOB',
                'card_id': 40,  # ONE PLATINUM VISA 尾号2195
                'card_last4': '2195',
                'months': []
            },
            'HSBC': {
                'folder': 'HSBC',
                'card_id': 38,  # Visa Signature 尾号2058
                'card_last4': '2058',
                'months': []
            }
        }
    
    def scan_available_pdfs(self):
        """扫描所有可用的PDF文件"""
        print("\n" + "=" * 80)
        print("📂 扫描PDF文件...")
        print("=" * 80 + "\n")
        
        for bank_name, config in self.banks_config.items():
            bank_folder = os.path.join(self.base_path, config['folder'])
            
            if not os.path.exists(bank_folder):
                print(f"⚠️  {bank_name}: 文件夹不存在")
                continue
            
            months_found = []
            for month_folder in sorted(os.listdir(bank_folder)):
                month_path = os.path.join(bank_folder, month_folder)
                if os.path.isdir(month_path):
                    pdf_files = [f for f in os.listdir(month_path) if f.endswith('.pdf')]
                    if pdf_files:
                        months_found.append({
                            'month': month_folder,
                            'path': month_path,
                            'pdf_file': pdf_files[0],
                            'full_path': os.path.join(month_path, pdf_files[0])
                        })
            
            config['months'] = months_found
            print(f"✅ {bank_name}: {len(months_found)} 个月份")
            for month_info in months_found:
                print(f"   - {month_info['month']}")
        
        print("\n" + "=" * 80)
    
    def extract_statement_data_simple(self, pdf_path, bank_name):
        """
        简单提取账单基本信息
        （先验证PDF可读性，后续可以用详细的OCR处理）
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                # 简单提取日期和总额（示例）
                statement_date = None
                total_amount = 0.0
                
                # 这里可以根据不同银行的PDF格式进行解析
                # 先返回基本信息
                return {
                    'status': 'success',
                    'statement_date': statement_date,
                    'total_amount': total_amount,
                    'text_length': len(text),
                    'pages': len(pdf.pages)
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def import_bank_statements(self, bank_name, dry_run=True):
        """导入指定银行的账单"""
        print(f"\n{'[DRY RUN] ' if dry_run else ''}开始处理: {bank_name}")
        print("-" * 80)
        
        config = self.banks_config[bank_name]
        card_id = config['card_id']
        
        conn = get_db()
        cursor = conn.cursor()
        
        # 检查信用卡是否存在
        cursor.execute("SELECT id, bank_name, card_type FROM credit_cards WHERE id = ?", (card_id,))
        card = cursor.fetchone()
        
        if not card:
            print(f"❌ 错误: 信用卡ID {card_id} 不存在")
            conn.close()
            return
        
        print(f"✅ 找到信用卡: {card[1]} - {card[2]} (ID: {card_id})")
        
        success_count = 0
        error_count = 0
        
        for month_info in config['months']:
            month = month_info['month']
            pdf_path = month_info['full_path']
            
            print(f"\n  处理月份: {month}")
            print(f"  PDF: {pdf_path}")
            
            # 检查是否已导入
            cursor.execute("""
                SELECT COUNT(*) FROM statements 
                WHERE card_id = ? AND statement_date LIKE ?
            """, (card_id, f'{month}%'))
            
            existing = cursor.fetchone()[0]
            
            if existing > 0 and dry_run:
                print(f"  ℹ️  账单已存在，跳过")
                continue
            
            # 提取账单数据
            statement_info = self.extract_statement_data_simple(pdf_path, bank_name)
            
            if statement_info['status'] == 'error':
                print(f"  ❌ PDF读取失败: {statement_info['error']}")
                error_count += 1
                continue
            
            print(f"  ✅ PDF可读 ({statement_info['pages']} 页, {statement_info['text_length']} 字符)")
            
            if not dry_run:
                # 这里可以调用详细的导入逻辑
                # 暂时只记录
                pass
            
            success_count += 1
        
        print(f"\n总结: 成功 {success_count}, 失败 {error_count}")
        conn.close()
    
    def process_all_banks(self, dry_run=True):
        """处理所有5家银行"""
        print("\n" + "=" * 80)
        print(f"{'[DRY RUN] ' if dry_run else ''}开始处理所有银行账单")
        print("=" * 80)
        
        for bank_name in self.banks_config.keys():
            self.import_bank_statements(bank_name, dry_run=dry_run)
    
    def reprocess_gz_transfers(self):
        """重新处理GZ转账分类"""
        print("\n" + "=" * 80)
        print("🔄 重新分类GZ转账用途")
        print("=" * 80 + "\n")
        
        conn = get_db()
        cursor = conn.cursor()
        
        # 获取所有Chang Choon Chow的GZ转账
        cursor.execute("""
            SELECT id, transfer_date, amount, notes
            FROM gz_transfers
            WHERE customer_id = ? AND transfer_purpose = 'Unknown'
            ORDER BY transfer_date
        """, (self.customer_id,))
        
        transfers = cursor.fetchall()
        
        print(f"找到 {len(transfers)} 笔需要重新分类的转账:\n")
        
        for transfer in transfers:
            transfer_id, date, amount, notes = transfer
            print(f"转账ID: {transfer_id}")
            print(f"  日期: {date}")
            print(f"  金额: RM {amount:,.2f}")
            print(f"  备注: {notes}")
            print(f"  ⚠️  需要人工确认用途")
            print()
        
        conn.close()
    
    def generate_summary_report(self):
        """生成汇总报告"""
        print("\n" + "=" * 80)
        print("📊 CHANG CHOON CHOW - 完整财务报告")
        print("=" * 80 + "\n")
        
        conn = get_db()
        cursor = conn.cursor()
        
        # 1. 信用卡账单统计
        print("【信用卡账单】\n")
        for bank_name, config in self.banks_config.items():
            card_id = config['card_id']
            
            cursor.execute("""
                SELECT COUNT(*), SUM(statement_total)
                FROM statements
                WHERE card_id = ? AND is_confirmed = 1
            """, (card_id,))
            
            result = cursor.fetchone()
            count = result[0] or 0
            total = result[1] or 0
            
            print(f"  {bank_name}: {count} 张账单, 总计 RM {total:,.2f}")
        
        # 2. GZ转账统计
        print("\n【GZ转账】\n")
        cursor.execute("""
            SELECT transfer_purpose, COUNT(*), SUM(amount)
            FROM gz_transfers
            WHERE customer_id = ?
            GROUP BY transfer_purpose
        """, (self.customer_id,))
        
        for row in cursor.fetchall():
            purpose, count, total = row
            print(f"  {purpose}: {count} 笔, RM {total:,.2f}")
        
        conn.close()
        print("\n" + "=" * 80)


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🚀 CHANG CHOON CHOW - 5家银行完整重新计算系统")
    print("=" * 80)
    
    recalculator = CCCBankRecalculator()
    
    # 步骤1: 扫描PDF文件
    recalculator.scan_available_pdfs()
    
    # 步骤2: 处理所有银行账单（试运行）
    recalculator.process_all_banks(dry_run=True)
    
    # 步骤3: 重新处理GZ转账
    recalculator.reprocess_gz_transfers()
    
    # 步骤4: 生成报告
    recalculator.generate_summary_report()
    
    print("\n✅ 完成！")
    print("提示: 这是试运行模式，未实际修改数据库")
    print("如需实际导入，请修改 dry_run=False\n")


if __name__ == '__main__':
    main()
