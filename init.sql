-- 初始化数据库
CREATE DATABASE IF NOT EXISTS testrunner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 设置时区
SET time_zone = '+08:00';

-- 确保用户有正确的权限
GRANT ALL PRIVILEGES ON testrunner.* TO 'testrunner'@'%';
FLUSH PRIVILEGES;