"""
测试脚本：验证贷款数据采集系统
测试BNM API和银行爬虫功能
"""
import sys
sys.path.insert(0, '/home/runner/workspace')

import asyncio
from accounting_app.services.bnm_api_client import bnm_client
from accounting_app.services.comprehensive_loan_scraper import comprehensive_scraper

def test_bnm_api():
    """测试BNM官方API"""
    print("=" * 80)
    print("📊 测试 BNM API (Bank Negara Malaysia 官方利率)")
    print("=" * 80)
    print()
    
    try:
        # 获取所有利率数据
        rates = bnm_client.get_all_rates()
        
        print("✅ BNM API连接成功")
        print()
        
        # 显示OPR
        if rates.get('opr'):
            print("隔夜政策利率 (OPR):")
            print(f"  利率: {rates['opr'].get('opr', 'N/A')}%")
            print(f"  生效日期: {rates['opr'].get('effective_date', 'N/A')}")
            print()
        
        # 显示数据来源
        print(f"数据来源: {', '.join(rates.get('data_sources', []))}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ BNM API测试失败: {e}")
        return False


def test_scraper_single_bank():
    """测试单个银行爬虫"""
    print("=" * 80)
    print("🕷️ 测试单个银行爬虫 (Maybank)")
    print("=" * 80)
    print()
    
    try:
        # 获取Maybank配置
        maybank = None
        for bank in comprehensive_scraper.config['commercial_banks']:
            if bank['code'] == 'maybank':
                maybank = bank
                break
        
        if not maybank:
            print("❌ 未找到Maybank配置")
            return False
        
        print(f"目标银行: {maybank['name']}")
        print(f"网站: {maybank['website']}")
        print()
        
        # 爬取产品
        products = comprehensive_scraper.scrape_institution(maybank)
        
        print(f"✅ 爬取成功")
        print(f"找到产品数: {len(products)}")
        print()
        
        # 显示产品详情
        if products:
            print("产品列表:")
            for idx, product in enumerate(products[:5], 1):
                print(f"\n  {idx}. {product['product']}")
                print(f"     类型: {product['type']}")
                print(f"     利率: {product['rate']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 银行爬虫测试失败: {e}")
        return False


def test_scraper_category():
    """测试按类别爬取（数字银行）"""
    print()
    print("=" * 80)
    print("🚀 测试按类别爬取 (数字银行 5家)")
    print("=" * 80)
    print()
    
    try:
        # 爬取数字银行
        products = comprehensive_scraper.scrape_by_category('digital_banks')
        
        print(f"✅ 爬取完成")
        print(f"总计产品数: {len(products)}")
        print()
        
        # 按银行分组统计
        stats = {}
        for product in products:
            bank = product['bank']
            stats[bank] = stats.get(bank, 0) + 1
        
        print("按银行统计:")
        for bank, count in stats.items():
            print(f"  - {bank}: {count} 个产品")
        
        return True
        
    except Exception as e:
        print(f"❌ 类别爬取测试失败: {e}")
        return False


def test_data_validation():
    """测试数据验证机制"""
    print()
    print("=" * 80)
    print("🛡️ 测试数据验证机制")
    print("=" * 80)
    print()
    
    # 模拟产品数据
    test_products = [
        {
            'source': 'test-bank',
            'bank': 'Test Bank',
            'product': 'Test Loan',
            'type': 'PERSONAL',
            'rate': '5.5',
            'summary': 'Test product'
        },
        {
            'source': 'invalid-bank',
            'bank': 'Invalid Bank',
            'product': None,  # 缺少产品名
            'type': 'HOME'
        },
        {
            'source': 'another-bank',
            'bank': 'Another Bank',
            'product': 'Another Loan',
            'type': 'BUSINESS',
            'rate': '7.2%',
            'summary': None  # 缺少summary，应自动补充
        }
    ]
    
    # 验证数据
    valid_products = comprehensive_scraper.validate_products(test_products)
    
    print(f"原始产品数: {len(test_products)}")
    print(f"验证通过数: {len(valid_products)}")
    print()
    
    # 检查利率标准化
    for product in valid_products:
        has_percent = '%' in product['rate']
        print(f"✅ {product['product']}: {product['rate']} ({'含%' if has_percent else '缺%'})")
    
    return len(valid_products) == 2  # 应该有2个有效产品


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "贷款数据采集系统测试套件" + " " * 34 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    results = []
    
    # 测试1：BNM API
    results.append(('BNM API', test_bnm_api()))
    
    # 测试2：单个银行爬虫
    results.append(('单个银行爬虫', test_scraper_single_bank()))
    
    # 测试3：按类别爬取
    results.append(('按类别爬取', test_scraper_category()))
    
    # 测试4：数据验证
    results.append(('数据验证', test_data_validation()))
    
    # 测试结果汇总
    print()
    print("=" * 80)
    print("📋 测试结果汇总")
    print("=" * 80)
    print()
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print()
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print()
        print("🎉 所有测试通过！系统运行正常。")
    else:
        print()
        print("⚠️ 部分测试失败，请检查日志。")


if __name__ == '__main__':
    run_all_tests()
