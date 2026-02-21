# 股票回测系统 MVP

一个基于拖拽式策略组合的股票回测可视化系统。

## 功能特点

- 📊 **数据获取**: 使用 akshare 获取A股历史数据
- 🧩 **模块化策略**: 支持拖拽组合多个策略
- 📈 **可视化回测**: K线图 + 买卖点标注 + 指标展示
- 🎯 **回测统计**: 收益率、胜率、交易次数等

## 支持的策略

1. **均线策略 (MA)**
   - 金叉买入：短期均线上穿长期均线
   - 死叉卖出：短期均线下穿长期均线
   - 可配置参数：短期周期、长期周期

2. **MACD策略**
   - 金叉买入：DIF上穿DEA
   - 死叉卖出：DIF下穿DEA
   - 可配置参数：快线周期、慢线周期、信号线周期

## 项目结构

```
project5/
├── backend/
│   ├── app.py              # Flask API服务
│   ├── data_fetcher.py     # 数据获取模块
│   ├── backtest.py         # 回测引擎
│   ├── strategies/         # 策略模块
│   │   ├── ma_strategy.py
│   │   └── macd_strategy.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
└── README.md
```

## 快速开始

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
cd backend
python app.py
```

服务将在 http://localhost:5000 启动

### 3. 打开前端页面

直接在浏览器中打开 `frontend/index.html` 文件

或者使用简单的HTTP服务器：

```bash
cd frontend
python -m http.server 8080
```

然后访问 http://localhost:8080

## 使用说明

1. **选择股票**: 从下拉列表中选择要回测的股票
2. **获取数据**: 点击"获取数据"按钮加载股票历史数据
3. **添加策略**: 从左侧拖拽策略模块到组合区
4. **调整参数**: 在组合区中修改策略参数
5. **运行回测**: 点击"运行回测"按钮执行回测
6. **查看结果**: 查看K线图、买卖点和回测统计

## API 接口

- `GET /api/stocks` - 获取股票列表
- `GET /api/stock/data?symbol=xxx` - 获取股票历史数据
- `GET /api/strategies` - 获取可用策略列表
- `POST /api/backtest` - 执行回测

## 技术栈

- **后端**: Python, Flask, akshare, pandas
- **前端**: HTML5, CSS3, JavaScript, ECharts
- **拖拽**: HTML5 Drag & Drop API

## 注意事项

- 首次运行需要安装 akshare 及其依赖
- 股票数据来自 akshare，需要网络连接
- 回测结果仅供参考，不构成投资建议