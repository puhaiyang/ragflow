# 0. 环境
以管理员打开powershell
> wsl --install
> wsl.exe --install ubuntu

进入系统，并安装uv
> wsl
> curl -LsSf https://astral.sh/uv/install.sh | sh
> source ~/.bashrc  # 或 source ~/.zshrc

安装依赖
> uv sync --python 3.10

> sudo apt update
> sudo apt install libicu-dev
> sudo apt install pkg-config
> sudo apt install build-essential

---
> cd ~
> cp -r /mnt/f/xugu/ragflow ~/ragflow
> cd ~/ragflow
> rm -rf .venv
> uv sync --python 3.10


# 1. 运行
```
docker run -d \
  --name nacos \
  -p 8848:8848 \
  -e MODE=standalone \
  -e NACOS_AUTH_ENABLE=true \
  -e NACOS_AUTH_IDENTITY_KEY=nacos \
  -e NACOS_AUTH_IDENTITY_VALUE=nacos \
  -e NACOS_AUTH_TOKEN=$(openssl rand -base64 48) \
  nacos/nacos-server:v2.2.1
```

访问，并配置配置
http://10.28.20.106:8848/

配置：
> NACOS_USERNAME=nacos;NACOS_NAMESAPCE_ID=phy_ragflow;NACOS_PASSWORD=nacos;NACOS_SERVER_ADDR=10.28.20.106:8848;PYTHONUNBUFFERED=1