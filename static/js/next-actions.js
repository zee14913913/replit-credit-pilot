/**
 * "下一步要做什么"面板组件
 * 根据上传的模块类型，显示相应的下一步操作
 */

class NextActionsPanel {
    constructor() {
        this.panel = null;
    }

    show(config) {
        const {
            module,
            company_id,
            file_id,
            statement_id,
            period
        } = config;

        // 移除旧面板
        this.hide();

        // 创建面板
        this.panel = document.createElement('div');
        this.panel.id = 'next-actions-panel';
        this.panel.className = 'next-actions-panel';
        
        const actions = this.getActionsForModule(module, company_id, file_id, statement_id, period);
        const title = window.i18n ? window.i18n.translate('next_steps_what_to_do') : '下一步要做什么';
        
        this.panel.innerHTML = `
            <div class="next-actions-container">
                <div class="next-actions-header">
                    <h3>[NEXT] ${title}</h3>
                    <button onclick="document.getElementById('next-actions-panel').remove()" class="close-btn">×</button>
                </div>
                <div class="next-actions-body">
                    ${actions}
                </div>
            </div>
        `;
        
        document.body.appendChild(this.panel);
        
        // 添加样式
        this.injectStyles();
    }

    getActionsForModule(module, company_id, file_id, statement_id, period) {
        // Get all translations
        const t = (key, fallback) => window.i18n ? window.i18n.translate(key) : fallback;
        
        const actionSets = {
            'bank': `
                <div class="action-item">
                    <a href="/api/bank-statements/${statement_id || file_id}" class="action-btn">
                        [CHART] ${t('view_parsing_results', '查看解析结果')}
                    </a>
                    <span class="action-desc">${t('view_identified_bank_transactions', '查看系统识别的银行交易')}</span>
                </div>
                <div class="action-item">
                    <a href="/exceptions?company_id=${company_id}&source=bank" class="action-btn">
                        [WARNING] ${t('go_to_exception_center_unidentified', '去异常中心处理未识别行')}
                    </a>
                    <span class="action-desc">${t('handle_failed_transactions', '处理解析失败的交易')}</span>
                </div>
                <div class="action-item">
                    <a href="/export/journal/csv?company_id=${company_id}&period=${period || ''}" class="action-btn">
                        [DOWNLOAD] ${t('export_journal_csv', '导出分录CSV')}
                    </a>
                    <span class="action-desc">${t('download_accounting_entries', '下载会计分录')}</span>
                </div>
                <div class="action-item">
                    <a href="/accounting_files?company_id=${company_id}&module=bank" class="action-btn">
                        [FOLDER] ${t('back_to_file_list', '回文件列表')}
                    </a>
                    <span class="action-desc">${t('view_all_bank_statements', '查看所有银行月结单')}</span>
                </div>
            `,
            
            'credit-card': `
                <div class="action-item">
                    <a href="/view-pdf/${file_id}" class="action-btn">
                        [PDF] ${t('view_original_pdf', '查看原始PDF')}
                    </a>
                    <span class="action-desc">${t('view_credit_card_statement_original', '查看信用卡账单原件')}</span>
                </div>
                <div class="action-item">
                    <a href="/transactions/${file_id}" class="action-btn">
                        [CARD] ${t('view_identified_transactions', '查看系统识别的交易')}
                    </a>
                    <span class="action-desc">${t('view_parsed_transaction_records', '查看解析后的交易记录')}</span>
                </div>
                <div class="action-item">
                    <a href="/generate-monthly-report/${company_id}" class="action-btn">
                        [CHART] ${t('generate_view_monthly_report_pdf', '生成/查看月报PDF')}
                    </a>
                    <span class="action-desc">${t('generate_customer_monthly_report', '生成客户月度报告')}</span>
                </div>
                <div class="action-item">
                    <a href="/customers/${company_id}" class="action-btn">
                        [USER] ${t('back_to_customer_page', '回客户页')}
                    </a>
                    <span class="action-desc">${t('return_to_customer_management', '返回客户管理页面')}</span>
                </div>
            `,
            
            'pos': `
                <div class="action-item">
                    <a href="/api/pos-invoices/list?company_id=${company_id}" class="action-btn">
                        [RECEIPT] ${t('view_auto_generated_invoice_list', '查看自动生成的客户发票列表')}
                    </a>
                    <span class="action-desc">${t('view_system_generated_invoices', '查看系统自动生成的发票')}</span>
                </div>
                <div class="action-item">
                    <a href="/download-invoices/${file_id}" class="action-btn">
                        [DOWNLOAD] ${t('download_generated_pdf_invoices', '下载本次生成的PDF发票')}
                    </a>
                    <span class="action-desc">${t('batch_download_invoice_pdf', '批量下载发票PDF')}</span>
                </div>
                <div class="action-item">
                    <a href="/exceptions?company_id=${company_id}&source=pos" class="action-btn">
                        [WARNING] ${t('go_to_exception_center_no_customer', '去异常中心看"找不到客户的交易"')}
                    </a>
                    <span class="action-desc">${t('handle_unmatched_customer_transactions', '处理无法匹配客户的交易')}</span>
                </div>
            `,
            
            'supplier': `
                <div class="action-item">
                    <a href="/api/supplier-invoices/${file_id}" class="action-btn">
                        [LIST] ${t('view_invoice_details', '查看发票详情')}
                    </a>
                    <span class="action-desc">${t('view_supplier_invoice_parsing_results', '查看供应商发票解析结果')}</span>
                </div>
                <div class="action-item">
                    <a href="/ap-aging?company_id=${company_id}" class="action-btn">
                        [CHART] ${t('view_accounts_payable_aging', '查看应付账款账龄')}
                    </a>
                    <span class="action-desc">${t('view_accounts_payable_report', '查看应付账款报表')}</span>
                </div>
            `,
            
            'reports': `
                <div class="action-item">
                    <a href="/api/reports/${file_id}" class="action-btn">
                        [CHART] ${t('view_reports', '查看报表')}
                    </a>
                    <span class="action-desc">${t('view_financial_reports', '查看财务报表')}</span>
                </div>
                <div class="action-item">
                    <a href="/accounting_files?company_id=${company_id}" class="action-btn">
                        [FOLDER] ${t('back_to_file_list', '回文件列表')}
                    </a>
                    <span class="action-desc">${t('return_to_file_management', '返回文件管理')}</span>
                </div>
            `
        };

        return actionSets[module] || `
            <div class="action-item">
                <a href="/accounting_files?company_id=${company_id}" class="action-btn">
                    [FOLDER] ${t('back_to_file_list', '回文件列表')}
                </a>
                <span class="action-desc">${t('return_to_file_management', '返回文件管理')}</span>
            </div>
        `;
    }

