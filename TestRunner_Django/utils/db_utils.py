"""
数据库工具函数
提供数据库连接和SQL执行功能
"""
import os
import time
import socket
import sys
import traceback
from typing import Dict, List, Union, Any, Optional
from loguru import logger

# 设置环境变量，强制Python使用UTF-8编码
os.environ["PYTHONIOENCODING"] = "utf-8"

# 在Windows下处理控制台输出编码
if sys.platform.startswith('win'):
    # 尝试设置控制台代码页为UTF-8
    try:
        os.system('chcp 65001 > nul')
    except:
        pass
    
    # 为控制台输出重新包装
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass

# 配置日志格式和输出
logger.remove()  # 移除默认处理器

# 确保logs目录存在
os.makedirs("logs", exist_ok=True)

# 全局变量存储处理器ID，便于管理
log_handlers = {
    'file': None,
    'stdout': None,
    'error_file': None
}

# 安全地添加日志处理器
def add_log_handler(handler_type, **kwargs):
    """安全地添加日志处理器，并记录处理器ID"""
    global log_handlers
    
    # 如果该类型的处理器已存在，先移除它
    if log_handlers[handler_type] is not None:
        try:
            # 检查处理器ID是否存在于logger的处理器列表中
            if log_handlers[handler_type] in [handler_id for handler_id in logger._core.handlers]:
                logger.remove(log_handlers[handler_type])
            log_handlers[handler_type] = None
        except Exception as e:
            print(f"移除旧的日志处理器时出错: {str(e)}")
    
    # 添加新的处理器
    try:
        handler_id = logger.add(**kwargs)
        log_handlers[handler_type] = handler_id
        return handler_id
    except Exception as e:
        print(f"添加日志处理器时出错: {str(e)}")
        return None

# 1. 添加文件日志处理器
add_log_handler(
    'file',
    sink="logs/sql_hooks.log",
    rotation="10 MB",  # 日志文件达到10MB时轮转
    retention="1 week",  # 保留一周的日志
    compression="zip",  # 压缩轮转后的日志
    enqueue=True,  # 使用队列，避免多进程写入冲突
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> | {extra}",
    backtrace=True,  # 增强错误跟踪
    diagnose=True,  # 记录诊断信息
    catch=True  # 捕获由处理程序引发的异常
)

# 2. 添加标准输出处理器（控制台日志）
add_log_handler(
    'stdout',
    sink=sys.stdout,
    level="INFO",  # 控制台只显示INFO级别以上的日志
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    colorize=True,
    enqueue=True,  # 使用队列，避免多线程写入问题
    catch=True  # 捕获由处理程序引发的异常
)

# 3. 添加错误日志处理器
add_log_handler(
    'error_file',
    sink="logs/sql_hooks_error.log",
    rotation="5 MB",
    retention="1 month",
    compression="zip",
    enqueue=True,
    level="ERROR",  # 只记录错误日志
    format="<red>{time:YYYY-MM-DD HH:mm:ss.SSS}</red> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>\n{exception}",
    backtrace=True,  # 增强错误跟踪
    diagnose=True,  # 记录诊断信息
    catch=True  # 捕获由处理程序引发的异常
)

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    SQL_READY = True
except ImportError:
    SQL_READY = False

def ensure_sql_ready():
    """确保SQL依赖已安装"""
    if SQL_READY:
        return True
        
    logger.error("""
    数据库扩展依赖未安装，请先安装后再试。
    使用pip安装:
    $ pip install sqlalchemy pymysql

    或者安装带SQL扩展的httprunner:
    $ pip install "httprunner[sql]"
    """)
    return False

def get_system_info():
    """获取系统信息用于日志记录"""
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return {"hostname": hostname, "ip": ip}
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}")
        return {"hostname": "unknown", "ip": "unknown"}

