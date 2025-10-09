"""
测试完整的咨询服务业务流程
从优化建议 → 预约咨询 → 签合同 → 代付 → 利润分成
"""

from advisory.optimization_proposal import OptimizationProposal
from advisory.consultation_booking import ConsultationBooking
from advisory.service_contract import ServiceContract
from advisory.payment_on_behalf import PaymentOnBehalf
from db.database import get_db

def test_complete_advisory_workflow():
    """测试完整业务流程"""
    
    print("=" * 80)
    print("🎯 测试INFINITE GZ完整咨询服务流程")
    print("=" * 80)
    
    # 获取测试客户
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM customers LIMIT 1')
        customer = cursor.fetchone()
        
        if not customer:
            print("❌ 没有客户数据")
            return
        
        customer_id = customer['id']
        customer_name = customer['name']
    
    print(f"\n📋 客户: {customer_name} (ID: {customer_id})")
    
    # ==================== 步骤 1: 生成优化建议 ====================
    print("\n" + "="*80)
    print("【步骤 1】生成优化建议对比方案")
    print("="*80)
    
    optimizer = OptimizationProposal()
    proposals = optimizer.get_all_proposals(customer_id)
    
    if not proposals:
        print("❌ 无法生成优化建议（可能客户数据不足）")
        return
    
    proposal = proposals[0]
    
    print(f"\n✅ 优化建议类型: {proposal['proposal_type']}")
    print(f"\n📊 现状 vs 优化方案对比：")
    print(f"   现状: {proposal['comparison']['before']}")
    print(f"   优化: {proposal['comparison']['after']}")
    print(f"   客户节省: {proposal['comparison']['you_save']}")
    print(f"   我们赚取: {proposal['comparison']['we_earn']}")
    
    suggestion_id = proposal['suggestion_id']
    
    # ==================== 步骤 2: 客户预约咨询 ====================
    print("\n" + "="*80)
    print("【步骤 2】客户接受建议，预约咨询")
    print("="*80)
    
    booking = ConsultationBooking()
    consultation_request = booking.create_consultation_request(
        customer_id=customer_id,
        suggestion_id=suggestion_id,
        preferred_method='meeting',
        preferred_date='2025-10-15 14:00:00',
        notes='希望详细了解债务整合方案'
    )
    
    if not consultation_request:
        print("❌ 预约请求失败")
        return
    
    print(f"✅ {consultation_request['message']}")
    print(f"   预约ID: {consultation_request['request_id']}")
    print(f"   联系方式: {'见面' if consultation_request['preferred_method'] == 'meeting' else '通话'}")
    
    request_id = consultation_request['request_id']
    
    # ==================== 步骤 3: 确认咨询安排 ====================
    print("\n" + "="*80)
    print("【步骤 3】INFINITE GZ确认咨询安排")
    print("="*80)
    
    confirmed = booking.confirm_consultation(
        request_id=request_id,
        confirmed_date='2025-10-15 15:00:00',
        meeting_location='INFINITE GZ办公室，Kuala Lumpur'
    )
    
    print(f"✅ 咨询已确认")
    print(f"   时间: {confirmed['confirmed_date']}")
    print(f"   地点: {confirmed['meeting_location']}")
    
    # ==================== 步骤 4: 完成咨询，客户决定继续 ====================
    print("\n" + "="*80)
    print("【步骤 4】咨询完成，客户决定使用服务")
    print("="*80)
    
    completed = booking.complete_consultation(
        request_id=request_id,
        outcome_notes='客户已了解详细方案，同意继续服务',
        proceed_with_service=True
    )
    
    print(f"✅ 咨询已完成")
    print(f"   客户决定: {'继续服务' if completed['proceed_with_service'] else '暂不继续'}")
    
    # ==================== 步骤 5: 生成授权合同 ====================
    print("\n" + "="*80)
    print("【步骤 5】生成授权同意合同")
    print("="*80)
    
    contract_service = ServiceContract()
    contract = contract_service.generate_authorization_contract(
        customer_id=customer_id,
        suggestion_id=suggestion_id,
        consultation_request_id=request_id
    )
    
    print(f"✅ 合同已生成")
    print(f"   合同编号: {contract['contract_number']}")
    print(f"   客户将获得: RM {contract['customer_gets']:.2f}")
    print(f"   我们将获得: RM {contract['our_fee']:.2f}")
    print(f"   合同文件: {contract['filename']}")
    
    contract_id = contract['contract_id']
    
    # ==================== 步骤 6: 双方签字 ====================
    print("\n" + "="*80)
    print("【步骤 6】双方签署合同")
    print("="*80)
    
    # 客户签字
    customer_sign = contract_service.sign_contract(contract_id, 'customer')
    print(f"✅ 客户已签字")
    
    # 公司签字
    company_sign = contract_service.sign_contract(contract_id, 'company')
    print(f"✅ 公司已签字")
    
    if company_sign['both_signed']:
        print(f"🎉 合同已生效！双方签字完成")
    
    # ==================== 步骤 7: 检查是否可以开始代付 ====================
    print("\n" + "="*80)
    print("【步骤 7】检查是否可以开始代付服务")
    print("="*80)
    
    payment_service = PaymentOnBehalf()
    can_start = payment_service.can_start_payment_service(contract_id)
    
    if can_start['can_start']:
        print(f"✅ {can_start['message']}")
    else:
        print(f"❌ {can_start['reason']}")
        return
    
    # ==================== 步骤 8: 开始代付 ====================
    print("\n" + "="*80)
    print("【步骤 8】开始为客户代付账单")
    print("="*80)
    
    # 获取客户的第一张信用卡
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id FROM credit_cards WHERE customer_id = ? LIMIT 1
        ''', (customer_id,))
        card = cursor.fetchone()
        card_id = card['id'] if card else None
    
    if card_id:
        payment_result = payment_service.record_payment_on_behalf(
            contract_id=contract_id,
            card_id=card_id,
            amount=2500.00,
            payment_type='bill_payment',
            notes='代付信用卡账单'
        )
        
        if payment_result['success']:
            print(f"✅ {payment_result['message']}")
        else:
            print(f"❌ {payment_result['reason']}")
    
    # ==================== 步骤 9: 计算实际利润分成 ====================
    print("\n" + "="*80)
    print("【步骤 9】计算实际利润分成（50% / 50%）")
    print("="*80)
    
    profit_share = payment_service.calculate_actual_profit_share(contract_id)
    
    print(f"✅ 利润分成计算完成")
    print(f"\n   📊 最终结算：")
    print(f"   总共为客户节省/赚取: {profit_share['breakdown']['total_saved_or_earned']}")
    print(f"   客户保留 (50%): {profit_share['breakdown']['customer_keeps_50%']}")
    print(f"   INFINITE GZ 服务费 (50%): {profit_share['breakdown']['infinite_gz_fee_50%']}")
    
    # ==================== 步骤 10: 记录客户支付服务费 ====================
    print("\n" + "="*80)
    print("【步骤 10】客户支付50%服务费")
    print("="*80)
    
    fee_payment = payment_service.record_fee_payment(
        contract_id=contract_id,
        payment_method='bank_transfer',
        transaction_ref='TXN20251010123456'
    )
    
    if fee_payment['success']:
        print(f"✅ {fee_payment['message']}")
    
    # ==================== 完整服务摘要 ====================
    print("\n" + "="*80)
    print("【服务完整摘要】")
    print("="*80)
    
    summary = payment_service.get_service_summary(contract_id)
    
    print(f"\n客户: {summary['contract']['customer_name']}")
    print(f"服务类型: {summary['contract']['service_type']}")
    print(f"合同编号: {summary['contract']['contract_number']}")
    print(f"合同状态: {summary['contract']['status']}")
    print(f"\n财务摘要:")
    print(f"  预估节省: RM {summary['financial_summary']['estimated_savings']:.2f}")
    print(f"  实际节省: RM {summary['financial_summary']['actual_savings']:.2f}")
    print(f"  客户获利: RM {summary['financial_summary']['customer_profit']:.2f}")
    print(f"  我们收费: RM {summary['financial_summary']['our_fee']:.2f}")
    print(f"  费用已付: {'是' if summary['financial_summary']['fee_paid'] else '否'}")
    
    print(f"\n代付历史: {len(summary['payment_history'])} 笔记录")
    for payment in summary['payment_history']:
        print(f"  - {payment['payment_date']}: RM {payment['amount']:.2f} ({payment['payment_type']})")
    
    print("\n" + "="*80)
    print("✅ 完整业务流程测试成功！")
    print("="*80)
    print("\n💡 业务模式总结：")
    print("   1. 为客户分析并生成优化建议")
    print("   2. 显示对比：现状 vs 优化方案")
    print("   3. 客户接受后预约咨询")
    print("   4. 见面/通话详细说明方案")
    print("   5. 生成授权合同，双方签字")
    print("   6. 签字后开始代付服务")
    print("   7. 完成后计算实际节省/赚取")
    print("   8. 50/50分成，只有省钱/赚钱才收费")
    print("   9. 如果没省钱/赚钱，不收分毫！")
    print("="*80)

if __name__ == '__main__':
    try:
        test_complete_advisory_workflow()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
