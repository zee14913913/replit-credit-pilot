let customerData = null;
let cashflowChart = null;
let spendingChart = null;

function initCustomer360Dashboard(customerId) {
    loadCustomerProfile(customerId);
}

async function loadCustomerProfile(customerId) {
    try {
        const response = await fetch(`/api/customers/${customerId}/loan-profile`);
        
        if (!response.ok) {
            throw new Error('Failed to load customer profile');
        }
        
        customerData = await response.json();
        
        renderCustomerBanner();
        renderCreditProfile();
        renderCashflowInsights();
        renderLoanCapabilities();
        renderProductMatches();
        
    } catch (error) {
        console.error('Error loading customer profile:', error);
        alert('Failed to load customer profile. Please try again.');
    }
}

function renderCustomerBanner() {
    document.getElementById('customerName').textContent = customerData.customer_name || 'Unknown Customer';
    document.getElementById('customerId').textContent = customerData.customer_id || '-';
}

function renderCreditProfile() {
    const riskGrade = customerData.risk_grade || 'N/A';
    const approvalOdds = customerData.approval_odds || 0;
    const dti = customerData.dti || 0;
    const foir = customerData.foir || 0;
    const ccrisBucket = customerData.ccris_bucket !== undefined ? customerData.ccris_bucket : '-';
    const ctosScore = customerData.ctos_score || '-';
    const monthlyIncome = customerData.income || 0;
    const totalCommitments = customerData.commitments || 0;
    const disposableIncome = monthlyIncome - totalCommitments;

    const riskGradeBadge = document.getElementById('riskGradeBadge');
    riskGradeBadge.querySelector('.grade-text').textContent = riskGrade;
    
    const gradeClass = 'grade-' + riskGrade.charAt(0).toLowerCase();
    riskGradeBadge.className = 'risk-grade-badge ' + gradeClass;

    renderApprovalOdds(approvalOdds);

    document.getElementById('dtiValue').textContent = (dti * 100).toFixed(1) + '%';
    document.getElementById('dtiStatus').textContent = getDTIStatus(dti);
    document.getElementById('dtiStatus').className = 'metric-status ' + getStatusClass(dti, 0.4);

    document.getElementById('foirValue').textContent = (foir * 100).toFixed(1) + '%';
    document.getElementById('foirStatus').textContent = getFOIRStatus(foir);
    document.getElementById('foirStatus').className = 'metric-status ' + getStatusClass(foir, 0.6);

    document.getElementById('ccrisBucket').textContent = ccrisBucket;
    document.getElementById('ccrisStatus').textContent = getCCRISStatus(ccrisBucket);
    document.getElementById('ccrisStatus').className = 'metric-status ' + getCCRISStatusClass(ccrisBucket);

    document.getElementById('ctosScore').textContent = ctosScore;
    if (ctosScore !== '-') {
        document.getElementById('ctosStatus').textContent = getCTOSStatus(ctosScore);
        document.getElementById('ctosStatus').className = 'metric-status ' + getCTOSStatusClass(ctosScore);
    }

    document.getElementById('monthlyIncome').textContent = 'RM ' + formatNumber(monthlyIncome);
    document.getElementById('totalCommitments').textContent = 'RM ' + formatNumber(totalCommitments);
    document.getElementById('disposableIncome').textContent = 'RM ' + formatNumber(disposableIncome);
}

function renderApprovalOdds(odds) {
    document.getElementById('approvalOddsValue').textContent = odds;
    
    const arc = document.getElementById('approvalOddsArc');
    const circumference = 471;
    const offset = circumference - (circumference * odds / 100);
    arc.style.strokeDashoffset = offset;
    
    if (odds >= 75) {
        arc.style.stroke = '#00ff87';
    } else if (odds >= 50) {
        arc.style.stroke = '#ffeb3b';
    } else if (odds >= 25) {
        arc.style.stroke = '#ff9800';
    } else {
        arc.style.stroke = '#f44336';
    }
}

function renderCashflowInsights() {
    const cashflowData = customerData.monthly_cashflow || [];
    const spendingData = customerData.credit_card_spending || [];

    if (cashflowChart) cashflowChart.destroy();
    if (spendingChart) spendingChart.destroy();

    const ctxCashflow = document.getElementById('cashflowChart').getContext('2d');
    cashflowChart = new Chart(ctxCashflow, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            datasets: [{
                label: 'Income',
                data: cashflowData.map(d => d.income || 0),
                borderColor: '#00ff87',
                backgroundColor: 'rgba(0, 255, 135, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Expenses',
                data: cashflowData.map(d => d.expenses || 0),
                borderColor: '#ff5722',
                backgroundColor: 'rgba(255, 87, 34, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: '12-Month Income & Expense Trends',
                    color: '#FF007F',
                    font: { size: 16 }
                },
                legend: {
                    labels: { color: '#fff' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#aaa' },
                    grid: { color: 'rgba(50, 36, 70, 0.3)' }
                },
                x: {
                    ticks: { color: '#aaa' },
                    grid: { color: 'rgba(50, 36, 70, 0.3)' }
                }
            }
        }
    });

    const ctxSpending = document.getElementById('spendingHeatmapChart').getContext('2d');
    spendingChart = new Chart(ctxSpending, {
        type: 'bar',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            datasets: [{
                label: 'Credit Card Spending',
                data: spendingData.map(d => d.amount || 0),
                backgroundColor: '#FF007F',
                borderColor: '#FF007F',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Credit Card Spending Heatmap',
                    color: '#FF007F',
                    font: { size: 16 }
                },
                legend: {
                    labels: { color: '#fff' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#aaa' },
                    grid: { color: 'rgba(50, 36, 70, 0.3)' }
                },
                x: {
                    ticks: { color: '#aaa' },
                    grid: { color: 'rgba(50, 36, 70, 0.3)' }
                }
            }
        }
    });
}

