import os, json, sys

LEVELS = {"error": 40, "warn": 30, "info": 20, "debug": 10}
LOG_LEVEL = LEVELS.get(os.getenv("LOG_LEVEL", "info").lower(), 20)

def _should(level: int) -> bool:
    return level >= LOG_LEVEL

def info(obj): 
    if _should(20): print("INFO:app:"+json.dumps(obj, ensure_ascii=False))
def warn(obj): 
    if _should(30): print("WARN:app:"+json.dumps(obj, ensure_ascii=False), file=sys.stderr)
def error(obj): 
    if _should(40): print("ERROR:app:"+json.dumps(obj, ensure_ascii=False), file=sys.stderr)
def debug(obj):
    if _should(10): print("DEBUG:app:"+json.dumps(obj, ensure_ascii=False))
