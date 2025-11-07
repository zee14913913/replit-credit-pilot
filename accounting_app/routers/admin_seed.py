from fastapi import APIRouter
from datetime import date
from decimal import Decimal
from sqlalchemy import select
from accounting_app.db import get_session
from accounting_app.models import Supplier, Transaction

router = APIRouter(prefix="/admin/seed", tags=["Admin"])

@router.post("/demo")
def seed_demo():
    """
    种子数据：创建演示供应商和交易记录
    幂等设计：重复调用不会重复插入
    """
    with get_session() as db:
        names = [
            ("DINAS RESTAURANT", "Kuala Lumpur", ""),
            ("HUAWEI", "Selangor", ""),
            ("PASAR RAYA", "Kuala Lumpur", ""),
        ]
        
        for nm, addr, reg in names:
            existing = db.scalar(
                select(Supplier).where(Supplier.supplier_name == nm)
            )
            if not existing:
                db.add(Supplier(
                    company_id=1,
                    supplier_code=nm[:10].upper().replace(" ", "_"),
                    supplier_name=nm,
                    address=addr,
                ))
        db.flush()
        
        dinas = db.scalar(select(Supplier).where(Supplier.supplier_name == "DINAS RESTAURANT"))
        huawei = db.scalar(select(Supplier).where(Supplier.supplier_name == "HUAWEI"))
        pasar = db.scalar(select(Supplier).where(Supplier.supplier_name == "PASAR RAYA"))
        
        today = date.today().replace(day=5)
        
        if dinas and not db.scalar(select(Transaction).where(Transaction.supplier_id == dinas.id)):
            db.add_all([
                Transaction(supplier_id=dinas.id, txn_date=today, description="Meals", amount=Decimal("300.00")),
                Transaction(supplier_id=dinas.id, txn_date=today, description="Meals", amount=Decimal("550.00")),
            ])
        
        if huawei and not db.scalar(select(Transaction).where(Transaction.supplier_id == huawei.id)):
            db.add_all([
                Transaction(supplier_id=huawei.id, txn_date=today, description="Device", amount=Decimal("700.00")),
                Transaction(supplier_id=huawei.id, txn_date=today, description="Service", amount=Decimal("500.00")),
            ])
        
        if pasar and not db.scalar(select(Transaction).where(Transaction.supplier_id == pasar.id)):
            db.add_all([
                Transaction(supplier_id=pasar.id, txn_date=today, description="Groceries", amount=Decimal("500.00")),
            ])
    
    return {"ok": True, "message": "Demo data seeded successfully"}
