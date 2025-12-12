#!/bin/bash
# =============================================
# 图书馆数据分析系统 - 数据链路执行脚本
# 用法: bash run.sh [步骤号]
#   不带参数: 执行全部步骤
#   带参数: 执行指定步骤 (1-6)
# =============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

# =============================================
# 步骤1: 上传原始数据到HDFS
# =============================================
step1_upload_to_hdfs() {
    print_header "步骤1: 上传原始数据到HDFS"
    
    print_step "1" "检查HDFS目录..."
    hdfs dfs -test -d ${HDFS_RAW_PATH}
    if [ $? -ne 0 ]; then
        print_step "1.1" "创建HDFS目录: ${HDFS_RAW_PATH}"
        hdfs dfs -mkdir -p ${HDFS_RAW_PATH}
    fi
    
    # 检查文件是否已存在
    print_step "2" "检查CSV文件是否已存在..."
    CSV_EXISTS=0
    for file in ${LOCAL_CSV_FILE}; do
        filename=$(basename "$file")
        hdfs dfs -test -e "${HDFS_RAW_PATH}/${filename}"
        if [ $? -eq 0 ]; then
            CSV_EXISTS=1
            print_warning "文件已存在: ${filename}"
        fi
    done
    
    if [ $CSV_EXISTS -eq 1 ]; then
        echo ""
        echo " HDFS上已存在CSV文件"
        read -p "是否重新上传？(yes/no，默认no): " reupload
        if [ "$reupload" != "yes" ]; then
            print_success "跳过上传，使用已有文件"
            hdfs dfs -ls ${HDFS_RAW_PATH}
            return 0
        fi
        print_step "3" "重新上传CSV文件..."
        hdfs dfs -put -f ${LOCAL_CSV_FILE} ${HDFS_RAW_PATH}/
    else
        print_step "3" "上传CSV文件到HDFS..."
        hdfs dfs -put ${LOCAL_CSV_FILE} ${HDFS_RAW_PATH}/
    fi
    
    if [ $? -eq 0 ]; then
        print_success "数据上传完成"
        hdfs dfs -ls ${HDFS_RAW_PATH}
        return 0
    else
        print_error "数据上传失败"
        return 1
    fi
}

# =============================================
# 步骤2: 创建Hive表结构
# =============================================
step2_create_hive_tables() {
    print_header "步骤2: 创建Hive表结构"
    
    HIVE_SCRIPT_DIR="${SCRIPT_DIR}/../bigdata/hive"
    
    print_step "1" "创建ODS层表（原始数据层）..."
    hive -S -f "${HIVE_SCRIPT_DIR}/01_create_ods.sql"
    if [ $? -ne 0 ]; then
        print_error "ODS层表创建失败"
        return 1
    fi
    
    print_step "2" "创建DWD层表（明细数据层）..."
    hive -S -f "${HIVE_SCRIPT_DIR}/02_create_dwd.sql"
    if [ $? -ne 0 ]; then
        print_error "DWD层表创建失败"
        return 1
    fi
    
    print_step "3" "创建DWS层表（汇总数据层）..."
    hive -S -f "${HIVE_SCRIPT_DIR}/03_create_dws.sql"
    if [ $? -ne 0 ]; then
        print_error "DWS层表创建失败"
        return 1
    fi
    
    print_step "4" "创建ADS层表（应用数据层）..."
    hive -S -f "${HIVE_SCRIPT_DIR}/04_create_ads.sql"
    if [ $? -ne 0 ]; then
        print_error "ADS层表创建失败"
        return 1
    fi
    
    print_success "Hive表结构创建完成（ODS/DWD/DWS/ADS）"
    return 0
}

# =============================================
# 步骤3: Spark数据清洗（ODS → DWD）
# =============================================
step3_spark_clean() {
    print_header "步骤3: Spark数据清洗（ODS → DWD）"
    
    spark-submit \
      --master yarn \
      --deploy-mode client \
      --name "01_data_clean" \
      --num-executors ${SPARK_NUM_EXECUTORS} \
      --executor-memory ${SPARK_EXECUTOR_MEMORY} \
      --executor-cores ${SPARK_EXECUTOR_CORES} \
      --driver-memory ${SPARK_DRIVER_MEMORY} \
      --conf spark.dynamicAllocation.enabled=false \
      --conf spark.sql.shuffle.partitions=20 \
      --conf spark.sql.warehouse.dir=${SPARK_WAREHOUSE_DIR} \
      --conf spark.yarn.queue=default \
      --conf spark.sql.sources.partitionOverwriteMode=dynamic \
      ${PYTHON_SCRIPT_DIR}/01_data_clean.py all
    
    if [ $? -eq 0 ]; then
        print_success "数据清洗完成（DWD层）"
        return 0
    else
        print_error "数据清洗失败"
        return 1
    fi
}

