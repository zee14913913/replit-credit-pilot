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
   Phase 8.2 — JS Engine (Part 2)
   Quick Estimate Calculation Engine
   ============================================================ */


// ============================================================
// Helper: Render evaluation results
// ============================================================

function showEvaluationResult(data) {
    console.log("Rendering evaluation result:", data);

    // Reveal panel
    const resultPanel = document.getElementById("evaluation-result");
    resultPanel.style.opacity = "1";

    // Risk grade
    document.getElementById("risk-grade").innerText = data.risk_grade || "—";

    // DTI / FOIR values
    document.getElementById("dti-value").innerText =
        data.dti !== undefined ? (data.dti * 100).toFixed(1) + "%" : "—";

    document.getElementById("foir-value").innerText =
        data.foir !== undefined ? (data.foir * 100).toFixed(1) + "%" : "—";

    // Max EMI / Loan
    document.getElementById("max-emi").innerText =
        data.max_emi !== undefined ? "RM " + data.max_emi.toLocaleString() : "—";

    document.getElementById("max-loan-amount").innerText =
        data.max_loan_amount !== undefined
            ? "RM " + data.max_loan_amount.toLocaleString()
            : "—";

    // Approval Odds Circle
    const odds = data.approval_odds || 0;
    const circle = document.getElementById("approval-odds");
    circle.innerText = odds + "%";

    // Color based on approval odds
    if (odds >= 85) circle.style.color = "#00ff99";
    else if (odds >= 60) circle.style.color = "#ffcc00";
    else circle.style.color = "#ff0066";
}


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

                showEvaluationResult(data);
                fetchProductRecommendations(data);
                fetchAIAdvisor(data);

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

                showEvaluationResult(data);
                fetchProductRecommendations(data);
                fetchAIAdvisor(data);

            } catch (err) {
                console.error("Quick-income-commitment error:", err);
            }
        });
    }
});


/* ============================================================
   Phase 8.2 — JS Engine (Part 3)
   Product Recommendations + AI Advisor Rendering
   ============================================================ */


// ============================================================
// Fetch Recommended Loan Products
// ============================================================

async function fetchProductRecommendations(data) {
    console.log("Fetching recommended products...");

    try {
        const res = await fetch("/loan-evaluate/products", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        console.log("Recommended products:", result);

        renderProducts(result.products || []);

    } catch (error) {
        console.error("Product recommendation error:", error);
    }
}


// ============================================================
// Fetch AI Advisor Explanation
// ============================================================

async function fetchAIAdvisor(data) {
    console.log("Fetching AI Advisor...");

    try {
        const res = await fetch("/loan-evaluate/advisor", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        console.log("AI Advisor:", result);

        renderAIAdvisor(result.explanation || "No advisor data.");

    } catch (error) {
        console.error("AI Advisor fetch error:", error);
    }
}


// ============================================================
// Render Product Cards
// ============================================================

function renderProducts(products) {
    const container = document.getElementById("products-container");
    container.innerHTML = "";

    document.getElementById("product-list").style.display = "block";

    if (!products.length) {
        container.innerHTML = `<p class="no-products">No matching products found.</p>`;
        return;
    }

    products.forEach(p => {
        const card = document.createElement("div");
        card.classList.add("product-card");

        card.innerHTML = `
            <div class="product-bank">${p.bank}</div>
            <div class="match-score">Match: ${p.match_score}%</div>
            <div class="interest-rate">Rate: ${(p.interest_rate * 100).toFixed(2)}%</div>
            <div class="loan-limit">Loan Limit: RM ${Number(p.max_loan_amount).toLocaleString()}</div>
            <div class="approval-odds">Approval: ${p.approval_odds}%</div>
        `;

        container.appendChild(card);
    });
}


// ============================================================
// Render AI Advisor Panel
// ============================================================

function renderAIAdvisor(text) {
    const advisorPanel = document.getElementById("ai-advisor-panel");

    advisorPanel.style.display = "block";

    advisorPanel.innerHTML = `
        <h3>AI Loan Advisor</h3>
        <p>${text}</p>
    `;
}
