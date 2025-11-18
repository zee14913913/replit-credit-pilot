/* ============================================================
   Modern Loan Evaluate — Three Mode System
   Phase 8.2 — JS Engine (Part 1)
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {
    console.log("Loan Evaluate JS Loaded");

    // Mode buttons
    const modeFull = document.getElementById("mode_auto");
    const modeIncome = document.getElementById("mode_income");
    const modeIncomeCommit = document.getElementById("mode_commit");

    // Sections
    const fullSection = document.getElementById("auto_mode_block");
    const incomeSection = document.getElementById("income_mode_block");
    const incomeCommitSection = document.getElementById("commit_mode_block");

    // Utility function for hiding all sections
    function hideAll() {
        if (fullSection) fullSection.classList.add("hidden");
        if (incomeSection) incomeSection.classList.add("hidden");
        if (incomeCommitSection) incomeCommitSection.classList.add("hidden");
    }

    // ============================================================
    // Mode Switching Logic
    // ============================================================

    if (modeFull) {
        modeFull.addEventListener("click", () => {
            hideAll();
            if (fullSection) fullSection.classList.remove("hidden");
            setActiveMode(modeFull);
        });
    }

    if (modeIncome) {
        modeIncome.addEventListener("click", () => {
            hideAll();
            if (incomeSection) incomeSection.classList.remove("hidden");
            setActiveMode(modeIncome);
        });
    }

    if (modeIncomeCommit) {
        modeIncomeCommit.addEventListener("click", () => {
            hideAll();
            if (incomeCommitSection) incomeCommitSection.classList.remove("hidden");
            setActiveMode(modeIncomeCommit);
        });
    }

    // Highlight selected mode button
    function setActiveMode(activeBtn) {
        [modeFull, modeIncome, modeIncomeCommit].forEach(btn => {
            if (btn) btn.classList.remove("active");
        });
        if (activeBtn) activeBtn.classList.add("active");
    }

    // Default
    hideAll();
    if (fullSection) fullSection.classList.remove("hidden");
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
    const btnIncome = document.getElementById("btn_qe_income");
    const incomeInput = document.getElementById("qe_income");

    if (btnIncome) {
        btnIncome.addEventListener("click", async () => {
            const income = parseFloat(incomeInput.value || 0);

            if (income <= 0) {
                alert('请输入有效的收入金额');
                return;
            }

            const payload = { income: income };

            try {
                const res = await fetch("/api/loans/quick-income", {
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
                alert('计算失败，请重试');
            }
        });
    }
});


// ============================================================
// Quick Estimate — Income + Commitments
// ============================================================

document.addEventListener("DOMContentLoaded", function () {
    const btnIncomeCommit = document.getElementById("btn_qe_commit");

    const incomeInput = document.getElementById("qe2_income");
    const commitInput = document.getElementById("qe2_commit");

    if (btnIncomeCommit) {
        btnIncomeCommit.addEventListener("click", async () => {
            const income = parseFloat(incomeInput.value || 0);
            const commitments = parseFloat(commitInput.value || 0);

            if (income <= 0) {
                alert('请输入有效的收入金额');
                return;
            }

            const payload = {
                income: income,
                commitments: commitments
            };

            try {
                const res = await fetch("/api/loans/quick-income-commitment", {
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
                alert('计算失败，请重试');
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
        const t = (key, fallback) => window.i18n ? window.i18n.translate(key) : fallback;
        alert(t('please_upload_one_document', '请至少上传一份文档以开始全自动评估'));
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
    const t = (key, fallback) => window.i18n ? window.i18n.translate(key) : fallback;
    const btnFullAuto = document.getElementById("btn-full-auto");
    if (btnFullAuto) {
        btnFullAuto.disabled = true;
        btnFullAuto.textContent = t('processing_button', '处理中...');
    }

    try {
        // POST到Flask端点
        const res = await fetch("/loan-evaluate/full-auto", {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.error || t('full_auto_eval_failed', '全自动评估失败'));
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
        alert(t('full_auto_eval_failed_prefix', '全自动评估失败：') + err.message);
    } finally {
        // 恢复按钮状态
        if (btnFullAuto) {
            btnFullAuto.disabled = false;
            btnFullAuto.textContent = t('start_automatic_evaluation', '开始自动评估');
        }
    }
}
