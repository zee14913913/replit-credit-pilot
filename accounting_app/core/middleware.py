import os, time, json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, PlainTextResponse

class SecurityAndLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, env: str = "dev"):
        super().__init__(app); self.env = env
    async def dispatch(self, request, call_next):
        t0 = time.time()
        resp: Response = await call_next(request)
        # 安全头
        resp.headers.setdefault("X-Content-Type-Options","nosniff")
        resp.headers.setdefault("X-Frame-Options","DENY")
        resp.headers.setdefault("Referrer-Policy","no-referrer")
        resp.headers.setdefault("Permissions-Policy","geolocation=(), microphone=(), camera=()")
        if self.env == "prod":
            resp.headers.setdefault("Strict-Transport-Security","max-age=31536000; includeSubDomains")
        # 日志
        ms = int((time.time()-t0)*1000)
        print("INFO:app:"+json.dumps({"method":request.method,"path":request.url.path,"status":resp.status_code,"ms":ms}, ensure_ascii=False))
        return resp

class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """
    每 IP 每分钟 N 次（默认 120），超限返回 429
    适合小场景，后期可换 redis 限流
    """
    BUCKET = {}
    def __init__(self, app, per_minute:int = None):
        super().__init__(app)
        self.limit = per_minute or int(os.getenv("RATE_LIMIT_PER_MIN", "120"))
    async def dispatch(self, request, call_next):
        ip = request.client.host if request.client else "unknown"
        now = int(time.time()//60)
        key = (ip, now)
        cnt = self.BUCKET.get(key, 0) + 1
        self.BUCKET[key] = cnt
        # 清理上一个窗口
        for k in list(self.BUCKET.keys()):
            if k[1] < now: self.BUCKET.pop(k, None)
        if cnt > self.limit:
            return PlainTextResponse("Too Many Requests", status_code=429)
        return await call_next(request)
