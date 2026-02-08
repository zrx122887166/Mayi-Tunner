import os
import sys
from httprunner import HttpRunner, Config, Step, RunRequest
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 从工具模块导入SQL执行函数
from utils.db_utils import execute_sql, get_database_connection_by_key

class TestSqlSetupHook(HttpRunner):
    def __init__(self):
        super().__init__()
        self._variables = {
            "url": "https://httpbin.org/get",
            "expected_status": 200,
            "sql_result": None
        }
    
    def test_sql_hook(self):
        # 配置测试用例
        config = Config("测试SQL钩子功能")
        config.variables(**self._variables)
        self.config = config
        
        # 准备测试环境
        db_uri = get_database_connection_by_key("testdemo")
        if db_uri:
            print(f"数据库连接URI: {db_uri}")
            # 创建数据库引擎
            from sqlalchemy import create_engine, text
            engine = create_engine(db_uri)
            conn = engine.connect()
            
            try:
                # 创建表并插入数据
                print("创建测试表...")
                conn.execute(text("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)"))
                conn.execute(text("INSERT INTO test_table (name) VALUES ('测试数据1')"))
                conn.execute(text("INSERT INTO test_table (name) VALUES ('测试数据2')"))
            except Exception as e:
                print(f"准备测试环境失败: {str(e)}")
            finally:
                conn.close()
        
        # 创建请求步骤
        request_obj = RunRequest("测试GET请求")
        
        # 设置数据库钩子（两种写法）
        # 方式1: 直接字典格式
        sql_hook1 = {
            "type": "sql",
            "db_key": "testdemo",
            "sql": "SELECT * FROM test_table WHERE id=1",
            "var_name": "sql_result1"
        }
        
        # 方式2: 嵌套字典格式
        sql_hook2 = {
            "sql_result2": {
                "type": "sql",
                "db_key": "testdemo", 
                "sql": "SELECT * FROM test_table WHERE id=2"
            }
        }
        
        # 添加setup钩子
        request_obj = request_obj.setup_hook(sql_hook1)
        request_obj = request_obj.setup_hook(sql_hook2)
        
        # 设置请求方法
        request_obj = request_obj.get("${url}")
        
        # 设置验证器
        request_obj = request_obj.validate().assert_equal("status_code", "${expected_status}")
        
        # 创建步骤并添加
        step = Step(request_obj)
        self.teststeps.append(step)
        
        # 运行测试
        try:
            # 运行测试
            self.test_start()
            
            # 获取测试报告摘要
            summary = self.get_summary()
            print(f"测试结果: {'成功' if summary.success else '失败'}")
            
            # 打印变量
            if summary.in_out and summary.in_out.export_vars:
                print(f"导出的变量: {summary.in_out.export_vars}")
            
            # 检查变量中是否包含SQL结果
            all_vars = summary.in_out.config_vars if summary.in_out else {}
            if "sql_result1" in all_vars:
                print(f"SQL钩子1结果: {all_vars['sql_result1']}")
            if "sql_result2" in all_vars:
                print(f"SQL钩子2结果: {all_vars['sql_result2']}")
            
            return summary
        except Exception as e:
            print(f"测试执行失败: {str(e)}")
            return None

if __name__ == "__main__":
    # 执行测试
    result = TestSqlSetupHook().test_sql_hook()
    if result:
        print(f"测试用例执行完成: {result.name}")
    else:
        print("测试用例执行失败")
    
    print("SQL钩子测试完成")
    print("欢迎下次使用~") 