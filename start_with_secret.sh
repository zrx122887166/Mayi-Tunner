#!/bin/bash

# 设置环境变量，这将被settings.py中的os.getenv读取
export SECRET_KEY="django-insecure-definitely-working-secret-key-for-testrunner-app-1234567890abcdefg"

# 现在运行Django命令
echo "Starting Django application with SECRET_KEY set..."
python /app/manage.py migrate --noinput
python /app/manage.py collectstatic --noinput
python /app/manage.py runserver 0.0.0.0:8000
