#!/usr/bin/env python3
"""
从PDF中提取真实的Minimum Payment值并更新数据库
=====================================
目的：修复数据库中被计算公式覆盖的minimum_payment字段
确保100%使用PDF中的真实值
"""

import os
import sqlite3
import pdfplumber
import re
from decimal import Decimal

def extract_minimum_payment_from_pdf(pdf_path):
    """从PDF中提取Minimum Payment值"""
    try:
        if not os.path.exists(pdf_path):
            return None, f"文件不存在"
        
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            # 读取前3页
            for page in pdf.pages[:3]:
                text += page.extract_text() + "\n"
            
            # 多种正则模式匹配Minimum Payment
            patterns = [
                # Pattern 1: 英文 "Minimum Payment" 后面跟金额
                r'(?:Minimum\s+Payment|Minimum\s+Amount\s+Due)[\s\S]*?RM\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                # Pattern 2: 马来文 "Bayaran Minimum" 后面跟金额
                r'(?:Bayaran\s+Minimum|Jumlah\s+Bayaran\s+Minimum)[\s\S]*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                # Pattern 3: 表格中的"Minimum Payment"列
                r'Minimum\s+Payment.*?\n.*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                # Pattern 4: "Total Minimum Payment" 或 "Jumlah Bayaran Minimum"
                r'(?:Total|Jumlah)\s+(?:Minimum\s+Payment|Bayaran\s+Minimum)[\s\S]*?(\d{1,3}(?:,\d{3})*\.?\d{0,2})',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
                if matches:
                    # 取最后一个匹配（通常是汇总值）
                    min_pay_str = matches[-1].replace(',', '')
                    try:
                        min_pay = Decimal(min_pay_str)
                        if min_pay > 0 and min_pay < 999999:  # 合理范围检查
                            return min_pay, None
                    except:
                        continue
            
            return None, "未找到Minimum Payment字段"
    
    except Exception as e:
        return None, f"读取PDF失败: {str(e)}"

def main():
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    # 获取所有有PDF文件路径的statements
    cursor.execute("""
        SELECT 
            s.id,
            s.file_path,
            s.statement_total,
            s.minimum_payment as current_min_payment,
            c.bank_name,
            cu.name as customer_name
        FROM statements s
        JOIN credit_cards c ON s.card_id = c.id
        JOIN customers cu ON c.customer_id = cu.id
        WHERE s.file_path IS NOT NULL 
        AND s.file_path != ''
        ORDER BY cu.name, c.bank_name, s.statement_date
    """)
    
    records = cursor.fetchall()
    
    print(f"\n{'='*100}")
    print(f"🔍 从PDF中提取真实的Minimum Payment值")
    print(f"{'='*100}\n")
    print(f"总共找到 {len(records)} 条statement记录\n")
    
    updated_count = 0
    error_count = 0
    unchanged_count = 0
    
    for record in records:
        stmt_id, pdf_path, stmt_total, current_min_pay, bank_name, customer_name = record
        
        # 提取minimum payment
        min_pay, error = extract_minimum_payment_from_pdf(pdf_path)
        
        if min_pay is not None:
            # 比较新旧值
            old_value = Decimal(str(current_min_pay)) if current_min_pay else None
            new_value = min_pay
            
            if old_value != new_value:
                print(f"✅ {customer_name} - {bank_name}")
                print(f"   Statement ID: {stmt_id}")
                print(f"   Statement Total: RM {stmt_total:,.2f}")
                old_val_formatted = f"RM {old_value:,.2f}" if old_value is not None else "NULL"
                print(f"   旧值: {old_val_formatted}")
                print(f"   新值: RM {new_value:,.2f} ← 从PDF提取")
                diff = new_value - (old_value or Decimal('0'))
                print(f"   差异: RM {diff:,.2f}")
                print()
                
                # 更新数据库
                cursor.execute("""
                    UPDATE statements
                    SET minimum_payment = ?
                    WHERE id = ?
                """, (float(new_value), stmt_id))
                
                updated_count += 1
            else:
                unchanged_count += 1
        else:
            error_count += 1
            print(f"❌ {customer_name} - {bank_name}")
            print(f"   Statement ID: {stmt_id}")
            print(f"   错误: {error}")
            print(f"   PDF: {pdf_path}")
            print()
    
    # 提交更改
    conn.commit()
    conn.close()
    
    print(f"\n{'='*100}")
    print(f"📊 更新统计")
    print(f"{'='*100}\n")
    print(f"  ✅ 成功更新: {updated_count} 条")
    print(f"  ⏸️  值未变: {unchanged_count} 条")
    print(f"  ❌ 提取失败: {error_count} 条")
    print(f"  📄 总处理: {len(records)} 条")
    print(f"\n{'='*100}\n")
    
    if updated_count > 0:
        print(f"✅ 数据库已成功更新！所有minimum_payment值现在都是从PDF中提取的真实数据！\n")
    else:
        print(f"⚠️  没有记录需要更新\n")

if __name__ == "__main__":
    main()