    hide() {
        const existingPanel = document.getElementById('next-actions-panel');
        if (existingPanel) {
            existingPanel.remove();
        }
    }

    injectStyles() {
        if (document.getElementById('next-actions-styles')) return;

        const style = document.createElement('style');
        style.id = 'next-actions-styles';
        style.textContent = `
            .next-actions-panel {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 400px;
                background: #1a1a1a;
                border: 2px solid #FF007F;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(255, 0, 127, 0.3);
                z-index: 9999;
                animation: slideUp 0.4s ease-out;
            }

            @keyframes slideUp {
                from {
                    transform: translateY(100px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }

            .next-actions-header {
                background: #FF007F;
                color: white;
                padding: 16px 20px;
                border-radius: 10px 10px 0 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .next-actions-header h3 {
                margin: 0;
                font-size: 18px;
            }

            .next-actions-header .close-btn {
                background: none;
                border: none;
                color: white;
                font-size: 28px;
                cursor: pointer;
                padding: 0;
                width: 32px;
                height: 32px;
                line-height: 1;
            }

            .next-actions-body {
                padding: 20px;
            }

            .action-item {
                margin-bottom: 16px;
                padding-bottom: 16px;
                border-bottom: 1px solid #322446;
            }

            .action-item:last-child {
                margin-bottom: 0;
                padding-bottom: 0;
                border-bottom: none;
            }

            .action-btn {
                display: block;
                background: #322446;
                color: white;
                padding: 12px 16px;
                border-radius: 8px;
                text-decoration: none;
                font-size: 15px;
                font-weight: 500;
                transition: all 0.2s;
                margin-bottom: 8px;
            }

            .action-btn:hover {
                background: #FF007F;
                transform: translateX(4px);
            }

            .action-desc {
                display: block;
                color: #999;
                font-size: 13px;
                padding-left: 16px;
            }

            @media (max-width: 768px) {
                .next-actions-panel {
                    width: calc(100% - 40px);
                    left: 20px;
                    right: 20px;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// 全局单例
window.NextActions = new NextActionsPanel();
