# 运动世界校园跑纯协议客户端（7.4.01）

##  快速开始

### 安装依赖
```bash
cd ~/run_free
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
python3 go.py run [--distance <要跑的距离>] [--time [要跑的时间]]
```
### 查看状态
python3 go.py status
### 登出
python3 go.py logout
