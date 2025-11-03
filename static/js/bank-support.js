async function fetchSupportedBanks() {
  const res = await fetch('/api/parsers/supported');
  if (!res.ok) throw new Error('failed_to_load_supported_banks');
  return res.json();
}

async function fetchBankMetrics() {
  const res = await fetch('/api/metrics/banks');
  if (!res.ok) return { banks: [] };
  return res.json();
}

function renderBankMatrix(container, banks, metrics) {
  const m = new Map((metrics.banks || []).map(x => [x.code, x]));
  container.innerHTML = `
    <div class="card card-matrix">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h3 class="mb-0" data-i18n="supported_banks_title">SUPPORTED BANKS (MY)</h3>
        <small data-i18n="supported_banks_updated">Updated</small>: ${new Date().toLocaleString()}
      </div>
      <div class="card-body">
        <table class="matrix-table">
          <thead>
            <tr>
              <th data-i18n="bank">Bank</th>
              <th data-i18n="capabilities">Capabilities</th>
              <th data-i18n="status">Status</th>
              <th data-i18n="success_rate">Success Rate</th>
              <th data-i18n="action">Action</th>
            </tr>
          </thead>
          <tbody>
            ${banks.map(b=>{
              const mm = m.get(b.code) || {};
              const statusBadge = !b.enabled ? '<span class="badge badge-gray" data-i18n="disabled">Disabled</span>'
                               : b.circuit_open ? '<span class="badge badge-warn">⚡ <span data-i18n="temporarily_unavailable">Temporarily Unavailable</span></span>'
                               : '<span class="badge badge-ok" data-i18n="available">Available</span>';
              const caps = [
                b.supports?.pdf ? '<span class="cap cap-on">PDF</span>' : '<span class="cap cap-off">PDF</span>',
                b.supports?.csv ? '<span class="cap cap-on">CSV</span>' : '<span class="cap cap-off">CSV</span>',
              ].join(' ');
              const sr = typeof mm.success_rate === 'number' ? (mm.success_rate*100).toFixed(0)+'%' : '-';
              const btn = (!b.enabled || b.circuit_open)
                ? `<button class="btn btn-outline" data-bank="${b.code}" data-action="use-template" data-i18n="use_csv_template">Use CSV Template</button>`
                : `<button class="btn btn-primary" data-bank="${b.code}" data-action="select-bank" data-i18n="choose_this_bank">Choose This Bank</button>`;
              return `
                <tr>
                  <td>${b.display_name || b.code}</td>
                  <td>${caps}</td>
                  <td>${statusBadge}</td>
                  <td>${sr}</td>
                  <td>${btn}</td>
                </tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>`;
}

export async function initBankSupportMatrix({ mountSelector, selectElSelector }) {
  try {
    const container = document.querySelector(mountSelector);
    if (!container) return;
    
    const [sup, met] = await Promise.all([fetchSupportedBanks(), fetchBankMetrics()]);
    const banks = sup.banks || [];
    renderBankMatrix(container, banks, met);

    const select = document.querySelector(selectElSelector);
    if (select) {
      select.innerHTML = `<option value="" data-i18n="auto_detect">Auto Detect</option>`;
      banks.forEach(b=>{
        const disabled = (!b.enabled || b.circuit_open) ? 'disabled' : '';
        const label = `${b.display_name || b.code}${b.circuit_open ? ' (⚡)' : ''}${!b.enabled ? ' (X)' : ''}`;
        const opt = document.createElement('option');
        opt.value = b.code;
        opt.textContent = label;
        if (disabled) opt.disabled = true;
        select.appendChild(opt);
      });

      container.addEventListener('click', (e)=>{
        const btn = e.target.closest('button[data-action]');
        if (!btn) return;
        const code = btn.dataset.bank;
        const action = btn.dataset.action;
        if (action === 'select-bank') {
          select.value = code;
          select.dispatchEvent(new Event('change'));
          document.getElementById('uploadForm')?.scrollIntoView({behavior:'smooth'});
        } else if (action === 'use-template') {
          const msg = window.i18n ? i18n('bank_unavailable_temporarily') : 'Bank temporarily unavailable. Use CSV template.';
          alert(msg);
          window.open('/static/templates/bank_statement_template.csv','_blank');
        }
      });
    }
    
    if (window.applyI18n) window.applyI18n();
  } catch (err) {
    console.error('Bank support matrix init failed', err);
  }
}
