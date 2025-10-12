from httprunner import HttpRunner, Config, Step, RunRequest

class TestEchoRequests(HttpRunner):
    """Echo请求测试用例"""
    
    config = (
        Config("Echo请求测试用例")
        .base_url("https://postman-echo.com")
        .verify(False)
    )
    
    teststeps = [
        Step(
            RunRequest("GET请求")
            .get("/get")
            .with_params(**{"foo": "bar"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.args.foo", "bar")
        ),
        
        Step(
            RunRequest("POST请求")
            .post("/post")
            .with_headers(**{"Content-Type": "application/json"})
            .with_json({
                "foo": "bar"
            })
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.json.foo", "bar")
        )
    ]

if __name__ == "__main__":
    TestEchoRequests().test_start()