def log_db_operation(operation, db_key=None, db_uri=None, sql=None, result=None, error=None):
    """记录数据库操作日志
    
    Args:
        operation: 操作类型
        db_key: 数据库配置键名
        db_uri: 数据库连接URI
        sql: SQL语句
        result: 操作结果
        error: 错误信息
    """
    sys_info = get_system_info()
    log_context = {
        "operation": operation,
        "db_key": db_key,
        "hostname": sys_info["hostname"],
        "ip": sys_info["ip"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 记录数据库连接URI（仅做安全处理）
    if db_uri:
        # 隐藏敏感信息
        if "://" in db_uri:
            parts = db_uri.split("://")
            if "@" in parts[1]:
                auth_parts = parts[1].split("@")
                if ":" in auth_parts[0]:
                    # 隐藏密码
                    user_pwd = auth_parts[0].split(":")
                    masked_uri = f"{parts[0]}://{user_pwd[0]}:******@{auth_parts[1]}"
                    log_context["db_uri"] = masked_uri
                else:
                    log_context["db_uri"] = db_uri
            else:
                log_context["db_uri"] = db_uri
        else:
            log_context["db_uri"] = db_uri

    # 记录SQL和结果
    if sql:
        log_context["sql"] = sql
    if result and not error:
        # 截断过长的结果
        log_context["result_type"] = type(result).__name__
        if isinstance(result, dict):
            log_context["result"] = {k: str(v)[:100] + "..." if isinstance(v, str) and len(str(v)) > 100 else v for k, v in result.items()}
        elif isinstance(result, list):
            if len(result) > 5:
                log_context["result"] = f"[{len(result)} 条记录]"
            else:
                log_context["result"] = result
        else:
            log_context["result"] = str(result)

    # 记录错误信息
    if error:
        log_context["error"] = str(error)
        log_context["traceback"] = traceback.format_exc()
        logger.bind(**log_context).error(f"SQL操作 [{operation}] 失败 - {str(error)}")
    else:
        logger.bind(**log_context).info(f"SQL操作 [{operation}] 成功")
    
    return log_context

def get_database_connection_by_id(db_id: int) -> Optional[str]:
    """
    根据数据库配置ID获取数据库连接字符串
    
    Args:
        db_id: 数据库配置ID
        
    Returns:
        数据库连接字符串或None
    """
    if not db_id:
        log_db_operation("获取数据库连接", error="数据库配置ID为空")
        logger.warning("数据库配置ID为空，无法获取连接")
        return None
        
    # 记录开始获取连接
    logger.info(f"开始根据ID获取数据库连接: db_id={db_id}")
    
    # 尝试从数据库配置表获取
    try:
        from database_configs.models import DatabaseConfig
        # 使用ID获取数据库配置
        db_config = DatabaseConfig.objects.get(id=db_id, is_active=True)
        if db_config:
            db_uri = db_config.connection_string
            log_db_operation("获取数据库连接", db_uri=db_uri)
            logger.info(f"成功获取数据库连接: ID={db_id} -> {db_uri}")
            return db_uri
    except Exception as e:
        logger.error(f"无法通过ID获取数据库配置: {str(e)}")
    
    error_msg = f"未找到数据库配置: ID={db_id}"
    log_db_operation("获取数据库连接", error=error_msg)
    logger.warning(error_msg)
    return None

def get_environment_database_id() -> Optional[int]:
    """
    获取当前运行环境绑定的数据库ID
    
    Returns:
        数据库配置ID或None
    """
    try:
        # 尝试从运行环境获取数据库ID
        from environments.models import Environment
        # 获取当前活动环境
        active_env = Environment.objects.filter(is_active=True).first()
        if active_env and active_env.database_config_id:
            logger.info(f"从当前环境获取数据库ID: {active_env.database_config_id}")
            return active_env.database_config_id
    except Exception as e:
        logger.error(f"获取环境绑定的数据库ID失败: {str(e)}")
    
    return None

def get_database_connection(db_id: Optional[int] = None) -> Optional[str]:
    """
    获取数据库连接字符串
    
    Args:
        db_id: 数据库配置ID，如果为None，则尝试使用当前环境的数据库
        
    Returns:
        数据库连接字符串或None
    """
    # 如果提供了数据库ID，直接使用
    if db_id:
        return get_database_connection_by_id(db_id)
    
    # 否则，尝试从当前环境获取数据库ID
    env_db_id = get_environment_database_id()
    if env_db_id:
        return get_database_connection_by_id(env_db_id)
    
    # 如果都没有，记录错误
    logger.error("无法获取数据库连接：未提供数据库ID且当前环境未绑定数据库")
    return None

def execute_sql(
    sql: str, 
    db_uri: str, 
    fetch_type: str = "all"
) -> Union[Dict[str, Any], List[Dict[str, Any]], Dict[str, int]]:
    """
    执行SQL语句
    
    Args:
        sql: SQL语句
        db_uri: 数据库连接URI
        fetch_type: 获取类型，可以是"one"、"all"或"none"
        
    Returns:
        根据fetch_type返回不同类型的结果：
        - "one": 单条记录字典
        - "all": 记录字典列表
        - "none": 执行结果字典，包含rowcount
    """
    # 验证SQL依赖
    if not ensure_sql_ready():
        error_msg = "SQL依赖未安装"
        log_db_operation("执行SQL", db_uri=db_uri, sql=sql, error=error_msg)
        return {"error": error_msg}
        
    # 验证参数
    if not sql:
        error_msg = "SQL语句为空"
        log_db_operation("执行SQL", db_uri=db_uri, error=error_msg)
        return {"error": error_msg}
        
    if not db_uri:
        error_msg = "数据库连接URI为空"
        log_db_operation("执行SQL", sql=sql, error=error_msg)
        return {"error": error_msg}
    
    # 预处理SQL语句
    original_sql = sql
    # 根据数据库连接URI判断数据库类型
    db_type = ""
    if db_uri.startswith('sqlite'):
        db_type = "sqlite"
    elif 'mysql' in db_uri.lower() or 'mariadb' in db_uri.lower():
        db_type = "mysql"
    elif 'postgresql' in db_uri.lower() or 'postgres' in db_uri.lower():
        db_type = "postgresql"
    
    logger.debug(f"检测到数据库类型: {db_type}")
    
    # 根据数据库类型处理SQL
    if db_type == "sqlite":
        # SQLite 不支持数据库前缀，需要处理
        # 检查SQL语句中是否有形如 "db_name.table_name" 的表引用
        if '.' in sql:
            # 尝试提取数据库名
            db_name = None
            if 'sqlite:///:memory:' in db_uri:
                # 内存数据库，尝试从SQL中解析可能的DB前缀
                parts = sql.split('.')
                if len(parts) >= 2:
                    possible_db_name = parts[0].split(' ')[-1] # 获取第一个点号前的最后一个单词
                    if possible_db_name and len(possible_db_name) > 0:
                        db_name = possible_db_name
            
            # 如果找到数据库名，替换所有形如 "db_name.table_name" 的引用为 "table_name"
            if db_name:
                # 使用正则表达式替换所有匹配
                import re
                sql = re.sub(r'\b' + re.escape(db_name) + r'\.', '', sql)
                logger.info(f"为SQLite调整SQL: {original_sql} -> {sql}")
            else:
                # 如果无法确定数据库名，尝试简单替换第一个点号前的部分
                parts = sql.split('.')
                if len(parts) >= 2:
                    # 找到第一个表名引用
                    for i, part in enumerate(parts):
                        if i < len(parts) - 1 and any(keyword in part.upper() for keyword in ['FROM', 'JOIN', 'UPDATE', 'INTO']):
                            # 找到可能包含表引用的部分
                            words = part.split()
                            if words:
                                # 获取最后一个单词，可能是数据库名
                                last_word = words[-1]
                                if last_word:
                                    # 替换形如 "last_word.xxx" 的所有引用
                                    sql = sql.replace(f"{last_word}.", "")
                                    logger.info(f"尝试为SQLite调整SQL: {original_sql} -> {sql}")
                                    break
    elif db_type == "mysql":
        # MySQL支持 db.table 语法，不需要特殊处理
        logger.debug(f"MySQL数据库，保持原始SQL: {sql}")
    elif db_type == "postgresql":
        # PostgreSQL使用schema.table语法，有时需要调整
        if '.' in sql:
            # 检查是否需要特殊处理
            logger.debug(f"PostgreSQL数据库，保持原始SQL: {sql}")
    else:
        # 未知数据库类型，保持原始SQL
        logger.debug(f"未知数据库类型，保持原始SQL: {sql}")
        
    # 记录SQL执行开始
    logger.debug(f"准备执行SQL[{fetch_type}]: {sql}", db_uri=db_uri)
    
    operation_name = f"执行SQL({fetch_type})"
    session = None
    
    try:
        # 创建数据库引擎和会话
        engine = create_engine(db_uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 执行SQL
        start_time = time.time()
        logger.debug(f"执行SQL: {sql}")
        
        # 使用text()函数包装SQL语句，确保正确处理
        result = session.execute(text(sql))
        
        # 获取结果
        if fetch_type == "one":
            row = result.fetchone()
            if row:
                # 转换为字典
                result_dict = dict(row._mapping)
                logger.debug(f"获取单条记录: {result_dict}")
                elapsed = time.time() - start_time
                log_db_operation(operation_name, db_uri=db_uri, sql=sql, result=result_dict)
                return result_dict
            elapsed = time.time() - start_time
            logger.debug(f"SQL执行耗时: {elapsed:.3f}秒，未获取到记录")
            log_db_operation(operation_name, db_uri=db_uri, sql=sql, result={})
            return {}
            
        elif fetch_type == "all":
            rows = result.fetchall()
            if rows:
                # 转换为字典列表
                result_list = [dict(row._mapping) for row in rows]
                logger.debug(f"获取记录列表, 共{len(result_list)}条")
                elapsed = time.time() - start_time
                log_db_operation(operation_name, db_uri=db_uri, sql=sql, result=result_list)
                return result_list
            elapsed = time.time() - start_time
            logger.debug(f"SQL执行耗时: {elapsed:.3f}秒，未获取到记录")
            log_db_operation(operation_name, db_uri=db_uri, sql=sql, result=[])
            return []
            
        else:
            # 非查询操作，返回影响的行数
            result_dict = {"rowcount": result.rowcount}
            session.commit()
            elapsed = time.time() - start_time
            logger.debug(f"SQL执行耗时: {elapsed:.3f}秒，影响行数: {result.rowcount}")
            log_db_operation(operation_name, db_uri=db_uri, sql=sql, result=result_dict)
            return result_dict
            
    except Exception as e:
        elapsed = time.time() - start_time if 'start_time' in locals() else 0
        error_msg = f"执行SQL失败: {str(e)}"
        logger.error(f"{error_msg}，耗时: {elapsed:.3f}秒")
        log_db_operation(operation_name, db_uri=db_uri, sql=sql, error=str(e))
        return {"error": str(e)}
    finally:
        if 'elapsed' not in locals():
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
        logger.debug(f"SQL执行结束，总耗时: {elapsed:.3f}秒")
        if session:
            try:
                session.close()
                logger.debug("数据库会话已关闭")
            except Exception as e:
                logger.warning(f"关闭数据库会话失败: {str(e)}") 

# 安全地关闭所有日志处理器
def close_all_log_handlers():
    """安全地关闭所有日志处理器，应在应用退出前调用"""
    global log_handlers
    
    for handler_type, handler_id in log_handlers.items():
        if handler_id is not None:
            try:
                # 检查处理器ID是否存在于logger的处理器列表中
                if handler_id in [h_id for h_id in logger._core.handlers]:
                    logger.remove(handler_id)
                    log_handlers[handler_type] = None
                    print(f"成功关闭日志处理器: {handler_type}")
            except Exception as e:
                print(f"关闭日志处理器 {handler_type} 时出错: {str(e)}")
    
    # 最后移除所有剩余的处理器
    try:
        logger.remove()
        print("已移除所有日志处理器")
    except Exception as e:
        print(f"移除所有日志处理器时出错: {str(e)}") 

# 监控日志处理器状态
def check_logger_status():
    """检查日志处理器状态，包括打开的文件数量等信息"""
    try:
        # 获取当前处理器数量
        handlers_count = len(logger._core.handlers)
        
        # 获取当前日志处理器信息
        handlers_info = []
        for handler_id, handler in logger._core.handlers.items():
            handler_type = type(handler).__name__
            sink_info = str(handler._sink)
            if hasattr(handler, "_sink") and hasattr(handler._sink, "name"):
                sink_info = handler._sink.name
            handlers_info.append({
                "id": handler_id,
                "type": handler_type,
                "sink": sink_info,
                "level": handler._levelno
            })
        
        # 获取已知处理器信息
        global log_handlers
        known_handlers = {handler_type: handler_id for handler_type, handler_id in log_handlers.items() if handler_id is not None}
        
        return {
            "handlers_count": handlers_count,
            "handlers_info": handlers_info,
            "known_handlers": known_handlers
        }
    except Exception as e:
        return {
            "error": f"检查日志状态时出错: {str(e)}"
        } 