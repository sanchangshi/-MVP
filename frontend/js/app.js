/**
 * 股票回测系统 - 主应用脚本
 */

// API 基础地址（自动判断环境）
const API_BASE = (() => {
    // 生产环境：使用 Render 后端地址
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        return 'https://stock-backtest-api.onrender.com';
    }
    // 本地开发环境
    return 'http://192.168.3.4:5000';
})();

// 生成浏览器指纹
function generateFingerprint() {
    const components = [];
    
    // 屏幕信息
    components.push(screen.width + 'x' + screen.height);
    components.push(screen.colorDepth);
    components.push(window.devicePixelRatio || 1);
    
    // 时区
    components.push(new Date().getTimezoneOffset());
    
    // 语言
    components.push(navigator.language || navigator.userLanguage);
    
    // 平台
    components.push(navigator.platform);
    
    // 用户代理
    components.push(navigator.userAgent);
    
    // Canvas 指纹
    try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillStyle = '#f60';
        ctx.fillRect(125, 1, 62, 20);
        ctx.fillStyle = '#069';
        ctx.fillText('Browser Fingerprint', 2, 15);
        components.push(canvas.toDataURL());
    } catch (e) {
        components.push('canvas-error');
    }
    
    // WebGL 指纹
    try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if (gl) {
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            if (debugInfo) {
                components.push(gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL));
                components.push(gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL));
            }
        }
    } catch (e) {
        components.push('webgl-error');
    }
    
    // 生成哈希
    const fingerprint = components.join('###');
    let hash = 0;
    for (let i = 0; i < fingerprint.length; i++) {
        const char = fingerprint.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return 'fp_' + Math.abs(hash).toString(36);
}

// 获取或创建浏览器指纹
const BROWSER_FINGERPRINT = (() => {
    const stored = localStorage.getItem('browser_fingerprint');
    if (stored) {
        return stored;
    }
    const fingerprint = generateFingerprint();
    localStorage.setItem('browser_fingerprint', fingerprint);
    return fingerprint;
})();

// 全局状态
const state = {
    stockPools: {},  // 股票池列表
    currentPool: 'hot',  // 当前选中的股票池（默认热门股）
    stocks: [],
    strategies: [],
    selectedStrategies: [],
    backtestResult: null,
    // 数据缓存
    dataCache: {
        symbol: null,
        startDate: null,
        endDate: null,
        data: null  // 缓存的股票数据
    }
};

// DOM 元素
const elements = {
    stockPool: document.getElementById('stockPool'),
    stockSelect: document.getElementById('stockSelect'),
    priceMode: document.getElementById('priceMode'),
    startDate: document.getElementById('startDate'),
    endDate: document.getElementById('endDate'),
    strategyList: document.getElementById('strategyList'),
    dropZone: document.getElementById('dropZone'),
    fetchDataBtn: document.getElementById('fetchDataBtn'),
    runBacktestBtn: document.getElementById('runBacktestBtn'),
    clearStrategiesBtn: document.getElementById('clearStrategiesBtn'),
    statsPanel: document.getElementById('statsPanel'),
    loading: document.getElementById('loading'),
    optimizeBtn: document.getElementById('optimizeBtn'),
    optimizeStrategy: document.getElementById('optimizeStrategy'),
    optimizeMetric: document.getElementById('optimizeMetric'),
    optimizeResult: document.getElementById('optimizeResult'),
    bestParams: document.getElementById('bestParams'),
    bestStats: document.getElementById('bestStats'),
    applyParamsBtn: document.getElementById('applyParamsBtn'),
    // 策略信号扫描
    stockScanBtn: document.getElementById('stockScanBtn'),
    scanCountDisplay: document.getElementById('scanCountDisplay'),
    scanResult: document.getElementById('scanResult'),
    scanSummary: document.getElementById('scanSummary'),
    scanList: document.getElementById('scanList')
};

// 最优参数缓存
let bestOptimizeParams = null;

// 调优次数管理（由后端 IP 控制）
const FREE_OPTIMIZE_LIMIT = 10;
let currentRemainingCount = FREE_OPTIMIZE_LIMIT;  // 当前剩余次数

