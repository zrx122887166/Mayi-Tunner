#!/bin/bash
set -e

echo "等待数据库启动..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done
echo "数据库已就绪！"

echo "执行数据库迁移..."
python manage.py migrate --noinput

echo "收集静态文件..."
python manage.py collectstatic --noinput --clear || true

echo "创建超级用户（如果不存在）..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123456')
    print('超级用户已创建: admin/admin123456')
else:
    print('超级用户已存在')
EOF

echo "启动应用..."
exec "$@"