/* ============================================================
   Modern Loan Evaluate — Three Mode System
   Phase 8.2 — JS Engine (Part 1)
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {
    console.log("Loan Evaluate JS Loaded");

    // Mode buttons
    const modeFull = document.getElementById("mode-full-auto");
    const modeIncome = document.getElementById("mode-income-only");
    const modeIncomeCommit = document.getElementById("mode-income-commit");

    // Sections
    const fullSection = document.getElementById("full-auto-section");
    const incomeSection = document.getElementById("quick-income-section");
    const incomeCommitSection = document.getElementById("quick-income-commit-section");

    // Result panel
    const resultPanel = document.getElementById("evaluation-result");
    const riskCard = document.getElementById("risk-card");
    const approvalCircle = document.getElementById("approval-odds");
    const maxLoanText = document.getElementById("max-loan-amount");
    const maxEmiText = document.getElementById("max-emi");
    const dtiText = document.getElementById("dti-value");
    const foirText = document.getElementById("foir-value");

    // Advisor & products
    const advisorPanel = document.getElementById("ai-advisor-panel");
    const productList = document.getElementById("product-list");

    // Utility function for hiding all sections
    function hideAll() {
        fullSection.style.display = "none";
        incomeSection.style.display = "none";
        incomeCommitSection.style.display = "none";
    }

    // ============================================================
    // Mode Switching Logic
    // ============================================================

    modeFull.addEventListener("click", () => {
        hideAll();
        fullSection.style.display = "block";
        setActiveMode(modeFull);

        resultPanel.style.opacity = "0";
    });

    modeIncome.addEventListener("click", () => {
        hideAll();
        incomeSection.style.display = "block";
        setActiveMode(modeIncome);

        resultPanel.style.opacity = "0";
    });

    modeIncomeCommit.addEventListener("click", () => {
        hideAll();
        incomeCommitSection.style.display = "block";
        setActiveMode(modeIncomeCommit);

        resultPanel.style.opacity = "0";
    });

    // Highlight selected mode button
    function setActiveMode(activeBtn) {
        [modeFull, modeIncome, modeIncomeCommit].forEach(btn => {
            btn.classList.remove("active-mode");
        });
        activeBtn.classList.add("active-mode");
    }

    // Default
    hideAll();
    fullSection.style.display = "block";
    setActiveMode(modeFull);

});


/* ============================================================
   Phase 8.4 — 所有渲染逻辑已迁移到loan_result_renderer.js
   使用window.renderLoanEvaluationResult()统一渲染
   ============================================================ */


// ============================================================
// Quick Estimate — Income Only
// ============================================================

document.addEventListener("DOMContentLoaded", function () {
    const btnIncome = document.getElementById("btn-income-calc");
    const incomeInput = document.getElementById("qe-income-input");

    if (btnIncome) {
        btnIncome.addEventListener("click", async () => {
            const income = parseFloat(incomeInput.value || 0);

            if (income <= 0) {
                alert("Please enter a valid income amount.");
                return;
            }

            const payload = { income: income };

            try {
                const res = await fetch("/loan-evaluate/quick_income", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                const data = await res.json();
                console.log("Quick Income Only data:", data);

                // Phase 8.4: Use unified renderer
                if (window.renderLoanEvaluationResult) {
                    window.renderLoanEvaluationResult(data);
                }

            } catch (err) {
                console.error("Quick-income error:", err);
            }
        });
    }
});


// ============================================================
// Quick Estimate — Income + Commitments
// ============================================================

document.addEventListener("DOMContentLoaded", function () {
    const btnIncomeCommit = document.getElementById("btn-income-commit-calc");

    const incomeInput = document.getElementById("qe2-income-input");
    const commitInput = document.getElementById("qe2-commit-input");

    if (btnIncomeCommit) {
        btnIncomeCommit.addEventListener("click", async () => {
            const income = parseFloat(incomeInput.value || 0);
            const commitments = parseFloat(commitInput.value || 0);

            if (income <= 0) {
                alert("Please enter a valid income amount.");
                return;
            }

            const payload = {
                income: income,
                commitments: commitments
            };

            try {
                const res = await fetch("/loan-evaluate/quick_income_commitment", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                const data = await res.json();
                console.log("Quick Income + Commit data:", data);

                // Phase 8.4: Use unified renderer
                if (window.renderLoanEvaluationResult) {
                    window.renderLoanEvaluationResult(data);
                }

            } catch (err) {
                console.error("Quick-income-commitment error:", err);
            }
        });
    }
});


/* ============================================================
   Phase 8.4 — 废弃函数已删除
   所有渲染逻辑已迁移到loan_result_renderer.js
   使用window.renderLoanEvaluationResult()统一渲染
   ============================================================ */


/* ============================================================
   Phase 8.3 — Full Automated Mode Handler
   ============================================================ */

async function handleFullAutoEvaluation() {
    console.log("Starting Full Auto Evaluation...");

    // 收集上传文件（匹配HTML的ID）
    const payslipFile = document.getElementById("payslip_file")?.files[0];
    const epfFile = document.getElementById("epf_file")?.files[0];
    const bankStatementFile = document.getElementById("bank_statement_file")?.files[0];
    const ctosFile = document.getElementById("ctos_file")?.files[0];
    const ccrisFile = document.getElementById("ccris_file")?.files[0];

    // 验证至少上传一个文件
    if (!payslipFile && !epfFile && !bankStatementFile && !ctosFile && !ccrisFile) {
        alert("Please upload at least one document to start Full Auto evaluation.");
        return;
    }

    // 构建FormData
    const formData = new FormData();
    if (payslipFile) formData.append("payslip_pdf", payslipFile);
    if (epfFile) formData.append("epf_pdf", epfFile);
    if (bankStatementFile) formData.append("bank_statement_pdf", bankStatementFile);
    if (ctosFile) formData.append("ctos_pdf", ctosFile);
    if (ccrisFile) formData.append("ccris_pdf", ccrisFile);

    // 显示加载状态
    const btnFullAuto = document.getElementById("btn-full-auto");
    if (btnFullAuto) {
        btnFullAuto.disabled = true;
        btnFullAuto.textContent = "Processing...";
    }

    try {
        // POST到Flask端点
        const res = await fetch("/loan-evaluate/full-auto", {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.error || "Full Auto evaluation failed");
        }

        const data = await res.json();
        console.log("Full Auto evaluation result:", data);

        // Phase 8.4: 合并payload并使用统一渲染器
        const mergedPayload = {
            ...data.eligibility,
            advisor: data.advisor,
            ai_advisor: data.advisor,
            products: data.products,
            recommended_products: data.products
        };

        if (window.renderLoanEvaluationResult) {
            window.renderLoanEvaluationResult(mergedPayload);
        }

    } catch (err) {
        console.error("Full Auto evaluation error:", err);
        alert("Full Auto evaluation failed: " + err.message);
    } finally {
        // 恢复按钮状态
        if (btnFullAuto) {
            btnFullAuto.disabled = false;
            btnFullAuto.textContent = "Start Automatic Evaluation";
        }
    }
}