function updateOptimizeCountDisplay(remaining) {
    if (remaining !== undefined) {
        currentRemainingCount = remaining;
    }
    
    // 查找或创建次数显示元素
    let countEl = document.getElementById('optimizeCountDisplay');
    if (!countEl) {
        countEl = document.createElement('div');
        countEl.id = 'optimizeCountDisplay';
        countEl.className = 'optimize-count';
        const optimizeLeft = document.querySelector('.optimize-left');
        if (optimizeLeft) {
            optimizeLeft.insertBefore(countEl, optimizeLeft.firstChild);
        }
    }
    
    if (currentRemainingCount <= 0) {
        countEl.className = 'optimize-count exhausted';
        countEl.innerHTML = `
            <span class="count-label">调优次数已用完</span>
            <span class="count-value">0/${FREE_OPTIMIZE_LIMIT}</span>
        `;
    } else if (currentRemainingCount <= 3) {
        countEl.className = 'optimize-count warning';
        countEl.innerHTML = `
            <span class="count-label">剩余调优次数：</span>
            <span class="count-value">${currentRemainingCount}/${FREE_OPTIMIZE_LIMIT}</span>
        `;
    } else {
        countEl.className = 'optimize-count';
        countEl.innerHTML = `
            <span class="count-label">剩余调优次数：</span>
            <span class="count-value">${currentRemainingCount}/${FREE_OPTIMIZE_LIMIT}</span>
        `;
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    await initApp();
    setupEventListeners();
    setupDragAndDrop();
    updateOptimizeCountDisplay();  // 显示调优次数
    initMessageBoard();  // 初始化留言板
});

/**
 * 初始化应用
 */
async function initApp() {
    showLoading(true);
    
    // 设置默认日期（默认2年）
    const today = new Date();
    const twoYearsAgo = new Date(today);
    twoYearsAgo.setFullYear(today.getFullYear() - 2);
    
    elements.endDate.value = today.toISOString().split('T')[0];
    elements.startDate.value = twoYearsAgo.toISOString().split('T')[0];
    
    try {
        // 并行加载股票池、股票列表和策略列表
        const [poolsRes, stocksRes, strategiesRes] = await Promise.all([
            fetch(`${API_BASE}/api/stock_pools`),
            fetch(`${API_BASE}/api/stocks?pool=hot`),
            fetch(`${API_BASE}/api/strategies`)
        ]);

        const poolsData = await poolsRes.json();
        const stocksData = await stocksRes.json();
        const strategiesData = await strategiesRes.json();

        if (poolsData.success) {
            state.stockPools = poolsData.data;
            renderStockPoolSelect();
        }

        if (stocksData.success) {
            state.stocks = stocksData.data;
            renderStockSelect();
        }

        if (strategiesData.success) {
            state.strategies = strategiesData.data;
            renderStrategyList();
        }
    } catch (error) {
        console.error('初始化失败:', error);
        alert('连接服务器失败，请确保后端服务已启动');
    } finally {
        showLoading(false);
    }
}

/**
 * 渲染股票池选择器
 */
function renderStockPoolSelect() {
    const options = Object.entries(state.stockPools).map(([key, pool]) => 
        `<option value="${key}">${pool.name} (${pool.count}只)</option>`
    ).join('');
    elements.stockPool.innerHTML = options;
    elements.stockPool.value = state.currentPool;
}

/**
 * 切换股票池
 */
