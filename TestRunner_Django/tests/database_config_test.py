"""
临时的数据库配置测试模块
用于提供数据库连接字符串给SQL钩子测试
"""
from loguru import logger

def get_database_connection_by_key(db_key):
    """
    模拟根据键获取数据库连接字符串
    
    Args:
        db_key: 数据库配置键名
        
    Returns:
        数据库连接字符串或None
    """
    # 测试用的SQLite内存数据库
    if db_key == "testdemo":
        return "sqlite:///:memory:"
    
    # 测试用的MySQL数据库，如果有实际的MySQL环境可以启用
    # if db_key == "testdemo":
    #     return "mysql+pymysql://root:password@localhost:3306/testdb?charset=utf8mb4"
    
    logger.warning(f"未找到数据库配置: {db_key}")
    return None

def get_environment_database_connection():
    """
    模拟获取环境变量中的数据库连接
    
    Returns:
        数据库连接字符串或None
    """
    # 使用SQLite内存数据库做测试
    return "sqlite:///:memory:" 