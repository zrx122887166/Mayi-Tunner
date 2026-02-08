# 基于python3.9创建镜像
FROM python:3.9

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    libpq-dev \
    pkg-config \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt /app/

# 【新增】添加国内 PyPI 源（加速安装，避免版本找不到）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装Python依赖（保留原命令，加 --upgrade pip 确保 pip 版本最新）
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . /app/

# 创建日志目录
RUN mkdir -p /app/logs

# 暴露端口
EXPOSE 8088

# 设置启动脚本权限
RUN chmod +x /app/docker-entrypoint.sh || true

# 启动命令
CMD ["gunicorn", "TestRunner.wsgi:application", "--bind", "0.0.0.0:8088", "--workers", "4", "--timeout", "120"]
