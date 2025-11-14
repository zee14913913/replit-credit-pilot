let smeProfileData = null;
let cashflowChart = null;
let arApChart = null;

async function initSME360Dashboard(companyId) {
    try {
        console.log('[SME 360] Initializing dashboard for company:', companyId);
        await loadSMEProfile(companyId);
    } catch (error) {
        console.error('[SME 360] Initialization failed:', error);
        showError('Failed to load SME dashboard');
    }
}

async function loadSMEProfile(companyId) {
    try {
        const response = await fetch(`/api/sme/${companyId}/loan-profile`);
        
        if (!response.ok) {
            throw new Error(`API returned ${response.status}`);
        }
        
        const data = await response.json();
        smeProfileData = data;
        
        console.log('[SME 360] Profile data loaded:', data);
        
        renderBusinessProfile(data);
        renderCashflowInsights(data);
        renderLoanCapabilities(data);
        renderProductRecommendations(data);
        
        updateLastUpdated();
        
    } catch (error) {
        console.error('[SME 360] Failed to load profile:', error);
        showError('Failed to load SME profile data');
    }
}

function renderBusinessProfile(data) {
    document.getElementById('companyName').textContent = data.company_name || 'Unknown Company';
    
    const brrBadge = document.getElementById('brrBadge');
    const brrValue = document.getElementById('brrValue');
    brrValue.textContent = data.brr_grade || '--';
    
    brrBadge.className = 'risk-badge';
    if (data.brr_grade <= 2) {
        brrBadge.classList.add('brr-1');
    } else if (data.brr_grade <= 4) {
        brrBadge.classList.add('brr-3');
    } else if (data.brr_grade <= 6) {
        brrBadge.classList.add('brr-5');
    } else {
        brrBadge.classList.add('brr-7');
    }
    
    const approvalOdds = data.approval_odds || 0;
    document.getElementById('approvalText').textContent = `${approvalOdds}%`;
    
    const circle = document.getElementById('approvalCircle');
    const circumference = 2 * Math.PI * 60;
    const offset = circumference - (approvalOdds / 100) * circumference;
    circle.style.strokeDashoffset = offset;
    
    document.getElementById('dscrValue').textContent = (data.dscr || 0).toFixed(2);
    document.getElementById('dsrValue').textContent = (data.dsr || 0).toFixed(2);
    document.getElementById('varianceValue').textContent = ((data.cashflow_variance || 0) * 100).toFixed(1) + '%';
    document.getElementById('ctosValue').textContent = data.ctos_sme_score || '--';
    
    const industryRisk = document.getElementById('industryRisk');
    const industryRiskLevel = data.industry_risk || 'Medium';
    industryRisk.textContent = industryRiskLevel;
    industryRisk.className = 'metric-value industry-risk';
    
    if (industryRiskLevel.toLowerCase() === 'low') {
        industryRisk.classList.add('low');
    } else if (industryRiskLevel.toLowerCase() === 'medium') {
        industryRisk.classList.add('medium');
    } else {
        industryRisk.classList.add('high');
    }
    
    document.getElementById('industryName').textContent = data.industry_name || 'General Business';
}

