#!/bin/bash

# 检查是否在 pipenv shell 中
if [[ -z "$PIPENV_ACTIVE" ]]; then
    echo "Not in pipenv shell, activating..."
    # 使用 pipenv shell 启动一个新的 shell 并执行当前脚本
    exec pipenv shell "bash $0 $@"
    exit 0
fi

# 设置环境变量
export DJANGO_SETTINGS_MODULE="TestRunner.settings"

# 项目目录
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $PROJECT_DIR

# 日志目录
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p $LOG_DIR

# 进程 ID 文件目录
PID_DIR="$PROJECT_DIR/pids"
mkdir -p $PID_DIR

# 启动 Gunicorn
echo "Starting Gunicorn..."
gunicorn TestRunner.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --worker-class=gthread \
    --worker-connections=1000 \
    --access-logfile $LOG_DIR/gunicorn-access.log \
    --error-logfile $LOG_DIR/gunicorn-error.log \
    --pid $PID_DIR/gunicorn.pid \
    --daemon

# 启动 Celery Worker
echo "Starting Celery Worker..."
celery -A TestRunner worker \
    --loglevel=info \
    --logfile=$LOG_DIR/celery-worker.log \
    --pidfile=$PID_DIR/celery-worker.pid \
    --detach

# 启动 Celery Beat
echo "Starting Celery Beat..."
celery -A TestRunner beat \
    --loglevel=info \
    --logfile=$LOG_DIR/celery-beat.log \
    --pidfile=$PID_DIR/celery-beat.pid \
    --detach

echo "All services started successfully!"
echo "Check logs in $LOG_DIR for more information." 