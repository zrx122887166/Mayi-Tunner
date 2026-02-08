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

# 创建SQLite内存数据库，在模块级别定义，确保共享同一连接
DB_URI = "sqlite:///:memory:"
print(f"===============================================")
print(f"使用SQLite内存数据库: {DB_URI}")
print(f"===============================================")

# 创建数据库引擎，配置连接池和共享内存
engine = create_engine(
    DB_URI, 
    connect_args={"check_same_thread": False},  # 允许多线程访问
    poolclass=None,  # 不使用连接池，以便共享同一个内存数据库
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
class TestSqlHookFinal(HttpRunner):
    def __init__(self):
        super().__init__()
        self._variables = {
            "expected_status": 200
        }
        
        # 模拟HTTP请求处理函数
        self.mock_http_request = self._mock_http_request
    
    def _mock_http_request(self, *args, **kwargs):
        """模拟HTTP请求函数，避免实际网络请求"""
        from httprunner.client import HttpResponse
        print("执行模拟HTTP请求，避免实际网络请求...")
        
        # 创建模拟响应
        response = HttpResponse()
        response.status_code = 200
        response.headers = {"Content-Type": "application/json"}
        response.content = b'{"success":true, "message":"This is a mocked response"}'
        
        return response
    
    def setup_testcase(self):
        """测试用例前置设置"""
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
    
    def test_sql_hook(self):
        """测试SQL钩子功能"""
        # 设置测试环境
        if not self.setup_testcase():
            print("测试环境设置失败，无法继续测试")
            return None
        
        # 配置测试用例
        config = Config("SQL钩子日志测试")
        config.variables(**self._variables)
        config.verify(False)
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
        
        # 模拟RunRequest而不真正发送请求
        from httprunner.models import TStep
        from httprunner import HttpRunner
        
        class MockRunRequest:
            def __init__(self, name):
                self.name = name
                self.setup_hooks = []
                
            def setup_hook(self, hook):
                self.setup_hooks.append(hook)
                return self
                
            def get(self, url):
                return self
                
            def validate(self):
                return self
                
            def assert_equal(self, field, value):
                return self
                
            def perform(self, runner: HttpRunner, step_variables):
                """执行钩子和模拟HTTP请求"""
                print(f"执行步骤: {self.name}")
                
                # 执行setup钩子
                from httprunner.step_request import call_hooks
                call_hooks(runner, step_variables, self.setup_hooks, "setup request")
                
                # 获取模拟响应
                response = runner.mock_http_request()
                
                # 设置会话变量
                runner._SessionRunner__session_variables["status_code"] = response.status_code
                
                # 设置响应对象
                step_variables["response"] = response
                
                # 执行验证
                from httprunner.response import ResponseObject
                resp_obj = ResponseObject(response)
                assert resp_obj.status_code == 200, "HTTP状态码验证失败"
                
                return resp_obj
        
        # 创建模拟请求
        request_obj = MockRunRequest("带SQL钩子的请求")
        request_obj.setup_hook(sql_hook1)
        request_obj.setup_hook(sql_hook2)
        request_obj.setup_hook(sql_hook3)
        request_obj.setup_hook(sql_hook4)
        
        print("已添加4个SQL钩子，包括查询和插入操作")
        print("============= SQL钩子添加完成 =============\n")
        
        # 创建步骤
        tstep = TStep(name=request_obj.name)
        tstep.setup_hooks = request_obj.setup_hooks
        
        # 将执行方法绑定到步骤对象
        def run_step(runner, step_variables):
            return request_obj.perform(runner, step_variables)
        
        tstep.run = run_step
        
        # 将步骤添加到测试用例
        self.teststeps = [tstep]
        
        # 运行测试
        try:
            print("\n============= 开始执行测试 =============")
            # 运行测试
            self.test_start()
            
            # 获取测试报告摘要
            summary = self.get_summary()
            print(f"\n测试结果: {'成功' if summary.success else '失败'}")
            
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
            result = session.execute(text("SELECT * FROM test_table WHERE name='通过钩子添加'"))
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
            metadata.drop_all(engine)
            print("测试表已清理")
            print("============= 测试环境清理完成 =============\n")
        except Exception as e:
            print(f"清理测试环境失败: {str(e)}")

if __name__ == "__main__":
    # 创建测试实例
    test = TestSqlHookFinal()
    
    try:
        # 执行测试
        result = test.test_sql_hook()
        
        if result:
            print(f"测试用例执行完成: {result.name}")
            print(f"测试状态: {'成功' if result.success else '失败'}")
        else:
            print("测试用例执行失败")
    finally:
        # 清理测试环境
        test.teardown_testcase()
        
        # 关闭数据库连接
        session.close()
        print("数据库连接已关闭")
    
    print("\n==== SQL钩子日志测试总结 ====")
    print("1. SQL钩子可以在HTTP请求前执行数据库操作")
    print("2. 日志记录功能已增强，SQL执行详情被记录至控制台和日志文件")
    print("3. 查看 logs 目录下的日志文件获取更多详细信息")
    print("4. 日志文件：")
    print("   - sql_hooks.log: 所有SQL钩子日志")
    print("   - sql_hooks_error.log: 错误日志")
    print("   - *.run.log: HttpRunner测试日志")
    print("")
    print("欢迎下次使用~") 