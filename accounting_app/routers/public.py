import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["public"])

HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>PDF OCR</title>
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <style>
    body{font-family:ui-sans-serif,system-ui,Arial;margin:40px;max-width:760px}
    .card{padding:16px;border:1px solid #ddd;border-radius:12px}
    .muted{color:#666}
    pre{white-space:pre-wrap;word-break:break-word;background:#f7f7f7;padding:12px;border-radius:8px}
    button{padding:8px 14px;border-radius:8px;border:1px solid #ccc;background:#fff;cursor:pointer}
    input[type=file],input[type=email]{margin-right:8px}
  </style>
</head>
<body>
  <h2>PDF 文字提取</h2>
  <div class="card">
    <form id="f">
      <input type="file" id="file" accept="application/pdf" required />
      <input type="email" id="email" placeholder="可选：完成后邮件通知" />
      <button type="submit">上传并处理</button>
    </form>
    <p class="muted" id="msg">请选择 PDF 文件后提交（最大 %MAX% MB）。</p>
    <div id="out"></div>
  </div>
<script>
const msg = document.getElementById('msg');
const out = document.getElementById('out');
document.getElementById('f').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const f = document.getElementById('file').files[0];
  if(!f){ alert('请选择PDF'); return; }
  if(f.size > (parseInt('%MAX%')*1024*1024)){ alert('文件超过限制'); return; }

  msg.textContent = '正在上传...';
  const fd = new FormData(); fd.append('file', f);

  const submit = await fetch('/files/pdf-to-text/submit', { method:'POST', body: fd });
  if(!submit.ok){ msg.textContent = '提交失败'; return; }
  const sub = await submit.json();
  msg.textContent = '已提交，任务ID：' + sub.task_id + '，等待完成...';

  async function poll(){
    const r = await fetch('/files/pdf-to-text/result/' + sub.task_id);
    const j = await r.json();
    if(j.status === 'done'){
      msg.textContent = '处理完成';
      out.innerHTML = '<h3>结果</h3><pre>'+ (j.result || '').replace(/[<>&]/g, m=>({"<":"&lt;",">":"&gt;","&":"&amp;"}[m])) +'</pre>';
    }else if(j.status === 'error'){
      msg.textContent = '处理出错：' + (j.error_msg || 'unknown');
    }else{
      setTimeout(poll, 1200);
    }
  }
  poll();
});
</script>
</body>
</html>
"""

@router.get("/portal", response_class=HTMLResponse)
async def portal(request: Request):
    need_key = os.getenv("PORTAL_KEY")
    if need_key:
        key = request.query_params.get("key")
        if key != need_key:
            raise HTTPException(status_code=404, detail="Not Found")

    limit = os.getenv("MAX_UPLOAD_MB", "10")
    return HTML.replace("%MAX%", str(limit))
