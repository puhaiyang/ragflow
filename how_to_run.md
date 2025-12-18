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
  -p 9848:9848 \
  -e MODE=standalone \
  -e NACOS_AUTH_ENABLE=true \
  -e NACOS_AUTH_IDENTITY_KEY=nacos \
  -e NACOS_AUTH_IDENTITY_VALUE=nacos \
  -e NACOS_AUTH_TOKEN=$(openssl rand -base64 48) \
  nacos/nacos-server:v2.2.1
```

访问，并配置配置
http://10.28.20.106:8848/

需要写入的配置为：
> service_conf.yaml

即：

> xugurtp-ai-ragflow.yml

---
配置：
> NACOS_USERNAME=nacos;NACOS_NAMESPACE_ID=phy_ragflow;NACOS_PASSWORD=nacos;NACOS_SERVER_ADDR=10.28.20.106:8848;PYTHONUNBUFFERED=1


运行：
> api/ragflow_server.py

运行时如果无法下载https://huggingface.co/的模型，需要配置网络代理：
```
export https_proxy=http://10.28.12.6:7078;
export http_proxy=http://10.28.12.6:7078;
export all_proxy=socks5://10.28.12.6:7078;
```


https://github.com/nacos-group/nacos-sdk-python/tree/2.0.7

启动ragflow:
> docker-compose up -d

关闭ragflow:
> docker-compose stop

查看ragflow的镜像:
> docker-compose ps

安装依赖时，使用以下脚本：
>  uv run download_deps.py --china-mirrors

配置代理
> export HF_ENDPOINT=https://hf-mirror.com

```
export https_proxy=http://10.28.12.6:7078;
export http_proxy=http://10.28.12.6:7078;
export all_proxy=socks5://10.28.12.6:7078;
```



下载xugu的python-driver:https://download_cloud.xugudb.com/v12.9.10/XuguDB-12.0.0-linux-x86_64-20250731-1209010.zip

xugu数据库的IP为：10.28.25.75
端口为：12345
库为:YSL
用户名和密码均为SYSDBA

> cd xgcondb/
> sudo cp libxugusql.so /usr/local/lib/
> sudo ldconfig


# 前端项目

> wsl
> curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
> source ~/.bashrc
> nvm install 20
> nvm use 20
> node -v
> npm install --legacy-peer-deps
> export NODE_OPTIONS="--max-old-space-size=4096"
> npm run dev


# 用户登录流程
1. 用户请求/v1/user/login接口，返回了一个token(uuid)，如：f24585b6dbea11f0979d0242ac180006
2. 用户请求其他接口时，会在header中传入token(base64编码,jwt)`authorization
ImYyNDU4NWI2ZGJlYTExZjA5NzlkMDI0MmFjMTgwMDA2Ig.aUO6Mg.2OKvvs7L9JkDl3rhIoW4dt_UO_E`
3. 后台根据jwt进行校验，进行鉴权校验。底层调用`_load_user`