# accounting_app/services/loans_harvester.py
import os
import datetime as dt
from typing import List, Dict, Any

TZ = os.getenv("TZ", "Asia/Kuala_Lumpur")

def _now_iso() -> str:
    return dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat()

def harvest_loans() -> List[Dict[str, Any]]:
    """
    贷款资讯聚合器（占位版）：
    - 若未配置 PERPLEXITY_API_KEY，则返回示例数据（不报错）
    - 若后续接入真实抓取逻辑：在 TODO 区替换即可
    """
    api_key = os.getenv("PERPLEXITY_API_KEY", "").strip()
    model = os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-large-128k-online")

    if not api_key:
        sample = [
            {
                "source": "Bank A",
                "product": "Home Loan Flexi 3.75%",
                "rate": 3.75,
                "type": "Home Loan",
                "link": "https://example.com/loans/bank-a-home-flexi",
                "snapshot": "首购族 90% 融资，灵活提前还款，无违约金。",
                "pulled_at": _now_iso(),
            },
            {
                "source": "Digital Bank X",
                "product": "Personal Loan Promo 6.88%",
                "rate": 6.88,
                "type": "Personal Loan",
                "link": "https://example.com/loans/dbx-personal-688",
                "snapshot": "极速放款，纯线上，无需抵押，最高 RM100k。",
                "pulled_at": _now_iso(),
            },
            {
                "source": "Fintech Y",
                "product": "SME Working Capital 7.20%",
                "rate": 7.20,
                "type": "SME",
                "link": "https://example.com/loans/fintechy-sme-720",
                "snapshot": "现金流周转，灵活还款，支持分期展期。",
                "pulled_at": _now_iso(),
            },
        ]
        return sample

    return []
