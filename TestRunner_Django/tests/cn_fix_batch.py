import os
import sys
import locale
import shutil

print("=== 中文编码修复工具 ===")

# 获取当前系统编码
current_encoding = locale.getpreferredencoding()
print(f"当前系统编码: {current_encoding}")

# 设置环境变量
os.environ["PYTHONIOENCODING"] = "utf-8"
print("已设置PYTHONIOENCODING=utf-8")

# 设置Windows控制台编码
if sys.platform.startswith('win'):
    os.system('chcp 65001')
    print("已设置控制台代码页为UTF-8 (65001)")
    
    # 设置标准输出和标准错误的编码
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    print("已更新标准输出和标准错误流的编码为UTF-8")

# 确保logs目录存在
os.makedirs("logs", exist_ok=True)
print("已确保logs目录存在")

# 添加.bat文件，设置代码页并运行Python脚本
bat_content = """@echo off
chcp 65001
echo 已设置控制台为UTF-8编码

python test_sql_hook_minimal.py
pause
"""

# 创建批处理文件
with open("run_test_utf8.bat", "w", encoding="utf-8") as f:
    f.write(bat_content)
print("已创建批处理文件: run_test_utf8.bat")

# 检查是否已经修复了utils/db_utils.py和httprunner/step_request.py
utils_file = "utils/db_utils.py"
step_request_file = "httprunner/step_request.py"

print(f"\n检查文件 {utils_file}...")
if os.path.exists(utils_file):
    print(f"文件存在: {utils_file}")
else:
    print(f"文件不存在: {utils_file}")

print(f"\n检查文件 {step_request_file}...")
if os.path.exists(step_request_file):
    print(f"文件存在: {step_request_file}")
else:
    print(f"文件不存在: {step_request_file}")

print("\n=== 测试中文输出 ===")
print("测试数据1，测试数据2")
print("SQL钩子，通过钩子添加，获取测试数据库连接")
print("这是一段中文文本，用于测试编码问题")
print("=== 测试结束 ===\n")

print("完成！现在可以运行 run_test_utf8.bat 来测试SQL钩子功能。")
print("欢迎下次使用~") 