function renderLoanCapabilities() {
    const maxEmi = customerData.max_emi || 0;
    const maxLoanAmount = customerData.max_loan_amount || 0;
    const riskAdjustedAmount = Math.round(maxLoanAmount * 0.8);

    document.getElementById('maxEmi').textContent = 'RM ' + formatNumber(maxEmi);
    document.getElementById('maxLoanAmount').textContent = 'RM ' + formatNumber(maxLoanAmount);
    document.getElementById('riskAdjustedAmount').textContent = 'RM ' + formatNumber(riskAdjustedAmount);
}

function renderProductMatches() {
    const products = customerData.recommended_products || [];
    const container = document.getElementById('productMatchesList');

    if (products.length === 0) {
        container.innerHTML = '<div class="loading-state"><i class="bi bi-inbox"></i> No product matches available at this time.</div>';
        return;
    }

    container.innerHTML = '';

    products.slice(0, 5).forEach(product => {
        const card = document.createElement('div');
        card.className = 'product-match-card';
        card.innerHTML = `
            <div class="product-header">
                <div class="product-bank">${product.bank}</div>
                <div class="product-odds">${product.approval_probability || 'N/A'}% Match</div>
            </div>
            <div class="product-name">${product.product_name}</div>
            <div class="product-details">
                <div class="detail-item">
                    <span class="detail-label">Interest Rate</span>
                    <span class="detail-value">${product.interest_rate_min || 0}% - ${product.interest_rate_max || 0}%</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Max Amount</span>
                    <span class="detail-value">RM ${formatNumber(product.max_loan_amount || 0)}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Max Tenure</span>
                    <span class="detail-value">${product.max_tenure || 0} months</span>
                </div>
            </div>
            <div class="product-reason">
                <i class="bi bi-lightbulb"></i> <strong>Why matched:</strong> ${product.match_reason || 'Based on your credit profile and loan requirements.'}
            </div>
            <button class="btn-apply" onclick="applyWithProduct('${product.product_id}')">
                <i class="bi bi-check-circle"></i> Apply with this Product
            </button>
        `;
        container.appendChild(card);
    });
}

function simulateLoan() {
    const loanAmount = parseFloat(document.getElementById('simLoanAmount').value) || 0;
    const tenure = parseInt(document.getElementById('simTenure').value) || 60;

    if (loanAmount <= 0 || tenure <= 0) {
        alert('Please enter valid loan amount and tenure.');
        return;
    }

    const assumedRate = 0.05;
    const monthlyRate = assumedRate / 12;
    const numPayments = tenure;
    
    const emi = (loanAmount * monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / 
                (Math.pow(1 + monthlyRate, numPayments) - 1);

    const currentCommitments = customerData.commitments || 0;
    const monthlyIncome = customerData.income || 0;
    
    const newTotalCommitments = currentCommitments + emi;
    const newDTI = newTotalCommitments / monthlyIncome;
    const newFOIR = (newTotalCommitments * 0.7) / monthlyIncome;

    let approvalOddsImpact = customerData.approval_odds || 0;
    if (newDTI > 0.4) approvalOddsImpact -= 20;
    else if (newDTI > 0.35) approvalOddsImpact -= 10;
    else if (newDTI > 0.3) approvalOddsImpact -= 5;

    approvalOddsImpact = Math.max(0, Math.min(100, approvalOddsImpact));

    document.getElementById('simEmi').textContent = 'RM ' + formatNumber(Math.round(emi));
    document.getElementById('simDti').textContent = (newDTI * 100).toFixed(1) + '%';
    document.getElementById('simFoir').textContent = (newFOIR * 100).toFixed(1) + '%';
    document.getElementById('simApprovalOdds').textContent = approvalOddsImpact.toFixed(0) + '%';

    document.getElementById('simulatorResults').style.display = 'block';
}

function applyWithProduct(productId) {
    window.location.href = `/loan-evaluate?product_id=${productId}`;
}

function getDTIStatus(dti) {
    if (dti < 0.3) return 'Excellent';
    if (dti < 0.4) return 'Good';
    if (dti < 0.5) return 'Fair';
    return 'Poor';
}

function getFOIRStatus(foir) {
    if (foir < 0.5) return 'Excellent';
    if (foir < 0.6) return 'Good';
    if (foir < 0.7) return 'Fair';
    return 'Poor';
}

function getCCRISStatus(bucket) {
    if (bucket === 0) return 'Perfect';
    if (bucket === 1) return 'Good';
    if (bucket === 2) return 'Fair';
    return 'Poor';
}

function getCTOSStatus(score) {
    if (score >= 700) return 'Excellent';
    if (score >= 650) return 'Good';
    if (score >= 600) return 'Fair';
    return 'Poor';
}

function getStatusClass(value, threshold) {
    if (value < threshold * 0.75) return 'excellent';
    if (value < threshold) return 'good';
    if (value < threshold * 1.25) return 'fair';
    return 'poor';
}

function getCCRISStatusClass(bucket) {
    if (bucket === 0) return 'excellent';
    if (bucket === 1) return 'good';
    if (bucket === 2) return 'fair';
    return 'poor';
}

function getCTOSStatusClass(score) {
    if (score >= 700) return 'excellent';
    if (score >= 650) return 'good';
    if (score >= 600) return 'fair';
    return 'poor';
}

function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
