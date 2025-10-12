#!/usr/bin/env python
import os
import sys
import platform
import subprocess

def main():
    """
    启动Celery Worker的主函数
    """
    print("正在启动Celery Worker...")
    
    # 构建Celery命令
    celery_cmd = [
        "uv", "run",
        "celery",
        "-A",
        "TestRunner",
        "worker",
        "--loglevel=info",
    ]
    
    # 根据操作系统类型添加不同的参数
    system = platform.system()
    if system == "Windows":
        # Windows环境使用solo池
        celery_cmd.append("--pool=solo")
        print("检测到Windows环境，使用solo池")
    else:
        # Linux/Unix环境使用prefork池（默认）
        # 可以根据CPU核心数设置并发数
        import multiprocessing
        concurrency = multiprocessing.cpu_count()
        celery_cmd.extend([
            "--concurrency", str(concurrency),
            "--pool=prefork"
        ])
        print(f"检测到{system}环境，使用prefork池，并发数：{concurrency}")
    
    # 执行命令
    try:
        print(f"执行命令: {' '.join(celery_cmd)}")
        subprocess.run(celery_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"启动Celery Worker失败: {e}")
        return 1
    except KeyboardInterrupt:
        print("Celery Worker已停止")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 