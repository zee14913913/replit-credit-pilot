#!/usr/bin/env python3
"""
Update all English translations to proper case format:
- Titles (containing 'title', 'nav_', '_header', '_heading') → ALL CAPS
- Subtitles/Body (everything else) → Title Case
"""

import re

def to_title_case(text):
    """Convert to Title Case (capitalize first letter of each word)"""
    # Don't capitalize common words unless they're the first word
    minor_words = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'in', 'of', 'on', 'or', 'the', 'to', 'vs', 'via'}
    
    words = text.split()
    if not words:
        return text
    
    # First word is always capitalized
    result = [words[0].capitalize()]
    
    # Rest of words follow rules
    for word in words[1:]:
        if word.lower() in minor_words:
            result.append(word.lower())
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)

def should_be_all_caps(key):
    """Determine if a translation key should be ALL CAPS"""
    # Keys that are clearly titles (h1, h2, h3 level headings)
    title_indicators = [
        'title', 'nav_', '_header', '_heading', 
        'management', 'center', 'dashboard', 'report',
        'system', 'portal', 'service', '_page',
        # Specific title-like keys
        'upload_bank_statement', 'supplier_aging_report', 
        'customer_aging_report', 'file_view', 'file_detail',
        'accounting_system', 'file_management'
    ]
    
    # Company/System names should stay as is
    if key in ['company_name', 'system_name']:
        return False
    
    # Exact match for specific title keys
    if key in title_indicators:
        return True
    
    # Check if key contains title indicators
    for indicator in title_indicators:
        if indicator in key and len(indicator) > 3:  # Avoid short false positives
            return True
    
    return False

def update_english_translations():
    """Read translations.py, update English translations, write back"""
    input_file = 'i18n/translations.py'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    updated_lines = []
    in_english_section = False
    current_key = None
    
    for line in lines:
        # Check if we're in the English section
        if "'en': {" in line:
            in_english_section = True
            updated_lines.append(line)
            continue
        
        # Check if we're leaving the English section
        if in_english_section and line.strip() == '},':
            in_english_section = False
            updated_lines.append(line)
            continue
        
        # Process English translation lines
        if in_english_section and ': ' in line and not line.strip().startswith('#'):
            # Extract key and value
            match = re.match(r"(\s*)'([^']+)':\s*'([^']*)'(,?)\s*$", line)
            if match:
                indent, key, value, comma = match.groups()
                
                # Skip if already processed (contains all caps or proper title case indicators)
                # Update based on rules
                if should_be_all_caps(key):
                    # Convert to ALL CAPS, but preserve special patterns like &, -, etc.
                    new_value = value.upper()
                else:
                    # Convert to Title Case
                    new_value = to_title_case(value)
                
                # Reconstruct line
                updated_line = f"{indent}'{key}': '{new_value}'{comma}\n"
                updated_lines.append(updated_line)
            else:
                # Keep line as is if it doesn't match pattern
                updated_lines.append(line)
        else:
            # Keep all other lines as is
            updated_lines.append(line)
    
    # Write back
    with open(input_file, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)
    
    print(f'✅ Updated English translations in {input_file}')
    print('   - Titles → ALL CAPS')
    print('   - Subtitles/Body → Title Case')

if __name__ == '__main__':
    update_english_translations()
    print('\n🎉 Case formatting complete!')
