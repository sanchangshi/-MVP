# Render 部署指南

本项目已配置好 Render 部署所需的文件，按照以下步骤即可完成部署。

## 📋 部署前准备

1. 确保项目代码已推送到 GitHub
2. 注册 [Render 账号](https://dashboard.render.com/register)（可用 GitHub 登录）

---

## 🚀 部署步骤

### 第一步：推送代码到 GitHub

```bash
# 初始化 Git（如果还没有）
git init

# 添加所有文件
git add .

# 提交
git commit -m "准备部署到 Render"

# 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/你的仓库名.git

# 推送
git push -u origin main
```

### 第二步：在 Render 创建后端服务

1. 登录 [Render Dashboard](https://dashboard.render.com/)
2. 点击 **New +** → **Web Service**
3. 连接你的 GitHub 仓库
4. 填写配置：
   - **Name**: `stock-backtest-api`（或自定义）
   - **Region**: `Singapore`（国内访问较稳定）
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
   - **Plan**: `Free`

5. 添加环境变量：
   - 点击 **Advanced** → **Add Environment Variable**
   - Key: `TUSHARE_TOKEN`
   - Value: `你的 Tushare Token`

6. 点击 **Deploy Web Service**

### 第三步：在 Render 创建前端服务

1. 点击 **New +** → **Static Site**
2. 连接同一个 GitHub 仓库
3. 填写配置：
   - **Name**: `stock-backtest-frontend`（或自定义）
   - **Region**: `Singapore`
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**: 留空（或填 `echo "No build needed"`）
   - **Publish Directory**: `.`

4. 点击 **Deploy Static Site**

### 第四步：更新前端 API 地址

部署完成后，需要更新 `frontend/js/app.js` 中的 API 地址：

```javascript
// 将这里的地址改为你的后端实际地址
return 'https://stock-backtest-api.onrender.com';
```

然后重新推送代码，前端会自动重新部署。

---

## ✅ 验证部署

1. 访问后端健康检查：`https://你的后端地址.onrender.com/`
   - 应返回：`{"status": "ok", "message": "股票回测系统API运行中"}`

2. 访问前端地址：`https://你的前端地址.onrender.com/`
   - 应正常显示页面

---

## ⚠️ 注意事项

### 免费版限制

| 限制项 | 说明 |
|--------|------|
| 休眠 | 15分钟无请求会休眠，首次访问需等待几秒 |
| 带宽 | 每月 100GB |
| 构建时间 | 每月 500 分钟 |
| 服务数量 | 最多 1 个 Web Service + 1 个 Static Site |

### IP 限制问题

部署后所有用户共享服务器 IP，原有的 IP 限制逻辑可能需要调整：
- 调优次数限制：所有用户共享配额
- 扫描次数限制：所有用户共享配额

建议改用浏览器指纹或用户账号系统来限制。

---

## 🔧 常见问题

### 1. 后端启动失败

检查日志，常见原因：
- 依赖安装失败：检查 `requirements.txt`
- 环境变量未设置：确保 `TUSHARE_TOKEN` 已配置

### 2. 前端无法连接后端

- 检查后端是否正常运行
- 检查 CORS 配置（已在 `app.py` 中配置）
- 检查前端 API 地址是否正确

### 3. 数据获取失败

- 检查 Tushare Token 是否有效
- 检查 Tushare API 配额是否用完

---

## 📞 技术支持

如有问题，请查看 Render 日志或提交 GitHub Issue。