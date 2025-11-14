/* ===========================================================
   Phase 9 — Loan Products Marketplace JavaScript
   =========================================================== */

let allProducts = [];
let filteredProducts = [];
let currentFilter = 'all';
let currentProduct = null;

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', function() {
    // Load products data from server
    if (window.productsData) {
        allProducts = window.productsData;
        filteredProducts = allProducts;
        renderProducts(filteredProducts);
    }

    // Setup event listeners
    setupSearchListener();
    setupFilterButtons();
    
    // Listen for language change events and re-render cards
    window.addEventListener('languageChanged', function(e) {
        console.log('Language changed to:', e.detail.lang);
        // Re-render all products with new translations
        renderProducts(filteredProducts);
        
        // If modal is open, refresh it with new translations
        if (currentProduct && !document.getElementById('productModal').classList.contains('hidden')) {
            openProductModal(currentProduct);
        }
    });
});

// ========== SEARCH FUNCTIONALITY ==========
function setupSearchListener() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            filteredProducts = allProducts.filter(p => {
                const bankMatch = p.bank.toLowerCase().includes(query);
                const nameMatch = p.product_name.toLowerCase().includes(query);
                return bankMatch || nameMatch;
            });
            applyCurrentFilter();
            renderProducts(filteredProducts);
        });
    }
}

// ========== FILTER FUNCTIONALITY ==========
function setupFilterButtons() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Update active state
            filterBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            // Apply filter
            currentFilter = this.getAttribute('data-filter');
            applyCurrentFilter();
            renderProducts(filteredProducts);
        });
    });
}

function applyCurrentFilter() {
    const searchQuery = document.getElementById('searchInput').value.toLowerCase();

    // Step 1: 搜索过滤
    filteredProducts = allProducts.filter(p => {
        if (!searchQuery) return true;
        const bankMatch = p.bank.toLowerCase().includes(searchQuery);
        const nameMatch = p.product_name.toLowerCase().includes(searchQuery);
        return bankMatch || nameMatch;
    });

    // Step 2: 类型过滤（仅对type filters应用，不对sorting modes应用）
    if (currentFilter === 'traditional_bank' || currentFilter === 'digital_bank' || currentFilter === 'fintech') {
        filteredProducts = filteredProducts.filter(p => p.type === currentFilter);
    }

    // Step 3: 排序（对sorting modes应用）- 先克隆数组避免变异原数组
    if (currentFilter === 'lowest_rate') {
        filteredProducts = [...filteredProducts].sort((a, b) => {
            const rateA = a.interest_rate ? a.interest_rate.min : (a.rate_range ? a.rate_range[0] : a.base_rate || 0);
            const rateB = b.interest_rate ? b.interest_rate.min : (b.rate_range ? b.rate_range[0] : b.base_rate || 0);
            return rateA - rateB;
        });
    } else if (currentFilter === 'highest_amount') {
        filteredProducts = [...filteredProducts].sort((a, b) => {
            const amountA = a.max_loan_amount || a.max_amount || 0;
            const amountB = b.max_loan_amount || b.max_amount || 0;
            return amountB - amountA;
        });
    }
}

// ========== RENDER PRODUCTS ==========
function renderProducts(products) {
    const grid = document.getElementById('productsGrid');
    if (!grid) return;

    grid.innerHTML = '';

    if (products.length === 0) {
        const noProductsText = window.i18n ? window.i18n.translate('no_products_found_dot') : 'No products found.';
        grid.innerHTML = `<p style="color: #aaa; text-align: center; grid-column: 1/-1;">${noProductsText}</p>`;
        return;
    }

    products.forEach(product => {
        const card = createProductCard(product);
        grid.appendChild(card);
    });
}

