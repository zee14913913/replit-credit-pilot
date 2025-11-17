#!/usr/bin/env python3
"""
CreditPilot Page Health Check Tool
===================================

Tests all critical page routes for errors and availability.

Usage:
    python3 scripts/page_health_check.py

Author: CreditPilot Development Team
Version: 1.0.0
Last Updated: 2025-11-17
"""

import requests
from typing import List, Dict, Tuple
import json
from datetime import datetime

class PageHealthChecker:
    """Check health of all CreditPilot pages."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:5000"):
        self.base_url = base_url
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def check_route(self, route: str, description: str, requires_auth: bool = False) -> Dict:
        """Check a single route."""
        url = f"{self.base_url}{route}"
        self.total_tests += 1
        
        try:
            response = requests.get(url, allow_redirects=False, timeout=5)
            
            # Success cases
            if response.status_code == 200:
                self.passed_tests += 1
                return {
                    'route': route,
                    'description': description,
                    'status': '✅ OK',
                    'status_code': 200,
                    'requires_auth': requires_auth
                }
            
            # Expected redirect to login
            elif response.status_code == 302 and requires_auth:
                if '/admin/login' in response.headers.get('Location', ''):
                    self.passed_tests += 1
                    return {
                        'route': route,
                        'description': description,
                        'status': '✅ OK (Protected)',
                        'status_code': 302,
                        'requires_auth': requires_auth
                    }
            
            # Error cases
            else:
                self.failed_tests += 1
                return {
                    'route': route,
                    'description': description,
                    'status': f'❌ ERROR {response.status_code}',
                    'status_code': response.status_code,
                    'requires_auth': requires_auth
                }
                
        except requests.exceptions.ConnectionError:
            self.failed_tests += 1
            return {
                'route': route,
                'description': description,
                'status': '❌ CONNECTION ERROR',
                'status_code': 0,
                'requires_auth': requires_auth,
                'error': 'Server not running'
            }
        except Exception as e:
            self.failed_tests += 1
            return {
                'route': route,
                'description': description,
                'status': f'❌ EXCEPTION',
                'status_code': 0,
                'requires_auth': requires_auth,
                'error': str(e)
            }
    
    def check_all_pages(self):
        """Check all critical pages."""
        print("╔═══════════════════════════════════════════════════════════════════╗")
        print("║     CreditPilot Page Health Check - All Routes Validation        ║")
        print("╚═══════════════════════════════════════════════════════════════════╝\n")
        
        # Define all routes to check
        routes = [
            # Public routes
            ('/', 'Homepage/Dashboard', False),
            ('/admin/login', 'Admin Login Page', False),
            
            # Protected routes (should redirect to login)
            ('/admin', 'Admin Dashboard', True),
            ('/customers', 'Customers List', True),
            ('/credit-cards', 'Credit Cards List', True),
            ('/credit-card/ledger', 'Credit Card Ledger', True),
            ('/loan-evaluate', 'Loan Evaluation', True),
            ('/receipts', 'Receipts Management', True),
            ('/savings/customers', 'Savings Customers', True),
            ('/savings/accounts', 'Savings Accounts', True),
            ('/reports/center', 'Report Center', True),
            ('/batch/auto-upload', 'Batch Upload', True),
            ('/monthly-summary', 'Monthly Summary', True),
        ]
        
        print("🔍 Testing pages...\n")
        
        for route, description, requires_auth in routes:
            result = self.check_route(route, description, requires_auth)
            if result:  # Check if result is not None
                self.results.append(result)
                # Print result
                print(f"{result['status']:20} {route:30} - {description}")
        
        self.print_summary()
        self.save_report()
    
    def print_summary(self):
        """Print summary of test results."""
        print("\n" + "=" * 70)
        print("📊 HEALTH CHECK SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        
        if self.failed_tests == 0:
            print("\n✅ ALL PAGES HEALTHY - 100% AVAILABILITY")
        else:
            print(f"\n⚠️ {self.failed_tests} PAGES HAVE ISSUES")
            print("\nFailed Routes:")
            for result in self.results:
                if result['status'].startswith('❌'):
                    print(f"  - {result['route']}: {result['status']}")
                    if 'error' in result:
                        print(f"    Error: {result['error']}")
        
        print("=" * 70)
    
    def save_report(self):
        """Save detailed report to file."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'success_rate': round((self.passed_tests / self.total_tests * 100), 2) if self.total_tests > 0 else 0,
            'results': self.results
        }
        
        with open('page_health_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: page_health_report.json")

def main():
    checker = PageHealthChecker()
    checker.check_all_pages()
    
    # Exit with error code if any tests failed
    if checker.failed_tests > 0:
        exit(1)
    else:
        exit(0)

if __name__ == '__main__':
    main()
