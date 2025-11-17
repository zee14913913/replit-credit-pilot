#!/usr/bin/env python3
"""
CreditPilot System-Wide Audit Tool
===================================

Comprehensive audit of all configuration, Python, CSS, HTML, and database files.
Identifies duplicates, deprecated files, and missing dependencies.

Usage:
    python3 scripts/system_audit.py --full
    python3 scripts/system_audit.py --config-only
    python3 scripts/system_audit.py --python-only

Author: CreditPilot Development Team
Version: 1.0.0
Last Updated: 2025-11-17
"""

import os
import json
import re
import ast
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
import subprocess

class SystemAuditor:
    """
    Comprehensive system auditor for CreditPilot.
    Scans all files and identifies duplicates, deprecations, and issues.
    """
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'git_commit': self._get_git_commit(),
            'config_files': [],
            'python_files': [],
            'css_files': [],
            'html_files': [],
            'database_configs': [],
            'duplicates': [],
            'deprecated': [],
            'issues': [],
            'statistics': {}
        }
        
        # Exclude patterns
        self.exclude_patterns = [
            'node_modules', '.git', '__pycache__', '.cache',
            '.pythonlibs', 'venv', 'env', '.venv'
        ]
    
    def _get_git_commit(self) -> str:
        """Get current git commit hash."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else 'unknown'
        except:
            return 'unknown'
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]
        except:
            return 'error'
    
    def _get_last_modified(self, file_path: Path) -> str:
        """Get file last modified time."""
        try:
            timestamp = file_path.stat().st_mtime
            return datetime.fromtimestamp(timestamp).isoformat()
        except:
            return 'unknown'
    
    def _get_git_last_modified(self, file_path: Path) -> str:
        """Get last git commit date for file."""
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%ci', str(file_path)],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else 'never'
        except:
            return 'unknown'
    
    def should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded from audit."""
        path_str = str(file_path)
        return any(pattern in path_str for pattern in self.exclude_patterns)
    
    # ========================================
    # Configuration Files Audit
    # ========================================
    
    def audit_config_files(self):
        """Audit all configuration files (.json, .yaml, .ini, .conf)."""
        print("\n🔍 Auditing configuration files...")
        
        config_extensions = ['.json', '.yaml', '.yml', '.ini', '.conf', '.toml']
        config_files = []
        
        for ext in config_extensions:
            for file_path in self.root_path.rglob(f'*{ext}'):
                if self.should_exclude(file_path):
                    continue
                
                file_info = {
                    'path': str(file_path.relative_to(self.root_path)),
                    'type': ext,
                    'size': file_path.stat().st_size,
                    'hash': self._get_file_hash(file_path),
                    'last_modified': self._get_last_modified(file_path),
                    'git_last_modified': self._get_git_last_modified(file_path),
                    'valid': self._validate_config_file(file_path)
                }
                
                config_files.append(file_info)
        
        # Detect duplicates by hash
        hash_groups = defaultdict(list)
        for cfg in config_files:
            hash_groups[cfg['hash']].append(cfg['path'])
        
        for hash_val, paths in hash_groups.items():
            if len(paths) > 1:
                self.report['duplicates'].append({
                    'type': 'config',
                    'hash': hash_val,
                    'files': paths
                })
        
        self.report['config_files'] = config_files
        print(f"  ✅ Found {len(config_files)} configuration files")
        print(f"  ⚠️ Found {len([d for d in self.report['duplicates'] if d['type'] == 'config'])} duplicate config groups")
    
    def _validate_config_file(self, file_path: Path) -> bool:
        """Validate config file format."""
        try:
            if file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    json.load(f)
                return True
            elif file_path.suffix in ['.yaml', '.yml']:
                # Skip YAML validation (requires pyyaml)
                return True
            return True
        except:
            return False
    
    # ========================================
    # Python Files Audit
    # ========================================
    
    def audit_python_files(self):
        """Audit all Python files."""
        print("\n🔍 Auditing Python files...")
        
        python_files = []
        all_imports = set()
        defined_modules = set()
        
        for file_path in self.root_path.rglob('*.py'):
            if self.should_exclude(file_path):
                continue
            
            imports = self._extract_imports(file_path)
            all_imports.update(imports)
            
            # Determine if module is defined
            module_name = str(file_path.relative_to(self.root_path)).replace('/', '.').replace('.py', '')
            defined_modules.add(module_name)
            
            file_info = {
                'path': str(file_path.relative_to(self.root_path)),
                'size': file_path.stat().st_size,
                'hash': self._get_file_hash(file_path),
                'last_modified': self._get_last_modified(file_path),
                'git_last_modified': self._get_git_last_modified(file_path),
                'imports': imports,
                'is_test': 'test_' in file_path.name or '/tests/' in str(file_path),
                'is_migration': 'migration' in str(file_path).lower(),
                'classification': 'unknown'  # Will be determined later
            }
            
            python_files.append(file_info)
        
        # Classify files as active, deprecated, or duplicate
        self._classify_python_files(python_files)
        
        # Check for missing imports
        self._check_missing_imports(all_imports, defined_modules)
        
        self.report['python_files'] = python_files
        print(f"  ✅ Found {len(python_files)} Python files")
        print(f"  📊 Active: {len([f for f in python_files if f['classification'] == 'active'])}")
        print(f"  📊 Deprecated: {len([f for f in python_files if f['classification'] == 'deprecated'])}")
        print(f"  📊 Test: {len([f for f in python_files if f['is_test']])}")
    
    def _extract_imports(self, file_path: Path) -> List[str]:
        """Extract all import statements from Python file."""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                tree = ast.parse(f.read())
                
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except:
            pass
        
        return imports
    
    def _classify_python_files(self, python_files: List[Dict]):
        """Classify Python files as active, deprecated, or duplicate."""
        # Files that are definitely active (entrypoints)
        active_entrypoints = {'app.py', 'accounting_app/main.py'}
        
        # Mark entrypoints as active
        for file_info in python_files:
            if file_info['path'] in active_entrypoints:
                file_info['classification'] = 'active'
            elif file_info['is_test']:
                file_info['classification'] = 'test'
            elif file_info['is_migration']:
                file_info['classification'] = 'migration'
            elif 'deprecated' in file_info['path'].lower() or 'old' in file_info['path'].lower():
                file_info['classification'] = 'deprecated'
                self.report['deprecated'].append({
                    'type': 'python',
                    'path': file_info['path'],
                    'reason': 'Path contains "deprecated" or "old"'
                })
            elif file_info['git_last_modified'] == 'never':
                file_info['classification'] = 'possibly_deprecated'
            else:
                # Default to active (conservative approach)
                file_info['classification'] = 'active'
    
    def _check_missing_imports(self, all_imports: Set[str], defined_modules: Set[str]):
        """Check for imports that reference non-existent modules."""
        # Filter to local imports only
        local_imports = {imp for imp in all_imports if not self._is_stdlib_or_external(imp)}
        
        missing_imports = local_imports - defined_modules
        
        for missing in missing_imports:
            self.report['issues'].append({
                'type': 'missing_import',
                'module': missing,
                'severity': 'warning'
            })
    
    def _is_stdlib_or_external(self, module_name: str) -> bool:
        """Check if module is stdlib or external package."""
        stdlib_prefixes = ['os', 'sys', 'json', 're', 'datetime', 'pathlib', 
                          'typing', 'collections', 'ast', 'hashlib', 'subprocess']
        external_prefixes = ['flask', 'fastapi', 'pandas', 'requests', 'reportlab',
                           'openpyxl', 'pdfplumber', 'PIL', 'plotly']
        
        return any(module_name.startswith(prefix) for prefix in stdlib_prefixes + external_prefixes)
    
    # ========================================
    # CSS/HTML Files Audit
    # ========================================
    
    def audit_css_files(self):
        """Audit all CSS files."""
        print("\n🔍 Auditing CSS files...")
        
        css_files = []
        
        for file_path in self.root_path.rglob('*.css'):
            if self.should_exclude(file_path):
                continue
            
            file_info = {
                'path': str(file_path.relative_to(self.root_path)),
                'size': file_path.stat().st_size,
                'hash': self._get_file_hash(file_path),
                'last_modified': self._get_last_modified(file_path),
                'git_last_modified': self._get_git_last_modified(file_path),
                'referenced_by': []  # Will be filled later
            }
            
            css_files.append(file_info)
        
        self.report['css_files'] = css_files
        print(f"  ✅ Found {len(css_files)} CSS files")
    
    def audit_html_files(self):
        """Audit all HTML template files."""
        print("\n🔍 Auditing HTML template files...")
        
        html_files = []
        
        for file_path in self.root_path.rglob('*.html'):
            if self.should_exclude(file_path):
                continue
            
            file_info = {
                'path': str(file_path.relative_to(self.root_path)),
                'size': file_path.stat().st_size,
                'hash': self._get_file_hash(file_path),
                'last_modified': self._get_last_modified(file_path),
                'git_last_modified': self._get_git_last_modified(file_path),
                'css_refs': self._extract_css_refs(file_path)
            }
            
            html_files.append(file_info)
        
        self.report['html_files'] = html_files
        print(f"  ✅ Found {len(html_files)} HTML template files")
    
    def _extract_css_refs(self, file_path: Path) -> List[str]:
        """Extract CSS file references from HTML."""
        css_refs = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Find <link rel="stylesheet" href="...">
            pattern = r'<link[^>]+href=["\']([^"\']+\.css)["\']'
            matches = re.findall(pattern, content, re.IGNORECASE)
            css_refs.extend(matches)
        except:
            pass
        
        return css_refs
    
    # ========================================
    # Database Configuration Audit
    # ========================================
    
    def audit_database_configs(self):
        """Audit database configurations."""
        print("\n🔍 Auditing database configurations...")
        
        db_files = []
        
        # Look for database.py, db.py, models.py files
        for pattern in ['**/database.py', '**/db.py', '**/models.py', '**/schema.py']:
            for file_path in self.root_path.glob(pattern):
                if self.should_exclude(file_path):
                    continue
                
                file_info = {
                    'path': str(file_path.relative_to(self.root_path)),
                    'type': 'python_db_module',
                    'last_modified': self._get_last_modified(file_path),
                    'git_last_modified': self._get_git_last_modified(file_path)
                }
                
                db_files.append(file_info)
        
        # Look for SQL migration files
        for file_path in self.root_path.rglob('*.sql'):
            if self.should_exclude(file_path):
                continue
            
            file_info = {
                'path': str(file_path.relative_to(self.root_path)),
                'type': 'sql_migration',
                'last_modified': self._get_last_modified(file_path),
                'git_last_modified': self._get_git_last_modified(file_path)
            }
            
            db_files.append(file_info)
        
        self.report['database_configs'] = db_files
        print(f"  ✅ Found {len(db_files)} database configuration files")
    
    # ========================================
    # Report Generation
    # ========================================
    
    def generate_statistics(self):
        """Generate summary statistics."""
        active_count = len([f for f in self.report['python_files'] if f['classification'] == 'active'])
        deprecated_count = len([f for f in self.report['python_files'] if f['classification'] == 'deprecated'])
        test_count = len([f for f in self.report['python_files'] if f['is_test']])
        
        self.report['statistics'] = {
            'total_config_files': len(self.report['config_files']),
            'total_python_files': len(self.report['python_files']),
            'total_css_files': len(self.report['css_files']),
            'total_html_files': len(self.report['html_files']),
            'total_database_configs': len(self.report['database_configs']),
            'total_duplicates': len(self.report['duplicates']),
            'total_deprecated': len(self.report['deprecated']),
            'total_issues': len(self.report['issues']),
            'python_active': active_count,
            'python_deprecated': deprecated_count,
            'python_test': test_count
        }
    
    def save_report(self, output_path: str = 'system_audit_report.json'):
        """Save audit report to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Full report saved to: {output_path}")
    
    def print_summary(self):
        """Print audit summary to console."""
        stats = self.report['statistics']
        
        print("\n" + "=" * 70)
        print("📊 SYSTEM AUDIT SUMMARY")
        print("=" * 70)
        print(f"Git Commit: {self.report['git_commit']}")
        print(f"Audit Time: {self.report['timestamp']}")
        print()
        print(f"📁 Configuration Files: {stats['total_config_files']}")
        print(f"🐍 Python Files: {stats['total_python_files']}")
        print(f"   - Active: {stats['python_active']}")
        print(f"   - Deprecated: {stats['python_deprecated']}")
        print(f"   - Tests: {stats['python_test']}")
        print(f"🎨 CSS Files: {stats['total_css_files']}")
        print(f"📄 HTML Templates: {stats['total_html_files']}")
        print(f"🗄️  Database Configs: {stats['total_database_configs']}")
        print()
        print(f"⚠️ Duplicate File Groups: {stats['total_duplicates']}")
        print(f"📦 Deprecated Files: {stats['total_deprecated']}")
        print(f"🚨 Issues Found: {stats['total_issues']}")
        print("=" * 70)
    
    def run_full_audit(self):
        """Run complete system audit."""
        print("╔═══════════════════════════════════════════════════════════════════╗")
        print("║       CreditPilot System Audit - Comprehensive Analysis          ║")
        print("╚═══════════════════════════════════════════════════════════════════╝")
        
        self.audit_config_files()
        self.audit_python_files()
        self.audit_css_files()
        self.audit_html_files()
        self.audit_database_configs()
        self.generate_statistics()
        self.print_summary()
        self.save_report()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='CreditPilot System Audit Tool')
    parser.add_argument('--full', action='store_true', help='Run full system audit')
    parser.add_argument('--config-only', action='store_true', help='Audit config files only')
    parser.add_argument('--python-only', action='store_true', help='Audit Python files only')
    parser.add_argument('--output', default='system_audit_report.json', help='Output file path')
    
    args = parser.parse_args()
    
    auditor = SystemAuditor()
    
    if args.config_only:
        auditor.audit_config_files()
    elif args.python_only:
        auditor.audit_python_files()
    else:
        auditor.run_full_audit()
    
    auditor.save_report(args.output)


if __name__ == '__main__':
    main()
