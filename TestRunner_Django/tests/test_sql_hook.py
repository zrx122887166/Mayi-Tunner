import os
import sys
from httprunner import HttpRunner, Config, Step, RunRequest
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 从工具模块导入SQL执行函数
from utils.db_utils import execute_sql, get_database_connection_by_key

# 测试SQL前后置钩子
class TestSqlHooks(HttpRunner):
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
        
        # 首先，模拟执行SQL钩子
        db_uri = get_database_connection_by_key("testdemo")
        if db_uri:
            print(f"数据库连接URI: {db_uri}")
            
            # 对于SQLite内存数据库，我们需要保持连接打开
            from sqlalchemy import create_engine, text
            engine = create_engine(db_uri)
            conn = engine.connect()
            
            try:
                # 创建一个临时表并执行查询
                print("创建临时表...")
                conn.execute(text("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)"))
                
                print("插入测试数据...")
                conn.execute(text("INSERT INTO test_table (name) VALUES ('测试数据')"))
                
                # 执行查询并获取结果
                print("查询数据...")
                result = conn.execute(text("SELECT * FROM test_table"))
                rows = [dict(row._mapping) for row in result.fetchall()]
                
                print(f"SQL查询结果: {rows}")
                
                # 将结果保存到变量中
                self._variables["sql_result"] = rows
            except Exception as e:
                print(f"SQL执行错误: {str(e)}")
            finally:
                conn.close()
        else:
            print("无法获取数据库连接")
        
        # 测试HTTP请求步骤
        request_step = Step(
            RunRequest("测试GET请求")
            .get("${url}")
            .validate()
            .assert_equal("status_code", "${expected_status}")
        )
        
        # 添加到测试步骤
        self.teststeps.append(request_step)
        
        # 运行测试
        try:
            # 正确处理测试运行结果
            self.test_start()
            # 获取测试报告摘要
            summary = self.get_summary()
            print(f"测试结果: {'成功' if summary.success else '失败'}")
            print(f"导出的变量: {summary.in_out.export_vars}")
            return summary
        except Exception as e:
            print(f"测试执行失败: {str(e)}")
            print(f"SQL查询结果: {self._variables.get('sql_result')}")
            return None
        
if __name__ == "__main__":
    # 执行测试
    result = TestSqlHooks().test_sql_hook()
    if result:
        print(f"测试用例执行完成: {result.name}")
    else:
        print("测试用例执行失败")
    
    print("SQL钩子测试完成")
    print("欢迎下次使用~") 