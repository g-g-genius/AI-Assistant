# 使用ubuntu最新版本作为基础镜像
FROM ubuntu:latest

# 更改ubuntu源为阿里云源
RUN sed -i 'sarchive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list
&& apt-get update && apt-get install -y coturn python3 python3-pip redis-server
&& rm -rf /var/lib/apt/lists/*

# 升级pip并安装FastAPI
RUN pip3 install --upgrade pip && pip3 install fastapi uvicorn
langchain_core langchain_openai langchain-community openai
google-search-results redis

# 设置Coturn的配置文件
COPY turnserver.conf /etc/turnserver.conf

# 设置Redis的配置文件
COPY redis.conf /etc/redis/redis.conf

# 设置redis的数据目录
VOLUME /data

WORKDIR /app

# 复制代码到容器中
COPY . /app

# 设置开放端口
EXPOSE 8000 3478 6379

# 启动服务
CMD ["sh", "-c", "turnserver -c /etc/turnserver.conf --listening-ip=0.0.0.0 --listening-port=3478
& redis-server /etc/redis/redis.conf --protected-mode no & sleep 3 &&
uvicorn server:app --host 0.0.0.0 --port 8000"]