function renderCashflowInsights(data) {
    const monthlyRevenue = data.monthly_revenue || [];
    const monthlyExpenses = data.monthly_expenses || [];
    
    const labels = monthlyRevenue.map((item, index) => `M${index + 1}`);
    const revenueValues = monthlyRevenue.map(item => item.amount || 0);
    const expenseValues = monthlyExpenses.map(item => item.amount || 0);
    
    if (cashflowChart) {
        cashflowChart.destroy();
    }
    
    const ctx1 = document.getElementById('cashflowChart').getContext('2d');
    cashflowChart = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Revenue',
                    data: revenueValues,
                    borderColor: '#00ff88',
                    backgroundColor: 'rgba(0, 255, 136, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Expenses',
                    data: expenseValues,
                    borderColor: '#ff3333',
                    backgroundColor: 'rgba(255, 51, 51, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#ffffff'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#888',
                        callback: function(value) {
                            return 'RM ' + value.toLocaleString();
                        }
                    },
                    grid: {
                        color: 'rgba(50, 36, 70, 0.3)'
                    }
                },
                x: {
                    ticks: {
                        color: '#888'
                    },
                    grid: {
                        color: 'rgba(50, 36, 70, 0.3)'
                    }
                }
            }
        }
    });
    
    const arAging = data.ar_aging || {};
    const apAging = data.ap_aging || {};
    
    const agingLabels = ['0-30 Days', '31-60 Days', '61-90 Days', '90+ Days'];
    const arValues = [
        arAging['0-30'] || 0,
        arAging['31-60'] || 0,
        arAging['61-90'] || 0,
        arAging['90+'] || 0
    ];
    const apValues = [
        apAging['0-30'] || 0,
        apAging['31-60'] || 0,
        apAging['61-90'] || 0,
        apAging['90+'] || 0
    ];
    
    if (arApChart) {
        arApChart.destroy();
    }
    
    const ctx2 = document.getElementById('arApChart').getContext('2d');
    arApChart = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: agingLabels,
            datasets: [
                {
                    label: 'AR (Receivables)',
                    data: arValues,
                    backgroundColor: '#FF007F',
                    borderColor: '#FF007F',
                    borderWidth: 1
                },
                {
                    label: 'AP (Payables)',
                    data: apValues,
                    backgroundColor: '#322446',
                    borderColor: '#322446',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#ffffff'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#888',
                        callback: function(value) {
                            return 'RM ' + value.toLocaleString();
                        }
                    },
                    grid: {
                        color: 'rgba(50, 36, 70, 0.3)'
                    }
                },
                x: {
                    ticks: {
                        color: '#888'
                    },
                    grid: {
                        color: 'rgba(50, 36, 70, 0.3)'
                    }
                }
            }
        }
    });
}

function renderLoanCapabilities(data) {
    const maxLoanAmount = data.max_loan_amount || 0;
    const maxEmi = data.max_emi || 0;
    const cgcEligibility = data.cgc_eligibility || false;
    
    document.getElementById('maxLoanAmount').textContent = `RM ${maxLoanAmount.toLocaleString()}`;
    document.getElementById('maxEmi').textContent = `RM ${maxEmi.toLocaleString()}`;
    
    const cgcStatus = document.getElementById('cgcStatus');
    cgcStatus.textContent = cgcEligibility ? 'Eligible' : 'Not Eligible';
    cgcStatus.className = 'capability-value cgc-status';
    cgcStatus.classList.add(cgcEligibility ? 'eligible' : 'not-eligible');
    
    document.getElementById('simRate').value = '5.5';
}

function renderProductRecommendations(data) {
    const products = data.recommended_products || [];
    const productsGrid = document.getElementById('productsGrid');
    
    if (products.length === 0) {
        productsGrid.innerHTML = `
            <div class="loading-state">
                <i class="bi bi-inbox"></i>
                <p>No SME products available</p>
            </div>
        `;
        return;
    }
    
    productsGrid.innerHTML = products.map(product => `
        <div class="product-card">
            <div class="product-header">
                <div class="product-bank">${product.bank || 'Unknown Bank'}</div>
                <div class="product-name">${product.product_name || 'SME Loan Product'}</div>
            </div>
            <div class="product-details">
                <div class="product-detail-item">
                    <span class="product-detail-label">Interest Rate</span>
                    <span class="product-detail-value">${(product.interest_rate_min || 4.5).toFixed(2)}% - ${(product.interest_rate_max || 6.5).toFixed(2)}%</span>
                </div>
                <div class="product-detail-item">
                    <span class="product-detail-label">Max Amount</span>
                    <span class="product-detail-value">RM ${(product.max_loan_amount || 0).toLocaleString()}</span>
                </div>
                <div class="product-detail-item">
                    <span class="product-detail-label">Max Tenure</span>
                    <span class="product-detail-value">${product.max_tenure || 60} months</span>
                </div>
                <div class="product-detail-item">
                    <span class="product-detail-label">Approval Odds</span>
                    <span class="product-detail-value">${product.approval_probability || 70}%</span>
                </div>
            </div>
            <div class="product-match">
                <div class="match-score">Match Score: ${product.match_score || 85}%</div>
                <div class="match-reason">${product.match_reason || 'Suitable for your business profile'}</div>
            </div>
            <div class="product-action">
                <button class="apply-btn" onclick="applyWithProduct('${product.product_id || ''}')">
                    <i class="bi bi-check-circle"></i> Select for Evaluation
                </button>
            </div>
        </div>
    `).join('');
}

