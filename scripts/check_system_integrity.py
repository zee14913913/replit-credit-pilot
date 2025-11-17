#!/usr/bin/env python3
"""
CreditPilot System Integrity Checker
=====================================

Verifies system health and configuration integrity.

Usage:
    python3 scripts/check_system_integrity.py
    python3 scripts/check_system_integrity.py --detailed

Author: CreditPilot Development Team
Version: 1.0.0
Last Updated: 2025-11-17
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple

class SystemIntegrityChecker:
    """Comprehensive system integrity validator."""
    
    def __init__(self):
        self.root = Path(".")
        self.errors = []
        self.warnings = []
        self.passed = []
        
    def check_all(self) -> bool:
        """Run all integrity checks."""
        print("╔═══════════════════════════════════════════════════════════════════╗")
        print("║     CreditPilot System Integrity Check - Full Validation         ║")
        print("╚═══════════════════════════════════════════════════════════════════╝\n")
        
        self.check_config_files()
        self.check_entry_points()
        self.check_database_files()
        self.check_deprecated_imports()
        self.check_environment_secrets()
        
        self.print_summary()
        return len(self.errors) == 0
    
    def check_config_files(self):
        """Verify all required config files exist and are valid."""
        print("🔍 Checking configuration files...")
        
        required_configs = [
            ('config/app_settings.json', 'Main application settings'),
            ('config/colors.json', 'UI color palette'),
            ('config/database.json', 'Database configuration'),
            ('config/business_rules.json', 'Business logic rules')
        ]
        
        for config_file, description in required_configs:
            if not Path(config_file).exists():
                self.errors.append(f"Missing required config: {config_file} ({description})")
                continue
            
            # Validate JSON format
            try:
                with open(config_file, 'r') as f:
                    json.load(f)
                self.passed.append(f"✅ {config_file}: Valid JSON")
            except json.JSONDecodeError as e:
                self.errors.append(f"Invalid JSON in {config_file}: {e}")
        
        print(f"  Checked {len(required_configs)} config files\n")
    
    def check_entry_points(self):
        """Verify core entry point files exist."""
        print("🔍 Checking entry point files...")
        
        entry_points = [
            ('app.py', 'Flask main entry point'),
            ('accounting_app/main.py', 'FastAPI backend entry point'),
            ('db/database.py', 'Database manager')
        ]
        
        for file_path, description in entry_points:
            if not Path(file_path).exists():
                self.errors.append(f"Missing entry point: {file_path} ({description})")
            else:
                self.passed.append(f"✅ {file_path}: Found")
        
        print(f"  Checked {len(entry_points)} entry points\n")
    
    def check_database_files(self):
        """Verify database files exist."""
        print("🔍 Checking database files...")
        
        db_file = Path('db/smart_loan_manager.db')
        if not db_file.exists():
            self.warnings.append("Database file not found (may be first run)")
        else:
            size_mb = db_file.stat().st_size / (1024 * 1024)
            self.passed.append(f"✅ Database exists ({size_mb:.2f} MB)")
        
        print(f"  Database status checked\n")
    
    def check_deprecated_imports(self):
        """Check if any active code imports from DEPRECATED folder."""
        print("🔍 Checking for deprecated imports...")
        
        deprecated_imports = 0
        active_py_files = list(Path(".").rglob("*.py"))
        
        for py_file in active_py_files:
            if 'DEPRECATED' in str(py_file):
                continue  # Skip deprecated files themselves
            if any(x in str(py_file) for x in ['.cache', '.pythonlibs', 'node_modules']):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'from DEPRECATED' in content or 'import DEPRECATED' in content:
                        self.errors.append(f"Deprecated import found in: {py_file}")
                        deprecated_imports += 1
            except:
                pass
        
        if deprecated_imports == 0:
            self.passed.append("✅ No deprecated imports found")
        
        print(f"  Scanned for deprecated imports\n")
    
    def check_environment_secrets(self):
        """Verify required environment secrets are set."""
        print("🔍 Checking environment secrets...")
        
        recommended_secrets = [
            'FLASK_SECRET_KEY',
            'OPENAI_API_KEY',
            'DATABASE_URL'
        ]
        
        for secret in recommended_secrets:
            if os.getenv(secret):
                self.passed.append(f"✅ {secret}: Set")
            else:
                self.warnings.append(f"Environment secret not set: {secret} (may cause runtime errors)")
        
        print(f"  Checked environment secrets\n")
    
    def print_summary(self):
        """Print summary report."""
        print("=" * 70)
        print("📊 SYSTEM INTEGRITY REPORT")
        print("=" * 70)
        
        print(f"\n✅ PASSED CHECKS: {len(self.passed)}")
        for item in self.passed[:5]:  # Show first 5
            print(f"  {item}")
        if len(self.passed) > 5:
            print(f"  ... and {len(self.passed) - 5} more")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.errors:
            print(f"\n❌ ERRORS: {len(self.errors)}")
            for error in self.errors:
                print(f"  - {error}")
            print("\n🚨 SYSTEM INTEGRITY: FAILED")
            print("   Fix errors above before deploying.")
        else:
            print("\n✅ SYSTEM INTEGRITY: PASSED")
            if self.warnings:
                print("   ⚠️ Note: Some warnings present, but system is functional.")
            else:
                print("   All checks passed successfully!")
        
        print("=" * 70)

def main():
    checker = SystemIntegrityChecker()
    success = checker.check_all()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
