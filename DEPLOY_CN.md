# 国内部署指南

## 部署方案

| 组件 | 平台 | 费用 | 需要信用卡 |
|------|------|------|-----------|
| 前端 | GitHub Pages | 永久免费 | ❌ 不需要 |
| 后端 | 阿里云函数计算 | 免费额度 | ❌ 不需要 |

---

## 一、部署后端（阿里云函数计算）

### 1. 安装 Serverless Devs 工具

```bash
# 安装 Node.js 后执行
npm install -g @serverless-devs/s

# 验证安装
s -v
```

### 2. 配置阿里云密钥

```bash
# 配置阿里云 AccessKey
s config add

# 按提示输入：
# - AccountID: 阿里云账号 ID
# - AccessKeyID: AccessKey ID
# - AccessKeySecret: AccessKey Secret
```

**获取 AccessKey**：
1. 登录 [阿里云控制台](https://ram.console.aliyun.com/manage/ak)
2. 创建 AccessKey（建议使用子账号）
3. 确保账号有函数计算相关权限

### 3. 部署函数

```bash
# 进入后端目录
cd backend

# 设置 Tushare Token 环境变量
export TUSHARE_TOKEN=你的token

# 部署
s deploy
```

### 4. 获取 API 地址

部署成功后，会输出类似：
```
url: https://xxxxx.cn-hangzhou.fc.aliyuncs.com/2016-08-15/proxy/stock-backtest-service/api/
```

这就是您的后端 API 地址。

---

## 二、部署前端（GitHub Pages）

### 1. 修改 API 地址

编辑 `frontend/js/app.js`，将生产环境 API 改为您的阿里云函数地址：

```javascript
const API_BASE = (() => {
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        return 'https://你的函数地址.cn-hangzhou.fc.aliyuncs.com/2016-08-15/proxy/stock-backtest-service/api';
    }
    return 'http://localhost:5000';
})();
```

### 2. 推送代码

```bash
git add .
git commit -m "更新 API 地址"
git push
```

### 3. 启用 GitHub Pages

1. 打开 GitHub 仓库
2. 点击 **Settings** → **Pages**
3. Source 选择 **Deploy from a branch**
4. Branch 选择 **main**，目录选择 **/frontend**
5. 点击 **Save**

### 4. 访问网站

几分钟后，您的网站将可通过以下地址访问：
```
https://你的用户名.github.io/仓库名/
```

---

## 三、阿里云函数计算免费额度

| 项目 | 免费额度 |
|------|---------|
| 调用次数 | 100 万次/月 |
| 执行时间 | 40 万 GB-秒/月 |
| 公网流出流量 | 1 GB/月 |

**对于小型应用完全够用！**

---

## 四、常见问题

### Q: 函数部署失败？

检查：
1. AccessKey 是否正确
2. 账号是否有函数计算权限
3. 区域是否支持（推荐：cn-hangzhou、cn-shanghai）

### Q: API 请求超时？

函数计算默认超时 60 秒，可在 `s.yaml` 中调整：
```yaml
timeout: 120  # 最大 600 秒
```

### Q: 跨域问题？

后端已配置 CORS，应该不会有跨域问题。如有问题，检查：
1. 前端 API 地址是否正确
2. 浏览器控制台错误信息

### Q: 如何查看日志？

```bash
# 查看函数日志
s logs
```

---

## 五、本地测试

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export TUSHARE_TOKEN=你的token

# 运行
python index.py
```

访问 http://localhost:9000 测试 API。