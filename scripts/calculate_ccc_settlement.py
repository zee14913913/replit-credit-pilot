#!/usr/bin/env python3
"""
Chang Choon Chow 结算计算器
从PDF原件重新解析，按最新规则计算

【核心规则】
1. 从原件PDF重新解析
2. Owner's Expenses = 非Supplier消费
3. GZ's Expenses = 7个Supplier消费 + 1% Fee
4. Owner's Payment = 客户自己付款
5. GZ's Payment (Direct) = GZ直接付银行
6. GZ's Payment (Indirect) = GZ转账→客户→银行

【Supplier List】
7sl, Dinas, Raub Syc Hainan, Ai Smart Tech, Huawei, Pasar Raya, Puchong Herbs

【最终结算公式】
最终应结算金额 = GZ OS Balance
"""

import os
import sys
import re
import pdfplumber
from datetime import datetime
from decimal import Decimal
from collections import defaultdict
import json

# Supplier List (7个供应商)
SUPPLIER_LIST = [
    '7SL',
    'DINAS',
    'RAUB SYC HAINAN',
    'AI SMART TECH',
    'HUAWEI',
    'PASAR RAYA',
    'PUCHONG HERBS'
]

# GZ Bank List (用于识别GZ Direct Payment)
GZ_BANK_LIST = [
    'INFINITE',
    'GZ',
    'KENG CHOW'
]


