#!/usr/bin/env python3
import os
import sys
import django
from django.conf import settings

# 直接在Python中设置SECRET_KEY，绕过环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TestRunner.settings')
os.environ['SECRET_KEY'] = 'django-insecure-final-attempt-secret-key-for-testrunner-application-1234567890abcdefg'

# 手动设置Django配置，确保SECRET_KEY可用
if not settings.configured:
    settings.configure(
        SECRET_KEY='django-insecure-final-attempt-secret-key-for-testrunner-application-1234567890abcdefg',
        DEBUG=True,
        USE_TZ=True,
        INSTALLED_APPS=[
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'rest_framework',
            'rest_framework.authtoken',
            'corsheaders',
            'import_export',
            'simpleui',
            # 添加其他必需的应用
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': '/app/data/testrunner.db',
            }
        },
        MIDDLEWARE=[
            'corsheaders.middleware.CorsMiddleware',
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ],
        ROOT_URLCONF='TestRunner.urls',
        ALLOWED_HOSTS=['*'],
    )

# 现在可以安全地导入Django组件
django.setup()

# 执行Django管理命令
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    # 执行迁移
    sys.argv = ['manage.py', 'migrate', '--noinput']
    execute_from_command_line(sys.argv)
    
    # 收集静态文件
    sys.argv = ['manage.py', 'collectstatic', '--noinput']
    execute_from_command_line(sys.argv)
    
    # 启动服务器
    sys.argv = ['manage.py', 'runserver', '0.0.0.0:8000']
    execute_from_command_line(sys.argv)
