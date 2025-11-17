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
        
        # Regex patterns for all color formats
        self.hex_pattern = re.compile(r'#[0-9A-Fa-f]{8}|#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{4}|#[0-9A-Fa-f]{3}')
        self.rgb_pattern = re.compile(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*[\d.]+)?\s*\)', re.IGNORECASE)
        self.hsl_pattern = re.compile(r'hsla?\s*\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%(?:\s*,\s*[\d.]+)?\s*\)', re.IGNORECASE)
        
        # Common CSS named colors that should be avoided
        self.named_colors = {
            'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown',
            'gray', 'grey', 'silver', 'gold', 'cyan', 'magenta', 'lime', 'maroon',
            'navy', 'olive', 'teal', 'aqua', 'fuchsia', 'indigo', 'violet', 'tan',
            'beige', 'khaki', 'coral', 'salmon', 'crimson', 'tomato', 'chocolate'
        }
        self.named_color_pattern = re.compile(r'\b(' + '|'.join(self.named_colors) + r')\b', re.IGNORECASE)
        
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
    
    def normalize_hex_color(self, color: str) -> str:
        """
        Normalize hex color to 6-digit uppercase format.
        Converts shorthand (#fff, #ffff) to full (#FFFFFF, #FFFFFFFF).
        """
        color = color.upper()
        
        # Convert 3-digit shorthand to 6-digit (#fff → #FFFFFF)
        if len(color) == 4:
            return '#' + ''.join([c*2 for c in color[1:]])
        
        # Convert 4-digit shorthand to 8-digit (#ffff → #FFFFFFFF)
        if len(color) == 5:
            return '#' + ''.join([c*2 for c in color[1:]])
        
        # Already normalized (6 or 8 digits)
        return color
    
    def rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """Convert RGB values to hex color."""
        return f'#{r:02X}{g:02X}{b:02X}'
    
    def hsl_to_rgb(self, h: float, s: float, l: float) -> tuple:
        """Convert HSL to RGB (simplified conversion)."""
        # Normalize
        h = h / 360.0
        s = s / 100.0
        l = l / 100.0
        
        if s == 0:
            r = g = b = int(l * 255)
        else:
            def hue_to_rgb(p, q, t):
                if t < 0: t += 1
                if t > 1: t -= 1
                if t < 1/6: return p + (q - p) * 6 * t
                if t < 1/2: return q
                if t < 2/3: return p + (q - p) * (2/3 - t) * 6
                return p
            
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = int(hue_to_rgb(p, q, h + 1/3) * 255)
            g = int(hue_to_rgb(p, q, h) * 255)
            b = int(hue_to_rgb(p, q, h - 1/3) * 255)
        
        return (r, g, b)
    
    def check_file(self, file_path: Path) -> None:
        """Check a single file for hardcoded colors"""
        self.stats['total_files'] += 1
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            file_violations = []
            
            for line_num, line in enumerate(lines, 1):
                violations_in_line = []
                
                # 1. Check hex colors (#RRGGBB, #RGB, #RRGGBBAA, #RGBA)
                hex_matches = self.hex_pattern.findall(line)
                for color in hex_matches:
                    normalized_color = self.normalize_hex_color(color)
                    # Strip alpha channel for validation (last 2 digits)
                    validation_color = normalized_color[:7] if len(normalized_color) > 7 else normalized_color
                    
                    is_approved = COLORS.validate_color(validation_color)
                    is_deprecated = COLORS.is_deprecated(validation_color)
                    
                    if is_deprecated:
                        violations_in_line.append({
                            'color': color,
                            'normalized': normalized_color,
                            'type': 'DEPRECATED',
                            'format': 'hex',
                            'message': f'Deprecated hex color {color} - Replace with core colors'
                        })
                        self.stats['deprecated_colors'] += 1
                    elif not is_approved:
                        violations_in_line.append({
                            'color': color,
                            'normalized': normalized_color,
                            'type': 'UNAPPROVED',
                            'format': 'hex',
                            'message': f'Unapproved hex color {color} - Not in color palette'
                        })
                        self.stats['unapproved_colors'] += 1
                
                # 2. Check RGB/RGBA colors
                rgb_matches = self.rgb_pattern.findall(line)
                for match in rgb_matches:
                    r, g, b = int(match[0]), int(match[1]), int(match[2])
                    hex_color = self.rgb_to_hex(r, g, b)
                    
                    is_approved = COLORS.validate_color(hex_color)
                    is_deprecated = COLORS.is_deprecated(hex_color)
                    
                    original = f'rgb({r}, {g}, {b})'
                    if is_deprecated:
                        violations_in_line.append({
                            'color': original,
                            'normalized': hex_color,
                            'type': 'DEPRECATED',
                            'format': 'rgb',
                            'message': f'Deprecated RGB color {original} ({hex_color}) - Replace with CSS variables'
                        })
                        self.stats['deprecated_colors'] += 1
                    elif not is_approved:
                        violations_in_line.append({
                            'color': original,
                            'normalized': hex_color,
                            'type': 'UNAPPROVED',
                            'format': 'rgb',
                            'message': f'Unapproved RGB color {original} ({hex_color}) - Use CSS variables'
                        })
                        self.stats['unapproved_colors'] += 1
                
                # 3. Check HSL/HSLA colors
                hsl_matches = self.hsl_pattern.findall(line)
                for match in hsl_matches:
                    h, s, l = float(match[0]), float(match[1]), float(match[2])
                    r, g, b = self.hsl_to_rgb(h, s, l)
                    hex_color = self.rgb_to_hex(r, g, b)
                    
                    is_approved = COLORS.validate_color(hex_color)
                    
                    original = f'hsl({h}, {s}%, {l}%)'
                    if not is_approved:
                        violations_in_line.append({
                            'color': original,
                            'normalized': hex_color,
                            'type': 'UNAPPROVED',
                            'format': 'hsl',
                            'message': f'Unapproved HSL color {original} ({hex_color}) - Use CSS variables'
                        })
                        self.stats['unapproved_colors'] += 1
                
                # 4. Check named colors
                named_matches = self.named_color_pattern.findall(line)
                for color_name in named_matches:
                    # Skip if it's part of a word (e.g., 'directory' contains 'red')
                    if not re.search(r'\b' + color_name + r'\s*:', line, re.IGNORECASE):
                        continue
                    
                    violations_in_line.append({
                        'color': color_name,
                        'normalized': color_name.lower(),
                        'type': 'UNAPPROVED',
                        'format': 'named',
                        'message': f'Named color "{color_name}" not allowed - Use CSS variables'
                    })
                    self.stats['unapproved_colors'] += 1
                
                # Add all violations from this line
                for violation in violations_in_line:
                    file_violations.append({
                        'line': line_num,
                        **violation
                    })
            
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
