"""
自动新闻搜索系统 - 获取信用卡、贷款、投资、商业相关的最新消息
"""
from datetime import datetime
from db.database import get_db

# 新闻搜索关键词配置
NEWS_SEARCH_TOPICS = {
    'credit_card': [
        'Malaysia credit card cashback promotion 2025',
        'Malaysia credit card latest offers deals 2025',
        'Malaysia bank credit card rewards 2025'
    ],
    'loans': [
        'Malaysia personal loan home loan rates 2025',
        'Malaysia bank mortgage rates latest 2025',
        'Malaysia auto loan car financing 2025'
    ],
    'investment': [
        'Malaysia fixed deposit FD rates 2025',
        'Malaysia bank investment products 2025',
        'Malaysia unit trust mutual fund 2025'
    ],
    'business': [
        'Malaysia SME business financing 2025',
        'Malaysia business loan rates latest 2025',
        'Malaysia bank SME support program 2025'
    ]
}

def extract_news_from_search_results(search_results, category):
    """
    从搜索结果中提取新闻 - 使用news_parser模块
    """
    from news.news_parser import extract_all_news
    
    # 使用news_parser解析搜索结果
    news_items = extract_all_news(search_results)
    
    return news_items

def save_pending_news(news_items):
    """
    保存待审核的新闻到数据库（带去重）
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 创建待审核新闻表（如果不存在）- 添加唯一约束
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_name TEXT,
                news_type TEXT,
                category TEXT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_url TEXT,
                effective_date TEXT,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                UNIQUE(bank_name, title, effective_date)
            )
        ''')
        
        # 插入待审核新闻（忽略重复）
        inserted_count = 0
        for news in news_items:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO pending_news 
                    (bank_name, news_type, category, title, content, source_url, effective_date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    news.get('bank_name'),
                    news.get('news_type'),
                    news.get('category'),
                    news['title'],
                    news['content'],
                    news.get('source_url'),
                    news.get('effective_date', datetime.now().strftime('%Y-%m-%d')),
                    datetime.now().isoformat()
                ))
                if cursor.rowcount > 0:
                    inserted_count += 1
            except Exception as e:
                print(f"Error inserting news: {e}")
                continue
        
        conn.commit()
        return inserted_count

def ensure_pending_news_table():
    """确保pending_news表存在（带UNIQUE约束）"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_name TEXT,
                news_type TEXT,
                category TEXT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_url TEXT,
                effective_date TEXT,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                UNIQUE(bank_name, title, effective_date)
            )
        ''')
        conn.commit()

def get_pending_news():
    """获取所有待审核新闻"""
    ensure_pending_news_table()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM pending_news 
            WHERE status = 'pending'
            ORDER BY created_at DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

def approve_news(news_id):
    """审核通过并发布新闻"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取待审核新闻
        cursor.execute('SELECT * FROM pending_news WHERE id = ?', (news_id,))
        news = dict(cursor.fetchone())
        
        # 添加到正式新闻表
        cursor.execute('''
            INSERT INTO banking_news 
            (bank_name, news_type, title, content, effective_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            news['bank_name'],
            news['news_type'],
            news['title'],
            news['content'],
            news['effective_date'],
            datetime.now().isoformat()
        ))
        
        # 更新状态为已发布
        cursor.execute('''
            UPDATE pending_news 
            SET status = 'approved' 
            WHERE id = ?
        ''', (news_id,))
        
        conn.commit()
        return True

def reject_news(news_id):
    """拒绝新闻"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE pending_news 
            SET status = 'rejected' 
            WHERE id = ?
        ''', (news_id,))
        conn.commit()
        return True