# =============================================
# 步骤4: Spark数据汇总（DWD → DWS）
# =============================================
step4_spark_aggregate() {
    print_header "步骤4: Spark数据汇总（DWD → DWS）"
    
    spark-submit \
      --master yarn \
      --deploy-mode client \
      --name "02_data_aggregate" \
      --num-executors ${SPARK_NUM_EXECUTORS} \
      --executor-memory ${SPARK_EXECUTOR_MEMORY} \
      --executor-cores ${SPARK_EXECUTOR_CORES} \
      --driver-memory ${SPARK_DRIVER_MEMORY} \
      --conf spark.dynamicAllocation.enabled=false \
      --conf spark.sql.shuffle.partitions=20 \
      --conf spark.sql.warehouse.dir=${SPARK_WAREHOUSE_DIR} \
      ${PYTHON_SCRIPT_DIR}/02_data_aggregate.py all
    
    if [ $? -eq 0 ]; then
        print_success "数据汇总完成（DWS层 - 5张表）"
        return 0
    else
        print_error "数据汇总失败"
        return 1
    fi
}

# =============================================
# 步骤5: Spark数据分析（DWS → ADS）
# =============================================
step5_spark_analyze() {
    print_header "步骤5: Spark数据分析（DWS → ADS）"
    
    spark-submit \
      --master yarn \
      --deploy-mode client \
      --name "03_data_analyze" \
      --num-executors ${SPARK_NUM_EXECUTORS} \
      --executor-memory ${SPARK_EXECUTOR_MEMORY} \
      --executor-cores ${SPARK_EXECUTOR_CORES} \
      --driver-memory ${SPARK_DRIVER_MEMORY} \
      --conf spark.dynamicAllocation.enabled=false \
      --conf spark.sql.shuffle.partitions=20 \
      --conf spark.sql.warehouse.dir=${SPARK_WAREHOUSE_DIR} \
      ${PYTHON_SCRIPT_DIR}/03_data_analyze.py
    
    if [ $? -eq 0 ]; then
        print_success "数据分析完成（ADS层 - 12张表）"
        return 0
    else
        print_error "数据分析失败"
        return 1
    fi
}

# =============================================
# 步骤6: 导出数据到MySQL（20张表）
# =============================================
step6_export_mysql() {
    print_header "步骤6: 导出数据到MySQL（20张表）"
    
    # 检查MySQL JDBC驱动
    if [ ! -f "${MYSQL_JDBC_JAR}" ]; then
        print_error "MySQL JDBC驱动不存在: ${MYSQL_JDBC_JAR}"
        print_warning "请下载并放置到该路径，或修改config.sh中的路径"
        return 1
    fi
    
    # 确保MySQL配置环境变量已导出（config.sh已导出，这里再次确认）
    export MYSQL_HOST MYSQL_PORT MYSQL_USER MYSQL_PASSWORD MYSQL_DATABASE
    
    print_step "1" "MySQL连接配置: ${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE}"
    
    spark-submit \
      --master yarn \
      --deploy-mode client \
      --name "04_data_export" \
      --num-executors 3 \
      --executor-memory 2G \
      --executor-cores 2 \
      --driver-memory 2G \
      --jars ${MYSQL_JDBC_JAR} \
      --conf spark.dynamicAllocation.enabled=false \
      --conf spark.sql.shuffle.partitions=20 \
      --conf spark.sql.warehouse.dir=${SPARK_WAREHOUSE_DIR} \
      ${PYTHON_SCRIPT_DIR}/04_data_export.py
    
    if [ $? -eq 0 ]; then
        print_success "数据导出完成（20张表）"
        return 0
    else
        print_error "数据导出失败"
        return 1
    fi
}

