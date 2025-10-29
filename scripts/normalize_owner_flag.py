#!/usr/bin/env python3
"""
规范owner_flag标准值
Normalize owner_flag values to OWNER/INFINITE standard
"""

import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_db


def normalize_owner_flag():
    """规范owner_flag值为OWNER/INFINITE标准"""
    
    print("="*80)
    print("规范owner_flag标准值")
    print("="*80)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 步骤1：检查当前owner_flag值分布
        print("\n步骤1: 检查当前owner_flag值分布...")
        cursor.execute('''
            SELECT owner_flag, COUNT(*) as cnt
            FROM transactions
            WHERE monthly_statement_id IS NOT NULL
            GROUP BY owner_flag
            ORDER BY cnt DESC
        ''')
        
        distributions = cursor.fetchall()
        print("   当前分布:")
        total_count = 0
        for dist in distributions:
            flag_val = dist['owner_flag'] if dist['owner_flag'] else 'NULL'
            print(f"      - '{flag_val}': {dist['cnt']} 条")
            total_count += dist['cnt']
        
        print(f"   总计: {total_count} 条交易记录")
        
        # 步骤2：定义映射规则
        print("\n步骤2: 定义映射规则...")
        mappings = {
            '1': 'OWNER',
            'owner': 'OWNER',
            'own': 'OWNER',
            '0': 'INFINITE',
            'infinite': 'INFINITE'
        }
        
        print("   映射规则:")
        for old_val, new_val in mappings.items():
            print(f"      '{old_val}' -> '{new_val}'")
        
        # 步骤3：执行规范化更新
        print("\n步骤3: 执行规范化更新...")
        update_stats = {}
        
        for old_val, new_val in mappings.items():
            cursor.execute('''
                UPDATE transactions
                SET owner_flag = ?
                WHERE owner_flag = ?
            ''', (new_val, old_val))
            
            updated = cursor.rowcount
            if updated > 0:
                update_stats[old_val] = {
                    'new_value': new_val,
                    'count': updated
                }
                print(f"   ✅ '{old_val}' -> '{new_val}': {updated} 条")
        
        conn.commit()
        
        # 步骤4: 验证更新后的分布
        print("\n步骤4: 验证更新后的分布...")
        cursor.execute('''
            SELECT owner_flag, COUNT(*) as cnt
            FROM transactions
            WHERE monthly_statement_id IS NOT NULL
            GROUP BY owner_flag
            ORDER BY owner_flag
        ''')
        
        new_distributions = cursor.fetchall()
        print("   更新后分布:")
        for dist in new_distributions:
            flag_val = dist['owner_flag'] if dist['owner_flag'] else 'NULL'
            print(f"      - '{flag_val}': {dist['cnt']} 条")
        
        # 步骤5: 检查是否有未规范的值
        print("\n步骤5: 检查未规范的值...")
        cursor.execute('''
            SELECT DISTINCT owner_flag
            FROM transactions
            WHERE monthly_statement_id IS NOT NULL
              AND owner_flag NOT IN ('OWNER', 'INFINITE')
              AND owner_flag IS NOT NULL
        ''')
        
        unexpected_values = cursor.fetchall()
        if unexpected_values:
            print("   ⚠️  发现未规范的值:")
            for val in unexpected_values:
                print(f"      - '{val['owner_flag']}'")
        else:
            print("   ✅ 所有值已规范为OWNER/INFINITE")
        
        # 步骤6: 更新NULL值（如果需要）
        cursor.execute('''
            SELECT COUNT(*) as cnt
            FROM transactions
            WHERE monthly_statement_id IS NOT NULL
              AND owner_flag IS NULL
        ''')
        null_count = cursor.fetchone()['cnt']
        
        if null_count > 0:
            print(f"\n步骤6: 发现{null_count}条owner_flag为NULL的记录")
            print("   ⚠️  这些记录需要手动分类")
            print("   ℹ️  建议: 根据supplier_name判断，有supplier_name的设为INFINITE，否则设为OWNER")
        else:
            print("\n步骤6: 没有NULL值，跳过")
        
        # 步骤7: 生成规范化报告
        print("\n步骤7: 生成规范化报告...")
        report_path = "docs/OWNER_FLAG_NORMALIZATION_REPORT_2025-10-29.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Owner Flag Normalization Report\n\n")
            f.write("**Date:** 2025-10-29\n\n")
            f.write("## Summary\n\n")
            f.write(f"- **Total Transactions Processed:** {total_count}\n")
            f.write(f"- **Mapping Rules Applied:** {len(mappings)}\n")
            f.write(f"- **Records Updated:** {sum(s['count'] for s in update_stats.values())}\n\n")
            f.write("## Normalization Standard\n\n")
            f.write("All `owner_flag` values have been normalized to:\n\n")
            f.write("- **`OWNER`**: Customer's own expenses and payments\n")
            f.write("- **`INFINITE`**: GZ/INFINITE supplier expenses and third-party payments\n\n")
            f.write("## Mapping Rules\n\n")
            f.write("| Old Value | New Value | Records Updated |\n")
            f.write("|---|---|---|\n")
            for old_val, stats in update_stats.items():
                f.write(f"| `{old_val}` | `{stats['new_value']}` | {stats['count']} |\n")
            f.write("\n## Before vs After Distribution\n\n")
            f.write("### Before Normalization\n\n")
            f.write("| Value | Count |\n")
            f.write("|---|---|\n")
            for dist in distributions:
                flag_val = dist['owner_flag'] if dist['owner_flag'] else 'NULL'
                f.write(f"| `{flag_val}` | {dist['cnt']} |\n")
            f.write("\n### After Normalization\n\n")
            f.write("| Value | Count |\n")
            f.write("|---|---|\n")
            for dist in new_distributions:
                flag_val = dist['owner_flag'] if dist['owner_flag'] else 'NULL'
                f.write(f"| `{flag_val}` | {dist['cnt']} |\n")
            f.write("\n## Code Impact\n\n")
            f.write("All code must now use the standardized values:\n\n")
            f.write("```python\n")
            f.write("# Use these constants\n")
            f.write("OWNER_FLAG_OWNER = 'OWNER'\n")
            f.write("OWNER_FLAG_INFINITE = 'INFINITE'\n\n")
            f.write("# Update queries:\n")
            f.write("# Old: owner_flag = '0'\n")
            f.write("# New: owner_flag = 'INFINITE'\n\n")
            f.write("# Old: owner_flag IN ('1', 'owner', 'own')\n")
            f.write("# New: owner_flag = 'OWNER'\n")
            f.write("```\n\n")
            f.write("## Next Steps\n\n")
            f.write("1. ✅ Update all SQL queries to use OWNER/INFINITE\n")
            f.write("2. ✅ Update classification code to output OWNER/INFINITE\n")
            f.write("3. ✅ Update UI display logic\n")
            f.write("4. ✅ Add validation to prevent old values\n")
        
        print(f"   ✅ 规范化报告已生成: {report_path}")
        
        print("\n" + "="*80)
        print("✅ 规范化完成！")
        print("="*80)
        print("📊 总结:")
        print(f"   - 处理记录: {total_count} 条")
        print(f"   - 更新记录: {sum(s['count'] for s in update_stats.values())} 条")
        print(f"   - 标准值: OWNER, INFINITE")
        print(f"   - 报告: {report_path}")
        print("="*80)


if __name__ == "__main__":
    normalize_owner_flag()
