# 使用Python 3.9镜像
FROM python:3.9-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖（MySQL客户端）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        default-libmysqlclient-dev \
        pkg-config \
        && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
# 先尝试官方源，如果失败会自动重试
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p /app/uploads /app/logs /app/instance

# 暴露端口（微信云托管会自动分配端口）
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; import os; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\", \"5000\")}/api/health')" || exit 1

# 启动命令
# 注意：微信云托管会自动设置PORT环境变量
CMD ["sh", "-c", "gunicorn main:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - --log-level info"]
