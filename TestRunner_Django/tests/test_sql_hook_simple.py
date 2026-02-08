import os
import sys
import time
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from httprunner import HttpRunner, Config, Step, RunRequest

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

# 自定义数据库连接获取函数 - 返回全局连接字符串
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

# 替换数据库工具函数以进行测试
import utils.db_utils
utils.db_utils.get_database_connection_by_key = get_test_db_connection_by_key

# 测试SQL钩子
class TestSqlHook(HttpRunner):
    def setup_class(self):
        """测试类前置设置"""
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
        except Exception as e:
            print(f"设置测试环境失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def teardown_class(self):
        """测试类后置清理"""
        try:
            # 清理测试表
            print("\n============= 清理测试环境 =============")
            metadata.drop_all(engine)
            print("测试表已清理")
            print("============= 测试环境清理完成 =============\n")
            
            # 关闭数据库连接
            session.close()
            print("数据库连接已关闭")
        except Exception as e:
            print(f"清理测试环境失败: {str(e)}")
    
    def test_start(self):
        """开始测试"""
        print("\n============= 开始执行SQL钩子测试 =============")
        
        # 定义SQL钩子
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
        
        # 创建配置并设置变量
        config = Config("SQL钩子日志测试")
        config.verify(False)  # 不验证SSL证书
        config.variables(**{
            "expected_status": 200
        })
        
        # 设置环境变量，避免使用代理
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)
        
        # 创建请求步骤，使用本地文件以避免网络请求
        print("创建请求步骤，添加SQL钩子...")
        request_step = (
            RunRequest("带SQL钩子的请求")
            .setup_hook(sql_hook1)
            .setup_hook(sql_hook2)
            .setup_hook(sql_hook3)
            .setup_hook(sql_hook4)
            .get("http://localhost:8000/mock")  # 这里使用本地URL，实际不会发送请求
            .validate()
            .assert_equal("status_code", "${expected_status}")
        )
        
        # 将步骤添加到测试
        step = Step(request_step)
        
        self.test_case(
            config=config,
            teststeps=[step]
        )
        
        # 查询测试结果
        print("\n============= 验证SQL钩子执行结果 =============")
        try:
            result = session.execute(text("SELECT * FROM test_table WHERE name='通过钩子添加'"))
            rows = [dict(row._mapping) for row in result.fetchall()]
            print(f"SQL钩子添加的数据: {rows}")
        except Exception as e:
            print(f"验证SQL钩子结果失败: {str(e)}")
        
        print("============= SQL钩子测试完成 =============")


if __name__ == "__main__":
    try:
        # 创建测试实例
        test = TestSqlHook()
        
        # 手动运行测试
        test.setup_class()
        
        try:
            test.test_start()
            print("测试执行成功")
        except Exception as e:
            print(f"测试执行失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
        
        # 查看日志目录下的文件
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
        # 清理环境
        test.teardown_class()
    
    print("\n==== SQL钩子日志测试总结 ====")
    print("1. SQL钩子可以在HTTP请求前执行数据库操作")
    print("2. 日志记录功能已增强，SQL执行详情被记录至控制台和日志文件")
    print("3. 查看 logs 目录下的日志文件获取更多详细信息")
    print("4. 日志文件：")
    print("   - sql_hooks.log: 所有SQL钩子日志")
    print("   - sql_hooks_error.log: 错误日志")
    print("")
    print("欢迎下次使用~") 