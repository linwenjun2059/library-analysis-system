# 🚀 快速启动指南

> 5分钟快速启动图书馆借阅分析系统

## 📋 前置条件检查

在开始之前，请确保以下服务已安装并运行：

```bash
# 1. 检查Java环境
java -version
# 应显示：java version "1.8.0_xxx"

# 2. 检查Hadoop集群
hdfs dfsadmin -report
# 应显示集群节点信息

# 3. 检查YARN
yarn node -list
# 应显示活跃节点

# 4. 检查Hive Metastore
jps | grep HiveMetaStore
# 应显示进程ID

# 5. 检查MySQL
mysql --version
# 应显示：mysql Ver 8.0.33

# 6. 检查Python
python3 --version
# 应显示：Python 3.6+

# 7. 检查Node.js（前端）
node -v
# 应显示：v16.0.0+

# 8. 检查Maven（后端）
mvn -version
# 应显示：Apache Maven 3.6+
```

## ⚙️ 快速配置

### 1. 配置大数据环境

编辑 `deploy/config.sh`，修改以下配置：

```bash
# MySQL配置（根据实际情况修改）
export MYSQL_HOST="master"              # MySQL主机地址
export MYSQL_USER="root"                 # MySQL用户名
export MYSQL_PASSWORD="780122"          # MySQL密码
export MYSQL_DATABASE="library_analysis" # 数据库名

# HDFS路径（根据实际情况修改）
export LOCAL_CSV_FILE="/opt/project/library-analysis-system/data/LENDHIST2019_2020.csv"
```

### 2. 配置后端服务

编辑 `backend/src/main/resources/application.yml`：

```yaml
spring:
  datasource:
    url: jdbc:mysql://master:3306/library_analysis?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true
    username: root
    password: 780122  # 修改为你的MySQL密码
```

### 3. 配置前端服务

前端使用代理配置，默认连接到 `http://localhost:8080/api`，如需修改请编辑 `frontend/vite.config.js`。

## 🎯 一键启动（完整流程）

### 步骤1：初始化数据库

```bash
# 创建数据库和表结构
mysql -uroot -p < bigdata/mysql/init_mysql.sql

# 验证表创建成功（应显示29张表）
mysql -uroot -p library_analysis -e "SHOW TABLES;" | wc -l
```

### 步骤2：安装Python依赖

```bash
# 安装Spark脚本所需的Python包
pip3 install -r bigdata/spark/requirements.txt
```

### 步骤3：执行数据链路

```bash
cd deploy
bash run.sh
```

**执行时间**：根据数据量大小，通常需要10-30分钟

**数据链路包含**：
1. ✅ 上传原始数据到HDFS
2. ✅ 创建Hive表结构（ODS/DWD/DWS/ADS）
3. ✅ 数据清洗（ODS → DWD）
4. ✅ 数据汇总（DWD → DWS）
5. ✅ 数据分析（DWS → ADS）
6. ✅ 导出MySQL（Hive → MySQL）
7. ⚙️ 推荐算法（可选）- 执行 `05_book_recommend.py`
8. ⚙️ 高级数据挖掘（可选）- 执行 `06_advanced_analysis.py`
9. ⚙️ 预测模型（可选）- 执行 `07_prediction_models.py`

### 步骤4：验证数据

```bash
cd deploy
bash verify.sh
```

**验证内容**：
- ✅ HDFS数据文件
- ✅ Hive表结构
- ✅ 数据量统计
- ✅ MySQL表数据

### 步骤5：启动后端服务

```bash
cd backend

# 编译打包
mvn clean package -DskipTests

# 启动服务
java -jar target/library-analysis-system-1.0.0.jar
```

**启动成功标志**：
```
Started LibraryAnalysisApplication in X.XXX seconds
```

**访问地址**：
- API地址：http://localhost:8080/api
- Swagger文档：http://localhost:8080/api/swagger-ui/index.html
- Druid监控：http://localhost:8080/api/druid/index.html（用户名：admin，密码：123456）

### 步骤6：启动前端服务

```bash
cd frontend

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev
```

**启动成功标志**：
```
  VITE v4.5.0  ready in XXX ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

**访问地址**：http://localhost:3000

## ✅ 验证启动成功

### 1. 检查后端服务

```bash
# 检查端口是否监听
netstat -tlnp | grep 8080

