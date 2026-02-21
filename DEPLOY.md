# 华为云 + GitHub Pages 部署指南

本项目使用华为云 FunctionGraph 部署后端，GitHub Pages 部署前端。

## 📋 部署架构

```
用户 → GitHub Pages (前端) → 华为云 FunctionGraph (后端API)
```

---

## 🚀 第一部分：部署后端到华为云

### 步骤 1：构建部署包

```bash
cd backend
python build_huawei.py
```

这会生成 `deployment_package.zip` 文件。

### 步骤 2：创建函数

1. 登录 [华为云控制台](https://console.huaweicloud.com/)
2. 搜索 **FunctionGraph** → 进入函数工作流
3. 点击 **创建函数**
4. 选择 **HTTP函数**
5. 填写基本信息：
   - **函数名称**: `stock-backtest-api`
   - **运行时**: Python 3.9
   - **内存**: 512MB
   - **超时时间**: 60秒
6. 点击 **创建函数**

### 步骤 3：上传代码

1. 进入函数详情页
2. 点击 **代码** 标签
3. 选择 **上传代码包**
4. 上传 `deployment_package.zip`
5. 设置 **执行入口**: `huawei_handler.handler`
6. 点击 **部署**

### 步骤 4：配置环境变量

1. 点击 **配置** 标签
2. 找到 **环境变量**
3. 添加：
   - `TUSHARE_TOKEN`: 你的 Tushare Token
4. 点击 **保存**

### 步骤 5：配置 API 网关触发器

1. 点击 **触发器** 标签
2. 点击 **创建触发器**
3. 选择 **API网关**
4. 配置：
   - **API名称**: `stock-backtest-api`
   - **分组**: 创建新分组或选择已有
   - **请求方式**: ANY
   - **安全认证**: 无认证（或自定义认证）
5. 点击 **确定**
6. 复制生成的 **API地址**（类似 `https://xxx.apig.xxx.myhuaweicloud.com/`）

### 步骤 6：配置 CORS

在 API 网关控制台配置 CORS，允许 GitHub Pages 域名访问：

1. 进入 API 网关控制台
2. 找到你的 API 分组
3. 配置跨域访问：
   - **允许的来源**: `https://sanchangshi.github.io`
   - **允许的方法**: GET, POST, OPTIONS
   - **允许的头部**: Content-Type, Authorization

---

## 🌐 第二部分：部署前端到 GitHub Pages

### 步骤 1：更新 API 地址

编辑 `frontend/js/app.js`，更新 API 地址：

```javascript
const API_BASE = (() => {
    // 生产环境：使用华为云 API 网关地址
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        return 'https://你的API网关地址.apig.xxx.myhuaweicloud.com';
    }
    // 本地开发环境
    return 'http://localhost:5000';
})();
```

### 步骤 2：推送代码

```bash
git add .
git commit -m "配置华为云 API 地址"
git push
```

### 步骤 3：启用 GitHub Pages

1. 进入 GitHub 仓库
2. 点击 **Settings** → **Pages**
3. **Source** 选择 `Deploy from a branch`
4. **Branch** 选择 `main`
5. **目录** 选择 `/frontend`
6. 点击 **Save**

### 步骤 4：访问网站

等待几分钟后，访问：
```
https://sanchangshi.github.io/-MVP/
```

---

## ✅ 验证部署

### 测试后端

```bash
curl https://你的API网关地址/
```

应返回：
```json
{"status": "ok", "message": "股票回测系统API运行中"}
```

### 测试前端

访问 GitHub Pages 地址，检查页面是否正常显示。

---

## ⚠️ 常见问题

### 1. 函数部署失败

- 检查代码包大小（不超过 50MB）
- 检查 `requirements.txt` 依赖是否正确
- 查看函数日志排查错误

### 2. API 调用超时

- 增加函数超时时间
- 检查 Tushare API 响应时间

### 3. CORS 错误

- 确认 API 网关已配置 CORS
- 检查允许的来源域名是否正确

### 4. 前端无法连接后端

- 检查 API 地址是否正确
- 检查 API 网关是否正常工作
- 检查浏览器控制台错误信息

---

## 📞 技术支持

如有问题，请查看：
- [华为云 FunctionGraph 文档](https://support.huaweicloud.com/functiongraph/index.html)
- [GitHub Pages 文档](https://docs.github.com/zh/pages)