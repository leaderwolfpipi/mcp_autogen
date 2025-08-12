# 基础镜像
FROM origin-hub-ai-registry.cn-shanghai.cr.aliyuncs.com/component/ubuntu:22.04-amd64

# 设置环境变量，防止交互
ENV DEBIAN_FRONTEND=noninteractive

# 先安装 ca-certificates
RUN apt-get update && \
    apt-get install -y ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 设置阿里云APT源
RUN sed -i 's|http://.*archive.ubuntu.com|https://mirrors.aliyun.com|g' /etc/apt/sources.list && \
    sed -i 's|http://security.ubuntu.com|https://mirrors.aliyun.com|g' /etc/apt/sources.list

# 再 update 并安装 Python
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app

# 配置pip为阿里云源并安装依赖
RUN pip3 install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple && \
    pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple && \
    pip3 install -r requirements.txt

# 暴露API端口（如FastAPI默认端口）
EXPOSE 8000

# 默认启动命令 - 启动API服务
CMD ["python3", "-m", "uvicorn", "api.api:app", "--host", "0.0.0.0", "--port", "8000"] 