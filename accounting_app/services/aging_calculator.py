"""
账龄计算服务 - AR/AP Aging Calculator
统一的账龄计算逻辑，被ManagementReport和API路由共享使用
"""
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import date
from typing import Dict, List
from ..models import SalesInvoice, PurchaseInvoice, Customer, Supplier


class AgingCalculator:
    """
    统一的账龄计算服务
    
    用途：
    1. API路由 (/reports/ar-aging/view, /reports/ap-aging/view)
    2. ManagementReportGenerator (引用而非重复实现)
    3. 确保账龄计算的一致性
    """
    
    @staticmethod
    def calculate_ar_aging(
        db: Session,
        company_id: int,
        as_of_date: date
    ) -> Dict:
        """
        计算应收账款账龄（AR Aging）
        
        Args:
            db: 数据库会话
            company_id: 公司ID
            as_of_date: 截止日期
            
        Returns:
            {
                "customers": [...],
                "total_0_30": Decimal,
                "total_31_60": Decimal,
                "total_61_90": Decimal,
                "total_90_plus": Decimal,
                "grand_total": Decimal
            }
        """
        # 获取所有未收回的销售发票（严格小于as_of_date）
        invoices = db.query(SalesInvoice).join(Customer).filter(
            SalesInvoice.company_id == company_id,
            SalesInvoice.balance_amount > 0,
            SalesInvoice.invoice_date < as_of_date  # 关键：排除未来发票
        ).all()
        
        # 按客户分组计算账龄
        customer_aging = {}
        
        for inv in invoices:
            days_overdue = (as_of_date - inv.due_date).days
            
            if inv.customer_id not in customer_aging:
                customer_aging[inv.customer_id] = {
                    'customer_id': inv.customer_id,
                    'customer_code': inv.customer.customer_code if inv.customer else '',
                    'customer_name': inv.customer.customer_name if inv.customer else '',
                    'aging_0_30': Decimal(0),
                    'aging_31_60': Decimal(0),
                    'aging_61_90': Decimal(0),
                    'aging_90_plus': Decimal(0),
                    'total_outstanding': Decimal(0)
                }
            
            amount = inv.balance_amount
            
            if days_overdue <= 30:
                customer_aging[inv.customer_id]['aging_0_30'] += amount
            elif days_overdue <= 60:
                customer_aging[inv.customer_id]['aging_31_60'] += amount
            elif days_overdue <= 90:
                customer_aging[inv.customer_id]['aging_61_90'] += amount
            else:
                customer_aging[inv.customer_id]['aging_90_plus'] += amount
            
            customer_aging[inv.customer_id]['total_outstanding'] += amount
        
        # 计算总计
        total_0_30 = sum(c['aging_0_30'] for c in customer_aging.values())
        total_31_60 = sum(c['aging_31_60'] for c in customer_aging.values())
        total_61_90 = sum(c['aging_61_90'] for c in customer_aging.values())
        total_90_plus = sum(c['aging_90_plus'] for c in customer_aging.values())
        grand_total = total_0_30 + total_31_60 + total_61_90 + total_90_plus
        
        return {
            "customers": list(customer_aging.values()),
            "total_0_30": total_0_30,
            "total_31_60": total_31_60,
            "total_61_90": total_61_90,
            "total_90_plus": total_90_plus,
            "grand_total": grand_total
        }
    
    @staticmethod
    def calculate_ap_aging(
        db: Session,
        company_id: int,
        as_of_date: date
    ) -> Dict:
        """
        计算应付账款账龄（AP Aging）
        
        Args:
            db: 数据库会话
            company_id: 公司ID
            as_of_date: 截止日期
            
        Returns:
            {
                "suppliers": [...],
                "total_0_30": Decimal,
                "total_31_60": Decimal,
                "total_61_90": Decimal,
                "total_90_plus": Decimal,
                "grand_total": Decimal
            }
        """
        # 获取所有未付清的采购发票（严格小于as_of_date）
        invoices = db.query(PurchaseInvoice).join(Supplier).filter(
            PurchaseInvoice.company_id == company_id,
            PurchaseInvoice.balance_amount > 0,
            PurchaseInvoice.invoice_date < as_of_date  # 关键：排除未来发票
        ).all()
        
        # 按供应商分组计算账龄
        supplier_aging = {}
        
        for inv in invoices:
            days_overdue = (as_of_date - inv.due_date).days
            
            if inv.supplier_id not in supplier_aging:
                supplier_aging[inv.supplier_id] = {
                    'supplier_id': inv.supplier_id,
                    'supplier_code': inv.supplier.supplier_code if inv.supplier else '',
                    'supplier_name': inv.supplier.supplier_name if inv.supplier else '',
                    'aging_0_30': Decimal(0),
                    'aging_31_60': Decimal(0),
                    'aging_61_90': Decimal(0),
                    'aging_90_plus': Decimal(0),
                    'total_outstanding': Decimal(0)
                }
            
            amount = inv.balance_amount
            
            if days_overdue <= 30:
                supplier_aging[inv.supplier_id]['aging_0_30'] += amount
            elif days_overdue <= 60:
                supplier_aging[inv.supplier_id]['aging_31_60'] += amount
            elif days_overdue <= 90:
                supplier_aging[inv.supplier_id]['aging_61_90'] += amount
            else:
                supplier_aging[inv.supplier_id]['aging_90_plus'] += amount
            
            supplier_aging[inv.supplier_id]['total_outstanding'] += amount
        
        # 计算总计
        total_0_30 = sum(s['aging_0_30'] for s in supplier_aging.values())
        total_31_60 = sum(s['aging_31_60'] for s in supplier_aging.values())
        total_61_90 = sum(s['aging_61_90'] for s in supplier_aging.values())
        total_90_plus = sum(s['aging_90_plus'] for s in supplier_aging.values())
        grand_total = total_0_30 + total_31_60 + total_61_90 + total_90_plus
        
        return {
            "suppliers": list(supplier_aging.values()),
            "total_0_30": total_0_30,
            "total_31_60": total_31_60,
            "total_61_90": total_61_90,
            "total_90_plus": total_90_plus,
            "grand_total": grand_total
        }
    
    @staticmethod
    def calculate_aging_summary_for_management_report(
        db: Session,
        company_id: int,
        as_of_date: date
    ) -> Dict:
        """
        为Management Report生成Aging摘要
        
        这个方法调用AR和AP aging计算，返回格式化的摘要
        确保Management Report使用相同的计算逻辑
        """
        ar_result = AgingCalculator.calculate_ar_aging(db, company_id, as_of_date)
        ap_result = AgingCalculator.calculate_ap_aging(db, company_id, as_of_date)
        
        return {
            "accounts_receivable": {
                "current": float(ar_result["total_0_30"]),
                "1_30_days": float(ar_result["total_31_60"]),
                "31_60_days": float(ar_result["total_61_90"]),
                "61_90_days": float(0),  # TODO: 分离current和0-30
                "over_90_days": float(ar_result["total_90_plus"]),
                "total": float(ar_result["grand_total"])
            },
            "accounts_payable": {
                "current": float(ap_result["total_0_30"]),
                "1_30_days": float(ap_result["total_31_60"]),
                "31_60_days": float(ap_result["total_61_90"]),
                "61_90_days": float(0),
                "over_90_days": float(ap_result["total_90_plus"]),
                "total": float(ap_result["grand_total"])
            },
            "as_of_date": as_of_date.isoformat()
        }
