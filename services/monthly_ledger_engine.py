"""
Monthly Ledger Engine
月度账本计算引擎 - 计算客户和INFINITE两条财务线
"""
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple
from services.ledger_classifier import LedgerClassifier


class MonthlyLedgerEngine:
    def __init__(self, db_path='db/smart_loan_manager.db'):
        self.db_path = db_path
        self.classifier = LedgerClassifier(db_path)
    
    def calculate_monthly_ledger_for_card(self, card_id: int, recalculate_all: bool = False):
        """
        计算指定信用卡的所有月度账本
        
        Args:
            card_id: 信用卡ID
            recalculate_all: 是否重新计算所有月份（默认只计算新月份）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取卡片和客户信息
            cursor.execute("""
                SELECT c.customer_id, cu.name
                FROM credit_cards c
                JOIN customers cu ON c.customer_id = cu.id
                WHERE c.id = ?
            """, (card_id,))
            card_info = cursor.fetchone()
            if not card_info:
                print(f"❌ Card ID {card_id} not found")
                return
            
            customer_id, customer_name = card_info
            
            # 获取所有账单（按月份排序）
            cursor.execute("""
                SELECT id, statement_date, statement_total, previous_balance
                FROM statements
                WHERE card_id = ?
                ORDER BY statement_date ASC
            """, (card_id,))
            statements = cursor.fetchall()
            
            if not statements:
                print(f"❌ No statements found for card ID {card_id}")
                return
            
            print(f"\n{'='*80}")
            print(f"计算 Card ID {card_id} 的月度账本 ({customer_name})")
            print(f"{'='*80}")
            print(f"共 {len(statements)} 个月的账单\n")
            
            # 存储上月余额和第一个statement标志
            previous_customer_balance = 0
            previous_infinite_balance = 0
            is_first_statement = True
            
            for statement_id, statement_date, statement_total, stmt_prev_balance in statements:
                month_start = statement_date[:7] + '-01'  # YYYY-MM-01
                
                # 检查是否已计算过
                if not recalculate_all:
                    cursor.execute("""
                        SELECT id FROM monthly_ledger 
                        WHERE card_id = ? AND month_start = ?
                    """, (card_id, month_start))
                    if cursor.fetchone():
                        print(f"⏭️  {statement_date[:7]} - 已计算，跳过")
                        # 读取已有的余额
                        cursor.execute("""
                            SELECT rolling_balance FROM monthly_ledger 
                            WHERE card_id = ? AND month_start = ?
                        """, (card_id, month_start))
                        result = cursor.fetchone()
                        if result:
                            previous_customer_balance = result[0]
                        
                        cursor.execute("""
                            SELECT rolling_balance FROM infinite_monthly_ledger 
                            WHERE card_id = ? AND month_start = ?
                        """, (card_id, month_start))
                        result = cursor.fetchone()
                        if result:
                            previous_infinite_balance = result[0]
                        
                        is_first_statement = False  # 跳过后不再是第一个
                        continue
                
                print(f"📅 处理 {statement_date[:7]} (Statement ID: {statement_id})")
                
                # 获取该月所有交易
                cursor.execute("""
                    SELECT id, description, amount, transaction_type
                    FROM transactions
                    WHERE statement_id = ?
                """, (statement_id,))
                transactions = cursor.fetchall()
                
                # 初始化统计
                customer_spend = 0
                customer_payments = 0
                infinite_spend = 0
                infinite_payments = 0
                infinite_supplier_transactions = []  # 用于发票生成
                
                # 分类并累计
                for txn_id, description, amount, txn_type in transactions:
                    if txn_type == 'purchase':
                        # 检查是否是INFINITE供应商
                        is_supplier, supplier_name = self.classifier.is_infinite_supplier(description)
                        if is_supplier:
                            infinite_spend += amount
                            infinite_supplier_transactions.append({
                                'transaction_id': txn_id,
                                'supplier_name': supplier_name,
                                'amount': amount,
                                'description': description
                            })
                        else:
                            customer_spend += amount
                    elif txn_type == 'payment':
                        # 分类付款
                        payment_type = self.classifier.classify_payment(description, customer_id)
                        if payment_type in ['customer', 'company']:
                            customer_payments += amount
                        else:
                            infinite_payments += amount
                
                # 计算滚动余额
                # 第一个statement: 使用stmt_prev_balance作为起点（如果>0，全部分配给客户）
                # 后续statement: 使用上月的rolling_balance作为起点，验证stmt_prev_balance
                
                if is_first_statement and stmt_prev_balance > 0:
                    # 第一个statement: 使用PDF中的Previous Balance作为起点
                    # 假设全部属于客户（第一个月通常还没有INFINITE业务）
                    previous_customer_balance = stmt_prev_balance
                    previous_infinite_balance = 0
                    print(f"  📍 第一个statement，使用Previous Balance: RM {stmt_prev_balance:.2f}（归入客户）")
                
                # 计算基于交易的余额
                calculated_customer_balance = previous_customer_balance + customer_spend - customer_payments
                calculated_infinite_balance = previous_infinite_balance + infinite_spend - infinite_payments
                calculated_total = calculated_customer_balance + calculated_infinite_balance
                
                # 对于非第一个statement，验证stmt_prev_balance是否匹配上月总余额
                if not is_first_statement and abs(stmt_prev_balance - (previous_customer_balance + previous_infinite_balance)) > 0.01:
                    expected_prev = previous_customer_balance + previous_infinite_balance
                    print(f"  ⚠️ Previous Balance不匹配: PDF={stmt_prev_balance:.2f}, 上月总计={expected_prev:.2f}")
                
                # 检查是否与Statement Total匹配，如果不匹配则有未提取的费用/利息
                missing_fees = statement_total - calculated_total
                
                # 如果有差额（费用/利息），归入客户账户
                if abs(missing_fees) > 0.01:
                    customer_rolling_balance = calculated_customer_balance + missing_fees
                    infinite_rolling_balance = calculated_infinite_balance
                    print(f"  ⚠️ 检测到未提取费用/利息: RM {missing_fees:.2f}（已归入客户账户）")
                else:
                    customer_rolling_balance = calculated_customer_balance
                    infinite_rolling_balance = calculated_infinite_balance
                
                # 计算供应商手续费
                supplier_fee = sum([
                    self.classifier.calculate_supplier_fee(txn['amount'], txn['supplier_name'])
                    for txn in infinite_supplier_transactions
                ])
                
                print(f"  客户消费: RM {customer_spend:,.2f}")
                print(f"  客户付款: RM {customer_payments:,.2f}")
                print(f"  客户余额: RM {customer_rolling_balance:,.2f}")
                print(f"  INFINITE消费: RM {infinite_spend:,.2f} (手续费: RM {supplier_fee:,.2f})")
                print(f"  INFINITE付款: RM {infinite_payments:,.2f}")
                print(f"  INFINITE余额: RM {infinite_rolling_balance:,.2f}")
                
                # 插入或更新客户月度账本
                cursor.execute("""
                    INSERT OR REPLACE INTO monthly_ledger 
                    (card_id, customer_id, month_start, statement_id, previous_balance, 
                     customer_spend, customer_payments, rolling_balance, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    card_id, customer_id, month_start, statement_id,
                    previous_customer_balance, customer_spend, customer_payments,
                    customer_rolling_balance, datetime.now()
                ))
                
                # 插入或更新INFINITE月度账本
                cursor.execute("""
                    INSERT OR REPLACE INTO infinite_monthly_ledger 
                    (card_id, customer_id, month_start, statement_id, previous_balance,
                     infinite_spend, supplier_fee, infinite_payments, rolling_balance, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    card_id, customer_id, month_start, statement_id,
                    previous_infinite_balance, infinite_spend, supplier_fee,
                    infinite_payments, infinite_rolling_balance, datetime.now()
                ))
                
                # 如果有INFINITE供应商交易，生成发票记录
                if infinite_supplier_transactions:
                    self._generate_supplier_invoices(
                        cursor, customer_id, statement_id, 
                        month_start, infinite_supplier_transactions
                    )
                
                # 更新上月余额
                previous_customer_balance = customer_rolling_balance
                previous_infinite_balance = infinite_rolling_balance
                
                # 标记已处理第一个statement
                is_first_statement = False
            
            conn.commit()
            print(f"\n✅ Card ID {card_id} 月度账本计算完成！")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            conn.close()
    
    def _generate_supplier_invoices(self, cursor, customer_id: int, statement_id: int, 
                                   month_start: str, transactions: List[Dict]):
        """生成供应商发票记录"""
        # 按供应商分组
        supplier_groups = {}
        for txn in transactions:
            supplier_name = txn['supplier_name']
            if supplier_name not in supplier_groups:
                supplier_groups[supplier_name] = []
            supplier_groups[supplier_name].append(txn)
        
        # 为每个供应商生成发票
        for supplier_name, txns in supplier_groups.items():
            total_amount = sum([t['amount'] for t in txns])
            supplier_fee = self.classifier.calculate_supplier_fee(total_amount, supplier_name)
            
            # 生成发票编号
            invoice_number = f"INF-{month_start[:7].replace('-', '')}-{supplier_name.replace(' ', '')[:10]}"
            
            # 检查是否已存在
            cursor.execute("""
                SELECT id FROM supplier_invoices 
                WHERE customer_id = ? AND statement_id = ? AND supplier_name = ?
            """, (customer_id, statement_id, supplier_name))
            
            if cursor.fetchone():
                # 更新
                cursor.execute("""
                    UPDATE supplier_invoices 
                    SET total_amount = ?, supplier_fee = ?, invoice_date = ?
                    WHERE customer_id = ? AND statement_id = ? AND supplier_name = ?
                """, (total_amount, supplier_fee, month_start, customer_id, statement_id, supplier_name))
            else:
                # 插入
                cursor.execute("""
                    INSERT INTO supplier_invoices 
                    (customer_id, statement_id, supplier_name, invoice_number, 
                     total_amount, supplier_fee, invoice_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (customer_id, statement_id, supplier_name, invoice_number,
                      total_amount, supplier_fee, month_start))
    
    def calculate_all_cards_for_customer(self, customer_id: int, recalculate_all: bool = False):
        """计算客户所有信用卡的月度账本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, bank_name, card_number_last4 
            FROM credit_cards 
            WHERE customer_id = ?
            ORDER BY bank_name, card_number_last4
        """, (customer_id,))
        cards = cursor.fetchall()
        conn.close()
        
        print(f"\n{'='*80}")
        print(f"开始计算客户 ID {customer_id} 的所有信用卡月度账本")
        print(f"{'='*80}")
        print(f"共 {len(cards)} 张信用卡\n")
        
        for card_id, bank_name, last4 in cards:
            print(f"\n📇 处理: {bank_name} (*{last4})")
            self.calculate_monthly_ledger_for_card(card_id, recalculate_all)
    
    def get_monthly_summary(self, customer_id: int, month_start: str = None):
        """获取客户的月度汇总"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if month_start:
            # 获取指定月份的汇总
            query = """
                SELECT 
                    c.bank_name,
                    c.card_number_last4,
                    ml.previous_balance,
                    ml.customer_spend,
                    ml.customer_payments,
                    ml.rolling_balance,
                    iml.infinite_spend,
                    iml.supplier_fee,
                    iml.infinite_payments,
                    iml.rolling_balance
                FROM monthly_ledger ml
                JOIN infinite_monthly_ledger iml 
                    ON ml.card_id = iml.card_id AND ml.month_start = iml.month_start
                JOIN credit_cards c ON ml.card_id = c.id
                WHERE ml.customer_id = ? AND ml.month_start = ?
                ORDER BY c.bank_name, c.card_number_last4
            """
            cursor.execute(query, (customer_id, month_start))
        else:
            # 获取最新月份的汇总
            query = """
                SELECT 
                    c.bank_name,
                    c.card_number_last4,
                    ml.month_start,
                    ml.previous_balance,
                    ml.customer_spend,
                    ml.customer_payments,
                    ml.rolling_balance,
                    iml.infinite_spend,
                    iml.supplier_fee,
                    iml.infinite_payments,
                    iml.rolling_balance
                FROM monthly_ledger ml
                JOIN infinite_monthly_ledger iml 
                    ON ml.card_id = iml.card_id AND ml.month_start = iml.month_start
                JOIN credit_cards c ON ml.card_id = c.id
                WHERE ml.customer_id = ?
                ORDER BY ml.month_start DESC, c.bank_name, c.card_number_last4
                LIMIT 10
            """
            cursor.execute(query, (customer_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results


# 测试代码
if __name__ == "__main__":
    engine = MonthlyLedgerEngine()
    
    # 为Chang Choon Chow (ID=5) 计算所有卡片的月度账本
    customer_id = 5
    
    print("开始计算月度账本...")
    engine.calculate_all_cards_for_customer(customer_id, recalculate_all=True)
    
    print("\n\n" + "="*80)
    print("查看最新月度汇总")
    print("="*80)
    results = engine.get_monthly_summary(customer_id)
    
    for row in results:
        print(f"\n{row[0]} (*{row[1]}) - {row[2]}")
        print(f"  客户: 上月 RM {row[3]:,.2f} + 消费 RM {row[4]:,.2f} - 付款 RM {row[5]:,.2f} = 余额 RM {row[6]:,.2f}")
        print(f"  INFINITE: 消费 RM {row[7]:,.2f} (手续费 RM {row[8]:,.2f}) - 付款 RM {row[9]:,.2f} = 余额 RM {row[10]:,.2f}")
