# 股票回测系统 MVP

一个基于拖拽式策略组合的股票回测可视化系统。

## 功能特点

- 📊 **数据获取**: 使用 akshare 获取A股历史数据
- 🧩 **模块化策略**: 支持拖拽组合多个策略
- 📈 **可视化回测**: K线图 + 买卖点标注 + 指标展示
- 🎯 **回测统计**: 收益率、胜率、交易次数等

## 支持的策略

1. **均线策略 (MA)** - 金叉买入/死叉卖出
2. **MACD策略** - DIF上穿DEA买入
3. **RSI策略** - 超卖回升买入
4. **布林带策略** - 下轨反弹买入
5. **KDJ策略** - K线金叉买入
6. **海龟策略** - 突破N日高点买入
7. **ATR止损策略** - ATR突破买入
8. **OBV能量潮策略** - OBV金叉买入

## 项目结构

```
project5/
├── backend/
│   ├── app.py              # Flask API服务
│   ├── data_fetcher.py     # 数据获取模块
│   ├── backtest.py         # 回测引擎
│   ├── strategies/         # 策略模块
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── zeabur.yaml             # Zeabur 部署配置
└── README.md
```

## 快速开始

### 本地开发

```bash
# 安装后端依赖
cd backend
pip install -r requirements.txt

# 启动后端服务
python app.py

# 打开前端页面
# 直接在浏览器中打开 frontend/index.html
```

## 部署指南

### 方案：Zeabur (后端) + Netlify (前端)

#### 1. 部署后端到 Zeabur

1. 登录 [Zeabur](https://zeabur.com)
2. 创建新项目，连接 GitHub 仓库
3. 添加服务，选择 `backend` 目录
4. Zeabur 会自动识别 Python 项目
5. 设置环境变量（如需要）
6. 部署完成后获取 API 地址

#### 2. 部署前端到 Netlify（免费）

1. 登录 [Netlify](https://netlify.com)
2. 点击 "Add new site" → "Import an existing project"
3. 连接 GitHub 仓库
4. 配置项目：
   - **Base directory**: `frontend`
   - **Publish directory**: `.` (留空即可)
5. 点击 Deploy
6. 部署完成后获取前端地址

#### 3. 更新前端 API 地址

编辑 `frontend/js/app.js`，更新 `API_BASE`：

```javascript
const API_BASE = (() => {
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        return 'https://your-backend.zeabur.app';  // 替换为你的 Zeabur 后端地址
    }
    return 'http://localhost:5000';
})();
```

### 环境变量

后端支持的环境变量：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| PORT | 服务端口 | 5000 |
| FLASK_ENV | 运行环境 | production |

## API 接口

- `GET /` - 健康检查
- `GET /api/stock_pools` - 获取股票池列表
- `GET /api/stocks?pool=xxx` - 获取股票列表
- `GET /api/stock/data?symbol=xxx` - 获取股票历史数据
- `GET /api/strategies` - 获取可用策略列表
- `POST /api/backtest` - 执行回测
- `POST /api/optimize` - 自动调优参数
- `POST /api/stock_scan_stream` - 实时选股(SSE)

## 技术栈

- **后端**: Python, Flask, akshare, pandas
- **前端**: HTML5, CSS3, JavaScript, ECharts
- **部署**: Zeabur + Netlify

## 注意事项

- 股票数据来自 akshare，需要网络连接
- 回测结果仅供参考，不构成投资建议