async function switchStockPool(poolKey) {
    if (poolKey === state.currentPool) return;
    
    state.currentPool = poolKey;
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/stocks?pool=${poolKey}`);
        const data = await response.json();
        
        if (data.success) {
            state.stocks = data.data;
            renderStockSelect();
        }
    } catch (error) {
        console.error('切换股票池失败:', error);
        alert('切换股票池失败');
    } finally {
        showLoading(false);
    }
}

/**
 * 渲染股票选择器
 */
function renderStockSelect() {
    elements.stockSelect.innerHTML = state.stocks.map(stock => 
        `<option value="${stock.code}">${stock.code} - ${stock.name}</option>`
    ).join('');
}

/**
 * 渲染策略列表
 */
function renderStrategyList() {
    elements.strategyList.innerHTML = state.strategies.map(strategy => `
        <div class="strategy-card ${strategy.type}" 
             data-strategy='${JSON.stringify(strategy)}'>
            <h4>${strategy.display_name}</h4>
            <p>点击添加到组合区</p>
        </div>
    `).join('');
}

/**
 * 设置事件监听
 */
function setupEventListeners() {
    elements.fetchDataBtn.addEventListener('click', fetchStockData);
    elements.runBacktestBtn.addEventListener('click', runBacktest);
    elements.clearStrategiesBtn.addEventListener('click', clearStrategies);
    elements.optimizeBtn.addEventListener('click', runOptimize);
    elements.applyParamsBtn.addEventListener('click', applyBestParams);
    
    // 策略信号扫描
    elements.stockScanBtn.addEventListener('click', runStockScan);
    
    // 股票池切换
    elements.stockPool.addEventListener('change', (e) => {
        switchStockPool(e.target.value);
    });
}

/**
 * 设置策略交互功能（点击添加）
 */
function setupDragAndDrop() {
    // 点击策略卡片添加到组合区
    elements.strategyList.addEventListener('click', (e) => {
        const card = e.target.closest('.strategy-card');
        if (card) {
            const strategyJson = card.dataset.strategy;
            if (strategyJson) {
                addStrategy(JSON.parse(strategyJson));
            }
        }
    });

    // 保留拖拽功能（可选）
    elements.strategyList.addEventListener('dragstart', (e) => {
        if (e.target.classList.contains('strategy-card')) {
            e.dataTransfer.setData('strategy', e.target.dataset.strategy);
            e.target.style.opacity = '0.5';
        }
    });

    elements.strategyList.addEventListener('dragend', (e) => {
        if (e.target.classList.contains('strategy-card')) {
            e.target.style.opacity = '1';
        }
    });

    elements.dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.dropZone.classList.add('drag-over');
    });

    elements.dropZone.addEventListener('dragleave', () => {
        elements.dropZone.classList.remove('drag-over');
    });

    elements.dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.dropZone.classList.remove('drag-over');
        const strategyJson = e.dataTransfer.getData('strategy');
        if (strategyJson) {
            addStrategy(JSON.parse(strategyJson));
        }
    });
}

/**
 * 添加策略到组合区
 */
function addStrategy(strategy) {
    const exists = state.selectedStrategies.find(s => s.name === strategy.name);
    if (exists) {
        alert('该策略已添加');
        return;
    }
    state.selectedStrategies.push({ ...strategy });
    renderSelectedStrategies();
    updateBacktestButton();
    updateScanButtonState();
}

/**
 * 渲染已选择的策略
 */
function renderSelectedStrategies() {
    if (state.selectedStrategies.length === 0) {
        elements.dropZone.innerHTML = '<p class="placeholder">点击左侧策略添加到这里</p>';
        return;
    }

    elements.dropZone.innerHTML = state.selectedStrategies.map((strategy, index) => `
        <div class="placed-strategy ${strategy.type}">
            <button class="remove-btn" onclick="removeStrategy(${index})">×</button>
            <h4>${strategy.display_name}</h4>
            <div class="params">
                ${Object.entries(strategy.params).map(([key, param]) => `
                    <div class="param-row">
                        <label>${param.label}:</label>
                        <input type="number" 
                               value="${param.value}" 
                               min="${param.min}" 
                               max="${param.max}"
                               onchange="updateParam(${index}, '${key}', this.value)">
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
}

/**
 * 移除策略
 */
function removeStrategy(index) {
    state.selectedStrategies.splice(index, 1);
    renderSelectedStrategies();
    updateBacktestButton();
    updateScanButtonState();
}

/**
 * 更新策略参数
 */
function updateParam(strategyIndex, paramName, value) {
    state.selectedStrategies[strategyIndex].params[paramName].value = parseInt(value);
}

/**
 * 清空策略
 */
function clearStrategies() {
    state.selectedStrategies = [];
    renderSelectedStrategies();
    updateBacktestButton();
    elements.statsPanel.style.display = 'none';
}

/**
 * 更新回测按钮状态
 */
function updateBacktestButton() {
    elements.runBacktestBtn.disabled = state.selectedStrategies.length === 0;
}

/**
 * 检查缓存是否有效
 */
function isCacheValid(symbol, startDate, endDate) {
    return state.dataCache.symbol === symbol &&
           state.dataCache.startDate === startDate &&
           state.dataCache.endDate === endDate &&
           state.dataCache.data !== null;
}

/**
 * 获取股票数据
 */
async function fetchStockData() {
    const symbol = elements.stockSelect.value;
    const startDate = elements.startDate.value.replace(/-/g, '');  // 格式: YYYYMMDD
    const endDate = elements.endDate.value.replace(/-/g, '');  // 格式: YYYYMMDD
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/stock/data?symbol=${symbol}&start_date=${startDate}&end_date=${endDate}`);
        const data = await response.json();
        
        if (data.success) {
            // 缓存数据
            state.dataCache = {
                symbol: symbol,
                startDate: startDate,
                endDate: endDate,
                data: data.data
            };
            alert(`成功获取 ${symbol} 的数据，共 ${data.data.dates.length} 条记录（已缓存）`);
        } else {
            alert('获取数据失败: ' + data.error);
        }
    } catch (error) {
        console.error('获取数据失败:', error);
        alert('获取数据失败，请检查网络连接');
    } finally {
        showLoading(false);
    }
}

