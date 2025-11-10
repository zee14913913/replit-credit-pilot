import os, sqlite3, time, csv, io, logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

DB = os.getenv("LOANS_DB_PATH", "/home/runner/loans.db")
TZ = os.getenv("TZ", "Asia/Kuala_Lumpur")
MIN_REFRESH_HOURS = int(os.getenv("MIN_REFRESH_HOURS", "20"))
USE_REAL_DATA = os.getenv("USE_REAL_LOAN_DATA", "false").lower() == "true"


def _conn():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init():
    """初始化数据库，支持12个详细字段"""
    con = _conn()
    cur = con.cursor()

    # 扩展的贷款产品表（12个字段）
    cur.execute("""CREATE TABLE IF NOT EXISTS loan_products_detailed(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT,                    -- 1. COMPANY (金融机构)
        loan_type TEXT,                  -- 2. LOAN TYPE (贷款类型)
        product_name TEXT,               -- 产品名称
        required_doc TEXT,               -- 3. REQUIRED DOC (所需文件)
        features TEXT,                   -- 4. FEATURES (特点)
        benefits TEXT,                   -- 5. BENEFITS (优势)
        fees_charges TEXT,               -- 6. FEES & CHARGES (费用)
        tenure TEXT,                     -- 7. TENURE (期限)
        rate TEXT,                       -- 8. RATE (利率)
        application_form_url TEXT,       -- 9. APPLICATION FORM (申请表链接)
        product_disclosure_url TEXT,     -- 10. PRODUCT DISCLOSURE (产品披露链接)
        terms_conditions_url TEXT,       -- 11. TERMS & CONDITIONS (条款链接)
        preferred_customer_type TEXT,    -- 12. 放贷方对借贷人的喜好
        institution_type TEXT,           -- 机构类型 (commercial, islamic, digital等)
        source_url TEXT,                 -- 数据来源URL
        pulled_at TEXT                   -- 采集时间
    )""")

    # 保留旧表以兼容现有系统
    cur.execute("""CREATE TABLE IF NOT EXISTS loan_updates(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT, bank TEXT, product TEXT, type TEXT, rate TEXT, summary TEXT, pulled_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS loan_intel(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT, product TEXT,
        preferred_customer TEXT, less_preferred TEXT, docs_required TEXT,
        feedback_summary TEXT, sentiment_score REAL, pulled_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS loan_meta_kv(
        k TEXT PRIMARY KEY, v TEXT
    )""")

    con.commit()
    con.close()


def _now_iso():
    return datetime.now(
        timezone.utc).astimezone().isoformat(timespec="seconds")


def get_last_harvest():
    con = _conn()
    cur = con.cursor()
    cur.execute("SELECT v FROM loan_meta_kv WHERE k='last_harvest_at'")
    row = cur.fetchone()
    con.close()
    return row["v"] if row else None


def set_last_harvest(ts: str):
    con = _conn()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO loan_meta_kv(k,v) VALUES('last_harvest_at',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
        (ts, ))
    con.commit()
    con.close()


def wipe_and_seed_demo():
    con = _conn()
    cur = con.cursor()
    cur.execute("DELETE FROM loan_updates")
    cur.execute("DELETE FROM loan_intel")
    ts = _now_iso()
    items = [
        ("bank-a", "Bank A", "Home Loan Flexi", "HOME", "3.75%",
         "房贷灵活方案，支持提前还款，无复利", ts),
        ("digital-x", "Digital Bank X", "Personal Loan Promo", "PERSONAL",
         "6.88%", "快速批核，线上签署，灵活分期", ts),
        ("fintech-y", "Fintech Y", "SME Working Capital", "SME", "7.20%",
         "营运资金周转，额度灵活", ts),
    ]
    cur.executemany(
        "INSERT INTO loan_updates(source,bank,product,type,rate,summary,pulled_at) VALUES(?,?,?,?,?,?,?)",
        items)
    intel = [
        ("bank-a", "Home Loan Flexi",
         "受薪族；固定雇佣 ≥ 12个月；月净收入 ≥ RM4,000；DSR ≤ 55%",
         "自雇不足12个月；频繁逾期；信用卡利用率 >70%", "3个月薪资单与银行流水、EPF/PCB、CTOS报告良好",
         "审批较快（5-7个工作日）；律师与估价合作资源多；提前还款便捷。", 0.84, ts),
        ("digital-x", "Personal Loan Promo", "受薪族；净收入 ≥ RM3,500；工作≥6个月",
         "高负债（DSR ≥ 70%）；近期多次查询", "工资单、e-BE税表、流水", "放款较快；移动端体验好；提早结清手续费低。",
         0.78, ts),
        ("fintech-y", "SME Working Capital", "中小企业；成立 ≥24个月；月流水≥RM80k",
         "现金为主、无正规账务；未注册GST/无报税", "公司流水、SSM、财报/报税", "客服响应快；额度灵活；要求财务资料规范。",
         0.74, ts),
    ]
    cur.executemany(
        """INSERT INTO loan_intel(source,product,preferred_customer,less_preferred,docs_required,feedback_summary,sentiment_score,pulled_at)
                       VALUES(?,?,?,?,?,?,?,?)""", intel)
    con.commit()
    con.close()
    set_last_harvest(ts)


