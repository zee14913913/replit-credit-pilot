/**
 * Evidence Archive Management
 * Option B实施 - 证据归档管理页面前端逻辑
 */

let evidenceData = [];
let currentUser = null;

document.addEventListener('DOMContentLoaded', function() {
    initPage();
});

async function initPage() {
    try {
        await loadEvidenceList();
        setupEventListeners();
    } catch (error) {
        console.error('初始化失败:', error);
        showToast('Failed to initialize page', 'error');
    }
}

function setupEventListeners() {
    const btnRotate = document.getElementById('btn-run-rotation');
    if (btnRotate) {
        btnRotate.addEventListener('click', runRotation);
    }
}

async function loadEvidenceList() {
    try {
        const response = await fetch('/downloads/evidence/list');
        const data = await response.json();
        
        if (!data.success) {
            throw new Error('Failed to load evidence list');
        }
        
        evidenceData = data.bundles.map(bundle => ({
            filename: bundle.filename,
            createdAt: formatCreatedAt(bundle.created_at),
            size: bundle.size,
            sha256: bundle.sha256,
            source: bundle.source
        }));
        
        renderTable();
    } catch (error) {
        console.error('加载证据列表失败:', error);
        document.getElementById('evidence-tbody').innerHTML = `
            <tr>
                <td colspan="6" class="no-records" data-i18n="failed_to_load">
                    Failed to load evidence bundles
                </td>
            </tr>
        `;
    }
}

function formatCreatedAt(timestamp) {
    if (timestamp === 'Unknown' || timestamp.length !== 14) {
        return 'Unknown';
    }
    
    const year = timestamp.substr(0, 4);
    const month = timestamp.substr(4, 2);
    const day = timestamp.substr(6, 2);
    const hour = timestamp.substr(8, 2);
    const minute = timestamp.substr(10, 2);
    const second = timestamp.substr(12, 2);
    
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

function renderTable() {
    const tbody = document.getElementById('evidence-tbody');
    
    if (evidenceData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="no-records" data-i18n="no_records">
                    No evidence bundles found
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = evidenceData.map(item => `
        <tr>
            <td>
                <i class="bi bi-file-earmark-zip"></i> ${item.filename}
            </td>
            <td>${item.createdAt}</td>
            <td>${formatBytes(item.size)}</td>
            <td><span class="sha256-hash" title="${item.sha256}">${item.sha256}</span></td>
            <td>${item.source}</td>
            <td>
                <a href="/downloads/evidence/file/${item.filename}" download class="btn-delete" style="margin-right: 0.5rem;">
                    <i class="bi bi-download"></i>
                </a>
                ${isAdmin() ? `
                <button class="btn-delete" onclick="deleteBundle('${item.filename}')">
                    <i class="bi bi-trash"></i>
                </button>
                ` : ''}
            </td>
        </tr>
    `).join('');
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function isAdmin() {
    const userRole = document.querySelector('[data-user-role]');
    return userRole && userRole.dataset.userRole === 'admin';
}

async function deleteBundle(filename) {
    const confirmMsg = getTranslation('confirm_delete') || `确认删除: ${filename}?`;
    if (!confirm(confirmMsg)) {
        return;
    }
    
    try {
        const response = await fetch('/downloads/evidence/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ filename })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Delete failed');
        }
        
        showToast(result.message || 'Deleted successfully', 'success');
        await loadEvidenceList();
    } catch (error) {
        console.error('删除失败:', error);
        showToast(error.message || 'Failed to delete', 'error');
    }
}

async function runRotation() {
    const confirmMsg = getTranslation('confirm_rotation') || '确认执行证据包轮转策略？';
    if (!confirm(confirmMsg)) {
        return;
    }
    
    const token = prompt('请输入TASK_SECRET_TOKEN:', '');
    if (!token) {
        return;
    }
    
    try {
        showToast(getTranslation('rotation_running') || '正在执行轮转...', 'info');
        
        const response = await fetch('/tasks/evidence/rotate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-TASK-TOKEN': token
            }
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Rotation failed');
        }
        
        const msg = getTranslation('rotation_done') || 
            `轮转完成！保留${result.kept.length}个，删除${result.deleted.length}个`;
        showToast(msg, 'success');
        
        await loadEvidenceList();
    } catch (error) {
        console.error('轮转失败:', error);
        showToast(error.message || 'Failed to run rotation', 'error');
    }
}

function getTranslation(key) {
    if (typeof getI18nText === 'function') {
        return getI18nText(key);
    }
    return null;
}

function showToast(message, type = 'info') {
    if (typeof window.showToast === 'function') {
        window.showToast(message, type);
    } else {
        alert(message);
    }
}