function simulateSMELoan() {
    if (!smeProfileData) {
        alert('Please wait for profile data to load');
        return;
    }
    
    const loanAmount = parseFloat(document.getElementById('simLoanAmount').value);
    const tenure = parseInt(document.getElementById('simTenure').value);
    const rate = parseFloat(document.getElementById('simRate').value);
    
    if (!loanAmount || !tenure || !rate) {
        alert('Please fill in all fields');
        return;
    }
    
    if (loanAmount < 10000 || loanAmount > 10000000) {
        alert('Loan amount must be between RM 10,000 and RM 10,000,000');
        return;
    }
    
    if (tenure < 12 || tenure > 120) {
        alert('Tenure must be between 12 and 120 months');
        return;
    }
    
    const monthlyRate = rate / 100 / 12;
    const emi = (loanAmount * monthlyRate * Math.pow(1 + monthlyRate, tenure)) / (Math.pow(1 + monthlyRate, tenure) - 1);
    
    const avgRevenue = smeProfileData.monthly_revenue && smeProfileData.monthly_revenue.length > 0
        ? smeProfileData.monthly_revenue.reduce((sum, item) => sum + (item.amount || 0), 0) / smeProfileData.monthly_revenue.length
        : 50000;
    
    const avgExpenses = smeProfileData.monthly_expenses && smeProfileData.monthly_expenses.length > 0
        ? smeProfileData.monthly_expenses.reduce((sum, item) => sum + (item.amount || 0), 0) / smeProfileData.monthly_expenses.length
        : 30000;
    
    const netCashflow = avgRevenue - avgExpenses;
    const newDscr = netCashflow / emi;
    
    let newApprovalOdds = 0;
    if (newDscr >= 1.5) {
        newApprovalOdds = 85;
    } else if (newDscr >= 1.25) {
        newApprovalOdds = 70;
    } else if (newDscr >= 1.0) {
        newApprovalOdds = 55;
    } else {
        newApprovalOdds = 30;
    }
    
    let riskImpact = 'Neutral';
    let riskClass = 'risk-neutral';
    
    if (newDscr > (smeProfileData.dscr || 1.5)) {
        riskImpact = 'Improved';
        riskClass = 'risk-positive';
    } else if (newDscr < (smeProfileData.dscr || 1.5)) {
        riskImpact = 'Degraded';
        riskClass = 'risk-negative';
    }
    
    document.getElementById('simEmi').textContent = `RM ${emi.toFixed(2)}`;
    document.getElementById('simDscr').textContent = newDscr.toFixed(2);
    document.getElementById('simApproval').textContent = `${newApprovalOdds}%`;
    
    const riskImpactEl = document.getElementById('simRiskImpact');
    riskImpactEl.textContent = riskImpact;
    riskImpactEl.className = riskClass;
    
    document.getElementById('simulatorResults').style.display = 'block';
}

function applyWithProduct(productId) {
    window.location.href = `/loan-evaluate?product_id=${productId}&mode=sme`;
}

function updateLastUpdated() {
    const now = new Date();
    const formatted = now.toLocaleString('en-MY', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    document.getElementById('lastUpdated').textContent = `Last updated: ${formatted}`;
}

function showError(message) {
    console.error('[SME 360] Error:', message);
    alert(message);
}
