import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["public"])

HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>PDF OCR</title>
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <style>
    :root { color-scheme: light dark; }
    body{font-family:ui-sans-serif,system-ui,Arial;margin:40px;max-width:760px}
    .row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
    .card{padding:16px;border:1px solid #ddd;border-radius:12px}
    .muted{color:#666}
    pre{white-space:pre-wrap;word-break:break-word;background:#f7f7f7;padding:12px;border-radius:8px}
    button{padding:8px 14px;border-radius:8px;border:1px solid #ccc;background:#fff;cursor:pointer}
    input[type=file],input[type=email]{padding:8px;border:1px solid #ccc;border-radius:8px}
    .toolbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
  </style>
</head>
<body>
  <div class="toolbar">
    <h2 id="title">PDF OCR</h2>
    <button id="langBtn" aria-label="Toggle Language">中文</button>
  </div>

  <div class="card">
    <form id="f">
      <div class="row" style="margin-bottom:8px">
        <input type="file" id="file" accept="application/pdf" aria-label="PDF file" required />
        <input type="email" id="email" placeholder="Optional: email on finish" aria-label="Notify email (optional)" />
        <button type="submit" id="submitBtn">Upload & Process</button>
      </div>
      <p class="muted" id="msg">Choose a PDF and submit. Max %MAX% MB.</p>
    </form>
    <div id="out"></div>
  </div>

<script>
const MAX_MB = parseInt("%MAX%");

// --- i18n dictionary ---
const I18N = {
  en: {
    title: "PDF OCR",
    btn_toggle: "中文",
    email_placeholder: "Optional: email on finish",
    submit: "Upload & Process",
    hint_choose: `Choose a PDF and submit. Max ${MAX_MB} MB.`,
    uploading: "Uploading...",
    submitted: (id) => `Submitted. Task ID: ${id}. Waiting...`,
    result_title: "Result",
    not_pdf: "Only PDF is allowed",
    too_big: "File exceeds limit",
    submit_failed: "Submit failed",
    processing_error: (m) => `Processing error: ${m||"unknown"}`,
  },
  zh: {
    title: "PDF 文字提取",
    btn_toggle: "English",
    email_placeholder: "可选：完成后邮件通知",
    submit: "上传并处理",
    hint_choose: `请选择 PDF 后提交。最大 ${MAX_MB} MB。`,
    uploading: "正在上传…",
    submitted: (id) => `已提交，任务ID：${id}，等待完成…`,
    result_title: "结果",
    not_pdf: "仅支持 PDF 文件",
    too_big: "文件超过大小限制",
    submit_failed: "提交失败",
    processing_error: (m) => `处理出错：${m||"未知错误"}`,
  }
};

// --- language resolve: ?lang=zh|en > localStorage > navigator ---
function resolveLang(){
  const qs = new URLSearchParams(location.search);
  const q = qs.get("lang");
  if (q === "zh" || q === "en") { localStorage.setItem("lang", q); return q; }
  const saved = localStorage.getItem("lang");
  if (saved === "zh" || saved === "en") return saved;
  const nav = (navigator.language || "en").toLowerCase();
  return nav.startsWith("zh") ? "zh" : "en";
}
let LANG = resolveLang();

function t(key, ...args){
  const pack = I18N[LANG] || I18N.en;
  const v = pack[key];
  return (typeof v === "function") ? v(...args) : v;
}

function applyTexts(){
  document.title = t("title");
  document.getElementById("title").textContent = t("title");
  document.getElementById("langBtn").textContent = t("btn_toggle");
  document.getElementById("email").placeholder = t("email_placeholder");
  document.getElementById("submitBtn").textContent = t("submit");
  document.getElementById("msg").textContent = t("hint_choose");
}

document.getElementById("langBtn").addEventListener("click", ()=>{
  LANG = (LANG === "zh" ? "en" : "zh");
  localStorage.setItem("lang", LANG);
  const u = new URL(location.href);
  u.searchParams.set("lang", LANG);
  history.replaceState(null, "", u.toString());
  applyTexts();
});

applyTexts();

// --- main logic ---
const msg = document.getElementById('msg');
const out = document.getElementById('out');

document.getElementById('f').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const f = document.getElementById('file').files[0];
  const email = document.getElementById('email').value.trim();

  if(!f){ alert(t("hint_choose")); return; }
  if(f.type !== "application/pdf"){ alert(t("not_pdf")); return; }
  if(f.size > (MAX_MB*1024*1024)){ alert(t("too_big")); return; }

  msg.textContent = t("uploading");
  const fd = new FormData();
  fd.append('file', f);
  if(email) fd.append('notify_email', email); // 作为 multipart 字段提交

  const submitResp = await fetch('/files/pdf-to-text/submit', { method:'POST', body: fd });
  if(!submitResp.ok){ msg.textContent = t("submit_failed"); return; }
  const sub = await submitResp.json();
  msg.textContent = t("submitted", sub.task_id);

  async function poll(){
    const r = await fetch('/files/pdf-to-text/result/' + sub.task_id);
    const j = await r.json();
    if(j.status === 'done'){
      msg.textContent = '';
      const safe = (j.result || '').replace(/[<>&]/g, m=>({"<":"&lt;","&":"&amp;",">":"&gt;"}[m]));
      out.innerHTML = '<h3>'+t("result_title")+'</h3><pre>'+ safe +'</pre>';
    }else if(j.status === 'error'){
      msg.textContent = t("processing_error", j.error_msg);
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
    # 可选：简单访问密钥
    need_key = os.getenv("PORTAL_KEY")
    if need_key:
        key = request.query_params.get("key")
        if key != need_key:
            raise HTTPException(status_code=404, detail="Not Found")

    limit = os.getenv("MAX_UPLOAD_MB", "10")
    return HTML.replace("%MAX%", str(limit))