function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.onclick = () => openProductModal(product);

    const bankInitial = product.bank.charAt(0).toUpperCase();
    const typeBadgeClass = product.type || 'traditional_bank';

    const minRate = product.interest_rate ? (product.interest_rate.min * 100).toFixed(2) : 
                     (product.rate_range ? (product.rate_range[0] * 100).toFixed(2) : 
                     (product.base_rate ? (product.base_rate * 100).toFixed(2) : '0.00'));
    const maxRate = product.interest_rate ? (product.interest_rate.max * 100).toFixed(2) : 
                     (product.rate_range ? (product.rate_range[1] * 100).toFixed(2) : 
                     (product.base_rate ? (product.base_rate * 100).toFixed(2) : '0.00'));

    const interestRateLabel = window.i18n ? window.i18n.translate('interest_rate_label') : 'Interest Rate';
    const maxLoanLabel = window.i18n ? window.i18n.translate('max_loan_label') : 'Max Loan';
    const maxTenureLabel = window.i18n ? window.i18n.translate('max_tenure_label') : 'Max Tenure';
    const approvalTimeLabel = window.i18n ? window.i18n.translate('approval_time_label') : 'Approval Time';
    const monthsUnit = window.i18n ? window.i18n.translate('months_unit') : 'months';
    const hoursUnit = window.i18n ? window.i18n.translate('hours_unit') : 'hours';
    const viewDetailsBtn = window.i18n ? window.i18n.translate('view_details_btn') : 'View Details';
    const selectBtn = window.i18n ? window.i18n.translate('select_btn') : 'Select';
    
    card.innerHTML = `
        <div class="product-card-header">
            <div class="bank-logo">${bankInitial}</div>
            <div class="product-info">
                <h3>${product.product_name}</h3>
                <p>${product.bank}</p>
                <span class="product-type-badge ${typeBadgeClass}">
                    ${formatProductType(product.type || 'traditional_bank')}
                </span>
            </div>
        </div>

        <div class="product-details">
            <div class="detail-row">
                <label>${interestRateLabel}</label>
                <span class="rate-highlight">${minRate}% - ${maxRate}%</span>
            </div>
            <div class="detail-row">
                <label>${maxLoanLabel}</label>
                <span>RM ${formatNumber(product.max_loan_amount || product.max_amount || 0)}</span>
            </div>
            <div class="detail-row">
                <label>${maxTenureLabel}</label>
                <span>${product.max_tenure} ${monthsUnit}</span>
            </div>
            <div class="detail-row">
                <label>${approvalTimeLabel}</label>
                <span>${product.approval_time_hours || 48} ${hoursUnit}</span>
            </div>
        </div>

        <div class="product-actions">
            <button class="btn-view-details" onclick="event.stopPropagation(); openProductModal(${JSON.stringify(product).replace(/"/g, '&quot;')})">
                <i class="bi bi-eye"></i> ${viewDetailsBtn}
            </button>
            <button class="btn-select" onclick="event.stopPropagation(); selectProduct(${JSON.stringify(product).replace(/"/g, '&quot;')})">
                <i class="bi bi-calculator"></i> ${selectBtn}
            </button>
        </div>
    `;

    return card;
}