# =============================================
# 步骤7: Spark推荐算法（可选）
# =============================================
step7_spark_recommend() {
    print_header "步骤7: Spark推荐算法"
    
    # 检查MySQL JDBC驱动
    if [ ! -f "${MYSQL_JDBC_JAR}" ]; then
        print_error "MySQL JDBC驱动不存在: ${MYSQL_JDBC_JAR}"
        print_warning "请下载并放置到该路径，或修改config.sh中的路径"
        return 1
    fi
    
    spark-submit \
      --master yarn \
      --deploy-mode client \
      --name "05_book_recommend" \
      --num-executors 1 \
      --executor-memory 3g \
      --executor-cores 2 \
      --driver-memory 1g \
      --conf spark.sql.shuffle.partitions=30 \
      --jars ${MYSQL_JDBC_JAR} \
      ${PYTHON_SCRIPT_DIR}/05_book_recommend.py all 

    if [ $? -eq 0 ]; then
        print_success "推荐算法完成"
        return 0
    else
        print_error "推荐算法失败"
        return 1
    fi
}

# =============================================
# 步骤8: 高级数据挖掘分析（关联规则+聚类）
# =============================================
step8_spark_advanced() {
    print_header "步骤8: 高级数据挖掘分析（FPGrowth+K-means）"
    
    # 检查MySQL JDBC驱动
    if [ ! -f "${MYSQL_JDBC_JAR}" ]; then
        print_error "MySQL JDBC驱动不存在: ${MYSQL_JDBC_JAR}"
        print_warning "请下载并放置到该路径，或修改config.sh中的路径"
        return 1
    fi
    
    spark-submit \
      --master yarn \
      --deploy-mode client \
      --name "06_advanced_analysis" \
      --num-executors 2 \
      --executor-memory 3g \
      --executor-cores 2 \
      --driver-memory 2g \
      --conf spark.sql.shuffle.partitions=20 \
      --jars ${MYSQL_JDBC_JAR} \
      ${PYTHON_SCRIPT_DIR}/06_advanced_analysis.py

    if [ $? -eq 0 ]; then
        print_success "高级数据挖掘分析完成（关联规则+用户聚类）"
        return 0
    else
        print_error "高级数据挖掘分析失败"
        return 1
    fi
}

# =============================================
# 步骤9: 预测模型分析（逾期风险+趋势+热度）
# =============================================
step9_spark_prediction() {
    print_header "步骤9: 预测模型分析（随机森林预测）"
    
    # 检查MySQL JDBC驱动
    if [ ! -f "${MYSQL_JDBC_JAR}" ]; then
        print_error "MySQL JDBC驱动不存在: ${MYSQL_JDBC_JAR}"
        print_warning "请下载并放置到该路径，或修改config.sh中的路径"
        return 1
    fi
    
    spark-submit \
      --master yarn \
      --deploy-mode client \
      --name "07_prediction_models" \
      --num-executors 2 \
      --executor-memory 3g \
      --executor-cores 2 \
      --driver-memory 2g \
      --conf spark.sql.shuffle.partitions=20 \
      --jars ${MYSQL_JDBC_JAR} \
      ${PYTHON_SCRIPT_DIR}/07_prediction_models.py

    if [ $? -eq 0 ]; then
        print_success "预测模型分析完成（逾期风险+借阅趋势+图书热度）"
        return 0
    else
        print_error "预测模型分析失败"
        return 1
    fi
}

# =============================================
# 执行全部步骤
# =============================================
run_all_steps() {
    print_header "图书馆数据分析系统 - 完整数据链路"
    echo "分区策略: year + month (历史数据 2019-2020)"
    echo "MySQL JDBC: ${MYSQL_JDBC_JAR}"
    echo ""
    
    START_TIME=$(date +%s)
    
    step1_upload_to_hdfs || exit 1
    echo ""
    
    step2_create_hive_tables || exit 1
    echo ""
    
    step3_spark_clean || exit 1
    echo ""
    
    step4_spark_aggregate || exit 1
    echo ""
    
    step5_spark_analyze || exit 1
    echo ""
    
    step6_export_mysql || exit 1
    echo ""
    
    # 推荐算法是可选的
    if [ "${RUN_RECOMMEND:-yes}" = "yes" ]; then
        step7_spark_recommend || print_warning "推荐算法失败（可选步骤）"
        echo ""
    fi
    
    # 高级数据挖掘分析是可选的
    if [ "${RUN_ADVANCED:-yes}" = "yes" ]; then
        step8_spark_advanced || print_warning "高级数据挖掘分析失败（可选步骤）"
        echo ""
    fi
    
    # 预测模型分析是可选的
    if [ "${RUN_PREDICTION:-yes}" = "yes" ]; then
        step9_spark_prediction || print_warning "预测模型分析失败（可选步骤）"
        echo ""
    fi
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    MINUTES=$((DURATION / 60))
    SECONDS=$((DURATION % 60))
    
    print_header "✅ 全部步骤执行完成！"
    echo "总耗时: ${MINUTES}分${SECONDS}秒"
    echo ""
    echo "验证结果请执行: bash verify.sh"
}