def harvest_real_data():
    """
    从真实数据源获取贷款数据
    - BNM API: 官方利率数据
    - 68家金融机构爬虫: 全面贷款产品
    """
    try:
        # 导入完整数据采集模块
        from accounting_app.services.bnm_api_client import bnm_client
        from accounting_app.services.comprehensive_loan_scraper import comprehensive_scraper

        logger.info("🚀 开始采集真实贷款数据（68家金融机构）...")

        # 1. 获取BNM利率数据
        logger.info("📊 获取BNM官方利率...")
        bnm_rates = bnm_client.get_all_rates()
        logger.info(f"  - OPR: {bnm_rates.get('opr', {}).get('opr', 'N/A')}%")

        # 2. 爬取所有金融机构贷款产品
        logger.info("🕷️ 爬取68家金融机构贷款产品...")
        all_products = comprehensive_scraper.scrape_all_institutions(
            max_workers=10)

        # 3. 验证数据
        valid_products = comprehensive_scraper.validate_products(all_products)

        # 4. 存储到数据库
        if valid_products:
            con = _conn()
            cur = con.cursor()
            cur.execute("DELETE FROM loan_updates")

            ts = _now_iso()
            items = [(p['source'], p['bank'], p['product'], p['type'],
                      p['rate'], p['summary'], ts) for p in valid_products]

            cur.executemany(
                "INSERT INTO loan_updates(source,bank,product,type,rate,summary,pulled_at) VALUES(?,?,?,?,?,?,?)",
                items)
            con.commit()
            con.close()

            logger.info(f"✅ 成功存储 {len(valid_products)} 个真实贷款产品")
            logger.info(f"   来自 68 家金融机构")

            # 导出CSV备份
            try:
                comprehensive_scraper.export_to_csv(
                    valid_products, '/home/runner/malaysia_loans_export.csv')
            except Exception as e:
                logger.warning(f"⚠️ CSV导出失败: {e}")

            set_last_harvest(ts)
            return True, ts
        else:
            logger.warning("⚠️ 未获取到有效的贷款产品，保持现有数据")
            return False, get_last_harvest()

    except Exception as e:
        logger.error(f"❌ 真实数据采集失败: {e}")
        logger.info("⚠️ 回退到演示数据")
        wipe_and_seed_demo()
        return True, get_last_harvest()


def harvest_if_due(force=False):
    """
    根据配置选择数据源：
    - USE_REAL_LOAN_DATA=true: 采集真实银行数据
    - USE_REAL_LOAN_DATA=false: 使用演示数据（默认）
    """
    init()
    last = get_last_harvest()
    if not force and last:
        try:
            last_dt = datetime.fromisoformat(last)
            if datetime.now(last_dt.tzinfo) - last_dt < timedelta(
                    hours=MIN_REFRESH_HOURS):
                return False, last
        except Exception:
            pass

    # 根据环境变量选择数据源
    if USE_REAL_DATA:
        logger.info("🌐 使用真实数据源（BNM API + 银行爬虫）")
        return harvest_real_data()
    else:
        logger.info("🎭 使用演示数据（快速启动）")
        wipe_and_seed_demo()
        return True, get_last_harvest()


def list_updates(q: str = None, limit: int = 100):
    con = _conn()
    cur = con.cursor()
    if q:
        like = f"%{q}%"
        cur.execute(
            """SELECT * FROM loan_updates
                       WHERE source LIKE ? OR bank LIKE ? OR product LIKE ? OR type LIKE ? OR summary LIKE ?
                       ORDER BY id DESC LIMIT ?""",
            (like, like, like, like, like, limit))
    else:
        cur.execute("SELECT * FROM loan_updates ORDER BY id DESC LIMIT ?",
                    (limit, ))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def list_intel(q: str = None, limit: int = 200):
    con = _conn()
    cur = con.cursor()
    if q:
        like = f"%{q}%"
        cur.execute(
            """SELECT * FROM loan_intel
                       WHERE source LIKE ? OR product LIKE ? OR preferred_customer LIKE ? OR less_preferred LIKE ? OR feedback_summary LIKE ?
                       ORDER BY id DESC LIMIT ?""",
            (like, like, like, like, like, limit))
    else:
        cur.execute("SELECT * FROM loan_intel ORDER BY id DESC LIMIT ?",
                    (limit, ))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def export_csv(rows: list) -> bytes:
    f = io.StringIO()
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
    if rows:
        w.writeheader()
        [w.writerow(r) for r in rows]
    return f.getvalue().encode("utf-8")
