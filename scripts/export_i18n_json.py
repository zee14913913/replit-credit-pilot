#!/usr/bin/env python3
"""
Export translations from i18n/translations.py to JSON files
Generates static/i18n/en.json and static/i18n/zh.json
"""

import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from i18n.translations import TRANSLATIONS

def export_translations():
    """Export translations to JSON files"""
    output_dir = 'static/i18n'
    os.makedirs(output_dir, exist_ok=True)
    
    for lang in ['en', 'zh']:
        output_file = os.path.join(output_dir, f'{lang}.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(TRANSLATIONS[lang], f, ensure_ascii=False, indent=2)
        print(f'✅ Exported {lang}.json to {output_file}')

if __name__ == '__main__':
    export_translations()
    print('\n🎉 Translation export complete!')
