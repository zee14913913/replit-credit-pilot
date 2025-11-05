import time
import threading
import collections
import requests
import os

WINDOW = 60
THRESH = 5
WEBHOOK = os.getenv("ALERT_WEBHOOK")

events = collections.deque()

def record(status: int):
    now = time.time()
    events.append((now, status >= 500))
    while events and now - events[0][0] > WINDOW:
        events.popleft()
    errs = sum(1 for t, e in events if e)
    if errs >= THRESH and WEBHOOK:
        try:
            requests.post(WEBHOOK, json={"text": f"[ALERT] {errs} errors in last {WINDOW}s"})
        except Exception:
            pass
