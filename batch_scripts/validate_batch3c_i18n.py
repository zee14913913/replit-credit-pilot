#!/usr/bin/env python3
"""
Batch 3C i18n Validation Script
Validates that all Chinese hardcoded texts have been replaced with i18n calls
"""

import re
import os

def count_patterns(file_path, pattern):
    """Count occurrences of a regex pattern in a file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return len(re.findall(pattern, content))

def find_chinese_texts(file_path):
    """Find all Chinese text occurrences (excluding those in t() or comments)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove HTML comments
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    
    # Remove Jinja comments
    content = re.sub(r'{#.*?#}', '', content, flags=re.DOTALL)
    
    # Find all Chinese characters
    chinese_pattern = r'[\u4e00-\u9fff]+'
    all_chinese = re.findall(chinese_pattern, content)
    
    # Filter out Chinese inside t() calls
    # This is a simple heuristic - find text that's likely hardcoded
    hardcoded = []
    for match in re.finditer(chinese_pattern, content):
        text = match.group()
        start = match.start()
        
        # Check if it's inside a t('...') or {{ t('...') }}
        before = content[max(0, start-50):start]
        if "t('" not in before and 't("' not in before:
            # Get context for reporting
            line_start = content.rfind('\n', 0, start) + 1
            line_end = content.find('\n', start)
            if line_end == -1:
                line_end = len(content)
            line = content[line_start:line_end].strip()
            hardcoded.append((text, line))
    
    return hardcoded

def validate_file(file_path, file_name):
    """Validate a single template file"""
    print(f"\n{'='*70}")
    print(f"📄 File: {file_name}")
    print('='*70)
    
    # Count t() function calls
    t_calls = count_patterns(file_path, r"t\(['\"]")
    print(f"  ✓ t() function calls: {t_calls}")
    
    # Count data-i18n attributes
    data_i18n = count_patterns(file_path, r'data-i18n="[^"]+"')
    print(f"  ✓ data-i18n attributes: {data_i18n}")
    
    # Find hardcoded Chinese texts
    hardcoded = find_chinese_texts(file_path)
    
    if hardcoded:
        print(f"  ⚠️  Remaining hardcoded Chinese texts: {len(hardcoded)}")
        for i, (text, line) in enumerate(hardcoded[:5], 1):  # Show first 5
            print(f"     {i}. '{text}' in: {line[:60]}...")
        if len(hardcoded) > 5:
            print(f"     ... and {len(hardcoded) - 5} more")
    else:
        print(f"  ✅ Remaining hardcoded Chinese texts: 0 (COMPLETE!)")
    
    return {
        't_calls': t_calls,
        'data_i18n': data_i18n,
        'hardcoded': len(hardcoded)
    }

def main():
    """Main validation function"""
    print("="*70)
    print(" " * 15 + "BATCH 3C I18N VALIDATION REPORT")
    print("="*70)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    files = {
        'edit_customer.html': os.path.join(base_dir, 'templates', 'edit_customer.html'),
        'add_credit_card.html': os.path.join(base_dir, 'templates', 'add_credit_card.html'),
        'add_customer.html': os.path.join(base_dir, 'templates', 'add_customer.html')
    }
    
    results = {}
    for file_name, file_path in files.items():
        if os.path.exists(file_path):
            results[file_name] = validate_file(file_path, file_name)
        else:
            print(f"\n⚠️  File not found: {file_name}")
    
    # Summary
    print(f"\n{'='*70}")
    print(" " * 20 + "SUMMARY REPORT")
    print('='*70)
    
    total_t_calls = sum(r['t_calls'] for r in results.values())
    total_data_i18n = sum(r['data_i18n'] for r in results.values())
    total_hardcoded = sum(r['hardcoded'] for r in results.values())
    
    print(f"\n  📊 Overall Statistics:")
    print(f"     • Total Files Processed: {len(results)}")
    print(f"     • Total t() Calls: {total_t_calls}")
    print(f"     • Total data-i18n Attributes: {total_data_i18n}")
    print(f"     • Total Remaining Hardcoded: {total_hardcoded}")
    
    # Check translation files
    print(f"\n  📚 Translation Files:")
    en_json = os.path.join(base_dir, 'static', 'i18n', 'en.json')
    zh_json = os.path.join(base_dir, 'static', 'i18n', 'zh.json')
    
    if os.path.exists(en_json):
        import json
        with open(en_json, 'r', encoding='utf-8') as f:
            en_data = json.load(f)
        print(f"     • en.json: {len(en_data)} keys")
    
    if os.path.exists(zh_json):
        import json
        with open(zh_json, 'r', encoding='utf-8') as f:
            zh_data = json.load(f)
        print(f"     • zh.json: {len(zh_data)} keys")
    
    # Final status
    print(f"\n  🎯 Status:")
    if total_hardcoded == 0:
        print(f"     ✅ ALL HARDCODED TEXTS REPLACED - 100% COMPLETE!")
    else:
        print(f"     ⚠️  {total_hardcoded} hardcoded text(s) remaining")
        print(f"     📝 Review the items listed above")
    
    print("\n" + "="*70)
    
    return total_hardcoded == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