/**
 * 运行回测
 */
async function runBacktest() {
    const symbol = elements.stockSelect.value;
    const startDate = elements.startDate.value.replace(/-/g, '');  // 格式: YYYYMMDD
    const endDate = elements.endDate.value.replace(/-/g, '');  // 格式: YYYYMMDD
    const priceMode = elements.priceMode.value;  // 'close' 或 'chase'
    const strategies = state.selectedStrategies.map(s => ({
        type: s.type,
        params: s.params
    }));

    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/backtest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol,
                strategies,
                initial_capital: 100000,
                start_date: startDate,
                end_date: endDate,
                price_mode: priceMode
            })
        });

        const data = await response.json();
        
        if (data.success) {
            state.backtestResult = data.data;
            renderBacktestResult(data.data);
        } else {
            alert('回测失败: ' + data.error);
        }
    } catch (error) {
        console.error('回测失败:', error);
        alert('回测失败，请检查网络连接');
    } finally {
        showLoading(false);
    }
}

/**
 * 渲染回测结果
 */
function renderBacktestResult(result) {
    elements.statsPanel.style.display = 'block';
    
    document.getElementById('initialCapital').textContent = `¥${result.initial_capital.toLocaleString()}`;
    document.getElementById('finalCapital').textContent = `¥${result.final_value.toLocaleString()}`;
    
    const returnEl = document.getElementById('totalReturn');
    returnEl.textContent = `${result.total_return >= 0 ? '+' : ''}${result.total_return}%`;
    returnEl.className = `stat-value ${result.total_return < 0 ? 'negative' : ''}`;
    
    document.getElementById('totalTrades').textContent = result.total_trades;
    document.getElementById('winRate').textContent = `${result.win_rate}%`;
}

/**
 * 显示/隐藏加载动画
 */
function showLoading(show) {
    elements.loading.style.display = show ? 'flex' : 'none';
}

/**
 * 运行参数优化
 */
