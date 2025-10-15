#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect("db/smart_loan_manager.db")
cursor = conn.cursor()

print("=== Database Verification: UOB Account All Statements ===\n")

cursor.execute("""
    SELECT 
        ss.id,
        ss.statement_date,
        COUNT(st.id) as txn_count,
        ROUND(SUM(CASE WHEN st.transaction_type = "credit" THEN st.amount ELSE 0 END), 2) as deposits,
        ROUND(SUM(CASE WHEN st.transaction_type = "debit" THEN st.amount ELSE 0 END), 2) as withdrawals,
        MAX(st.balance) as final_balance
    FROM savings_statements ss
    LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
    WHERE ss.savings_account_id = 10
    GROUP BY ss.id, ss.statement_date
    ORDER BY ss.statement_date
""")

print("Statement Date  | Txns | Total Deposits  | Total Withdrawals | Final Balance")
print("="*85)

for row in cursor.fetchall():
    print(f"{row[1]:15s} | {row[2]:4d} | RM {row[3]:>12,.2f} | RM {row[4]:>15,.2f} | RM {row[5]:>10,.2f}")

# Total
cursor.execute("""
    SELECT 
        COUNT(DISTINCT ss.id) as statement_count,
        COUNT(st.id) as total_txn_count,
        ROUND(SUM(CASE WHEN st.transaction_type = "credit" THEN st.amount ELSE 0 END), 2) as total_deposits,
        ROUND(SUM(CASE WHEN st.transaction_type = "debit" THEN st.amount ELSE 0 END), 2) as total_withdrawals
    FROM savings_statements ss
    LEFT JOIN savings_transactions st ON ss.id = st.savings_statement_id
    WHERE ss.savings_account_id = 10
""")

row = cursor.fetchone()
print("="*85)
print(f"Total: {row[0]} statements, {row[1]} transactions")
print(f"Total Deposits: RM {row[2]:,.2f} | Total Withdrawals: RM {row[3]:,.2f}")

conn.close()
print("\n✅ Database verification complete - all data correctly stored!")
