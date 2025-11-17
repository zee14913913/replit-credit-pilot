#!/usr/bin/env python3
"""
CreditPilot Color Compliance Checker
=====================================

Scans all Python, CSS, and HTML files for hardcoded hex color values.
Reports violations and provides recommendations for fixing them.

Usage:
    python3 scripts/check_color_compliance.py
    
    # Generate detailed report
    python3 scripts/check_color_compliance.py --detailed
    
    # Check specific directory
    python3 scripts/check_color_compliance.py --path static/css

Author: CreditPilot Development Team
Version: 1.0.0
Last Updated: 2025-11-17
"""

import re
import os
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import json

# Import color configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.colors import COLORS


class ColorComplianceChecker:
    """
    Scans codebase for hardcoded color values and validates against
    approved color palette from config/colors.json
    """
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.violations = []
        self.stats = {
            'total_files': 0,
            'files_with_violations': 0,
            'total_violations': 0,
            'deprecated_colors': 0,
            'unapproved_colors': 0
        }
        
        # Regex pattern for hex colors
        self.hex_pattern = re.compile(r'#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3}')
        
        # Files to exclude
        self.excluded_patterns = [
            'node_modules',
            '.git',
            '__pycache__',
            '.cache',
            '.pythonlibs',
            'archived',
            'test_excel_formatting.py',  # Test file with sample data
            'scripts/check_color_compliance.py',  # This file
            'config/colors.py',  # Color configuration module
            'config/colors.json'  # Color configuration data
        ]
        
        # File extensions to check
        self.extensions = ['.py', '.css', '.html', '.htm']
    
    def should_check_file(self, file_path: Path) -> bool:
        """Check if file should be scanned"""
        # Check extension
        if file_path.suffix not in self.extensions:
            return False
        
        # Check excluded patterns
        for pattern in self.excluded_patterns:
            if pattern in str(file_path):
                return False
        
        return True
    
    def scan_directory(self, directory: Path = None) -> None:
        """Scan directory for color compliance violations"""
        if directory is None:
            directory = self.root_path
        
        print(f"🔍 Scanning directory: {directory}")
        print("=" * 70)
        
        for file_path in directory.rglob('*'):
            if not file_path.is_file():
                continue
            
            if not self.should_check_file(file_path):
                continue
            
            self.check_file(file_path)
        
        self.print_summary()
    
    def check_file(self, file_path: Path) -> None:
        """Check a single file for hardcoded colors"""
        self.stats['total_files'] += 1
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            file_violations = []
            
            for line_num, line in enumerate(lines, 1):
                # Find all hex colors in line
                matches = self.hex_pattern.findall(line)
                
                for color in matches:
                    # Normalize color
                    normalized_color = color.upper()
                    
                    # Check if color is approved
                    is_approved = COLORS.validate_color(normalized_color)
                    is_deprecated = COLORS.is_deprecated(normalized_color)
                    
                    if is_deprecated:
                        file_violations.append({
                            'line': line_num,
                            'color': color,
                            'type': 'DEPRECATED',
                            'message': f'Deprecated color {color} - Replace with core colors'
                        })
                        self.stats['deprecated_colors'] += 1
                    
                    elif not is_approved:
                        file_violations.append({
                            'line': line_num,
                            'color': color,
                            'type': 'UNAPPROVED',
                            'message': f'Unapproved color {color} - Not in color palette'
                        })
                        self.stats['unapproved_colors'] += 1
            
            if file_violations:
                self.violations.append({
                    'file': str(file_path.relative_to(self.root_path)),
                    'violations': file_violations
                })
                self.stats['files_with_violations'] += 1
                self.stats['total_violations'] += len(file_violations)
        
        except Exception as e:
            print(f"⚠️ Error checking {file_path}: {e}")
    
    def print_summary(self) -> None:
        """Print compliance check summary"""
        print("\n" + "=" * 70)
        print("📊 COLOR COMPLIANCE CHECK SUMMARY")
        print("=" * 70)
        print(f"Total files scanned: {self.stats['total_files']}")
        print(f"Files with violations: {self.stats['files_with_violations']}")
        print(f"Total violations: {self.stats['total_violations']}")
        print(f"  - Deprecated colors: {self.stats['deprecated_colors']}")
        print(f"  - Unapproved colors: {self.stats['unapproved_colors']}")
        print()
        
        if self.violations:
            print("❌ COMPLIANCE STATUS: FAILED")
            print()
            print("📝 VIOLATIONS BY FILE:")
            print("-" * 70)
            
            for file_data in self.violations:
                print(f"\n📁 {file_data['file']} ({len(file_data['violations'])} violations)")
                
                for violation in file_data['violations']:
                    print(f"   Line {violation['line']}: [{violation['type']}] {violation['message']}")
            
            print("\n" + "=" * 70)
            print("🔧 RECOMMENDED ACTIONS:")
            print("=" * 70)
            print()
            print("1. PYTHON FILES (.py):")
            print("   Replace:")
            print("     COLOR_BLACK = colors.HexColor('#000000')")
            print("   With:")
            print("     from config.colors import COLORS")
            print("     COLOR_BLACK = colors.HexColor(COLORS.core.black)")
            print()
            print("2. CSS FILES (.css):")
            print("   Replace:")
            print("     background: #FF007F;")
            print("   With:")
            print("     background: var(--color-hot-pink);")
            print()
            print("3. HTML FILES (.html):")
            print("   Replace:")
            print("     <div style='color: #FF007F;'>")
            print("   With:")
            print("     <div style='color: var(--color-hot-pink);'>")
            print()
            print("4. DEPRECATED COLORS:")
            print("   - Gold (#D4AF37) → var(--color-hot-pink)")
            print("   - Orange-red (#FF5722) → var(--color-hot-pink)")
            print("   - Silver (#C0C0C0) → var(--color-hot-pink)")
            print()
        else:
            print("✅ COMPLIANCE STATUS: PASSED")
            print("All files comply with CreditPilot color standards!")
    
    def export_report(self, output_path: str = "color_compliance_report.json") -> None:
        """Export detailed compliance report to JSON"""
        report = {
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'stats': self.stats,
            'violations': self.violations,
            'approved_colors': COLORS.get_web_ui_palette(),
            'deprecated_colors': COLORS.deprecated.to_dict()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed report exported to: {output_path}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Check CreditPilot codebase for color compliance'
    )
    parser.add_argument(
        '--path',
        default='.',
        help='Path to scan (default: current directory)'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Generate detailed JSON report'
    )
    parser.add_argument(
        '--export',
        default='color_compliance_report.json',
        help='Output path for detailed report'
    )
    
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║        CreditPilot Color Compliance Checker v1.0.0                ║
║        Ensuring brand consistency across the platform             ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    checker = ColorComplianceChecker(args.path)
    checker.scan_directory()
    
    if args.detailed:
        checker.export_report(args.export)
    
    # Exit with error code if violations found
    exit_code = 1 if checker.violations else 0
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