async function runOptimize() {
    const symbol = elements.stockSelect.value;
    const strategyType = elements.optimizeStrategy.value;
    const metric = elements.optimizeMetric.value;
    const priceMode = elements.priceMode.value;  // 获取价格模式
    const startDate = elements.startDate.value.replace(/-/g, '');  // 格式: YYYYMMDD
    const endDate = elements.endDate.value.replace(/-/g, '');  // 格式: YYYYMMDD

    showLoading(true);
    elements.optimizeResult.style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE}/api/optimize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol,
                strategy_type: strategyType,
                optimization_metric: metric,
                initial_capital: 100000,
                price_mode: priceMode,
                start_date: startDate,
                end_date: endDate,
                fingerprint: BROWSER_FINGERPRINT
            })
        });

        const data = await response.json();
        
        if (data.success) {
            // 更新剩余次数显示
            updateOptimizeCountDisplay(data.data.remaining_count);
            
            bestOptimizeParams = {
                strategyType: strategyType,
                params: data.data.best_params
            };
            renderOptimizeResult(data.data);
        } else {
            // 如果是次数限制错误
            if (data.limit_exceeded) {
                updateOptimizeCountDisplay(0);
            }
            alert('优化失败: ' + data.error);
        }
    } catch (error) {
        console.error('优化失败:', error);
        alert('优化失败，请检查网络连接');
    } finally {
        showLoading(false);
    }
}

/**
 * 渲染优化结果
 */
function renderOptimizeResult(data) {
    elements.optimizeResult.style.display = 'block';
    
    // 渲染最优参数
    const params = data.best_params;
    let paramsHtml = '';
    
    if (data.strategy_type === 'ma') {
        paramsHtml = `
            <div class="param-item">
                <span class="param-label">短期均线:</span>
                <span class="param-value">${params.short_period}</span>
            </div>
            <div class="param-item">
                <span class="param-label">长期均线:</span>
                <span class="param-value">${params.long_period}</span>
            </div>
        `;
    } else if (data.strategy_type === 'macd') {
        paramsHtml = `
            <div class="param-item">
                <span class="param-label">快线周期:</span>
                <span class="param-value">${params.fast_period}</span>
            </div>
            <div class="param-item">
                <span class="param-label">慢线周期:</span>
                <span class="param-value">${params.slow_period}</span>
            </div>
            <div class="param-item">
                <span class="param-label">信号线周期:</span>
                <span class="param-value">${params.signal_period}</span>
            </div>
        `;
    } else if (data.strategy_type === 'rsi') {
        paramsHtml = `
            <div class="param-item">
                <span class="param-label">RSI周期:</span>
                <span class="param-value">${params.period}</span>
            </div>
            <div class="param-item">
                <span class="param-label">超卖阈值:</span>
                <span class="param-value">${params.oversold}</span>
            </div>
            <div class="param-item">
                <span class="param-label">超买阈值:</span>
                <span class="param-value">${params.overbought}</span>
            </div>
        `;
    } else if (data.strategy_type === 'bollinger') {
        paramsHtml = `
            <div class="param-item">
                <span class="param-label">计算周期:</span>
                <span class="param-value">${params.period}</span>
            </div>
            <div class="param-item">
                <span class="param-label">标准差倍数:</span>
                <span class="param-value">${params.std_dev}</span>
            </div>
        `;
    } else if (data.strategy_type === 'kdj') {
        paramsHtml = `
            <div class="param-item">
                <span class="param-label">N周期:</span>
                <span class="param-value">${params.n_period}</span>
            </div>
            <div class="param-item">
                <span class="param-label">M1周期:</span>
                <span class="param-value">${params.m1_period}</span>
            </div>
            <div class="param-item">
                <span class="param-label">M2周期:</span>
                <span class="param-value">${params.m2_period}</span>
            </div>
        `;
    } else if (data.strategy_type === 'turtle') {
        paramsHtml = `
            <div class="param-item">
                <span class="param-label">入场周期:</span>
                <span class="param-value">${params.entry_period}</span>
            </div>
            <div class="param-item">
                <span class="param-label">出场周期:</span>
                <span class="param-value">${params.exit_period}</span>
            </div>
        `;
    } else if (data.strategy_type === 'atr') {
        paramsHtml = `
            <div class="param-item">
                <span class="param-label">ATR周期:</span>
                <span class="param-value">${params.period}</span>
            </div>
            <div class="param-item">
                <span class="param-label">止损倍数:</span>
                <span class="param-value">${params.multiplier}</span>
            </div>
        `;
    } else if (data.strategy_type === 'obv') {
        paramsHtml = `
            <div class="param-item">
                <span class="param-label">OBV周期:</span>
                <span class="param-value">${params.obv_period}</span>
            </div>
            <div class="param-item">
                <span class="param-label">MA周期:</span>
                <span class="param-value">${params.ma_period}</span>
            </div>
        `;
    }
    
    elements.bestParams.innerHTML = paramsHtml;
    
    // 渲染最优结果统计
    const bestResult = data.best_result;
    elements.bestStats.innerHTML = `
        <div class="stat-item-small">
            <span>收益率:</span>
            <span class="${bestResult.total_return >= 0 ? 'positive' : 'negative'}">${bestResult.total_return >= 0 ? '+' : ''}${bestResult.total_return}%</span>
        </div>
        <div class="stat-item-small">
            <span>胜率:</span>
            <span>${bestResult.win_rate}%</span>
        </div>
        <div class="stat-item-small">
            <span>交易次数:</span>
            <span>${bestResult.total_trades}</span>
        </div>
    `;
}

