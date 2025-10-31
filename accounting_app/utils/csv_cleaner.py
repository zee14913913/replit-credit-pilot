"""
CSV清理工具 - 处理Excel特殊格式的银行月结单
将 ="xxx" 格式转换为标准CSV格式
"""
import csv
import re
from datetime import datetime


def clean_excel_csv(input_file: str, output_file: str) -> dict:
    """
    清理Excel格式的CSV文件
    
    参数：
    - input_file: 原始CSV文件路径
    - output_file: 清理后的CSV文件路径
    
    返回：清理统计信息
    """
    cleaned_rows = []
    skipped_rows = 0
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    # 跳过标题行（CURRENT ACCOUNT STATEMENT）
    data_start_index = 0
    for i, row in enumerate(rows):
        if 'Date' in str(row) and 'Transaction Description' in str(row):
            data_start_index = i
            break
    
    if data_start_index == 0:
        raise ValueError("未找到CSV列标题行")
    
    # 处理数据行
    for i, row in enumerate(rows[data_start_index + 1:], start=1):
        if len(row) < 7:
            skipped_rows += 1
            continue
        
        # 清理每个字段的 ="xxx" 格式
        cleaned_row = []
        for cell in row:
            # 去除 ="" 包裹
            cell_str = str(cell).strip()
            if cell_str.startswith('="') and cell_str.endswith('"'):
                cell_str = cell_str[2:-1]
            elif cell_str.startswith('='):
                cell_str = cell_str[1:]
            
            # 去除多余的引号
            cell_str = cell_str.strip('"').strip()
            cleaned_row.append(cell_str)
        
        # 检查是否是期初余额行
        if 'Balance from previous statement' in cleaned_row[1]:
            skipped_rows += 1
            continue
        
        # 转换为标准格式：Date, Description, Reference, Debit, Credit, Balance
        try:
            date_str = cleaned_row[0]  # 10-07-2024
            description = cleaned_row[1]  # Transaction Description
            cheque = cleaned_row[2]  # Cheque No.
            reference = cleaned_row[3]  # Ref. No.
            deposit = cleaned_row[4]  # Deposit
            withdrawal = cleaned_row[5]  # Withdrawal
            balance = cleaned_row[6]  # Balance
            
            # 转换日期格式：10-07-2024 → 2024-07-10
            if date_str and '-' in date_str:
                parts = date_str.split('-')
                if len(parts) == 3:
                    date_str = f"{parts[2]}-{parts[1]}-{parts[0]}"
            
            # 构建完整描述（合并Ref. No.）
            full_description = description
            if reference:
                full_description = f"{description} | {reference}"
            
            # 合并Cheque No.和Ref. No.作为Reference
            full_reference = cheque if cheque else reference
            
            # 确定Debit/Credit
            debit_amount = withdrawal if withdrawal else "0.00"
            credit_amount = deposit if deposit else "0.00"
            
            # 处理空余额：使用上一笔的余额或0
            if not balance:
                # 如果是同一天的多笔交易，余额可能为空
                # 我们暂时使用0，稍后可以计算
                balance = "0.00"
            
            cleaned_rows.append([
                date_str,
                full_description,
                full_reference,
                debit_amount,
                credit_amount,
                balance
            ])
        
        except IndexError:
            skipped_rows += 1
            continue
    
    # 写入清理后的CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # 写入标准列标题
        writer.writerow(['Date', 'Description', 'Reference', 'Debit', 'Credit', 'Balance'])
        writer.writerows(cleaned_rows)
    
    return {
        "input_file": input_file,
        "output_file": output_file,
        "total_rows": len(cleaned_rows),
        "skipped_rows": skipped_rows,
        "success": True
    }


if __name__ == "__main__":
    # 测试清理工具
    result = clean_excel_csv(
        "attached_assets/05-08-2024_1761943485800.csv",
        "accounting_app/static/maybank_july2024_cleaned.csv"
    )
    print(f"✅ CSV清理完成：")
    print(f"   原始文件：{result['input_file']}")
    print(f"   清理文件：{result['output_file']}")
    print(f"   有效行数：{result['total_rows']}")
    print(f"   跳过行数：{result['skipped_rows']}")
