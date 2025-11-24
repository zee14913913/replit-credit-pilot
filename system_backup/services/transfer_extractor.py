"""
Transfer Extractor Service
从储蓄账户交易中提取INFINITE转账记录
"""
import sqlite3
from datetime import datetime
from typing import List, Dict
from services.ledger_classifier import LedgerClassifier


def parse_transaction_date(date_str: str) -> datetime:
    """
    解析交易日期 - 支持多种格式
    
    Args:
        date_str: 日期字符串 (支持 "DD-MM-YYYY" 或 "YYYY-MM-DD")
    
    Returns:
        datetime对象
    """
    if not date_str:
        return None
    
    # 尝试 DD-MM-YYYY 格式 (savings_transactions)
    try:
        return datetime.strptime(date_str, '%d-%m-%Y')
    except:
        pass
    
    # 尝试 YYYY-MM-DD 格式 (statements)
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        pass
    
    # 尝试 DD/MM/YYYY 格式
    try:
        return datetime.strptime(date_str, '%d/%m/%Y')
    except:
        pass
    
    return None


class TransferExtractor:
    def __init__(self, db_path='db/smart_loan_manager.db'):
        self.db_path = db_path
        self.classifier = LedgerClassifier(db_path)
    
    def extract_infinite_transfers_for_customer(self, customer_id: int, 
                                               start_date: str = None, 
                                               end_date: str = None):
        """
        提取客户的所有INFINITE转账记录
        
        Args:
            customer_id: 客户ID
            start_date: 开始日期 (YYYY-MM-DD)，可选
            end_date: 结束日期 (YYYY-MM-DD)，可选
        
        Returns:
            List of transfer records
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取所有储蓄账户交易
            query = """
                SELECT 
                    st.id as transaction_id,
                    st.transaction_date,
                    st.description,
                    st.amount,
                    st.transaction_type,
                    sa.account_number_last4,
                    sa.bank_name
                FROM savings_transactions st
                JOIN savings_statements ss ON st.savings_statement_id = ss.id
                JOIN savings_accounts sa ON ss.savings_account_id = sa.id
                WHERE sa.customer_id = ?
            """
            
            params = [customer_id]
            
            if start_date:
                query += " AND st.transaction_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND st.transaction_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY st.transaction_date ASC"
            
            cursor.execute(query, params)
            transactions = cursor.fetchall()
            
            print(f"\n{'='*80}")
            print(f"提取客户 ID {customer_id} 的INFINITE转账记录")
            print(f"{'='*80}")
            print(f"共 {len(transactions)} 笔储蓄账户交易\n")
            
            # 筛选转给客户的转账
            infinite_transfers = []
            
            for txn in transactions:
                txn_id, txn_date, description, amount, txn_type, account_num, bank_name = txn
                
                # 只关注支出（debit）
                if txn_type != 'debit' or not amount or amount == 0:
                    continue
                
                # 检查是否是转给客户的转账
                is_transfer, recipient_name = self.classifier.is_transfer_to_customer(
                    description, customer_id
                )
                
                if is_transfer:
                    # 解析日期并转换为标准格式
                    parsed_date = parse_transaction_date(txn_date)
                    if parsed_date:
                        standard_date = parsed_date.strftime('%Y-%m-%d')
                        month_start = parsed_date.strftime('%Y-%m-01')
                    else:
                        standard_date = txn_date
                        month_start = txn_date[:7] + '-01'  # fallback
                    
                    infinite_transfers.append({
                        'transaction_id': txn_id,
                        'transfer_date': standard_date,
                        'payer_name': f"{bank_name} (*{account_num[-4:]})",
                        'payee_name': recipient_name,
                        'amount': amount,
                        'description': description,
                        'month_start': month_start
                    })
                    
                    print(f"✅ {standard_date}: {recipient_name} - RM {amount:,.2f}")
                    print(f"   描述: {description}")
                    print(f"   账户: {bank_name} (*{account_num[-4:]})")
                    print()
            
            print(f"\n{'='*80}")
            print(f"找到 {len(infinite_transfers)} 笔INFINITE转账记录")
            print(f"{'='*80}\n")
            
            return infinite_transfers
            
        finally:
            conn.close()
    
    def save_infinite_transfers(self, customer_id: int, card_id: int = None):
        """
        保存INFINITE转账记录到数据库
        
        Args:
            customer_id: 客户ID
            card_id: 信用卡ID（可选，如果为None则保存所有卡片）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取客户的所有信用卡
            if card_id:
                cursor.execute("""
                    SELECT id FROM credit_cards WHERE id = ? AND customer_id = ?
                """, (card_id, customer_id))
                cards = cursor.fetchall()
            else:
                cursor.execute("""
                    SELECT id FROM credit_cards WHERE customer_id = ?
                """, (customer_id,))
                cards = cursor.fetchall()
            
            if not cards:
                print(f"❌ No credit cards found for customer ID {customer_id}")
                return
            
            # 提取所有INFINITE转账
            transfers = self.extract_infinite_transfers_for_customer(customer_id)
            
            if not transfers:
                print("ℹ️  没有找到INFINITE转账记录")
                return
            
            # 为每张卡保存转账记录
            total_saved = 0
            for card_tuple in cards:
                current_card_id = card_tuple[0]
                
                for transfer in transfers:
                    # 检查是否已存在
                    cursor.execute("""
                        SELECT id FROM infinite_transfers 
                        WHERE card_id = ? 
                        AND savings_transaction_id = ? 
                        AND transfer_date = ?
                    """, (current_card_id, transfer['transaction_id'], transfer['transfer_date']))
                    
                    if cursor.fetchone():
                        continue
                    
                    # 插入新记录
                    cursor.execute("""
                        INSERT INTO infinite_transfers 
                        (card_id, customer_id, savings_transaction_id, transfer_date, 
                         payer_name, payee_name, amount, description, month_start)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        current_card_id,
                        customer_id,
                        transfer['transaction_id'],
                        transfer['transfer_date'],
                        transfer['payer_name'],
                        transfer['payee_name'],
                        transfer['amount'],
                        transfer['description'],
                        transfer['month_start']
                    ))
                    total_saved += 1
            
            conn.commit()
            print(f"\n✅ 成功保存 {total_saved} 笔INFINITE转账记录")
            
            # 更新infinite_monthly_ledger的transfer_count
            for card_tuple in cards:
                current_card_id = card_tuple[0]
                cursor.execute("""
                    UPDATE infinite_monthly_ledger 
                    SET transfer_count = (
                        SELECT COUNT(*) 
                        FROM infinite_transfers 
                        WHERE card_id = infinite_monthly_ledger.card_id 
                        AND month_start = infinite_monthly_ledger.month_start
                    )
                    WHERE card_id = ?
                """, (current_card_id,))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            conn.close()
    
    def get_transfers_summary(self, customer_id: int, month_start: str = None):
        """获取转账汇总"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if month_start:
                # 获取指定月份的转账
                cursor.execute("""
                    SELECT 
                        transfer_date,
                        payee_name,
                        amount,
                        description,
                        payer_name
                    FROM infinite_transfers
                    WHERE customer_id = ? AND month_start = ?
                    ORDER BY transfer_date ASC
                """, (customer_id, month_start))
            else:
                # 获取所有转账按月汇总
                cursor.execute("""
                    SELECT 
                        month_start,
                        COUNT(*) as transfer_count,
                        SUM(amount) as total_amount
                    FROM infinite_transfers
                    WHERE customer_id = ?
                    GROUP BY month_start
                    ORDER BY month_start DESC
                """, (customer_id,))
            
            results = cursor.fetchall()
            return results
            
        finally:
            conn.close()


# 测试代码
if __name__ == "__main__":
    extractor = TransferExtractor()
    
    customer_id = 5  # Chang Choon Chow
    
    print("=== 步骤 1: 提取INFINITE转账记录 ===")
    transfers = extractor.extract_infinite_transfers_for_customer(customer_id)
    
    if transfers:
        print("\n=== 步骤 2: 保存转账记录到数据库 ===")
        extractor.save_infinite_transfers(customer_id)
        
        print("\n=== 步骤 3: 查看转账汇总 ===")
        summary = extractor.get_transfers_summary(customer_id)
        
        print(f"\n{'月份':<12} {'转账次数':>10} {'转账金额':>15}")
        print("-" * 40)
        for row in summary:
            print(f"{row[0][:7]:<12} {row[1]:>10} RM {row[2]:>12,.2f}")
    else:
        print("\nℹ️  没有找到INFINITE转账记录")
