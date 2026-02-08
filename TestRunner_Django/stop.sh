#!/bin/bash

# 检查是否在 pipenv shell 中
if [[ -z "$PIPENV_ACTIVE" ]]; then
    echo "Not in pipenv shell, activating..."
    # 使用 pipenv shell 启动一个新的 shell 并执行当前脚本
    exec pipenv shell "bash $0 $@"
    exit 0
fi

# 项目目录
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $PROJECT_DIR
PID_DIR="$PROJECT_DIR/pids"

# 停止 Gunicorn
if [ -f "$PID_DIR/gunicorn.pid" ]; then
    echo "Stopping Gunicorn..."
    kill -TERM $(cat "$PID_DIR/gunicorn.pid")
    rm -f "$PID_DIR/gunicorn.pid"
fi

# 停止 Celery Worker
if [ -f "$PID_DIR/celery-worker.pid" ]; then
    echo "Stopping Celery Worker..."
    kill -TERM $(cat "$PID_DIR/celery-worker.pid")
    rm -f "$PID_DIR/celery-worker.pid"
fi

# 停止 Celery Beat
if [ -f "$PID_DIR/celery-beat.pid" ]; then
    echo "Stopping Celery Beat..."
    kill -TERM $(cat "$PID_DIR/celery-beat.pid")
    rm -f "$PID_DIR/celery-beat.pid"
fi

# 确保所有 Celery 进程都已停止
echo "Making sure all Celery processes are stopped..."
pkill -f "celery worker"
pkill -f "celery beat"

echo "All services stopped successfully!" 