import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["public"])

HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Task History</title>
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <style>
    :root { color-scheme: light dark; }
    body{font-family:ui-sans-serif,system-ui;margin:40px;max-width:1000px}
    table{width:100%;border-collapse:collapse;margin-top:10px}
    th,td{border:1px solid #ccc;padding:8px;text-align:left;vertical-align:top}
    th{background:#f2f2f2}
    button{padding:6px 12px;border-radius:6px;border:1px solid #ccc;background:#fff;cursor:pointer}
    input,select{padding:6px;border:1px solid #ccc;border-radius:6px}
    .toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;justify-content:space-between}
    .left{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
    .muted{color:#666}
    a.link{color:inherit;text-decoration:underline}
  </style>
</head>
<body>
  <div class="toolbar">
    <div class="left">
      <a id="backLink" class="link" href="/portal">← Portal</a>
      <strong id="title">Task History</strong>
      <span class="muted" id="subtitle"></span>
    </div>
    <div>
      <button id="langBtn">中文</button>
    </div>
  </div>

  <div class="left" style="margin-top:12px">
    <input id="q" placeholder="Search text..." />
    <button id="searchBtn">Search</button>
    <label class="muted" id="countLabel"></label>
  </div>

  <table id="tbl">
    <thead>
      <tr>
        <th>ID</th>
        <th>Status</th>
        <th>Time</th>
        <th>Filename</th>
        <th>Preview</th>
        <th>Action</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>

  <div class="left" style="margin-top:12px">
    <button id="prevBtn">◀ Prev</button>
    <span class="muted" id="pageInfo"></span>
    <button id="nextBtn">Next ▶</button>
  </div>

<script>
// --- i18n ---
const I18N = {
  en: {
    title: "Task History",
    subtitle: "Recent OCR tasks",
    btn_toggle: "中文",
    back: "← Portal",
    search_ph: "Search text...",
    search_btn: "Search",
    th: ["ID","Status","Time","Filename","Preview","Action"],
    act_view: "Download TXT",
    act_delete: "Delete",
    prev: "◀ Prev", next: "Next ▶",
    page: (p,t) => `Page ${p}`,
    total: (n) => `Total ${n}`,
    confirm_del: "Delete this task?",
    portal: "Portal",
  },
  zh: {
    title: "任务历史",
    subtitle: "近期 OCR 任务",
    btn_toggle: "English",
    back: "← 返回 Portal",
    search_ph: "搜索文本…",
    search_btn: "搜索",
    th: ["ID","状态","时间","文件名","内容预览","操作"],
    act_view: "下载 TXT",
    act_delete: "删除",
    prev: "◀ 上一页", next: "下一页 ▶",
    page: (p,t) => `第 ${p} 页`,
    total: (n) => `共 ${n} 条`,
    confirm_del: "确定删除该任务吗？",
    portal: "Portal",
  }
};

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

// key 透传
const NEED_KEY = "%NEED_KEY%" === "1";
const KEY_VALUE = "%KEY_VALUE%";

function applyTexts(){
  document.title = t("title");
  document.getElementById("title").textContent = t("title");
  document.getElementById("subtitle").textContent = t("subtitle");
  document.getElementById("langBtn").textContent = t("btn_toggle");
  const back = document.getElementById("backLink");
  back.textContent = t("back");
  const u = new URL("/portal", location.origin);
  u.searchParams.set("lang", LANG);
  if (NEED_KEY) u.searchParams.set("key", KEY_VALUE);
  back.href = u.toString();

  document.getElementById("q").placeholder = t("search_ph");
  document.getElementById("searchBtn").textContent = t("search_btn");
  document.getElementById("prevBtn").textContent = t("prev");
  document.getElementById("nextBtn").textContent = t("next");

  const ths = document.querySelectorAll("#tbl thead th");
  const labels = t("th");
  ths.forEach((th, i) => th.textContent = labels[i] || th.textContent);
}

document.getElementById("langBtn").addEventListener("click", ()=>{
  LANG = (LANG === "zh" ? "en" : "zh");
  localStorage.setItem("lang", LANG);
  const u = new URL(location.href);
  u.searchParams.set("lang", LANG);
  if (NEED_KEY) u.searchParams.set("key", KEY_VALUE);
  history.replaceState(null, "", u.toString());
  applyTexts();
  page = 1; load(); // 语言切换时刷新列表
});

applyTexts();

// --- list logic ---
let page = 1;
let limit = 10;
let total = 0;

document.getElementById("searchBtn").addEventListener("click", ()=>{
  page = 1; load();
});
document.getElementById("prevBtn").addEventListener("click", ()=>{
  if(page>1){ page--; load(); }
});
document.getElementById("nextBtn").addEventListener("click", ()=>{
  const maxPage = Math.max(1, Math.ceil(total/limit));
  if(page<maxPage){ page++; load(); }
});

async function load(){
  const q = document.getElementById("q").value.trim();
  const qs = new URLSearchParams();
  if(q) qs.set("q", q);
  qs.set("skip", (page-1)*limit);
  qs.set("limit", limit);

  const res = await fetch('/files/history?'+qs.toString());
  const j = await res.json();
  total = j.total || 0;
  document.getElementById("countLabel").textContent = t("total")(total);
  document.getElementById("pageInfo").textContent = t("page")(page, total);

  const tb = document.querySelector("#tbl tbody");
  tb.innerHTML = '';
  (j.tasks || []).forEach(row=>{
    const tr = document.createElement('tr');
    const prev = (row.preview || '').replace(/[<>&]/g, m=>({"<":"&lt;",">":"&gt;","&":"&amp;"}[m]));
    tr.innerHTML = `
      <td>${row.task_id}</td>
      <td>${row.status}</td>
      <td>${row.time || ""}</td>
      <td>${row.filename || ""}</td>
      <td>${prev}</td>
      <td>
        <button onclick="downloadTxt('${row.task_id}')">${t("act_view")}</button>
        <button onclick="downloadOriginal('${row.task_id}')">Original PDF</button>
        <button onclick="delTask('${row.task_id}')">${t("act_delete")}</button>
      </td>
    `;
    tb.appendChild(tr);
  });
}

async function downloadTxt(id){
  const r = await fetch('/files/pdf-to-text/result/'+id);
  const j = await r.json();
  const text = j.result || '(no result)';
  const blob = new Blob([text],{type:'text/plain'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = id+'.txt';
  a.click(); URL.revokeObjectURL(url);
}

async function downloadOriginal(id){
  location.href = '/files/original/' + id;
}

async function delTask(id){
  if(!confirm(t("confirm_del"))) return;
  const r = await fetch('/files/history/'+id, {method:'DELETE'});
  if(r.ok) load();
}

load();
</script>
</body>
</html>
"""

@router.get("/portal/history", response_class=HTMLResponse)
async def history_page(request: Request):
    need_key = os.getenv("PORTAL_KEY")
    if need_key and request.query_params.get("key") != need_key:
        raise HTTPException(status_code=404, detail="Not Found")
    need_key_flag = "1" if bool(need_key) else "0"
    key_value = request.query_params.get("key", "") if need_key else ""
    return HTML.replace("%NEED_KEY%", need_key_flag).replace("%KEY_VALUE%", key_value)