class CCCSettlementCalculator:
    """Chang Choon Chow 结算计算器"""
    
    def __init__(self):
        self.customer_code = "Be_rich_CCC"
        self.customer_name = "Chang Choon Chow"
        self.pdf_base_path = f"static/uploads/customers/{self.customer_code}/credit_cards"
        
        # 数据存储
        self.monthly_data = defaultdict(lambda: {
            'owner_expenses': Decimal('0'),
            'owner_payments': Decimal('0'),
            'gz_expenses': Decimal('0'),
            'gz_direct_payments': Decimal('0'),
            'gz_indirect_payments': Decimal('0'),
            'merchant_fees': Decimal('0'),
            'transactions': []
        })
        
        self.pdf_files = []
        self.parse_errors = []
        
    def find_all_pdfs(self):
        """查找所有PDF文件"""
        print("=" * 80)
        print("📋 查找Chang Choon Chow的所有PDF原件")
        print("=" * 80)
        
        for root, dirs, files in os.walk(self.pdf_base_path):
            for file in files:
                if file.endswith('.pdf'):
                    full_path = os.path.join(root, file)
                    self.pdf_files.append(full_path)
        
        # 按路径排序
        self.pdf_files.sort()
        
        print(f"\n✅ 找到 {len(self.pdf_files)} 个PDF文件")
        
        # 按银行分类
        banks = defaultdict(list)
        for pdf in self.pdf_files:
            if 'Alliance' in pdf:
                banks['Alliance Bank'].append(pdf)
            elif 'HSBC' in pdf:
                banks['HSBC'].append(pdf)
            elif 'Hong' in pdf or 'HLB' in pdf:
                banks['Hong Leong Bank'].append(pdf)
            elif 'Maybank' in pdf:
                banks['Maybank'].append(pdf)
            elif 'UOB' in pdf:
                banks['UOB'].append(pdf)
        
        print("\n按银行分类：")
        for bank, files in sorted(banks.items()):
            print(f"  {bank}: {len(files)} 个文件")
        
        return len(self.pdf_files)
    
    def parse_single_pdf(self, pdf_path):
        """解析单个PDF文件"""
        try:
            # 提取月份
            month_match = re.search(r'(\d{4}-\d{2})', pdf_path)
            if not month_match:
                self.parse_errors.append(f"无法提取月份: {pdf_path}")
                return None
            
            statement_month = month_match.group(1)
            
            # 提取银行
            bank_name = "Unknown"
            if 'Alliance' in pdf_path:
                bank_name = "Alliance Bank"
            elif 'HSBC' in pdf_path:
                bank_name = "HSBC"
            elif 'Hong' in pdf_path or 'HLB' in pdf_path:
                bank_name = "Hong Leong Bank"
            elif 'Maybank' in pdf_path:
                bank_name = "Maybank"
            elif 'UOB' in pdf_path:
                bank_name = "UOB"
            
            # 读取PDF文本
            with pdfplumber.open(pdf_path) as pdf:
                all_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
            
            if not all_text:
                self.parse_errors.append(f"PDF无文本内容: {pdf_path}")
                return None
            
            # 解析交易
            transactions = self._extract_transactions_from_text(all_text, bank_name)
            
            # 提取Previous Balance
            previous_balance = self._extract_previous_balance(all_text)
            
            return {
                'pdf_path': pdf_path,
                'bank_name': bank_name,
                'statement_month': statement_month,
                'previous_balance': previous_balance,
                'transactions': transactions,
                'text_length': len(all_text)
            }
            
        except Exception as e:
            self.parse_errors.append(f"解析错误 {pdf_path}: {str(e)}")
            return None
    
    def _extract_previous_balance(self, text):
        """提取Previous Balance"""
        patterns = [
            r'Previous Balance[\s:]+RM\s*([\d,]+\.?\d*)',
            r'PREVIOUS BALANCE[\s:]+RM\s*([\d,]+\.?\d*)',
            r'B/F BALANCE[\s:]+RM\s*([\d,]+\.?\d*)',
            r'Opening Balance[\s:]+RM\s*([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                return Decimal(amount_str)
        
        return Decimal('0')
    
    def _extract_transactions_from_text(self, text, bank_name):
        """从文本中提取交易记录"""
        transactions = []
        
        # 简化解析：提取DR和CR交易
        # 这里需要根据不同银行的格式进行适配
        
        # 示例：Alliance Bank格式
        # 日期 描述 DR CR
        lines = text.split('\n')
        
        for line in lines:
            # 跳过空行
            if not line.strip():
                continue
            
            # 查找DR交易（消费）
            dr_match = re.search(r'([\d/]+)\s+(.+?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})\s*$', line)
            if dr_match:
                date_str = dr_match.group(1)
                description = dr_match.group(2).strip()
                amount = Decimal(dr_match.group(3).replace(',', ''))
                
                transactions.append({
                    'date': date_str,
                    'description': description,
                    'amount': amount,
                    'type': 'DR'
                })
            
            # 查找CR交易（付款/退款）
            cr_match = re.search(r'([\d/]+)\s+(.+?)\s+CR\s+(\d{1,3}(?:,\d{3})*\.\d{2})', line)
            if cr_match:
                date_str = cr_match.group(1)
                description = cr_match.group(2).strip()
                amount = Decimal(cr_match.group(3).replace(',', ''))
                
                transactions.append({
                    'date': date_str,
                    'description': description,
                    'amount': amount,
                    'type': 'CR'
                })
        
        return transactions
    
    def classify_transaction(self, transaction):
        """分类交易"""
        description = transaction['description'].upper()
        amount = transaction['amount']
        txn_type = transaction['type']
        
        # 判断是否为Supplier消费
        is_supplier = False
        for supplier in SUPPLIER_LIST:
            if supplier.upper() in description:
                is_supplier = True
                break
        
        # 判断是否为GZ付款
        is_gz_payment = False
        if txn_type == 'CR':
            for gz_bank in GZ_BANK_LIST:
                if gz_bank.upper() in description:
                    is_gz_payment = True
                    break
        
        return {
            'is_supplier': is_supplier,
            'is_gz_payment': is_gz_payment,
            'is_owner_payment': txn_type == 'CR' and not is_gz_payment,
            'is_owner_expense': txn_type == 'DR' and not is_supplier
        }
    
    def calculate_monthly_ledger(self, parsed_data):
        """计算月度账本"""
        if not parsed_data:
            return
        
        statement_month = parsed_data['statement_month']
        transactions = parsed_data['transactions']
        
        for txn in transactions:
            classification = self.classify_transaction(txn)
            
            # Owner Expenses
            if classification['is_owner_expense']:
                self.monthly_data[statement_month]['owner_expenses'] += txn['amount']
            
            # GZ Expenses (Supplier + 1% Fee)
            if classification['is_supplier']:
                principal = txn['amount']
                fee = principal * Decimal('0.01')
                
                self.monthly_data[statement_month]['gz_expenses'] += principal
                self.monthly_data[statement_month]['merchant_fees'] += fee
                self.monthly_data[statement_month]['owner_expenses'] += fee  # Fee算Owner的
            
            # Owner Payments
            if classification['is_owner_payment']:
                self.monthly_data[statement_month]['owner_payments'] += txn['amount']
            
            # GZ Direct Payments
            if classification['is_gz_payment']:
                self.monthly_data[statement_month]['gz_direct_payments'] += txn['amount']
            
            # 保存交易记录
            self.monthly_data[statement_month]['transactions'].append({
                'description': txn['description'],
                'amount': float(txn['amount']),
                'type': txn['type'],
                'classification': classification
            })
    
    def calculate_os_balance(self):
        """计算OS Balance"""
        print("\n" + "=" * 80)
        print("💰 计算OS Balance（按最新规则）")
        print("=" * 80)
        
        owner_os = Decimal('0')
        gz_os = Decimal('0')
        
        print(f"\n{'月份':<12} {'Owner消费':<15} {'Owner付款':<15} {'Owner OS':<15} {'GZ消费':<15} {'GZ付款':<15} {'GZ OS':<15}")
        print("-" * 120)
        
        for month in sorted(self.monthly_data.keys()):
            data = self.monthly_data[month]
            
            # Owner OS Balance
            owner_expense = data['owner_expenses']
            owner_payment = data['owner_payments']
            owner_os += owner_expense - owner_payment
            
            # GZ OS Balance
            gz_expense = data['gz_expenses']
            gz_payment = data['gz_direct_payments'] + data['gz_indirect_payments']
            gz_os += gz_expense - gz_payment
            
            print(f"{month:<12} {owner_expense:>14.2f} {owner_payment:>14.2f} {owner_os:>14.2f} {gz_expense:>14.2f} {gz_payment:>14.2f} {gz_os:>14.2f}")
        
        print("-" * 120)
        print(f"{'累计':<12} {'':<15} {'':<15} {owner_os:>14.2f} {'':<15} {'':<15} {gz_os:>14.2f}")
        
        return {
            'owner_os_balance': float(owner_os),
            'gz_os_balance': float(gz_os),
            'final_settlement': float(gz_os)
        }
    
    def generate_report(self, result):
        """生成结算报告"""
        print("\n" + "=" * 80)
        print("📊 Chang Choon Chow 最终结算报告")
        print("=" * 80)
        
        print(f"\n客户: {self.customer_name}")
        print(f"客户代码: {self.customer_code}")
        print(f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n解析PDF数量: {len(self.pdf_files)} 个")
        print(f"解析成功: {len(self.pdf_files) - len(self.parse_errors)} 个")
        print(f"解析失败: {len(self.parse_errors)} 个")
        
        print("\n" + "=" * 80)
        print("最终结算金额")
        print("=" * 80)
        
        print(f"\nOwner OS Balance: RM {result['owner_os_balance']:,.2f}")
        print(f"GZ OS Balance: RM {result['gz_os_balance']:,.2f}")
        
        print(f"\n{'=' * 80}")
        print(f"🎯 最终应结算金额: RM {result['final_settlement']:,.2f}")
        print(f"{'=' * 80}")
        
        if result['final_settlement'] > 0:
            print(f"\n✅ INFINITE GZ 应支付给 OWNER: RM {result['final_settlement']:,.2f}")
        elif result['final_settlement'] < 0:
            print(f"\n✅ OWNER 应支付给 INFINITE GZ: RM {abs(result['final_settlement']):,.2f}")
        else:
            print(f"\n✅ 双方账目平衡，无需结算")
        
        # 保存报告到文件
        report_data = {
            'customer': self.customer_name,
            'customer_code': self.customer_code,
            'report_date': datetime.now().isoformat(),
            'result': result,
            'monthly_details': {
                month: {
                    'owner_expenses': float(data['owner_expenses']),
                    'owner_payments': float(data['owner_payments']),
                    'gz_expenses': float(data['gz_expenses']),
                    'gz_direct_payments': float(data['gz_direct_payments']),
                    'merchant_fees': float(data['merchant_fees']),
                    'transaction_count': len(data['transactions'])
                }
                for month, data in self.monthly_data.items()
            }
        }
        
        report_path = f"reports/CCC_Settlement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('reports', exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存: {report_path}")
        
        return report_path
    
    def run(self):
        """执行完整的结算计算流程"""
        print("\n" + "=" * 80)
        print("🚀 Chang Choon Chow 结算计算器")
        print("=" * 80)
        
        # 步骤1: 查找所有PDF
        pdf_count = self.find_all_pdfs()
        if pdf_count == 0:
            print("\n❌ 未找到PDF文件！")
            return None
        
        # 步骤2: 解析每个PDF
        print("\n" + "=" * 80)
        print("📖 解析PDF文件")
        print("=" * 80)
        
        parsed_count = 0
        for idx, pdf_path in enumerate(self.pdf_files, 1):
            print(f"\n[{idx}/{pdf_count}] 解析: {os.path.basename(pdf_path)}")
            
            parsed_data = self.parse_single_pdf(pdf_path)
            if parsed_data:
                self.calculate_monthly_ledger(parsed_data)
                parsed_count += 1
                print(f"  ✅ 成功 - {len(parsed_data['transactions'])} 条交易")
            else:
                print(f"  ❌ 失败")
        
        print(f"\n解析完成: {parsed_count}/{pdf_count} 个文件成功")
        
        # 步骤3: 计算OS Balance
        result = self.calculate_os_balance()
        
        # 步骤4: 生成报告
        report_path = self.generate_report(result)
        
        return result


if __name__ == "__main__":
    calculator = CCCSettlementCalculator()
    result = calculator.run()
    
    if result:
        print("\n✅ 结算计算完成！")
        sys.exit(0)
    else:
        print("\n❌ 结算计算失败！")
        sys.exit(1)