/**
 * 显示VIP升级提示
 */
function showVipModal() {
    alert('VIP功能开发中，敬请期待！\n\nVIP会员可享受：\n- 无限次参数调优\n- 查看完整优化参数\n- 更多高级策略');
}

/**
 * 应用最优参数到策略组合区
 */
function applyBestParams() {
    if (!bestOptimizeParams) {
        alert('没有可应用的优化参数');
        return;
    }
    
    const strategyType = bestOptimizeParams.strategyType;
    const params = bestOptimizeParams.params;
    
    // 查找对应策略
    const strategy = state.strategies.find(s => s.type === strategyType);
    if (!strategy) {
        alert('找不到对应策略');
        return;
    }
    
    // 创建带优化参数的策略副本
    const optimizedStrategy = JSON.parse(JSON.stringify(strategy));
    
    // 更新参数值
    Object.keys(params).forEach(key => {
        if (optimizedStrategy.params[key]) {
            optimizedStrategy.params[key].value = params[key];
        }
    });
    
    // 更新显示名称
    if (strategyType === 'ma') {
        optimizedStrategy.display_name = `均线策略(MA${params.short_period}/MA${params.long_period}) [优化]`;
    } else if (strategyType === 'macd') {
        optimizedStrategy.display_name = `MACD策略(${params.fast_period},${params.slow_period},${params.signal_period}) [优化]`;
    } else if (strategyType === 'rsi') {
        optimizedStrategy.display_name = `RSI策略(${params.period},${params.oversold},${params.overbought}) [优化]`;
    } else if (strategyType === 'bollinger') {
        optimizedStrategy.display_name = `布林带策略(${params.period},${params.std_dev}) [优化]`;
    }
    
    // 移除同类型的旧策略
    state.selectedStrategies = state.selectedStrategies.filter(s => s.type !== strategyType);
    
    // 添加优化后的策略
    state.selectedStrategies.push(optimizedStrategy);
    renderSelectedStrategies();
    updateBacktestButton();
    
    alert('已应用优化参数到策略组合区');
}

/**
 * 留言板功能
 */
const MESSAGE_STORAGE_KEY = 'user_messages';

// 初始化留言板
function initMessageBoard() {
    const submitBtn = document.getElementById('submitMessage');
    if (submitBtn) {
        submitBtn.addEventListener('click', submitMessage);
    }
    renderMessages();
}

// 获取留言列表
function getMessages() {
    const messages = localStorage.getItem(MESSAGE_STORAGE_KEY);
    return messages ? JSON.parse(messages) : [];
}

// 保存留言
function saveMessage(name, content) {
    const messages = getMessages();
    const newMessage = {
        id: Date.now(),
        name: name || '匿名用户',
        content: content,
        time: new Date().toLocaleString('zh-CN')
    };
    messages.unshift(newMessage);  // 新留言放前面
    
    // 最多保留50条留言
    if (messages.length > 50) {
        messages.pop();
    }
    
    localStorage.setItem(MESSAGE_STORAGE_KEY, JSON.stringify(messages));
    return newMessage;
}

