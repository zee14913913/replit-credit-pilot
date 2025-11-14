// static/js/loan_evaluate.js
// Loan Evaluate frontend engine
// Supports: Full Automated Mode (file upload), Quick Estimate (income only), Quick Estimate (income + commitments)
// Renders: risk card, approval odds, loan summary, AI advisor text, top product cards

(() => {
  // ---- Helpers ----
  const $ = id => document.getElementById(id);
  const formatRM = (v) => {
    if (v === null || v === undefined || isNaN(v)) return '—';
    return Number(v).toLocaleString('en-MY', { maximumFractionDigits: 0 });
  };
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const percent = v => `${Math.round(clamp(v, 0, 100))}%`;

  // Small sigmoid for smoothing percentages
  function sigmoid(x) {
    return 1 / (1 + Math.exp(-x));
  }

  // Map risk score to grade label & color
  function gradeFromScore(score) {
    // score: 0-100
    if (score >= 92) return { grade: 'A+', color: 'grade-a-plus' };
    if (score >= 82) return { grade: 'A', color: 'grade-a' };
    if (score >= 72) return { grade: 'B+', color: 'grade-b-plus' };
    if (score >= 62) return { grade: 'B', color: 'grade-b' };
    if (score >= 52) return { grade: 'C', color: 'grade-c' };
    return { grade: 'D', color: 'grade-d' };
  }

  // Estimate approval odds based on simplified model
  function estimateApprovalOdds({ dti, creditScore = 700, ccrisBucket = 0, riskScore = 70 }) {
    // base: riskScore
    // adjust by credit and buckets and DTI
    let base = riskScore; // 0-100
    // credit adjustment
    if (creditScore >= 750) base += 8;
    else if (creditScore >= 700) base += 4;
    else if (creditScore >= 650) base -= 2;
    else base -= 8;
    // CCRIS penalty
    base -= (ccrisBucket * 6);
    // DTI penalty: each 1% above 50% reduce small amount
    if (dti > 50) base -= (dti - 50) * 0.8;
    // Map through sigmoid-ish smoothing
    const scaled = 100 / (1 + Math.exp(-((base - 50) / 12)));
    return Math.round(clamp(scaled, 5, 99));
  }

  // pick top 3 banks by simple logic using approvalOdds & risk grade
  function recommendBanks(approvalOdds) {
    // This is a heuristic placeholder; backend will return real products in Full Auto mode
    if (approvalOdds >= 90) {
      return [
        { bank: 'Public Bank', rate: '4.8%', approval: approvalOdds, maxLoan: 150000, tenure: 84 },
        { bank: 'Standard Chartered', rate: '5.2%', approval: approvalOdds - 1, maxLoan: 180000, tenure: 84 },
        { bank: 'Maybank', rate: '5.5%', approval: approvalOdds - 2, maxLoan: 150000, tenure: 84 }
      ];
    } else if (approvalOdds >= 70) {
      return [
        { bank: 'CIMB', rate: '6.0%', approval: approvalOdds, maxLoan: 100000, tenure: 84 },
        { bank: 'Hong Leong', rate: '6.5%', approval: approvalOdds - 3, maxLoan: 120000, tenure: 84 },
        { bank: 'RHB', rate: '6.8%', approval: approvalOdds - 5, maxLoan: 100000, tenure: 84 }
      ];
    } else {
      return [
        { bank: 'GXBank (Digital)', rate: '9.2%', approval: approvalOdds, maxLoan: 50000, tenure: 60 },
        { bank: 'Boost Bank (Micro)', rate: '11.0%', approval: approvalOdds - 3, maxLoan: 30000, tenure: 48 },
        { bank: 'AEON', rate: '12.5%', approval: approvalOdds - 5, maxLoan: 60000, tenure: 48 }
      ];
    }
  }

  // ---- Rendering helpers ----
  function showElement(el) {
    if (!el) return;
    el.classList.remove('hidden');
  }
  function hideElement(el) {
    if (!el) return;
    el.classList.add('hidden');
  }

  function renderRiskCard({ riskGradeLabel, dti, foir, ccrisBucket, creditScore, employment }) {
    $('risk_grade').textContent = riskGradeLabel || '—';
    $('r_dti').textContent = (dti !== undefined) ? `${dti.toFixed(1)}%` : '—';
    $('r_foir').textContent = (foir !== undefined) ? `${foir.toFixed(1)}%` : '—';
    $('r_bucket').textContent = (ccrisBucket !== undefined) ? ccrisBucket : '—';
    $('r_credit').textContent = creditScore || '—';
    $('r_emp').textContent = employment || '—';
    showElement($('risk_card'));
  }

  function renderOdds(oddsPercent) {
    $('odds_circle').textContent = `${oddsPercent}%`;
    showElement($('odds_card'));
  }

  function renderLoanSummary({ maxEmi, maxLoan }) {
    $('r_max_emi').textContent = maxEmi ? formatRM(maxEmi) : '—';
    $('r_max_loan').textContent = maxLoan ? formatRM(maxLoan) : '—';
    showElement($('loan_summary'));
  }

  function renderAIAdvisor(text) {
    $('advisor_text').textContent = text || 'We could not generate advice for this profile.';
    showElement($('ai_advisor'));
  }

  function renderProducts(products) {
    const container = $('products_container');
    container.innerHTML = '';
    if (!products || products.length === 0) {
      hideElement($('product_list'));
      return;
    }
    products.forEach(p => {
      const card = document.createElement('div');
      card.className = 'product-card';
      card.innerHTML = `
        <div class="product-card-inner">
          <div class="product-top">
            <div class="bank-name">${p.bank}</div>
            <div class="product-rate">${p.rate}</div>
          </div>
          <div class="product-body">
            <div>Max Loan: RM ${formatRM(p.maxLoan)}</div>
            <div>Tenure: up to ${p.tenure} months</div>
            <div>Approval: ${p.approval}%</div>
          </div>
          <div class="product-actions">
            <button class="btn small apply-btn" data-bank="${p.bank}">Apply</button>
            <button class="btn small report-btn" data-bank="${p.bank}">Download</button>
          </div>
        </div>
      `;
      container.appendChild(card);
    });
    showElement($('product_list'));
  }

  // ---- Estimate engines (client-side simplified) ----

  function estimateIncomeOnly(income) {
    // income = monthly nett income
    const monthlyIncome = Number(income || 0);
    // Conservative defaults: use 30% of income as EMI capacity
    const maxEmi = Math.max(0, monthlyIncome * 0.30);
    const maxLoan = Math.round(maxEmi * 84); // 7 years * 12
    // estimate DTI approximate: assume commitments 0 => DTI = EMI / income
    const dti = monthlyIncome > 0 ? (maxEmi / monthlyIncome) * 100 : 0;
    // FOIR assume 30% as well
    const foir = dti; // simplified
    // riskScore heuristic: higher income gives slight boost
    const incomeFactor = clamp((monthlyIncome / 10000) * 20 + 50, 20, 95); // 20..95
    const riskScore = Math.round(incomeFactor);
    const approvalOdds = estimateApprovalOdds({ dti, creditScore: 700, ccrisBucket: 0, riskScore });
    const products = recommendBanks(approvalOdds);
    const advisor = `Quick estimate based on monthly nett income RM ${formatRM(monthlyIncome)}. Estimated approval odds ${approvalOdds}%. To improve odds, upload CTOS/Bank Statement for accurate assessment.`;
    return {
      dti, foir, riskScore, approvalOdds, maxEmi: Math.round(maxEmi), maxLoan, products, advisor
    };
  }

  function estimateIncomeAndCommitments(income, commitments) {
    const monthlyIncome = Number(income || 0);
    const monthlyCommit = Number(commitments || 0);
    // DTI = (existing commitments + estimated new emi) / income => we solve for new emi capacity
    // Use bank heuristic: allow DTI up to 50% (conservative)
    // Max EMI capacity = income * 0.4 - existing commitments (but not negative)
    let maxEmi = Math.max(0, monthlyIncome * 0.40 - monthlyCommit);
    // fallback: if result negative, set 0
    const maxLoan = Math.round(maxEmi * 84);
    const dti = monthlyIncome ? ((monthlyCommit + maxEmi) / monthlyIncome) * 100 : 0;
    // FOIR approximate = same as DTI in simplified model
    const foir = dti;
    // riskScore heuristic: lower if commitments high
    const commitRatio = monthlyIncome ? monthlyCommit / monthlyIncome : 0;
    let riskBase = 70 - (commitRatio * 40); // reduce with more commitments
    // clamp
    const riskScore = Math.round(clamp(riskBase, 20, 95));
    const approvalOdds = estimateApprovalOdds({ dti, creditScore: 700, ccrisBucket: 0, riskScore });
    const products = recommendBanks(approvalOdds);
    const advisor = `Estimate based on net income RM ${formatRM(monthlyIncome)} and commitments RM ${formatRM(monthlyCommit)}. Estimated approval odds ${approvalOdds}%. Improve odds by reducing commitments or increasing income.`;
    return { dti, foir, riskScore, approvalOdds, maxEmi: Math.round(maxEmi), maxLoan, products, advisor };
  }

  // ---- Full automated mode: handle file uploads ----
  async function submitAutoEvaluation() {
    const ctosFile = $('ctos_file').files[0];
    const ccrisFile = $('ccris_file').files[0];
    const icFront = $('ic_front').files[0];
    const icBack = $('ic_back').files[0];

    if (!ctosFile && !ccrisFile && !icFront) {
      alert('Please upload at least one document (CTOS / CCRIS / IC) to start automated evaluation.');
      return;
    }

    // Show a loading state
    const btn = $('btn_auto_submit');
    btn.disabled = true;
    btn.textContent = 'Processing...';

    try {
      const fd = new FormData();
      if (ctosFile) fd.append('ctos', ctosFile);
      if (ccrisFile) fd.append('ccris', ccrisFile);
      if (icFront) fd.append('ic_front', icFront);
      if (icBack) fd.append('ic_back', icBack);
      // Add mode metadata
      fd.append('mode', 'modern');
      fd.append('data_mode', 'auto');

      // Note: adjust API endpoint if your backend expects a specific path /customer_id param
      const response = await fetch('/api/loans/evaluate', {
        method: 'POST',
        body: fd
      });

      if (!response.ok) {
        const txt = await response.text();
        throw new Error(`Server error: ${response.status} ${txt}`);
      }

      const result = await response.json();
      // Expected result shape (based on backend contract):
      // { risk_grade, final_dti, max_emi, max_loan_amount, approval_odds, recommended_products: [...], advisor_text: '...' }
      const riskGrade = result.risk_grade || result.riskScore || '—';
      const dti = result.final_dti !== undefined ? Number(result.final_dti) * 100 : (result.dti || 0);
      const foir = result.foir !== undefined ? Number(result.foir) * 100 : (result.foir || 0);
      const ccrisBucket = result.ccris_bucket !== undefined ? result.ccris_bucket : '—';
      const credit = result.credit_score || result.credit_score || '—';
      const employment = result.employment_status || '—';
      const odds = result.approval_odds !== undefined ? Math.round(result.approval_odds) : estimateApprovalOdds({ dti, riskScore: 70 });
      const maxEmi = result.max_emi || result.max_emi_calculated || null;
      const maxLoan = result.max_loan_amount || result.max_loan_amount_calculated || null;
      const advisorText = result.advisor_text || result.ai_advice || 'AI advisor summary not available.';
      const products = result.recommended_products || result.products || [];

      renderRiskCard({
        riskGradeLabel: riskGrade,
        dti: dti,
        foir,
        ccrisBucket,
        creditScore: credit,
        employment
      });
      renderOdds(odds);
      renderLoanSummary({ maxEmi, maxLoan });
      renderAIAdvisor(advisorText);

      // if backend returns products, map to our local display format
      const mappedProducts = products.length ? products.map(p => ({
        bank: p.bank || p.provider || 'Unknown',
        rate: (p.interest_rate ? `${(p.interest_rate * 100).toFixed(2)}%` : (p.rate || 'N/A')),
        approval: Math.round(p.approval_odds || p.approval || odds),
        maxLoan: p.max_loan_amount || p.max_loan || (maxLoan || 0),
        tenure: p.max_tenure || p.tenure || 84
      })) : recommendBanks(odds);
      renderProducts(mappedProducts);
    } catch (err) {
      console.error('Auto evaluation failed', err);
      alert('Automated evaluation failed: ' + (err.message || 'Unknown error'));
    } finally {
      btn.disabled = false;
      btn.textContent = 'Start Automated Evaluation';
    }
  }

  // ---- Quick estimate handlers ----
  function handleQuickIncome() {
    const income = Number($('qe_income').value || 0);
    if (!income || income <= 0) {
      alert('Please enter a valid nett income (RM).');
      return;
    }
    const res = estimateIncomeOnly(income);
    const gradeInfo = gradeFromScore(res.riskScore);
    renderRiskCard({
      riskGradeLabel: gradeInfo.grade,
      dti: res.dti,
      foir: res.foir,
      ccrisBucket: 0,
      creditScore: 700,
      employment: 'Unknown'
    });
    renderOdds(res.approvalOdds);
    renderLoanSummary({ maxEmi: res.maxEmi, maxLoan: res.maxLoan });
    renderAIAdvisor(res.advisor);
    renderProducts(res.products);
  }

  function handleQuickIncomeCommit() {
    const income = Number($('qe2_income').value || 0);
    const commit = Number($('qe2_commit').value || 0);
    if (!income || income <= 0) {
      alert('Please enter a valid nett income (RM).');
      return;
    }
    const res = estimateIncomeAndCommitments(income, commit);
    const gradeInfo = gradeFromScore(res.riskScore);
    renderRiskCard({
      riskGradeLabel: gradeInfo.grade,
      dti: res.dti,
      foir: res.foir,
      ccrisBucket: 0,
      creditScore: 700,
      employment: 'Unknown'
    });
    renderOdds(res.approvalOdds);
    renderLoanSummary({ maxEmi: res.maxEmi, maxLoan: res.maxLoan });
    renderAIAdvisor(res.advisor);
    renderProducts(res.products);
  }

  // ---- Mode switching ----
  function setMode(mode) {
    const autoBlock = $('auto_mode_block');
    const incBlock = $('income_mode_block');
    const commitBlock = $('commit_mode_block');

    // reset active class
    $('mode_auto').classList.remove('active');
    $('mode_income').classList.remove('active');
    $('mode_commit').classList.remove('active');

    hideElement($('risk_card'));
    hideElement($('odds_card'));
    hideElement($('loan_summary'));
    hideElement($('ai_advisor'));
    hideElement($('product_list'));

    if (mode === 'auto') {
      $('mode_auto').classList.add('active');
      autoBlock.classList.remove('hidden');
      incBlock.classList.add('hidden');
      commitBlock.classList.add('hidden');
    } else if (mode === 'income') {
      $('mode_income').classList.add('active');
      autoBlock.classList.add('hidden');
      incBlock.classList.remove('hidden');
      commitBlock.classList.add('hidden');
    } else if (mode === 'commit') {
      $('mode_commit').classList.add('active');
      autoBlock.classList.add('hidden');
      incBlock.classList.add('hidden');
      commitBlock.classList.remove('hidden');
    }
  }

  // ---- Attach event handlers ----
  function init() {
    // mode buttons
    $('mode_auto').addEventListener('click', () => setMode('auto'));
    $('mode_income').addEventListener('click', () => setMode('income'));
    $('mode_commit').addEventListener('click', () => setMode('commit'));

    // Quick estimate buttons
    $('btn_qe_income').addEventListener('click', handleQuickIncome);
    $('btn_qe_commit').addEventListener('click', handleQuickIncomeCommit);

    // Auto submit
    $('btn_auto_submit').addEventListener('click', submitAutoEvaluation);

    // Delegated product button listeners (apply/report) -- dynamic content
    document.addEventListener('click', (ev) => {
      const target = ev.target;
      if (target.matches('.apply-btn')) {
        const bank = target.dataset.bank;
        alert(`Redirecting to application flow for ${bank} (placeholder).`);
        // Implement redirection to application page or open loan application modal
      } else if (target.matches('.report-btn')) {
        const bank = target.dataset.bank;
        alert(`Generating report for product: ${bank} (placeholder).`);
        // Hook into report generation API if needed
      }
    });

    // Default mode = Full Automated
    setMode('auto');
  }

  // start when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
