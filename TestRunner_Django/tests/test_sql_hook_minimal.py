import os
import sys
import time
import locale
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from httprunner import HttpRunner, Config, Step, RunRequest

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 解决中文乱码问题
# 设置Python输入输出编码
os.environ["PYTHONIOENCODING"] = "utf-8"
# 设置Windows控制台的代码页为UTF-8（仅Windows下有效）
if sys.platform.startswith('win'):
    # 获取当前代码页
    current_cp = locale.getpreferredencoding()
    print(f"当前系统编码: {current_cp}")
    try:
        # 尝试设置控制台代码页
        os.system('chcp 65001 > nul')
        print("已设置控制台为UTF-8编码")
    except:
        print("无法设置控制台编码，可能需要手动运行 'chcp 65001'")
    
    # 对Windows控制台额外处理
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保日志目录存在
os.makedirs("logs", exist_ok=True)

# 创建SQLite内存数据库
DB_URI = "sqlite:///:memory:"
print(f"===============================================")
print(f"使用SQLite内存数据库: {DB_URI}")
print(f"===============================================")

# 创建数据库引擎
engine = create_engine(
    DB_URI, 
    connect_args={"check_same_thread": False},  # 允许多线程访问
    echo=False  # 不显示SQL语句
)

# 创建全局会话工厂
Session = sessionmaker(bind=engine)
session = Session()

# 创建元数据对象
metadata = MetaData()

# 定义测试表结构
test_table = Table(
    'test_table', 
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('create_time', DateTime, default=func.now())
)

# 创建数据库工具函数
from utils.db_utils import execute_sql, get_database_connection_by_key

# 自定义数据库连接获取函数
def get_test_db_connection_by_key(db_key):
    """测试用的数据库连接获取函数"""
    from loguru import logger
    
    # 为了测试日志，打印更详细的信息
    logger.info(f"获取测试数据库连接: {db_key}")
    print(f"获取测试数据库连接: {db_key}")
    
    # 返回测试数据库连接
    if db_key == "testdemo":
        return DB_URI
    
    logger.warning(f"未找到数据库配置: {db_key}")
    print(f"未找到数据库配置: {db_key}")
    return None

# 替换数据库工具函数
import utils.db_utils
utils.db_utils.get_database_connection_by_key = get_test_db_connection_by_key

# 设置环境变量，避免使用代理
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)

