"""
定时任务调度器
功能：管理所有定时任务的执行
"""
import schedule
import time
from accounting_app.tasks.ai_daily_report import generate_daily_report


def run_scheduler():
    """
    启动定时任务调度器
    
    定时任务：
    - AI日报：每天早上08:00自动生成
    """
    # 注册AI日报定时任务（每天08:00）
    schedule.every().day.at("08:00").do(generate_daily_report)
    
    print("\n" + "="*60)
    print("⏰ AI日报计划任务已启动")
    print("="*60)
    print("📅 执行时间：每天 08:00")
    print("📝 任务：生成AI财务日报")
    print("💾 存储位置：ai_logs表")
    print("="*60 + "\n")
    
    # 持续运行调度器
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次


# 支持直接运行测试
if __name__ == "__main__":
    print("🧪 测试模式：立即执行一次AI日报生成...")
    generate_daily_report()
    
    print("\n⏰ 启动调度器（Ctrl+C 退出）...")
    run_scheduler()
