#!/bin/bash
# =============================================
# 数据链路统一配置文件
# =============================================

# 日期配置
export ETL_DATE=$(date +%Y%m%d)

# HDFS路径配置
export HDFS_RAW_PATH="/data/library/raw"
export LOCAL_CSV_FILE="/opt/project/library-analysis-system/data/LENDHIST2019_2020.csv"

# Hive配置
export HIVE_METASTORE_URI="thrift://master:9083"
export SPARK_WAREHOUSE_DIR="/user/hive/warehouse"

# Spark脚本目录
export PYTHON_SCRIPT_DIR="/opt/project/library-analysis-system/bigdata/spark"

# MySQL配置
export MYSQL_HOST="master"
export MYSQL_PORT="3306"
export MYSQL_USER="root"
export MYSQL_PASSWORD="780122"
export MYSQL_DATABASE="library_analysis"

# MySQL JDBC驱动（修正路径）
export MYSQL_JDBC_JAR="/opt/app/spark/jars/mysql-connector-j-8.0.33.jar"

# Spark资源配置
export SPARK_EXECUTOR_MEMORY="1500m"
export SPARK_EXECUTOR_CORES="2"
export SPARK_NUM_EXECUTORS="2"
export SPARK_DRIVER_MEMORY="1g"

# 工具函数
print_header() {
    echo ""
    echo "============================================="
    echo "$1"
    echo "============================================="
}

print_step() {
    echo ""
    echo "[步骤 $1] $2"
}

print_success() {
    echo "✓ $1"
}

print_error() {
    echo "❌ 错误: $1" >&2
}

print_warning() {
    echo "⚠ 警告: $1"
}