// 提交留言
function submitMessage() {
    const contentInput = document.getElementById('messageContent');
    const content = contentInput.value.trim();
    
    if (!content) {
        alert('请输入留言内容');
        return;
    }
    
    saveMessage('', content);  // 不传昵称，默认匿名
    
    // 清空输入
    contentInput.value = '';
    
    // 刷新留言列表
    renderMessages();
    
    alert('留言发表成功！');
}

// 渲染留言列表
function renderMessages() {
    const messageList = document.getElementById('messageList');
    if (!messageList) return;
    
    const messages = getMessages();
    
    if (messages.length === 0) {
        messageList.innerHTML = '<div class="message-empty">暂无留言，快来发表第一条留言吧！</div>';
        return;
    }
    
    messageList.innerHTML = messages.map(msg => `
        <div class="message-item">
            <div class="message-header">
                <span class="message-author">${escapeHtml(msg.name)}</span>
                <span class="message-time">${msg.time}</span>
            </div>
            <div class="message-text">${escapeHtml(msg.content)}</div>
        </div>
    `).join('');
}

// HTML转义，防止XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== 策略信号扫描功能 ====================

const FREE_STOCK_SCAN_LIMIT = 3;
let currentScanRemainingCount = FREE_STOCK_SCAN_LIMIT;

/**
 * 更新扫描按钮状态
 */
function updateScanButtonState() {
    const hasStrategies = state.selectedStrategies.length > 0;
    elements.stockScanBtn.disabled = !hasStrategies;
    
    // 更新扫描次数显示
    updateScanCountDisplay(currentScanRemainingCount);
}

/**
 * 更新扫描次数显示
 */
function updateScanCountDisplay(remaining) {
    if (remaining !== undefined) {
        currentScanRemainingCount = remaining;
    }
    
    const countValue = elements.scanCountDisplay.querySelector('.count-value');
    if (!countValue) return;
    
    countValue.textContent = `${currentScanRemainingCount}/${FREE_STOCK_SCAN_LIMIT}`;
    
    // 更新样式
    elements.scanCountDisplay.classList.remove('warning', 'exhausted');
    if (currentScanRemainingCount <= 0) {
        elements.scanCountDisplay.classList.add('exhausted');
    } else if (currentScanRemainingCount <= 2) {
        elements.scanCountDisplay.classList.add('warning');
    }
}

/**
 * 运行策略信号扫描 - 使用 SSE 流式进度
 */
