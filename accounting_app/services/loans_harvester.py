# accounting_app/services/loans_harvester.py
import os
import datetime as dt
from typing import List, Dict, Any

TZ = os.getenv("TZ", "Asia/Kuala_Lumpur")

def _now_iso() -> str:
    return dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat()

def harvest_loans() -> List[Dict[str, Any]]:
    """
    贷款资讯聚合器（占位版 + 银行偏好与口碑情报）：
    - 未配置 PERPLEXITY_API_KEY 时：返回示例数据（不触发外部请求）
    - 日后接入 Perplexity：在 TODO 区替换采集逻辑即可
    返回结构：
    [
      {
        "source": "Bank / Lender 名称",
        "product": "产品名",
        "rate": 3.75,           # 利率（可选）
        "type": "Home Loan",
        "link": "https://...",
        "snapshot": "本产品一句话说明",
        "pulled_at": "...ISO...",
        "intel": {              # 新增：偏好与口碑
          "preferred_customer": "偏好客户画像（如：受薪族、稳定收入≥RM4k、EPF ≥ X）",
          "less_preferred": "不偏好的客户（如：自雇初创、信用历史短、DSR>70%）",
          "docs_required": "材料偏好（如：3个月薪资单/EPF/PCB、6个月流水、CTOS良好）",
          "feedback_summary": "网评摘要（优缺点；放款速度/审批严格度/费用体验）",
          "sentiment_score": 0.82  # 0~1，越高越正面
        }
      },
      ...
    ]
    """
    api_key = os.getenv("PERPLEXITY_API_KEY", "").strip()
    model = os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-large-128k-online")

    if not api_key:
        now = _now_iso()
        return [
            {
                "source": "Bank A",
                "product": "Home Loan Flexi 3.75%",
                "rate": 3.75,
                "type": "Home Loan",
                "link": "https://example.com/loans/bank-a-home-flexi",
                "snapshot": "首购族 90% 融资；灵活提前还款，无违约金。",
                "pulled_at": now,
                "intel": {
                    "preferred_customer": "受薪族；固定雇佣 ≥ 12 个月；月净收入 ≥ RM4,000；DSR ≤ 55%",
                    "less_preferred": "自雇不足 12 个月；频繁逾期；信用卡利用率 >70%",
                    "docs_required": "3 个月薪资单与银行流水、EPF/PCB、CTOS 报告良好",
                    "feedback_summary": "审批较快（5-7个工作日）；律师与估价合作资源多；提前还款便捷。",
                    "sentiment_score": 0.84
                }
            },
            {
                "source": "Digital Bank X",
                "product": "Personal Loan Promo 6.88%",
                "rate": 6.88,
                "type": "Personal Loan",
                "link": "https://example.com/loans/dbx-personal-688",
                "snapshot": "纯线上，无抵押；最高 RM100k；放款快。",
                "pulled_at": now,
                "intel": {
                    "preferred_customer": "受薪族；净收入 ≥ RM3,500；工作满 6 个月；良好还款记录",
                    "less_preferred": "高负债（DSR ≥ 70%）；近期多次查询；不稳定收入",
                    "docs_required": "工资单/雇佣证明、e-BE 税表 或 EPF、近 3-6 个月流水",
                    "feedback_summary": "体验好、放款快，但利率区间较宽；逾期费用严格。",
                    "sentiment_score": 0.78
                }
            },
            {
                "source": "Fintech Y",
                "product": "SME Working Capital 7.20%",
                "rate": 7.20,
                "type": "SME",
                "link": "https://example.com/loans/fintechy-sme-720",
                "snapshot": "营运资金融通；可分期展期。",
                "pulled_at": now,
                "intel": {
                    "preferred_customer": "中小企业；成立 ≥ 24 个月；月流水 ≥ RM80k；税务合规",
                    "less_preferred": "现金为主且无正规的账务与发票；频繁退票；董事过度负债",
                    "docs_required": "6-12 个月公司对公流水、SSM 文件、近两年财报/报税、CTOS/CCRIS 正常",
                    "feedback_summary": "审批灵活、额度适中；对资料规范性较看重；放款速度一般。",
                    "sentiment_score": 0.74
                }
            }
        ]

    return []
