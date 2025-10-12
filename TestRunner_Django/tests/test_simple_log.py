"""
简单的中文日志测试
"""
import os
import sys
import time
from loguru import logger

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

# 确保logs目录存在
os.makedirs("logs", exist_ok=True)

# 移除默认的日志处理器
logger.remove()

# 添加文件日志处理器
logger.add(
    "logs/simple_test.log",
    rotation="1 MB", 
    retention="1 week",
    encoding="utf-8",  # 明确指定编码
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} - {message}"
)

# 添加控制台处理器
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
    colorize=True
)

# 记录中文日志
logger.info("=== 开始测试中文日志 ===")
logger.debug("这是一条调试信息")
logger.info("这是一条普通信息")
logger.success("这是一条成功信息")
logger.warning("这是一条警告信息")
logger.error("这是一条错误信息")
logger.info("测试数据1，测试数据2")
logger.info("SQL钩子，通过钩子添加，获取测试数据库连接")

# 记录带变量的日志
name = "张三"
age = 25
logger.info(f"用户名: {name}, 年龄: {age}")
logger.info("用户 {} 的年龄是 {}", name, age)

# 记录带结构化数据的日志
data = {
    "name": "李四",
    "age": 30,
    "skills": ["Python", "Django", "SQL"]
}
logger.info(f"用户数据: {data}")

logger.info("=== 测试结束 ===")

# 查看日志文件
print(f"\n日志文件已生成: logs/simple_test.log")
print("尝试读取日志文件内容...")

try:
    with open("logs/simple_test.log", "r", encoding="utf-8") as f:
        content = f.read()
        print("\n日志文件内容预览:\n")
        print(content[:500] + "..." if len(content) > 500 else content)
except Exception as e:
    print(f"读取日志文件失败: {str(e)}")

print("\n欢迎下次使用~") 