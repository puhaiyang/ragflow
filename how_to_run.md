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