# =============================================
# 显示使用说明
# =============================================
show_usage() {
    cat << EOF

用法: bash run.sh [步骤号]

不带参数: 执行全部步骤 (1-9)
带参数: 执行指定步骤

📋 分层数仓流程（6步骤 + 算法）:
  1 - 上传原始数据到HDFS
  2 - 创建Hive表结构 (ODS/DWD/DWS/ADS)
  3 - 数据清洗 (ODS → DWD) 
       脚本：01_data_clean.py
       输出：3张维度表（用户、图书、借阅明细）
  4 - 数据汇总 (DWD → DWS)
       脚本：02_data_aggregate.py
       输出：5张汇总表
  5 - 数据分析 (DWS → ADS)
       脚本：03_data_analyze.py
       输出：12张分析表
  6 - 导出MySQL (Hive → MySQL)
       脚本：04_data_export.py
       输出：23张表（维度3 + 汇总5 + 聚合5 + 功能10）
  7 - 推荐算法（可选）
       脚本：05_book_recommend.py
       输出：推荐表（ALS协同过滤+内容推荐+热门推荐）
  8 - 高级数据挖掘（可选）
       脚本：06_advanced_analysis.py
       输出：关联规则（FPGrowth）+ 用户聚类（K-means）
  9 - 预测模型（可选）
       脚本：07_prediction_models.py
       输出：逾期风险预测 + 借阅趋势预测 + 图书热度预测

完整数据流程: 
  CSV文件 → HDFS → ODS层 → Spark清洗 → DWD层（明细数据）
  → Spark聚合 → DWS层（汇总统计）→ Spark分析 → ADS层（应用主题）
  → MySQL导出 → 前端展示

注意: 
  - 分区策略: 按year+month双层分区（适合2019-2020历史数据）
  - 完整分层: ODS → DWD → DWS → ADS → MySQL

示例:
  bash run.sh        # 执行全部步骤
  bash run.sh 3      # 只执行步骤3
  bash run.sh 5      # 只执行步骤5

验证:
  bash verify.sh     # 验证所有步骤
  bash verify.sh 3   # 验证步骤3

EOF
}

# =============================================
# 主函数
# =============================================
main() {
    STEP=$1
    
    if [ -z "$STEP" ]; then
        # 不带参数，执行全部步骤
        run_all_steps
    elif [ "$STEP" = "-h" ] || [ "$STEP" = "--help" ]; then
        # 显示帮助
        show_usage
    else
        # 执行指定步骤
        case $STEP in
            1)
                step1_upload_to_hdfs
                ;;
            2)
                step2_create_hive_tables
                ;;
            3)
                step3_spark_clean
                ;;
            4)
                step4_spark_aggregate
                ;;
            5)
                step5_spark_analyze
                ;;
            6)
                step6_export_mysql
                ;;
            7)
                step7_spark_recommend
                ;;
            8)
                step8_spark_advanced
                ;;
            9)
                step9_spark_prediction
                ;;
            *)
                print_error "无效的步骤号: $STEP (有效范围: 1-9)"
                show_usage
                exit 1
                ;;
        esac
        
        if [ $? -eq 0 ]; then
            echo ""
            print_success "✓ 步骤${STEP}执行完成"
            echo "验证结果: bash verify.sh ${STEP}"
        else
            echo ""
            print_error "✗ 步骤${STEP}执行失败"
            exit 1
        fi
    fi
}

main "$@"
