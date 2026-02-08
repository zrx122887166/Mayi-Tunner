import os
import sys

# 设置环境变量编码
os.environ["PYTHONIOENCODING"] = "utf-8"

# 在Windows下设置控制台编码
if sys.platform.startswith('win'):
    try:
        # 设置控制台代码页为UTF-8
        os.system('chcp 65001')
        print("已设置控制台为UTF-8编码")
    except:
        print("无法设置控制台编码")
    
    # 对控制台输出进行编码处理
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        print("已设置控制台输出编码为UTF-8")
    except:
        print("无法设置输出编码")

print("\n=== 中文输出测试 ===")
print("测试数据1，测试数据2")
print("SQL钩子，通过钩子添加，获取测试数据库连接")
print("这是一段中文文本，用于测试编码问题")
print("=== 测试结束 ===\n")

print("输出到文件测试...")
# 确保logs目录存在
os.makedirs("logs", exist_ok=True)

# 测试文件输出
with open("logs/cn_test.txt", "w", encoding="utf-8") as f:
    f.write("=== 文件中文输出测试 ===\n")
    f.write("测试数据1，测试数据2\n")
    f.write("SQL钩子，通过钩子添加，获取测试数据库连接\n")
    f.write("这是一段中文文本，用于测试编码问题\n")
    f.write("=== 测试结束 ===\n")

print(f"已写入测试文件: logs/cn_test.txt")
print("欢迎下次使用~") 