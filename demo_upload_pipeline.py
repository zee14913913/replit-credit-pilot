"""
Upload Pipeline 演示脚本
展示完整的文件上传、解析、分类、对比流程
"""
from services.upload_orchestrator import UploadOrchestrator
from services.owner_gz_classifier import OwnerGZClassifier

def demo_lee_e_kai_upload():
    """
    演示：LEE E KAI的AmBank Islamic账单上传
    """
    print("="*80)
    print("🚀 CreditPilot Upload Pipeline 演示")
    print("="*80)
    print("\n示例：LEE E KAI - AmBank Islamic 2025年10月账单\n")
    
    # ========================================
    # 模拟数据
    # ========================================
    
    # 1. 模拟解析结果
    mock_parsed_data = {
        'owner_name': 'LEE E KAI',
        'customer_code': 'LEE_EK_009',
        'bank_name': 'AmBank Islamic',
        'statement_date': '2025-10-28',
        'due_date': '2025-11-15',
        'statement_total': 14515.00,
        'minimum_payment': 450.00
    }
    
    # 2. 模拟交易记录（156笔交易）
    mock_transactions = [
        # Owner's Expenses（个人消费）
        {'merchant_name': 'STARBUCKS PAVILION KL', 'amount': 28.50, 'transaction_date': '2025-10-01', 'description': ''},
        {'merchant_name': 'MCDONALD BANGSAR', 'amount': 15.90, 'transaction_date': '2025-10-02', 'description': ''},
        {'merchant_name': 'SHOPPING MALL', 'amount': 320.00, 'transaction_date': '2025-10-03', 'description': 'Clothing'},
        {'merchant_name': 'CINEMA TGV', 'amount': 45.00, 'transaction_date': '2025-10-05', 'description': ''},
        {'merchant_name': 'RESTAURANT JALAN ALOR', 'amount': 85.00, 'transaction_date': '2025-10-06', 'description': ''},
        
        # GZ's Expenses（INFINITE GZ业务支出）
        {'merchant_name': '7SL TRADING', 'amount': 2500.00, 'transaction_date': '2025-10-10', 'description': 'Office supplies'},
        {'merchant_name': 'DINAS RAUB', 'amount': 1800.00, 'transaction_date': '2025-10-12', 'description': 'Equipment'},
        {'merchant_name': 'AI SMART TECH SDN BHD', 'amount': 1200.00, 'transaction_date': '2025-10-15', 'description': 'Tech services'},
        {'merchant_name': 'HUAWEI STORE', 'amount': 450.00, 'transaction_date': '2025-10-18', 'description': 'Business phone'},
        {'merchant_name': 'TESCO COMMERCIAL', 'amount': 365.00, 'transaction_date': '2025-10-20', 'description': 'Office groceries'},
        
        # 更多Owner交易
        {'merchant_name': 'PHARMACY GUARDIAN', 'amount': 55.00, 'transaction_date': '2025-10-22', 'description': ''},
        {'merchant_name': 'GYM FITNESS FIRST', 'amount': 180.00, 'transaction_date': '2025-10-25', 'description': 'Monthly fee'},
        {'merchant_name': 'CAFE OLD TOWN', 'amount': 22.00, 'transaction_date': '2025-10-27', 'description': ''},
    ]
    
    # 补充更多交易使总额接近14515.00
    # Owner: 约8200
    for i in range(82):
        mock_transactions.append({
            'merchant_name': f'SHOP_{i:03d}',
            'amount': 92.00,
            'transaction_date': f'2025-10-{(i % 28) + 1:02d}',
            'description': 'Personal expense'
        })
    
    # GZ: 约6315
    for i in range(56):
        mock_transactions.append({
            'merchant_name': f'SUPPLIER_{i:03d}',
            'amount': 108.00,
            'transaction_date': f'2025-10-{(i % 28) + 1:02d}',
            'description': 'Business expense'
        })
    
    # ========================================
    # 执行Pipeline
    # ========================================
    
    orchestrator = UploadOrchestrator()
    classifier = OwnerGZClassifier()
    
    # Stage 1: Owner/GZ分类
    print("\n" + "="*80)
    print("📊 Stage 1: Owner/GZ自动分类")
    print("="*80)
    
    result = classifier.execute_full_classification(
        transaction_uuid='demo-uuid-12345',
        transactions=mock_transactions,
        statement_total=mock_parsed_data['statement_total'],
        customer_name=mock_parsed_data['owner_name'],
        bank_name=mock_parsed_data['bank_name'],
        statement_date=mock_parsed_data['statement_date'],
        due_date=mock_parsed_data['due_date'],
        minimum_payment=mock_parsed_data['minimum_payment']
    )
    
    # ========================================
    # 展示结果
    # ========================================
    
    print("\n" + "="*80)
    print("✅ 分类完成！")
    print("="*80)
    
    comparison = result['comparison_result']
    
    print(f"\n📈 Owner's Expenses（个人消费）")
    print(f"   交易数: {comparison['owner_count']} 笔")
    print(f"   总额: RM {comparison['owner_total']:,.2f}")
    
    print(f"\n🏢 GZ's Expenses（INFINITE GZ业务支出）")
    print(f"   交易数: {comparison['gz_count']} 笔")
    print(f"   总额: RM {comparison['gz_total']:,.2f}")
    
    print(f"\n📊 验证结果")
    print(f"   计算总额: RM {comparison['calculated_total']:,.2f}")
    print(f"   原件总额: RM {comparison['statement_total']:,.2f}")
    print(f"   差异: RM {comparison['difference']:,.2f}")
    print(f"   状态: {'✅ 验证通过' if comparison['is_match'] else '❌ 需要审核'}")
    
    # ========================================
    # 展示对比表格
    # ========================================
    
    print("\n" + "="*80)
    print("📄 对比表格预览")
    print("="*80)
    print(result['comparison_table'])
    
    # ========================================
    # 展示原件路径
    # ========================================
    
    print("\n" + "="*80)
    print("📂 文件存储路径（固定位置，绝不丢失）")
    print("="*80)
    
    original_path = (
        f"static/uploads/customers/{mock_parsed_data['customer_code']}/"
        f"statements/original/{mock_parsed_data['bank_name']}/2025-10/"
        f"{mock_parsed_data['bank_name']}_2025-10-28_ORIGINAL.pdf"
    )
    
    backup_path = original_path.replace('static/uploads', 'static/uploads_backup')
    
    print(f"\n主存储: {original_path}")
    print(f"备份: {backup_path}")
    
    print("\n" + "="*80)
    print("✅ Pipeline完成！文件已安全存储")
    print("="*80)
    
    return result


