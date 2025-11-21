/**
 * AI预测分析前端模块
 * Safe for AI V3 Stable Baseline - 不修改现有代码
 */

class AIPredictManager {
    constructor() {
        this.customerId = null;
        this.chartInstance = null;
    }

    /**
     * 初始化预测模块
     * @param {number} customerId - 客户ID
     */
    init(customerId) {
        this.customerId = customerId;
        this.loadHealthScore();
        this.loadTrends();
    }

    /**
     * 加载财务健康评分
     */
    async loadHealthScore() {
        const scoreBox = document.getElementById('ai-health-score');
        if (!scoreBox) return;

        const t = (key, fallback) => window.i18n ? window.i18n.translate(key) : fallback;
        const loadingText = t('loading_text', '加载中...');
        scoreBox.innerHTML = `<div style="text-align:center; color:#888;">${loadingText}</div>`;

        try {
            const res = await fetch(`/api/ai-assistant/health-score/${this.customerId}`);
            const data = await res.json();

            const noDataText = t('no_data_available', '暂无数据');
            if (data.error || !data.score) {
                scoreBox.innerHTML = `<div style="color:#ff4444;">[ERROR] ${data.error || noDataText}</div>`;
                return;
            }

            const score = data.score;
            const explanation = data.ai_explanation;

            // Translatable text
            const scoreBreakdownText = t('score_breakdown_details', '分数明细');
            const aiAdvisorText = t('ai_advisor_recommendations', 'AI顾问建议');

            // 评分颜色
            let scoreColor = '#FF007F'; // Hot Pink
            if (score.total_score >= 80) scoreColor = '#00FF7F'; // 绿色
            else if (score.total_score >= 60) scoreColor = '#FFD700'; // 金色
            else if (score.total_score >= 40) scoreColor = '#FFA500'; // 橙色
            else scoreColor = '#FF4444'; // 红色

            scoreBox.innerHTML = `
                <div style="text-align:center; margin-bottom:20px;">
                    <div style="font-size:3rem; font-weight:900; color:${scoreColor}; text-shadow: 0 0 10px ${scoreColor};">
                        ${score.total_score}
                    </div>
                    <div style="color:#FF007F; font-weight:700; font-size:1.2rem; margin-top:8px;">
                        ${score.grade} - ${score.health_status}
                    </div>
                </div>
                
                <div style="background:#0a0a0a; padding:16px; border-radius:8px; margin-bottom:16px;">
                    <div style="color:#ccc; margin-bottom:12px; font-weight:600;">[CHART] ${scoreBreakdownText}：</div>
                    ${Object.entries(score.breakdown).map(([key, item]) => `
                        <div style="margin-bottom:10px;">
                            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                                <span style="color:#ddd;">${item.description}</span>
                                <span style="color:#FF007F; font-weight:700;">${item.score}/${item.max}</span>
                            </div>
                            <div style="background:#222; height:8px; border-radius:4px; overflow:hidden;">
                                <div style="background:#FF007F; height:100%; width:${(item.score/item.max)*100}%; border-radius:4px;"></div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div style="background:#1a1228; padding:14px; border-radius:8px; border-left:4px solid #FF007F;">
                    <div style="color:#FF007F; font-weight:700; margin-bottom:8px;">[AI] ${aiAdvisorText}</div>
                    <div style="color:#ddd; line-height:1.6;">${explanation}</div>
                </div>
            `;
        } catch (error) {
            const loadingFailedText = t('loading_failed_error', '加载失败');
            scoreBox.innerHTML = `<div style="color:#ff4444;">[ERROR] ${loadingFailedText}: ${error.message}</div>`;
        }
    }

    /**
     * 加载趋势图表
     */
    async loadTrends() {
        const chartBox = document.getElementById('ai-trend-chart');
        if (!chartBox) return;

        const t = (key, fallback) => window.i18n ? window.i18n.translate(key) : fallback;

        try {
            const res = await fetch(`/api/ai-assistant/trends/${this.customerId}`);
            const data = await res.json();

            const noTrendDataText = t('no_trend_data_available', '暂无趋势数据');
            if (data.count === 0) {
                chartBox.innerHTML = `<div style="color:#888; text-align:center; padding:40px;">${noTrendDataText}</div>`;
                return;
            }

            // 创建图表
            this.renderTrendChart(chartBox, data);
        } catch (error) {
            const loadingFailedText = t('loading_failed_error', '加载失败');
            chartBox.innerHTML = `<div style="color:#ff4444;">[ERROR] ${loadingFailedText}: ${error.message}</div>`;
        }
    }

    /**
     * 渲染趋势图表（使用Chart.js）
     */
    renderTrendChart(container, data) {
        container.innerHTML = '<canvas id="ai-trend-canvas"></canvas>';
        const canvas = document.getElementById('ai-trend-canvas');
        const ctx = canvas.getContext('2d');

        const t = (key, fallback) => window.i18n ? window.i18n.translate(key) : fallback;

        // 销毁旧图表
        if (this.chartInstance) {
            this.chartInstance.destroy();
        }

        // 创建新图表
        this.chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: t('chart_expenses_rm', '支出 (RM)'),
                        data: data.expenses,
                        borderColor: '#322446',
                        backgroundColor: 'rgba(50, 36, 70, 0.1)',
                        tension: 0.3
                    },
                    {
                        label: t('chart_payments_rm', '还款 (RM)'),
                        data: data.payments,
                        borderColor: '#FF007F',
                        backgroundColor: 'rgba(255, 0, 127, 0.1)',
                        tension: 0.3
                    },
                    {
                        label: '余额 (RM)',
                        data: data.balances,
                        borderColor: '#00BFFF',
                        backgroundColor: 'rgba(0, 191, 255, 0.1)',
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#fff',
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#ccc' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#ccc' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                }
            }
        });
    }

    /**
     * 获取未来3个月预测
     */
    async loadPrediction() {
        const predBox = document.getElementById('ai-prediction');
        if (!predBox) return;

        const t = (key, fallback) => window.i18n ? window.i18n.translate(key) : fallback;
        predBox.innerHTML = `<div style="text-align:center; color:#888;">[LOADING] ${t('loading_text', '加载中...')}</div>`;

        try {
            const res = await fetch('/api/ai-assistant/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ customer_id: this.customerId })
            });

            const data = await res.json();

            if (data.prediction.error) {
                predBox.innerHTML = `<div style="color:#ff4444;">[ERROR] ${data.prediction.error}</div>`;
                return;
            }

            const pred = data.prediction;
            const insights = data.ai_insights;

            predBox.innerHTML = `
                <div style="margin-bottom:20px;">
                    <div style="color:#FF007F; font-weight:700; margin-bottom:12px;">[FORECAST] ${t('future_3_months_prediction', '未来 3 个月预测')}</div>
                    ${pred.predictions.map(p => `
                        <div style="background:#0a0a0a; padding:12px; border-radius:8px; margin-bottom:10px; border-left:3px solid #FF007F;">
                            <div style="color:#ddd; font-weight:600; margin-bottom:8px;">${p.statement_month}</div>
                            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                                <span style="color:#ccc;">${t('predicted_expenses_label', '预测支出:')}</span>
                                <span style="color:#322446; font-weight:700;">RM ${p.predicted_expenses.toFixed(2)}</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                                <span style="color:#ccc;">${t('predicted_payments_label', '预测还款:')}</span>
                                <span style="color:#FF007F; font-weight:700;">RM ${p.predicted_payments.toFixed(2)}</span>
                            </div>
                            <div style="display:flex; justify-content:space-between;">
                                <span style="color:#ccc;">${t('predicted_balance_label', '预测余额:')}</span>
                                <span style="color:#00BFFF; font-weight:700;">RM ${p.predicted_balance.toFixed(2)}</span>
                            </div>
                            <div style="margin-top:6px; text-align:right; color:#888; font-size:0.85rem;">
                                ${t('confidence_label', '置信度:')} ${(p.confidence * 100).toFixed(0)}%
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div style="background:#1a1228; padding:14px; border-radius:8px; border-left:4px solid #FF007F;">
                    <div style="color:#FF007F; font-weight:700; margin-bottom:8px;">[AI] ${t('ai_insights', 'AI洞察')}</div>
                    <div style="color:#ddd; line-height:1.6;">${insights}</div>
                </div>
            `;
        } catch (error) {
            predBox.innerHTML = `<div style="color:#ff4444;">[ERROR] ${t('loading_failed_error', '加载失败')}: ${error.message}</div>`;
        }
    }
}

// 全局实例
window.aiPredictManager = new AIPredictManager();
