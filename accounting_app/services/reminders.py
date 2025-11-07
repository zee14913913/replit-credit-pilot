import os, pytz, datetime as dt
from apscheduler.schedulers.background import BackgroundScheduler
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client as Twilio

TZ = os.getenv("TZ","Asia/Kuala_Lumpur")
RUN_HOUR = int(os.getenv("REMINDER_HOUR","8"))

def _send_email(to, subject, html):
    key=os.getenv("SENDGRID_API_KEY")
    if not key: return False
    sg=SendGridAPIClient(key)
    msg=Mail(from_email=os.getenv("MAIL_FROM","noreply@creditpilot.digital"),
             to_emails=to, subject=subject, html_content=html)
    sg.send(msg); return True

def _send_sms(to, body, whatsapp=False):
    sid=os.getenv("TWILIO_SID"); tok=os.getenv("TWILIO_TOKEN")
    from_sms=os.getenv("TWILIO_FROM")
    from_wa=os.getenv("TWILIO_WHATSAPP_FROM")
    if not (sid and tok): return False
    cli=Twilio(sid, tok)
    if whatsapp:
        cli.messages.create(from_=f"whatsapp:{from_wa}", to=f"whatsapp:{to}", body=body)
    else:
        cli.messages.create(from_=from_sms, to=to, body=body)
    return True

def _due_items_today():
    today=dt.date.today()
    demo=[
        {"customer":"Chen","card":"Maybank ****1234","due":"2025-11-10","amount":2500.0,
         "email":"chen@example.com","phone":"+60123456789"}
    ]
    return demo

def run_once():
    for it in _due_items_today():
        d=it["due"]; amt=it["amount"]; card=it["card"]
        subject=f"[CreditPilot] Upcoming Due · {card}"
        html=f"<p>Hi {it['customer']},</p><p>Your card {card} will be due on {d}. Amount: RM {amt:.2f}.</p>"
        body=f"Reminder: {card} due {d}, RM {amt:.2f}"
        _send_email(it["email"], subject, html)
        _send_sms(it["phone"], body, whatsapp=False)
        if os.getenv("ENABLE_WHATSAPP","0")=="1":
            _send_sms(it["phone"], body, whatsapp=True)

def start_scheduler():
    tz=pytz.timezone(TZ)
    sch=BackgroundScheduler(timezone=tz)
    sch.add_job(run_once, "cron", hour=RUN_HOUR, minute=0)
    sch.start()
    return sch
