# TestRunner

一个基于Django REST Framework和Vue3的现代化接口测试平台。

## ✨ 特性

- 🎯 **接口管理**：完整的API接口管理和调试功能
- 📝 **测试用例**：灵活的测试用例编写和管理
- 🔄 **测试任务**：支持批量执行和定时任务
- 📊 **测试报告**：详细的测试结果展示和统计
- 🗃️ **数据库操作**：内置SQL钩子支持
- 🌐 **环境管理**：多环境配置和变量管理
- 🔧 **自定义函数**：支持Python自定义函数扩展

## 🏗️ 技术栈

### 后端
- Django 4.x
- Django REST Framework
- Celery（异步任务）
- PostgreSQL/MySQL/SQLite
- UV（包管理）

### 前端
- Vue 3
- TypeScript
- Arco Design
- Vite
- Pinia（状态管理）

## 📦 项目结构

```
TestRunner/
├── TestRunner_Django/     # Django后端
│   ├── TestRunner/        # 项目配置
│   ├── testcases/         # 测试用例模块
│   ├── testtasks/         # 测试任务模块
│   ├── users/             # 用户模块
│   └── utils/             # 工具函数
└── TestRunner_Vue/        # Vue前端
    ├── src/
    │   ├── api/           # API接口
    │   ├── components/    # 公共组件
    │   ├── views/         # 页面视图
    │   ├── stores/        # 状态管理
    │   └── router/        # 路由配置
    └── public/
```

## 🚀 快速开始

### 后端启动

1. 安装依赖（使用UV）
```bash
cd TestRunner_Django
uv sync
```

2. 配置数据库
```bash
# 修改 TestRunner/settings.py 中的数据库配置
```

3. 执行迁移
```bash
uv run python manage.py migrate
```

4. 创建超级用户
```bash
uv run python manage.py createsuperuser
```

5. 启动服务
```bash
uv run python manage.py runserver
```

6. 启动Celery（可选）
```bash
uv run celery -A TestRunner worker -l info
```

### 前端启动

1. 安装依赖
```bash
cd TestRunner_Vue
npm install
# 或
pnpm install
```

2. 配置API地址
```bash
# 在 TestRunner_Vue 目录创建 .env 文件
# 添加：VITE_API_BASE_URL=http://localhost:8000/api
```

3. 启动开发服务器
```bash
npm run dev
```

4. 构建生产版本
```bash
npm run build
```

## 📝 环境变量配置

### 后端环境变量
在 `TestRunner_Django` 目录创建 `.env` 文件：
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
CELERY_BROKER_URL=redis://localhost:6379/0
```

### 前端环境变量
在 `TestRunner_Vue` 目录创建 `.env` 文件：
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

## 🔧 主要功能模块

### 1. 接口管理
- 接口分组和模块化管理
- 请求参数配置（Headers、Params、Body）
- 响应数据提取和断言
- SQL钩子支持（前置/后置操作）

### 2. 测试用例
- 多步骤测试用例编写
- 变量提取和引用
- 断言配置
- 用例标签和分组

### 3. 测试任务
- 批量执行测试用例
- 定时任务支持
- 环境选择
- 实时执行状态

### 4. 测试报告
- 详细的执行日志
- 步骤级别的结果展示
- 统计图表
- 报告导出

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👥 作者

- [@lucky-Testrunner](https://github.com/lucky-Testrunner)

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者！

## 📮 联系方式

如有问题或建议，欢迎：
- 提交 Issue
- 发起 Pull Request
- 联系项目维护者

---

⭐ 如果这个项目对你有帮助，请给它一个星标！