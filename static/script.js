// TimeLog JavaScript 功能

// 全局变量
let currentStatus = null;
let statusUpdateInterval = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 初始化应用
function initializeApp() {
    updateNavbarStatus();
    
    // 每30秒更新一次状态
    statusUpdateInterval = setInterval(updateNavbarStatus, 30000);
    
    // 设置Toast容器
    initializeToast();
}

// 更新导航栏状态显示
function updateNavbarStatus() {
    fetch('/api/current_status')
        .then(response => response.json())
        .then(data => {
            currentStatus = data;
            const statusElement = document.getElementById('navbar-status');
            
            if (data.active) {
                const categoryMap = {
                    'study': '📚 学习',
                    'game': '🎮 游戏',
                    'other': '📋 其他'
                };
                
                statusElement.innerHTML = `
                    <span class="badge bg-success">
                        <i class="bi bi-play-circle-fill"></i>
                        ${categoryMap[data.category]} - ${data.duration}分钟
                    </span>
                `;
            } else {
                statusElement.innerHTML = `
                    <span class="badge bg-secondary">
                        <i class="bi bi-pause-circle"></i> 空闲
                    </span>
                `;
            }
        })
        .catch(error => {
            console.error('获取状态失败:', error);
        });
}

// 显示Toast通知
function showToast(message, type = 'info') {
    const toast = document.getElementById('notification-toast');
    const toastBody = document.getElementById('toast-message');
    const toastElement = new bootstrap.Toast(toast);
    
    // 设置消息内容
    toastBody.textContent = message;
    
    // 设置Toast样式
    const toastHeader = toast.querySelector('.toast-header');
    const icon = toastHeader.querySelector('i');
    
    // 移除之前的类
    toast.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info');
    icon.classList.remove('bi-check-circle', 'bi-exclamation-triangle', 'bi-info-circle', 'bi-x-circle');
    
    // 根据类型设置样式和图标
    switch(type) {
        case 'success':
            toast.classList.add('bg-success', 'text-white');
            icon.classList.add('bi-check-circle');
            break;
        case 'danger':
        case 'error':
            toast.classList.add('bg-danger', 'text-white');
            icon.classList.add('bi-x-circle');
            break;
        case 'warning':
            toast.classList.add('bg-warning');
            icon.classList.add('bi-exclamation-triangle');
            break;
        default:
            toast.classList.add('bg-info', 'text-white');
            icon.classList.add('bi-info-circle');
    }
    
    // 显示Toast
    toastElement.show();
}

// 初始化Toast
function initializeToast() {
    const toastElements = document.querySelectorAll('.toast');
    toastElements.forEach(function(element) {
        new bootstrap.Toast(element);
    });
}

// API请求辅助函数
function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    return fetch(url, { ...defaultOptions, ...options })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
}

// 开始任务
function startTask(taskName, category) {
    if (!taskName || !taskName.trim()) {
        showToast('请输入任务名称', 'warning');
        return Promise.reject('任务名称不能为空');
    }
    
    return apiRequest('/api/start_task', {
        method: 'POST',
        body: JSON.stringify({
            task: taskName.trim(),
            category: category || 'study'
        })
    })
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            updateNavbarStatus();
            return data;
        } else {
            showToast(data.message, 'danger');
            throw new Error(data.message);
        }
    })
    .catch(error => {
        console.error('开始任务失败:', error);
        showToast('开始任务失败，请重试', 'danger');
        throw error;
    });
}

// 停止任务
function stopTask() {
    return apiRequest('/api/stop_task', {
        method: 'POST'
    })
    .then(data => {
        if (data.success) {
            showToast(`${data.message}，持续 ${data.duration} 分钟`, 'success');
            updateNavbarStatus();
            return data;
        } else {
            showToast(data.message, 'warning');
            throw new Error(data.message);
        }
    })
    .catch(error => {
        console.error('停止任务失败:', error);
        showToast('停止任务失败，请重试', 'danger');
        throw error;
    });
}

// 获取统计数据
function getStatsData(days = 7) {
    return apiRequest(`/api/stats_data?days=${days}`)
        .catch(error => {
            console.error('获取统计数据失败:', error);
            showToast('获取统计数据失败', 'danger');
            throw error;
        });
}

// 清除所有数据
function clearAllData() {
    if (confirm('⚠️ 确定要清除所有时间记录数据吗？此操作不可恢复！')) {
        return apiRequest('/api/clear_data', {
            method: 'POST'
        })
        .then(data => {
            if (data.success) {
                showToast(data.message, 'success');
                updateNavbarStatus();
                // 刷新页面
                setTimeout(() => location.reload(), 1500);
                return data;
            } else {
                showToast('清除数据失败', 'danger');
                throw new Error('清除数据失败');
            }
        })
        .catch(error => {
            console.error('清除数据失败:', error);
            showToast('清除数据失败，请重试', 'danger');
            throw error;
        });
    }
    return Promise.reject('用户取消操作');
}

// 格式化时间
function formatDuration(minutes) {
    if (minutes < 60) {
        return `${minutes.toFixed(1)} 分钟`;
    } else {
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;
        return `${hours} 小时 ${remainingMinutes.toFixed(0)} 分钟`;
    }
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 计算百分比
function calculatePercentage(value, total) {
    if (total === 0) return 0;
    return Math.round((value / total) * 100);
}

// 获取类别显示名称
function getCategoryDisplay(category) {
    const categoryMap = {
        'study': '📚 学习',
        'game': '🎮 游戏',
        'other': '📋 其他'
    };
    return categoryMap[category] || category;
}

// 获取类别颜色
function getCategoryColor(category) {
    const colorMap = {
        'study': '#198754',    // success green
        'game': '#ffc107',     // warning yellow
        'other': '#0dcaf0'     // info cyan
    };
    return colorMap[category] || '#6c757d';
}

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
    }
});

// 错误处理
window.addEventListener('error', function(event) {
    console.error('页面错误:', event.error);
    showToast('页面发生错误，请刷新重试', 'danger');
});

// 网络状态检测
window.addEventListener('online', function() {
    showToast('网络连接已恢复', 'success');
    updateNavbarStatus();
});

window.addEventListener('offline', function() {
    showToast('网络连接断开', 'warning');
});
