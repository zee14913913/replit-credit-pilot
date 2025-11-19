import express from "express";
import cors from "cors";
import bodyParser from "body-parser";

const app = express();
app.use(cors());
app.use(bodyParser.json({ limit: "50mb" }));

// --------------------
// MCP Discovery
// --------------------
app.get("/mcp", (req, res) => {
  res.json({
    mcp: "1.0",
    tools: [
      { name: "parse_credit_statement", description: "解析信用卡账单 PDF" },
      { name: "parse_bank_statement", description: "解析银行月结单 PDF" },
      { name: "clean_csv", description: "清洗 CSV 文件" },
      { name: "run_loans_ai", description: "贷款预测与分析" },
      { name: "run_financial_report", description: "生成财务分析报告" },
      { name: "n8n_trigger", description: "触发 N8N Webhook" },
      { name: "supabase_upsert", description: "保存数据到 Supabase" },
      { name: "audit_log", description: "记录审计日志" }
    ]
  });
});

// -----------------------
// 1. parse_credit_statement
// -----------------------
app.post("/mcp/parse_credit_statement", async (req, res) => {
  res.json({
    status: "ok",
    parsed: "credit_statement_json_here"
  });
});

// -----------------------
// 2. parse_bank_statement
// -----------------------
app.post("/mcp/parse_bank_statement", async (req, res) => {
  res.json({
    status: "ok",
    parsed: "bank_statement_json_here"
  });
});

// -----------------------
// 3. clean_csv
// -----------------------
app.post("/mcp/clean_csv", async (req, res) => {
  res.json({
    status: "ok",
    cleaned: "cleaned_csv_here"
  });
});

// -----------------------
// 4. run_loans_ai
// -----------------------
app.post("/mcp/run_loans_ai", async (req, res) => {
  res.json({
    status: "ok",
    loan_prediction: "loan_result_json_here"
  });
});

// -----------------------
// 5. run_financial_report
// -----------------------
app.post("/mcp/run_financial_report", async (req, res) => {
  res.json({
    status: "ok",
    report: "financial_report_markdown_here"
  });
});

// -----------------------
// 6. n8n_trigger
// -----------------------
app.post("/mcp/n8n_trigger", async (req, res) => {
  const { webhook_url, payload } = req.body;

  const result = await fetch(webhook_url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const json = await result.json();

  res.json({
    status: "ok",
    result: json
  });
});

// -----------------------
// 7. supabase_upsert
// -----------------------
app.post("/mcp/supabase_upsert", async (req, res) => {
  res.json({
    status: "ok",
    saved: true
  });
});

// -----------------------
// 8. audit_log
// -----------------------
app.post("/mcp/audit_log", async (req, res) => {
  console.log("AUDIT LOG:", req.body);
  res.json({
    status: "ok",
    logged: true
  });
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, "0.0.0.0", () => console.log(`CreditPilot MCP Server running on port ${PORT}`));