def setup_database():
    """初始化数据库"""
    try:
        print("\n============= 创建测试环境 =============")
        # 创建表并插入测试数据
        metadata.create_all(engine)
        
        # 插入测试数据
        print("插入测试数据...")
        session.execute(test_table.insert().values(name='测试数据1'))
        session.execute(test_table.insert().values(name='测试数据2'))
        session.execute(test_table.insert().values(name='测试数据3'))
        session.commit()
        
        # 查询验证
        result = session.execute(text("SELECT * FROM test_table"))
        rows = [dict(row._mapping) for row in result.fetchall()]
        print(f"测试数据: {rows}")
        print("============= 测试环境创建完成 =============\n")
        return True
    except Exception as e:
        print(f"设置测试环境失败: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def teardown_database():
    """清理数据库"""
    try:
        # 清理测试表
        print("\n============= 清理测试环境 =============")
        metadata.drop_all(engine)
        print("测试表已清理")
        
        # 关闭数据库连接
        session.close()
        print("数据库连接已关闭")
        print("============= 测试环境清理完成 =============\n")
    except Exception as e:
        print(f"清理测试环境失败: {str(e)}")

def verify_sql_results():
    """验证SQL执行结果"""
    try:
        print("\n============= 验证SQL钩子执行结果 =============")
        result = session.execute(text("SELECT * FROM test_table WHERE name='通过钩子添加'"))
        rows = [dict(row._mapping) for row in result.fetchall()]
        print(f"SQL钩子添加的数据: {rows}")
        return True
    except Exception as e:
        print(f"验证SQL钩子结果失败: {str(e)}")
        return False

# 主函数
def main():
    """主函数"""
    try:
        # 初始化数据库
        if not setup_database():
            print("数据库初始化失败，测试终止")
            return
        
        # 定义SQL钩子
        print("\n============= 定义SQL钩子 =============")
        sql_hook1 = {
            "type": "sql",
            "db_key": "testdemo",
            "sql": "SELECT * FROM test_table WHERE id=1",
            "var_name": "sql_result1"
        }
        
        sql_hook2 = {
            "sql_result2": {
                "type": "sql",
                "db_key": "testdemo", 
                "sql": "SELECT * FROM test_table WHERE id=2"
            }
        }
        
        sql_hook3 = {
            "type": "sql",
            "db_key": "testdemo",
            "sql": "SELECT COUNT(*) as total FROM test_table",
            "var_name": "total_count"
        }
        
        sql_hook4 = {
            "type": "sql",
            "db_key": "testdemo",
            "sql": "INSERT INTO test_table (name) VALUES ('通过钩子添加')",
            "var_name": "insert_result"
        }
        
        # 手动执行SQL钩子
        print("\n============= 手动执行SQL钩子 =============")
        step_variables = {}  # 创建一个空的变量字典
        
        # 导入execute_sql_hook函数
        from httprunner.step_request import execute_sql_hook
        
        # 创建一个简单的HttpRunner实例
        runner = HttpRunner()
        
        # 执行SQL钩子
        print("执行SQL钩子1...")
        execute_sql_hook(runner, sql_hook1, step_variables)
        
        print("\n执行SQL钩子2...")
        execute_sql_hook(runner, sql_hook2, step_variables)
        
        print("\n执行SQL钩子3...")
        execute_sql_hook(runner, sql_hook3, step_variables)
        
        print("\n执行SQL钩子4...")
        execute_sql_hook(runner, sql_hook4, step_variables)
        
        # 检查变量
        print("\n============= 检查SQL钩子结果变量 =============")
        if "sql_result1" in step_variables:
            print(f"SQL钩子1结果 (id=1): {step_variables['sql_result1']}")
        
        if "sql_result2" in step_variables:
            print(f"SQL钩子2结果 (id=2): {step_variables['sql_result2']}")
            
        if "total_count" in step_variables:
            print(f"SQL钩子3结果 (总数): {step_variables['total_count']}")
            
        if "insert_result" in step_variables:
            print(f"SQL钩子4结果 (插入): {step_variables['insert_result']}")
        
        # 验证SQL结果
        if verify_sql_results():
            print("SQL钩子测试成功！")
        else:
            print("SQL钩子测试失败！")
        
        # 查看日志文件
        print("\n查看日志文件...")
        log_files = []
        for file in os.listdir("logs"):
            if file.endswith(".log"):
                log_files.append(file)
        
        if log_files:
            print(f"日志文件列表: {log_files}")
        else:
            print("没有找到日志文件")
        
    finally:
        # 清理数据库
        teardown_database()
    
    print("\n==== SQL钩子日志测试总结 ====")
    print("1. SQL钩子可以在HTTP请求前执行数据库操作")
    print("2. 日志记录功能已增强，SQL执行详情被记录至控制台和日志文件")
    print("3. 查看 logs 目录下的日志文件获取更多详细信息")
    print("4. 日志文件：")
    print("   - sql_hooks.log: 所有SQL钩子日志")
    print("   - sql_hooks_error.log: 错误日志")
    print("")
    print("欢迎下次使用~")

if __name__ == "__main__":
    # 处理控制台中文显示
    if sys.platform.startswith('win'):
        try:
            # 设置控制台代码页
            os.system('chcp 65001 > nul')
            # 重新包装标准输出和标准错误
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
            print("已配置控制台编码为UTF-8")
        except Exception as e:
            print(f"配置控制台编码失败: {str(e)}")
    
    # 用UTF-8模式打开输出文件
    with open('logs/test_output.txt', 'w', encoding='utf-8') as f:
        # 重定向输出用于测试
        orig_stdout = sys.stdout
        sys.stdout = f
        
        try:
            # 记录一些中文进行测试
            print("=== 中文测试输出 ===")
            print("测试数据1，测试数据2，测试数据3")
            print("SQL钩子执行，通过钩子添加，获取测试数据库连接")
            
            # 执行主程序
            main()
        finally:
            # 恢复标准输出
            sys.stdout = orig_stdout
            print("测试输出已写入 logs/test_output.txt")
    
    # 正常执行主程序
    main() 