async function runStockScan() {
    if (state.selectedStrategies.length === 0) {
        alert('请先添加策略到策略组合区');
        return;
    }
    
    const pool = state.currentPool;
    const strategies = state.selectedStrategies.map(s => ({
        type: s.type,
        params: s.params
    }));
    
    // 获取进度条元素
    const scanProgress = document.getElementById('scanProgress');
    const scanProgressText = document.getElementById('scanProgressText');
    const scanProgressPercent = document.getElementById('scanProgressPercent');
    const scanProgressBar = document.getElementById('scanProgressBar');
    const scanProgressDetail = document.getElementById('scanProgressDetail');
    
    // 显示进度条，隐藏结果
    scanProgress.style.display = 'block';
    elements.scanResult.style.display = 'none';
    
    // 重置进度条
    scanProgressText.textContent = '准备中...';
    scanProgressPercent.textContent = '0%';
    scanProgressBar.style.width = '0%';
    scanProgressDetail.textContent = '';
    
    // 禁用扫描按钮
    elements.stockScanBtn.disabled = true;
    
    // 存储扫描结果
    let scanResults = [];
    
    try {
        // 使用 fetch 发送 POST 请求，然后处理 SSE 流
        const response = await fetch(`${API_BASE}/api/stock_scan_stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pool,
                strategies,
                fingerprint: BROWSER_FINGERPRINT
            })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            // 解码数据并添加到缓冲区
            buffer += decoder.decode(value, { stream: true });
            
            // 解析 SSE 消息
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // 保留不完整的行
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const jsonStr = line.substring(6);
                        const event = JSON.parse(jsonStr);
                        
                        switch (event.type) {
                            case 'start':
                                scanProgressText.textContent = event.message;
                                break;
                                
                            case 'fetch_progress':
                                scanProgressText.textContent = '获取股票数据...';
                                scanProgressPercent.textContent = `${event.percent}%`;
                                scanProgressBar.style.width = `${event.percent}%`;
                                scanProgressDetail.textContent = event.message;
                                break;
                                
                            case 'scan_start':
                                scanProgressText.textContent = event.message;
                                scanProgressPercent.textContent = '0%';
                                scanProgressBar.style.width = '0%';
                                scanProgressDetail.textContent = '';
                                break;
                                
                            case 'scan_progress':
                                scanProgressPercent.textContent = `${event.percent}%`;
                                scanProgressBar.style.width = `${event.percent}%`;
                                scanProgressDetail.textContent = event.message;
                                break;
                                
                            case 'signal_found':
                                // 实时添加发现的信号
                                scanResults.push(event.data);
                                // 更新结果预览
                                updateScanResultPreview(scanResults);
                                break;
                                
                            case 'complete':
                                // 扫描完成
                                scanProgress.style.display = 'none';
                                updateScanCountDisplay(event.data.remaining_count);
                                renderScanResult(event.data);
                                scanResults = []; // 重置
                                break;
                                
                            case 'error':
                                scanProgress.style.display = 'none';
                                if (event.limit_exceeded) {
                                    updateScanCountDisplay(0);
                                }
                                alert('扫描失败: ' + event.error);
                                break;
                        }
                    } catch (e) {
                        console.error('解析 SSE 消息失败:', e, line);
                    }
                }
            }
        }
    } catch (error) {
        console.error('扫描失败:', error);
        scanProgress.style.display = 'none';
        alert('扫描失败，请检查网络连接');
    } finally {
        elements.stockScanBtn.disabled = false;
    }
}

/**
 * 更新扫描结果预览（实时显示发现的信号）
 */
function updateScanResultPreview(results) {
    if (results.length === 0) return;
    
    // 显示结果区域
    elements.scanResult.style.display = 'block';
    
    // 更新摘要
    elements.scanSummary.innerHTML = `
        正在扫描中... 已发现 <strong>${results.length}</strong> 只有买入信号
    `;
    
    // 更新列表（只显示最新的结果）
    elements.scanList.innerHTML = results.map(item => `
        <div class="scan-item" onclick="selectStockFromScan('${item.code}')">
            <div class="scan-item-left">
                <span class="scan-item-code">${item.code}</span>
                <span class="scan-item-name">${item.name}</span>
                <span class="scan-item-price">¥${item.price.toFixed(2)}</span>
            </div>
            <div class="scan-item-signals">
                ${item.signals.map(s => `<span class="signal-tag">${s.signal}</span>`).join('')}
            </div>
        </div>
    `).join('');
}

/**
 * 渲染扫描结果
 */
function renderScanResult(data) {
    elements.scanResult.style.display = 'block';
    
    // 渲染摘要
    elements.scanSummary.innerHTML = `
        共扫描 <strong>${data.total_stocks}</strong> 只股票，
        发现 <strong>${data.signal_stocks}</strong> 只有买入信号
    `;
    
    // 渲染结果列表
    if (data.results.length === 0) {
        elements.scanList.innerHTML = '<div class="message-empty">当前没有发现买入信号</div>';
        return;
    }
    
    elements.scanList.innerHTML = data.results.map(item => `
        <div class="scan-item" onclick="selectStockFromScan('${item.code}')">
            <div class="scan-item-left">
                <span class="scan-item-code">${item.code}</span>
                <span class="scan-item-name">${item.name}</span>
                <span class="scan-item-price">¥${item.price.toFixed(2)}</span>
            </div>
            <div class="scan-item-signals">
                ${item.signals.map(s => `<span class="signal-tag">${s.signal}</span>`).join('')}
            </div>
        </div>
    `).join('');
}

/**
 * 从扫描结果选择股票
 */
function selectStockFromScan(code) {
    elements.stockSelect.value = code;
    // 滚动到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
