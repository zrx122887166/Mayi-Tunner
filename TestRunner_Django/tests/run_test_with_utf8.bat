@echo off
REM 设置UTF-8编码环境变量
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8

REM 设置控制台代码页为UTF-8
chcp 65001

REM 运行Python脚本
echo 以UTF-8编码运行测试脚本...
python test_sql_hook_minimal.py

REM 暂停以查看结果
pause 