// ========== PRODUCT MODAL ==========
function openProductModal(product) {
    currentProduct = product;
    const modal = document.getElementById('productModal');
    
    // Get translated units
    const monthsUnit = window.i18n ? window.i18n.translate('months_unit') : 'months';
    const hoursUnit = window.i18n ? window.i18n.translate('hours_unit') : 'hours';
    const variesText = window.i18n ? window.i18n.translate('varies') : 'Varies';

    // Fill modal content
    document.getElementById('modalBankLogo').textContent = product.bank.charAt(0).toUpperCase();
    document.getElementById('modalProductName').textContent = product.product_name;
    document.getElementById('modalBankName').textContent = product.bank;

    const minRate = product.interest_rate ? (product.interest_rate.min * 100).toFixed(2) : 
                     (product.rate_range ? (product.rate_range[0] * 100).toFixed(2) : 
                     (product.base_rate ? (product.base_rate * 100).toFixed(2) : '0.00'));
    const maxRate = product.interest_rate ? (product.interest_rate.max * 100).toFixed(2) : 
                     (product.rate_range ? (product.rate_range[1] * 100).toFixed(2) : 
                     (product.base_rate ? (product.base_rate * 100).toFixed(2) : '0.00'));

    document.getElementById('modalRateMin').textContent = minRate + '%';
    document.getElementById('modalRateMax').textContent = maxRate + '%';

    document.getElementById('modalMaxAmount').textContent = 'RM ' + formatNumber(product.max_loan_amount || product.max_amount || 0);
    document.getElementById('modalMaxTenure').textContent = product.max_tenure + ' ' + monthsUnit;
    document.getElementById('modalMinIncome').textContent = product.min_income ? 'RM ' + formatNumber(product.min_income) : variesText;
    document.getElementById('modalApprovalTime').textContent = (product.approval_time_hours || 48) + ' ' + hoursUnit;

    // Features
    const featuresContainer = document.getElementById('modalFeatures');
    featuresContainer.innerHTML = '';
    const noFeaturesText = window.i18n ? window.i18n.translate('no_features_listed') : 'No features listed.';
    if (product.features && product.features.length > 0) {
        product.features.forEach(feature => {
            const div = document.createElement('div');
            div.className = 'feature-item';
            div.innerHTML = `<i class="bi bi-check-circle-fill" style="color: #00ff87; margin-right: 8px;"></i> ${feature}`;
            featuresContainer.appendChild(div);
        });
    } else {
        featuresContainer.innerHTML = `<p style="color: #aaa;">${noFeaturesText}</p>`;
    }

    // Eligibility
    const eligibilityContainer = document.getElementById('modalEligibility');
    eligibilityContainer.innerHTML = '';
    const minIncomeLabel = window.i18n ? window.i18n.translate('minimum_income') : 'Minimum income';
    const creditScoreLabel = window.i18n ? window.i18n.translate('credit_score') : 'Credit score';
    const ccrisBucketLabel = window.i18n ? window.i18n.translate('ccris_bucket') : 'CCRIS bucket';
    const standardEligibilityText = window.i18n ? window.i18n.translate('standard_eligibility') : 'Standard bank eligibility applies.';
    
    const eligibilityItems = [];
    if (product.min_income) eligibilityItems.push(`${minIncomeLabel}: RM ${formatNumber(product.min_income)}`);
    if (product.min_credit_score) eligibilityItems.push(`${creditScoreLabel}: ${product.min_credit_score}+`);
    if (product.ccris_bucket_max !== undefined) eligibilityItems.push(`${ccrisBucketLabel}: ≤${product.ccris_bucket_max}`);

    if (eligibilityItems.length > 0) {
        eligibilityItems.forEach(item => {
            const div = document.createElement('div');
            div.className = 'eligibility-item';
            div.textContent = item;
            eligibilityContainer.appendChild(div);
        });
    } else {
        eligibilityContainer.innerHTML = `<p style="color: #aaa;">${standardEligibilityText}</p>`;
    }

    modal.classList.remove('hidden');
}

function closeProductModal() {
    const modal = document.getElementById('productModal');
    modal.classList.add('hidden');
    currentProduct = null;
}

function selectProductForEvaluation() {
    if (!currentProduct) return;
    selectProduct(currentProduct);
}

// ========== SELECT PRODUCT ==========
function selectProduct(product) {
    // Store product_id in session (via API call)
    fetch('/api/loan-products/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: product.product_id || product.bank })
    })
    .then(() => {
        // Redirect to loan evaluation page
        window.location.href = '/loan-evaluate?product_id=' + encodeURIComponent(product.product_id || product.bank);
    })
    .catch(err => {
        console.error('Error selecting product:', err);
        // Fallback: direct redirect
        window.location.href = '/loan-evaluate?product_id=' + encodeURIComponent(product.product_id || product.bank);
    });
}

// ========== HELPER FUNCTIONS ==========
function formatProductType(type) {
    const typeKeyMap = {
        'traditional_bank': 'product_type_traditional_bank',
        'digital_bank': 'product_type_digital_bank',
        'fintech': 'product_type_fintech'
    };
    const key = typeKeyMap[type] || 'product_type_traditional_bank';
    return window.i18n ? window.i18n.translate(key) : 'Bank';
}

function formatNumber(num) {
    if (!num) return '0';
    return num.toLocaleString('en-MY');
}
