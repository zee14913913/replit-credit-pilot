/* ===========================================================
   Phase 8.4 — Loan Result Renderer Module
   统一处理loan_evaluate.html三个模式的结果渲染
   =========================================================== */

/**
 * 主渲染函数 - 协调所有子渲染器
 * @param {Object} data - API返回的完整评估数据
 */
function renderLoanEvaluationResult(data) {
    console.log("Rendering loan evaluation result:", data);

    if (!data) {
        console.error("No data provided to renderer");
        return;
    }

    // 渲染各个组件
    renderRiskCard(data);
    renderApprovalOdds(data.approval_odds);
    renderLoanSummary(data);
    renderAIAdvisor(data.ai_advisor || data.advisor);
    renderProducts(data.recommended_products || data.products || []);

    // 显示所有卡片
    showAllCards();
}

/**
 * 渲染风险评估卡片
 */
function renderRiskCard(data) {
    const card = document.getElementById("risk_card");
    const gradeEl = document.getElementById("risk_grade");
    
    if (!card || !gradeEl) return;

    // 设置风险等级
    const riskGrade = data.risk_grade || "N/A";
    gradeEl.textContent = riskGrade;
    
    // 动态添加风险等级样式
    gradeEl.className = "risk-grade";
    if (riskGrade) {
        gradeEl.classList.add(`grade-${riskGrade.toLowerCase()}`);
    }

    // 填充风险指标
    document.getElementById("r_dti").textContent = 
        data.dti_ratio ? `${(data.dti_ratio * 100).toFixed(1)}%` : 
        data.final_dti ? data.final_dti : "—";

    document.getElementById("r_foir").textContent = 
        data.foir_ratio ? `${(data.foir_ratio * 100).toFixed(1)}%` : 
        data.final_foir ? data.final_foir : "—";

    document.getElementById("r_bucket").textContent = 
        data.ccris_bucket !== undefined ? `Bucket ${data.ccris_bucket}` : "—";

    document.getElementById("r_credit").textContent = 
        data.credit_score || data.ctos_sme_score || "—";

    document.getElementById("r_emp").textContent = 
        data.employment_status || "—";

    card.classList.remove("hidden");
}

/**
 * 渲染审批概率圈
 */
function renderApprovalOdds(odds) {
    const card = document.getElementById("odds_card");
    const circle = document.getElementById("odds_circle");
    
    if (!card || !circle) return;

    if (!odds && odds !== 0) {
        circle.textContent = "—%";
        circle.className = "odds-circle";
    } else {
        circle.textContent = `${odds}%`;
        
        // 动态设置颜色
        circle.className = "odds-circle";
        if (odds >= 70) {
            circle.classList.add("high");
        } else if (odds >= 50) {
            circle.classList.add("medium");
        } else {
            circle.classList.add("low");
        }
    }

    card.classList.remove("hidden");
}

/**
 * 渲染贷款摘要（最大EMI和最大贷款额度）
 */
function renderLoanSummary(data) {
    const card = document.getElementById("loan_summary");
    
    if (!card) return;

    document.getElementById("r_max_emi").textContent = 
        data.max_emi ? formatCurrency(data.max_emi) : "—";

    document.getElementById("r_max_loan").textContent = 
        data.max_loan_amount ? formatCurrency(data.max_loan_amount) : "—";

    card.classList.remove("hidden");
}

/**
 * 渲染AI顾问建议
 */
function renderAIAdvisor(advisorText) {
    const card = document.getElementById("ai_advisor");
    const textEl = document.getElementById("advisor_text");
    
    if (!card || !textEl) return;

    if (advisorText && advisorText.trim()) {
        textEl.textContent = advisorText;
        card.classList.remove("hidden");
    } else {
        textEl.textContent = "系统正在分析您的财务状况，请稍候...";
        card.classList.remove("hidden");
    }
}

/**
 * 渲染产品推荐列表
 */
function renderProducts(products) {
    const listEl = document.getElementById("product_list");
    const container = document.getElementById("products_container");
    
    if (!listEl || !container) return;

    // 清空容器
    container.innerHTML = "";

    if (!products || products.length === 0) {
        container.innerHTML = "<p style='color: #aaa; text-align: center;'>No recommended products available.</p>";
        listEl.classList.remove("hidden");
        return;
    }

    // 渲染每个产品（最多显示10个）
    products.slice(0, 10).forEach(product => {
        const card = document.createElement("div");
        card.className = "product-card";

        card.innerHTML = `
            <h4>${product.bank || product.product_name || "Unknown Bank"}</h4>
            <div class="product-info">
                <div>
                    <strong>Interest Rate:</strong>
                    <span>${product.interest_rate || product.rate_display || "N/A"}</span>
                </div>
                <div>
                    <strong>Max Loan:</strong>
                    <span>RM ${formatNumber(product.max_loan_amount || 0)}</span>
                </div>
                <div>
                    <strong>Tenure:</strong>
                    <span>${product.tenure || "Flexible"}</span>
                </div>
                <div>
                    <strong>Approval Odds:</strong>
                    <span>${product.approval_odds || product.approval_probability || "—"}%</span>
                </div>
            </div>
            <div class="match-score">
                <strong>Match Score: </strong>
                <span>${product.match_score || product.score || "—"}%</span>
            </div>
        `;

        container.appendChild(card);
    });

    listEl.classList.remove("hidden");
}

/**
 * 显示所有卡片（移除hidden类）
 */
function showAllCards() {
    const cards = [
        "risk_card",
        "odds_card",
        "loan_summary",
        "ai_advisor",
        "product_list"
    ];

    cards.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.classList.remove("hidden");
        }
    });
}

/**
 * 隐藏所有结果卡片
 */
function hideAllCards() {
    const cards = [
        "risk_card",
        "odds_card",
        "loan_summary",
        "ai_advisor",
        "product_list"
    ];

    cards.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.classList.add("hidden");
        }
    });
}

/**
 * 格式化货币
 */
function formatCurrency(value) {
    if (!value && value !== 0) return "—";
    return parseFloat(value).toLocaleString('en-MY', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * 格式化数字
 */
function formatNumber(value) {
    if (!value && value !== 0) return "0";
    return parseFloat(value).toLocaleString('en-MY');
}

// 导出函数供loan_evaluate.js使用
window.renderLoanEvaluationResult = renderLoanEvaluationResult;
window.hideAllCards = hideAllCards;