# 测试API
curl http://localhost:8080/api/health
```

### 2. 检查前端服务

打开浏览器访问：http://localhost:3000

应能看到登录页面。

### 3. 测试登录

**默认测试账号**（已在数据库初始化脚本中创建）：
- 高级管理员：`admin` / `123456`
- 图书管理员：`librarian` / `123456`

> 💡 **提示**：普通用户账号需要通过后端API注册，或在MySQL的 `sys_user` 表中手动创建。

## 🔧 快速启动（仅前后端）

如果只需要启动前后端服务（不执行数据链路），可以跳过步骤3和步骤4：

```bash
# 1. 初始化数据库（如果未初始化）
mysql -uroot -p < bigdata/mysql/init_mysql.sql

# 2. 启动后端
cd backend && mvn clean package -DskipTests && java -jar target/library-analysis-system-1.0.0.jar

# 3. 启动前端（新终端）
cd frontend && npm install && npm run dev
```

## 🐛 常见问题快速解决

### 问题1：MySQL连接失败

**错误信息**：`Communications link failure`

**解决方法**：
```bash
# 检查MySQL服务是否运行
systemctl status mysql
# 或
service mysql status

# 检查MySQL端口
netstat -tlnp | grep 3306

# 检查MySQL用户权限
mysql -uroot -p -e "SELECT user, host FROM mysql.user WHERE user='root';"
```

### 问题2：Hadoop/Hive连接失败

**错误信息**：`Connection refused` 或 `NameNode is in safe mode`

**解决方法**：
```bash
# 检查Hadoop服务
jps | grep -E "NameNode|DataNode|ResourceManager|NodeManager"

# 退出安全模式（如果进入）
hdfs dfsadmin -safemode leave

# 检查Hive Metastore
jps | grep HiveMetaStore
# 如果未运行，启动Metastore
nohup hive --service metastore > /dev/null 2>&1 &
```

### 问题3：Spark任务失败

**错误信息**：`OutOfMemoryError` 或 `Container killed`

**解决方法**：
```bash
# 编辑 deploy/config.sh，调整资源
export SPARK_EXECUTOR_MEMORY="2g"      # 增加executor内存
export SPARK_DRIVER_MEMORY="2g"        # 增加driver内存
export SPARK_NUM_EXECUTORS="3"         # 增加executor数量
```

### 问题4：前端无法连接后端

**错误信息**：`Network Error` 或 `CORS error`

**解决方法**：
```bash
# 检查后端是否启动
curl http://localhost:8080/api/health

# 检查前端代理配置
# 编辑 frontend/vite.config.js，确保proxy配置正确
```

### 问题5：端口被占用

**错误信息**：`Address already in use`

**解决方法**：
```bash
# 查找占用端口的进程
lsof -i :8080  # 后端端口
lsof -i :3000  # 前端端口

# 杀死进程
kill -9 <PID>

# 或修改端口
# 后端：编辑 backend/src/main/resources/application.yml
# 前端：编辑 frontend/vite.config.js
```

## 📊 启动后验证清单

- [ ] MySQL数据库已创建，包含29张表
- [ ] Hive表结构已创建（ODS/DWD/DWS/ADS层）
- [ ] HDFS中有原始数据文件
- [ ] MySQL中有业务数据（至少部分表有数据）
- [ ] 后端服务启动成功，端口8080可访问
- [ ] Swagger文档可访问
- [ ] 前端服务启动成功，端口3000可访问
- [ ] 可以正常登录系统
- [ ] 各功能页面可以正常访问

## 🎉 启动完成！

如果所有检查项都通过，恭喜你！系统已成功启动。

**下一步**：
- 📖 查看 [README.md](README.md) 了解详细功能
- 🔍 访问 Swagger 文档测试API
- 📊 登录系统查看数据分析结果

## 💡 提示

- **首次启动**：建议执行完整的数据链路（步骤1-6），确保数据完整
- **日常开发**：可以只启动前后端服务（快速启动模式）
- **数据更新**：运行 `deploy/run.sh` 重新处理数据
- **查看日志**：后端日志在 `backend/logs/` 目录

---

**遇到问题？** 查看 [README.md](README.md) 中的"常见问题"部分。

