#!/bin/bash

# 设置环境变量
export DJANGO_SETTINGS_MODULE=TestRunner.settings

# 启动Celery Worker
echo "正在启动Celery Worker..."
celery -A TestRunner worker --loglevel=info --concurrency=$(nproc)

# 脚本使用说明
# 1. 确保脚本有执行权限: chmod +x start_celery.sh
# 2. 执行脚本: ./start_celery.sh
# 3. 如需后台运行: nohup ./start_celery.sh > celery.log 2>&1 & 