def demo_constraints_check():
    """
    演示：Architect强制性约束检查
    """
    print("\n" + "="*80)
    print("🛡️  ARCHITECT强制性约束检查")
    print("="*80)
    
    checks = [
        "✅ 文件必须通过Upload Orchestrator",
        "✅ 禁止直接调用FileStorageManager.save_file()",
        "✅ 必须提取7个强制字段",
        "✅ 置信度必须≥0.98",
        "✅ 必须执行Owner/GZ分类",
        "✅ 必须生成对比表格",
        "✅ 必须双写（主存储+备份）",
        "✅ 必须注册到file_registry",
        "✅ 每个状态变更必须记录到audit log",
        "✅ 原件路径固定，禁止移动/删除"
    ]
    
    for check in checks:
        print(f"  {check}")
    
    print("\n" + "="*80)
    print("🚨 违反任何约束 → 自动失败或转人工审核")
    print("="*80)


def demo_full_system():
    """
    完整系统演示
    """
    print("\n\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "CreditPilot Upload System V2.0" + " "*28 + "║")
    print("║" + " "*15 + "强制性文件处理Pipeline + Owner/GZ分类" + " "*22 + "║")
    print("╚" + "="*78 + "╝")
    
    # 1. 演示上传流程
    demo_lee_e_kai_upload()
    
    # 2. 演示约束检查
    demo_constraints_check()
    
    print("\n\n" + "="*80)
    print("🎉 系统演示完成！")
    print("="*80)
    print("\n核心功能：")
    print("  1. ✅ 自动识别文件主人（LEE E KAI）")
    print("  2. ✅ 自动分类Owner/GZ支出")
    print("  3. ✅ 计算各类别总额")
    print("  4. ✅ 生成对比表格（计算 vs 原件）")
    print("  5. ✅ 验证计算准确性（差异≤RM 0.01）")
    print("  6. ✅ 原件固定位置存储")
    print("  7. ✅ 双写备份机制")
    print("  8. ✅ 完整审计追踪")
    print("  9. ✅ Architect强制约束")
    print("  10. ✅ 防止文件丢失")
    print("\n" + "="*80)


if __name__ == '__main__':
    demo_full_system()
