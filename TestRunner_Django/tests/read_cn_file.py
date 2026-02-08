import os
import sys

print("\n=== 测试读取中文文件 ===")
try:
    # 读取文件内容
    with open("logs/cn_test.txt", "r", encoding="utf-8") as f:
        content = f.read()
        print("文件内容:")
        print(content)
except Exception as e:
    print(f"读取文件失败: {str(e)}")

print("=== 测试结束 ===\n")

# 创建一个新的测试文件
print("创建新的测试文件...")
try:
    with open("logs/cn_test2.txt", "w", encoding="utf-8") as f:
        f.write("=== 中文测试文件2 ===\n")
        f.write("这是第二个中文测试文件\n")
        f.write("用于验证编码问题\n")
        f.write("欢迎下次使用~\n")
    print("文件创建成功: logs/cn_test2.txt")
except Exception as e:
    print(f"创建文件失败: {str(e)}")

print("欢迎下次使用~") 