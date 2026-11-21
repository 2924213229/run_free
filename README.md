# 运动世界校园跑纯协议客户端（7.4.01）

##  快速开始
### 环境需要
1. python 3.8版本及以上
2. nodejs 20版本及以上
3. Playwright Chromium（过人机验证滑块用的）
### 克隆仓库
git clone https://github.com/2924213229/run_free.git

### 安装依赖
```bash
cd run_free
npm install playwright --registry=https://registry.npmmirror.com
npx playwright install chromium
```

### 登录
```bash
python3 go.py login --user <phonenumber> --password <pwd>
```
登陆后会保存一个.session.json文件，这样只需要最初登陆一次，后面无需登陆
### 跑步
```bash
python3 go.py run [--distance <要跑的距离>] [--time <要跑的时间>]

```
distance和time可选，默认距离2km，时间720s

### 查看状态
python3 go.py status
### 登出
python3 go.py logout
