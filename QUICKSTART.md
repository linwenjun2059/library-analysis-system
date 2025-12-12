# 📋 部署与运维完整指南

> 本文档整合了所有部署相关内容，包括环境准备、数据链路执行、问题排查等。

---

## 📑 目录

- [一、环境准备](#一环境准备)
- [二、数据链路执行](#二数据链路执行)
- [三、步骤验证](#三步骤验证)
- [四、后端部署](#四后端部署)
- [五、前端部署](#五前端部署)
- [六、问题排查](#六问题排查)
- [七、性能优化](#七性能优化)
- [八、运维监控](#八运维监控)

---

## ⚡ 快速开始检查清单

在执行数据链路之前，请确保完成以下步骤：

- [ ] **Hadoop集群正常运行**
  ```bash
  hdfs dfsadmin -report
  yarn node -list
  ```

- [ ] **Hive Metastore已启动**
  ```bash
  jps | grep HiveMetaStore
  hive -e "SHOW DATABASES"
  ```

- [ ] **⭐ MySQL表已创建（必须！）**
  ```bash
  mysql -uroot -p780122 < ../bigdata/mysql/init_mysql.sql
  mysql -uroot -p780122 library_analysis -e "SHOW TABLES;"
  # 预期：29张表
  ```

- [ ] **CSV数据文件已准备**
  ```bash
  ls -lh /home/hadoop/LENDHIST2019_2020.csv
  ```

- [ ] **Python依赖已安装**
  ```bash
  pip3 list | grep -E "pandas|pymysql"
  ```

- [ ] **MySQL JDBC驱动已下载**
  ```bash
  ls -lh /opt/app/spark/jars/mysql-connector-j-8.0.33.jar
  ```

**完成以上检查后，即可开始执行数据链路！**

```bash
cd /home/hadoop/library-analysis-system/deploy
bash run.sh
```

---

## 一、环境准备

### 1.1 集群配置

**推荐配置**（10万条数据）：

| 节点 | 角色 | 配置 |
|-----|------|------|
| master | NameNode, ResourceManager, Hive Metastore | 8G内存, 4核CPU |
| slave1 | DataNode, NodeManager | 4G内存, 4核CPU |
| slave2 | DataNode, NodeManager | 4G内存, 4核CPU |

### 1.2 软件版本

```bash
# 必需组件
Hadoop: 3.3.6
Hive: 3.1.2
Spark: 3.5.6
MySQL: 8.0
JDK: 1.8
Python: 3.6+

# 可选组件（前后端）
Node.js: 16+
Maven: 3.6+
```

### 1.3 前置检查

```bash
# 检查Hadoop
hdfs dfsadmin -report
yarn node -list

# 检查Hive Metastore
jps | grep HiveMetaStore
hive -e "SHOW DATABASES"

# 检查MySQL
mysql -u root -p780122 -e "SELECT VERSION()"

# 检查Python依赖
python3 --version
pip3 list | grep -E "pandas|pymysql"
```

### 1.4 初始化MySQL数据库 ⭐ 必须

**⚠️ 重要：在执行数据链路之前，必须先创建MySQL表！**

```bash
# 1. 上传SQL初始化脚本到master节点
scp bigdata/mysql/init_mysql.sql hadoop@master:/home/hadoop/

# 2. SSH登录master节点
ssh hadoop@master

# 3. 执行MySQL初始化脚本
mysql -uroot -p780122 < /opt/project/bigdata/mysql/init_mysql.sql

# 4. 验证表已创建
mysql -uroot -p780122 library_analysis -e "SHOW TABLES;"
```

**预期输出（29张表）**：
```
+--------------------------------+
| Tables_in_library_analysis     |
+--------------------------------+
| active_users                   |
| book_association_rules         |
| book_dimension                 |
| book_heat_prediction           |
| book_lend_summary              |
| book_recommend_base            |
| book_recommendations           |
| cluster_summary                |
| collection_utilization_analysis|
| daily_stats                    |
| dept_lend_summary              |
| dept_preference                |
| hot_books                      |
| lend_trend                     |
| lend_trend_prediction          |
| major_reading_profile          |
| operation_dashboard            |
| overdue_analysis               |
| overdue_risk_prediction        |
| recent_lend_records            |
| recommendation_stats           |
| subject_lend_summary           |
| sys_user                       |
| time_distribution              |
| user_clusters                  |
| user_dimension                 |
| user_lend_summary              |
| user_profile                   |
| user_ranking                   |
+--------------------------------+
29 rows in set (0.00 sec)
```

**表结构说明**：
- **维度表（3张）**：user_dimension, book_dimension, recent_lend_records
- **汇总表（5张）**：user_lend_summary, book_lend_summary, dept_lend_summary, subject_lend_summary, daily_stats
- **聚合表（5张）**：hot_books, active_users, dept_preference, lend_trend, operation_dashboard
- **功能表（10张）**：book_recommendations, recommendation_stats, user_profile, major_reading_profile, overdue_analysis, collection_utilization_analysis, time_distribution, user_ranking, book_recommend_base, sys_user
- **挖掘表（3张）**：book_association_rules, user_clusters, cluster_summary
- **预测表（3张）**：overdue_risk_prediction, lend_trend_prediction, book_heat_prediction

**可选：测试MySQL连接**
```bash
# 使用测试脚本验证连接和表状态
cd /home/hadoop/library-analysis-system/deploy
bash test_mysql_connection.sh
```

### 1.5 准备数据

```bash
# 将CSV文件放到master节点
scp LENDHIST2019_2020.csv hadoop@master:/home/hadoop/
```

---

## 二、数据链路执行

### 2.1 脚本结构（已简化）

```
deploy/
├── config.sh                 # 统一配置文件
├── run.sh                    # 数据链路执行脚本（9个步骤）
├── verify.sh                 # 数据链路验证脚本
├── clean_old_data.sh         # 数据清理脚本
└── test_mysql_connection.sh  # MySQL连接测试脚本
```

**说明**：
- `run.sh` - 整合了所有9个步骤，可一键执行或分步执行
- `verify.sh` - 整合了所有验证逻辑，可验证单步或全部
- `config.sh` - 集中管理所有配置项
- `clean_old_data.sh` - 清理中间数据，保留HDFS原始文件
- `test_mysql_connection.sh` - 测试MySQL连接和表状态

### 2.2 上传脚本

```bash
# 在Windows/Mac上
cd /path/to/library-analysis-system
scp deploy/*.sh hadoop@master:/home/hadoop/library-analysis-system/deploy/
```

### 2.3 配置修改

```bash
# SSH登录master
ssh hadoop@master

# 进入脚本目录
cd /home/hadoop/library-analysis-system/deploy

# 修改配置（如需要）
vim config.sh
```

**关键配置项**：

```bash
# MySQL密码
export MYSQL_PASSWORD="780122"

# MySQL JDBC驱动路径
export MYSQL_JDBC_JAR="/home/hadoop/mysql-connector-java-8.0.33.jar"

# Spark资源配置（根据集群调整）
export SPARK_EXECUTOR_MEMORY="1500m"
export SPARK_EXECUTOR_CORES="2"
export SPARK_NUM_EXECUTORS="2"
export SPARK_DRIVER_MEMORY="1g"

# 数据路径
export LOCAL_CSV_FILE="/home/hadoop/LENDHIST2019_2020.csv"
```

### 2.4 数据格式检查（重要）⚠️

在执行数据清洗之前，**强烈建议**先运行数据格式检查脚本，确保CSV文件格式正确：

```bash
# 检查本地CSV文件格式
chmod +x check_data_format.sh
./check_data_format.sh
```

**检查项目：**
- ✅ 文件存在性和大小
- ✅ 文件编码（UTF-8）
- ✅ CSV表头列名（USERID, BOOK_ID, LEND_DATE等大写字段）
- ✅ 分隔符（必须是逗号`,`）
- ✅ 空值统计（USERID、BOOK_ID、LEND_DATE）
- ✅ 预估有效记录数

**预期输出示例：**

```
✅ 数据格式检查完成

总数据行数: 99255
预计过滤记录数: 0
预计有效记录数: 99255

📌 提示:
1. CSV文件使用逗号(,)作为分隔符 - ✅
2. 表头使用大写字母（USERID, BOOK_ID等）- ✅
3. 日期格式支持: 2020-01-1321:23:17 或 2020-01-13 21:23:17
```

> **注意：** 如果检查发现问题（如编码错误、列名不匹配、分隔符错误），请先修复数据文件，再继续后续步骤。

### 2.5 执行方式

#### 方式1：一键执行（推荐新手）

```bash
chmod +x *.sh
bash run.sh
```

执行全部9个步骤（步骤7-9为可选算法），预计耗时：15-25分钟

#### 方式2：分步执行（推荐调试）

```bash
# 步骤1: 上传数据到HDFS (10秒)
bash run.sh 1
bash verify.sh 1

# 步骤2: 创建Hive表 (30秒)
bash run.sh 2
bash verify.sh 2

# 步骤3: 数据清洗 - ODS→DWD (2-5分钟) ⚠️ 核心步骤
bash run.sh 3
bash verify.sh 3

# 步骤4: 数据汇总 - DWD→DWS (1-2分钟)
bash run.sh 4
bash verify.sh 4

# 步骤5: 数据分析 - DWS→ADS (1-2分钟)
bash run.sh 5
bash verify.sh 5

# 步骤6: 导出MySQL - Hive→MySQL (1-3分钟)
bash run.sh 6
bash verify.sh 6

# 步骤7: 推荐算法 (3-5分钟)
bash run.sh 7
bash verify.sh 7

# 步骤8: 高级数据挖掘 - FPGrowth+K-means (2-4分钟)
bash run.sh 8
bash verify.sh 8

# 步骤9: 预测模型 - 随机森林 (2-4分钟)
bash run.sh 9
bash verify.sh 9
```

#### 查看帮助

```bash
bash run.sh --help
bash verify.sh --help
```

---

## 三、步骤验证

### 3.1 验证脚本使用

```bash
# 验证单个步骤
bash verify.sh 1  # 验证步骤1
bash verify.sh 3  # 验证步骤3

# 验证所有步骤
bash verify.sh
```

### 3.2 各步骤验证标准

#### 步骤1: HDFS上传

**验证命令**：
```bash
bash verify.sh 1
```

**预期结果**：
```
✓ HDFS文件存在，大小: 15.2 M
文件行数: 99255
```

**手动检查**：
```bash
hdfs dfs -ls /data/library/raw/
hdfs dfs -cat /data/library/raw/LENDHIST2019_2020.csv | head -3
```

---

#### 步骤2: Hive建表

**验证命令**：
```bash
bash verify.sh 2
```

**预期结果**：
```
✓ Hive数据库已创建
library_ads
library_dwd
library_dws
library_ods

✓ DWD层表已创建
dwd_book_info
dwd_lend_detail
dwd_user_info
```

**手动检查**：
```bash
hive -e "SHOW DATABASES"
hive -e "USE library_dwd; SHOW TABLES"
```

---

#### 步骤3: Spark清洗 ⚠️

**验证命令**：
```bash
bash verify.sh 3
```

**预期结果**：
```
用户维度记录数: 15234
图书维度记录数: 12456
借阅明细记录数: 99254
✓ Spark数据清洗成功
```

**如果出现0条数据**，请跳转到 [六、问题排查 → 6.1](#61-数据清洗后0条记录)

**手动检查**：
```bash
hive -e "
SELECT COUNT(*) FROM library_dwd.dwd_user_info WHERE dt='$(date +%Y%m%d)';
SELECT COUNT(*) FROM library_dwd.dwd_book_info WHERE dt='$(date +%Y%m%d)';
SELECT COUNT(*) FROM library_dwd.dwd_lend_detail WHERE dt='$(date +%Y%m%d)';
"
```

---

#### 步骤4: Hive聚合

**验证命令**：
```bash
bash verify.sh 4
```

**预期结果**：
```
用户统计记录数: 15234
图书统计记录数: 12456
✓ Hive数据聚合成功
```

---

#### 步骤5: Spark分析

**验证命令**：
```bash
bash verify.sh 5
```

**预期结果**：
```
热门图书记录数: 50
✓ Spark数据分析成功

前5条热门图书:
+------------------+--------------+
| title            | borrow_count |
+------------------+--------------+
| 图书A            | 523          |
+------------------+--------------+
```

**手动检查**：
```bash
mysql -u root -p780122 -h master -D library_analysis -e "
SELECT title, borrow_count FROM hot_books 
ORDER BY borrow_count DESC LIMIT 5;
"
```

---

#### 步骤6: 导出MySQL

**验证命令**：
```bash
bash verify.sh 6
```

**预期结果**：
```
✓ MySQL表导出成功（20张表）
```

**手动检查**：
```bash
mysql -u root -p780122 -h master -D library_analysis -e "
SELECT table_name, table_rows FROM information_schema.tables 
WHERE table_schema='library_analysis';
"
```

---

### 3.3 最终验证

```bash
# 验证所有步骤
bash verify.sh

# 查看MySQL最终结果
mysql -u root -p780122 -h master -D library_analysis -e "
SELECT '推荐数据' as 表名, COUNT(*) as 记录数 FROM book_recommendations
UNION ALL
SELECT '热门图书', COUNT(*) FROM hot_books;
"
```

**成功标志**：
```
+-----------+----------+
| 表名       | 记录数   |
+-----------+----------+
| 推荐数据   | 50000    |
| 热门图书   | 50       |
+-----------+----------+
```

---

## 四、后端部署

### 4.1 修改配置

```bash
cd backend/src/main/resources

# 修改application.yml
vim application.yml
```

**关键配置**：
```yaml
spring:
  datasource:
    url: jdbc:mysql://master:3306/library_analysis
    username: root
    password: 780122

server:
  port: 8080
```

### 4.2 打包部署

```bash
cd backend

# 打包
mvn clean package -DskipTests

# 运行
java -jar target/library-analysis-0.0.1-SNAPSHOT.jar

# 或后台运行
nohup java -jar target/library-analysis-0.0.1-SNAPSHOT.jar > app.log 2>&1 &
```

### 4.3 验证后端

```bash
# 检查服务
curl http://localhost:8080/api/health

# 查看日志
tail -f app.log
```

---

## 五、前端部署

### 5.1 修改配置

```bash
cd frontend

# 修改API地址
vim .env.development
```

```
VITE_API_BASE_URL=http://master:8080/api
```

### 5.2 本地开发模式

```bash
npm install
npm run dev
```

访问: http://localhost:3000

### 5.3 生产部署

```bash
# 构建
npm run build

# 部署到Nginx
cp -r dist/* /usr/share/nginx/html/
```

---
## 六、问题排查

### 6.1 数据清洗后0条记录

**现象**：
```
清洗后记录数: 0
用户维度记录数: 0
图书维度记录数: 0
```

**原因**：CSV分隔符不匹配

**排查步骤**：

1. **查看CSV文件实际格式**：
```bash
hdfs dfs -cat /data/library/raw/LENDHIST2019_2020.csv | head -3
```

2. **判断分隔符**：
   - Tab分隔（`\t`）：字段之间有明显空白
   - 逗号分隔（`,`）：字段之间是逗号

3. **修改Python脚本**：
```bash
vim /home/hadoop/library-analysis-system/bigdata/spark/data_clean.py

# 找到第59行
# Tab分隔：
.option("delimiter", "\t")

# 逗号分隔：
.option("delimiter", ",")
```

4. **重新运行**：
```bash
bash run.sh 3
bash verify.sh 3
```

---

### 6.2 MySQL JDBC驱动不存在

**错误信息**：
```
File file:/opt/app/spark/jars/mysql-connector-java-8.0.33.jar does not exist
```

**解决方案**：

```bash
# 手动下载到config.sh配置的路径
cd /home/hadoop
wget https://repo1.maven.org/maven2/mysql/mysql-connector-java/8.0.33/mysql-connector-java-8.0.33.jar

# 验证
ls -lh mysql-connector-java-8.0.33.jar
```

---

### 6.3 Yarn资源不足

**错误信息**：
```
Requested more than the maximum memory capability of the cluster
```

**解决方案**：

修改 `config.sh` 降低资源配置：

```bash
vim config.sh

# 修改为：
export SPARK_EXECUTOR_MEMORY="1g"    # 从1500m降低
export SPARK_NUM_EXECUTORS="1"       # 从2降低到1
export SPARK_DRIVER_MEMORY="512m"    # 从1g降低
```

---

### 6.4 Hive Metastore连接失败

**错误信息**：
```
Could not connect to meta store using any of the URIs provided
```

**检查**：
```bash
# 检查Metastore服务
jps | grep HiveMetaStore

# 如果没有，启动它
hive --service metastore &

# 检查MySQL连接
mysql -u root -p780122 -e "USE hive_metastore; SHOW TABLES"
```

---

### 6.5 Python依赖缺失

**错误信息**：
```
ModuleNotFoundError: No module named 'pandas'
```

**解决方案**：
```bash
pip3 install --user pandas pymysql
```

---

### 6.6 MySQL表未创建

**现象**：
```bash
# 执行步骤6导出MySQL时报错
ERROR 1146 (42S02): Table 'library_analysis.user_dimension' doesn't exist
```

**原因**：未执行MySQL初始化脚本

**解决方案**：
```bash
# 1. 检查表是否存在
mysql -uroot -p780122 library_analysis -e "SHOW TABLES;"

# 2. 如果表不存在，执行初始化脚本
 mysql -uroot -p780122 < /opt/project/library-analysis-system/bigdata/mysql/init_mysql.sql

# 3. 验证29张表已创建
bash test_mysql_connection.sh
```

---

### 6.7 MySQL连接失败

**现象**：
```bash
# clean_old_data.sh清理时报错
❌ MySQL连接失败！
   主机: master
   用户: root
```

**排查步骤**：

1. **检查MySQL服务**：
```bash
systemctl status mysqld
# 如果未启动
systemctl start mysqld
```

2. **测试连接**：
```bash
mysql -uroot -p780122 -hmaster -e "SELECT 1;"

# 或使用测试脚本
bash test_mysql_connection.sh
```

3. **检查防火墙**：
```bash
firewall-cmd --list-ports
firewall-cmd --add-port=3306/tcp --permanent
firewall-cmd --reload
```

4. **检查MySQL配置**：
```bash
# 确保MySQL允许远程连接
vim /etc/my.cnf

# 检查bind-address（应该是0.0.0.0或注释掉）
# bind-address = 0.0.0.0
```

---

### 6.8 清理脚本无法清空MySQL表

**现象**：
```bash
bash clean_old_data.sh
# MySQL表数据仍然存在
```

**原因**：之前版本的脚本使用了错误的SQL语法 `TRUNCATE TABLE IF EXISTS`

**解决方案**：
```bash
# 1. 确保使用最新版本的clean_old_data.sh
git pull origin main

# 2. 手动清空所有表（如果脚本失败）
mysql -uroot -p780122 library_analysis << EOF
TRUNCATE TABLE user_dimension;
TRUNCATE TABLE book_dimension;
TRUNCATE TABLE recent_lend_records;
TRUNCATE TABLE user_lend_summary;
TRUNCATE TABLE book_lend_summary;
TRUNCATE TABLE dept_lend_summary;
TRUNCATE TABLE subject_lend_summary;
TRUNCATE TABLE daily_stats;
TRUNCATE TABLE hot_books;
TRUNCATE TABLE active_users;
TRUNCATE TABLE dept_preference;
TRUNCATE TABLE lend_trend;
TRUNCATE TABLE operation_dashboard;
TRUNCATE TABLE book_recommendations;
EOF

# 3. 使用改进的清理脚本
bash clean_old_data.sh
```

**验证清理成功**：
```bash
# 所有表的行数应该为0
mysql -uroot -p780122 library_analysis -e "
SELECT table_name, table_rows 
FROM information_schema.tables 
WHERE table_schema='library_analysis';
"
```

---

## 七、性能优化

### 7.1 Spark优化

修改 `config.sh`：

```bash
# 增加并行度
export SPARK_SHUFFLE_PARTITIONS="40"  # 默认20

# 增加Executor资源（如果集群允许）
export SPARK_EXECUTOR_MEMORY="2g"
export SPARK_NUM_EXECUTORS="3"
```

### 7.2 Hive优化

```sql
-- 开启动态分区
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;

-- 开启压缩
SET hive.exec.compress.output=true;
SET mapreduce.output.fileoutputformat.compress.codec=org.apache.hadoop.io.compress.SnappyCodec;
```

### 7.3 MySQL优化

```sql
-- 添加索引
ALTER TABLE book_recommendations ADD INDEX idx_user_id (user_id);
ALTER TABLE hot_books ADD INDEX idx_borrow_count (borrow_count DESC);
```

---

## 八、运维监控

### 8.1 日志查看

```bash
# Hadoop日志
tail -f /opt/app/hadoop/logs/hadoop-*.log

# Yarn日志
yarn logs -applicationId <application_id>

# Hive日志
tail -f /opt/app/hive/logs/hive.log

# Spark日志
tail -f /opt/app/spark/logs/spark-*.out

# 后端日志
tail -f app.log
```

### 8.2 集群监控

- **Yarn WebUI**: http://master:8088
- **HDFS WebUI**: http://master:9870
- **Spark History**: http://master:18080

### 8.3 定时调度

使用Cron定时执行：

```bash
crontab -e

# 每天凌晨2点执行
0 2 * * * cd /home/hadoop/library-analysis-system/deploy && bash run.sh >> /home/hadoop/pipeline.log 2>&1
```

---

## 📝 快速参考

### 常用命令

```bash
# 验证所有步骤
bash verify.sh

# 重新运行某一步
bash run.sh 3

# 查看配置
cat config.sh

# 一键执行全部
bash run.sh

# 查看帮助
bash run.sh --help
bash verify.sh --help
```

### 预计耗时（10万条数据）

| 步骤 | 名称 | 耗时 |
|-----|------|------|
| 步骤1 | 上传HDFS | 10秒 |
| 步骤2 | 创建Hive表 | 30秒 |
| 步骤3 | 数据清洗（ODS→DWD） | 2-5分钟 |
| 步骤4 | 数据汇总（DWD→DWS） | 1-2分钟 |
| 步骤5 | 数据分析（DWS→ADS） | 1-2分钟 |
| 步骤6 | 导出MySQL（20张表） | 1-3分钟 |
| 步骤7 | 推荐算法（可选） | 3-5分钟 |
| 步骤8 | 高级挖掘（可选） | 2-4分钟 |
| 步骤9 | 预测模型（可选） | 2-4分钟 |
| **总计** | **完整流程** | **15-25分钟** |

---

**如有其他问题，请查看项目README或提交Issue。**
