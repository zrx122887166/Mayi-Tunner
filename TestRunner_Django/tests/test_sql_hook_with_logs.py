import os
import sys
import time
from sqlalchemy import create_engine, text
from httprunner import HttpRunner, Config, Step, RunRequest

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 确保日志目录存在
os.makedirs("logs", exist_ok=True)

# 创建SQLite文件数据库，而不是内存数据库，这样可以持久化
DB_FILE = "logs/test_sql.db"
DB_URI = f"sqlite:///{DB_FILE}"

print(f"===============================================")
print(f"SQLite数据库文件位置: {os.path.abspath(DB_FILE)}")
print(f"SQLite数据库连接URI: {DB_URI}")
print(f"===============================================")

# 创建数据库引擎和连接
engine = create_engine(DB_URI)
conn = engine.connect()

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

# 替换原始函数以进行测试
import utils.db_utils
utils.db_utils.get_database_connection_by_key = get_test_db_connection_by_key

# 测试SQL钩子
class TestSqlHookWithLogs(HttpRunner):
    def __init__(self):
        super().__init__()
        self._variables = {
            "url": "https://httpbin.org/get",
            "expected_status": 200
        }
    
    def setup_testcase(self):
        """测试用例前置设置"""
        try:
            print("\n============= 创建测试环境 =============")
            # 创建测试表
            print("创建测试表...")
            conn.execute(text("DROP TABLE IF EXISTS test_table"))
            conn.execute(text("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT, create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
            
            # 插入测试数据
            print("插入测试数据...")
            conn.execute(text("INSERT INTO test_table (name) VALUES ('测试数据1')"))
            conn.execute(text("INSERT INTO test_table (name) VALUES ('测试数据2')"))
            conn.execute(text("INSERT INTO test_table (name) VALUES ('测试数据3')"))
            
            # 查询验证
            result = conn.execute(text("SELECT * FROM test_table"))
            rows = [dict(row._mapping) for row in result.fetchall()]
            print(f"测试数据: {rows}")
            print("============= 测试环境创建完成 =============\n")
            
            return True
        except Exception as e:
            print(f"设置测试环境失败: {str(e)}")
            return False
    
    def test_sql_hook(self):
        """测试SQL钩子功能"""
        # 设置测试环境
        if not self.setup_testcase():
            print("测试环境设置失败，无法继续测试")
            return None
        
        # 配置测试用例
        config = Config("SQL钩子日志测试")
        config.variables(**self._variables)
        self.config = config
        
        print("\n============= 添加SQL钩子 =============")
        
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
        
        # 创建测试步骤
        request_obj = (
            RunRequest("带SQL钩子的请求")
            .setup_hook(sql_hook1)
            .setup_hook(sql_hook2)
            .setup_hook(sql_hook3)
            .setup_hook(sql_hook4)
            .get("${url}")
            .validate()
            .assert_equal("status_code", "${expected_status}")
        )
        
        print("已添加4个SQL钩子，包括查询和插入操作")
        print("============= SQL钩子添加完成 =============\n")
        
        # 创建步骤并添加
        step = Step(request_obj)
        self.teststeps.append(step)
        
        # 运行测试
        try:
            print("\n============= 开始执行测试 =============")
            # 运行测试
            self.test_start()
            
            # 获取测试报告摘要
            summary = self.get_summary()
            print(f"\n测试结果: {'成功' if summary.success else '失败'}")
            
            # 打印导出的变量
            if summary.in_out and summary.in_out.export_vars:
                print(f"导出的变量: {summary.in_out.export_vars}")
            
            # 在会话变量中查找SQL结果
            session_vars = self.get_session_variables()
            
            print("\n============= SQL钩子执行结果 =============")
            if "sql_result1" in session_vars:
                print(f"SQL钩子1结果 (id=1): {session_vars['sql_result1']}")
            
            if "sql_result2" in session_vars:
                print(f"SQL钩子2结果 (id=2): {session_vars['sql_result2']}")
                
            if "total_count" in session_vars:
                print(f"SQL钩子3结果 (总数): {session_vars['total_count']}")
                
            if "insert_result" in session_vars:
                print(f"SQL钩子4结果 (插入): {session_vars['insert_result']}")
            
            # 验证插入是否成功
            result = conn.execute(text("SELECT * FROM test_table WHERE name='通过钩子添加'"))
            rows = [dict(row._mapping) for row in result.fetchall()]
            print(f"\n验证插入结果: {rows}")
            
            print("============= 测试执行完成 =============\n")
            return summary
        except Exception as e:
            print(f"测试执行失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def get_session_variables(self):
        """获取会话变量"""
        if hasattr(self, "_SessionRunner__session_variables"):
            return self._SessionRunner__session_variables
        return {}
    
    def teardown_testcase(self):
        """测试用例后置清理"""
        try:
            # 清理测试表
            print("\n============= 清理测试环境 =============")
            conn.execute(text("DROP TABLE IF EXISTS test_table"))
            print("测试表已清理")
            print("============= 测试环境清理完成 =============\n")
        except Exception as e:
            print(f"清理测试环境失败: {str(e)}")

if __name__ == "__main__":
    # 创建测试实例
    test = TestSqlHookWithLogs()
    
    try:
        # 执行测试
        result = test.test_sql_hook()
        
        if result:
            print(f"测试用例执行完成: {result.name}")
        else:
            print("测试用例执行失败")
    finally:
        # 清理测试环境
        test.teardown_testcase()
        
        # 关闭数据库连接
        conn.close()
        print("数据库连接已关闭")
    
    print("SQL钩子日志测试完成")
    print("检查 logs 目录下的日志文件以查看详细日志")
    print("欢迎下次使用~") 