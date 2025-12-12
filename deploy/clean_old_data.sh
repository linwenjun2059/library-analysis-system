#!/bin/bash
# =============================================
# 清理旧数据脚本 - 删除旧分区数据，准备重新执行
# 用法: bash clean_old_data.sh
# 
# ⚠️  重要说明：
# 1. 如果每次都完整运行 run.sh，此脚本通常是多余的
#    - run.sh 步骤2会 DROP TABLE（清理Hive表）
#    - run.sh 步骤6-9使用 mode("overwrite")（覆盖MySQL数据）
# 
# 2. 此脚本适用于以下场景：
#    - 只想清理数据，不重新创建表结构
#    - 单独清理MySQL，不运行整个流程
#    - 故障恢复：某个步骤失败后，手动清理重试
#    - 清理旧分区数据（部分清理）
# =============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

echo "========================================"
echo "清理旧数据（保留HDFS原始文件）"
echo "========================================"
echo ""
echo "⚠️  警告：此操作将删除以下数据："
echo "  1. Hive DWD层 - 3张明细表"
echo "  2. Hive DWS层 - 5张汇总表"
echo "  3. Hive ADS层 - 12张分析表"
echo "  4. MySQL数据 - 28张表数据（不包括sys_user系统表）"
echo ""
echo "✅ 保留以下数据（不会删除）："
echo "  - HDFS原始CSV文件（${HDFS_RAW_PATH}）"
echo "  - Hive ODS层表结构"
echo "  - MySQL系统表 (sys_user)"
echo ""
echo "💡 提示："
echo "  - 如果每次都完整运行 run.sh，此脚本通常是多余的"
echo "  - run.sh 会自动清理并重建所有表"
echo "  - 此脚本主要用于：只清理数据、故障恢复、部分清理"
echo ""
read -p "确定要清理吗？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "已取消清理"
    exit 0
fi

echo ""
echo "开始清理..."
echo ""

# 全局统计变量
TOTAL_SUCCESS=0
TOTAL_FAILED=0

# =============================================
# 1. 清理Hive DWD层数据（3张表）
# 注意：run.sh 步骤2会 DROP TABLE，这里清理是多余的
# 但保留用于：只清理数据不重建表结构的场景
# =============================================
echo "🔷 [1/4] 清理DWD层数据（3张表）..."

DWD_TABLES=("dwd_user_info" "dwd_book_info" "dwd_lend_detail")
DWD_SUCCESS=0
DWD_FAILED=0

for table in "${DWD_TABLES[@]}"; do
    # 先检查表是否存在
    TABLE_EXISTS=$(hive -S -e "USE library_dwd; SHOW TABLES LIKE '${table}';" 2>/dev/null)
    
    if [ -n "$TABLE_EXISTS" ]; then
        # 表存在，尝试删除
        hive -S -e "USE library_dwd; DROP TABLE ${table};" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  ✓ ${table}"
            ((DWD_SUCCESS++))
            ((TOTAL_SUCCESS++))
        else
            echo "  ✗ ${table} (删除失败)"
            ((DWD_FAILED++))
            ((TOTAL_FAILED++))
        fi
    else
        echo "  - ${table} (表不存在，跳过)"
    fi
done

echo ""
echo "  DWD层清理结果: 成功 ${DWD_SUCCESS}/3, 失败 ${DWD_FAILED}/3"

# =============================================
# 2. 清理Hive DWS层数据（5张表）
# 注意：run.sh 步骤2会 DROP TABLE，这里清理是多余的
# =============================================
echo ""
echo "🔷 [2/4] 清理DWS层数据（5张表）..."

DWS_TABLES=("dws_user_lend_summary" "dws_book_lend_summary" "dws_dept_lend_summary" "dws_subject_lend_summary" "dws_daily_stats")
DWS_SUCCESS=0
DWS_FAILED=0

for table in "${DWS_TABLES[@]}"; do
    TABLE_EXISTS=$(hive -S -e "USE library_dws; SHOW TABLES LIKE '${table}';" 2>/dev/null)
    
    if [ -n "$TABLE_EXISTS" ]; then
        hive -S -e "USE library_dws; DROP TABLE ${table};" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  ✓ ${table}"
            ((DWS_SUCCESS++))
            ((TOTAL_SUCCESS++))
        else
            echo "  ✗ ${table} (删除失败)"
            ((DWS_FAILED++))
            ((TOTAL_FAILED++))
        fi
    else
        echo "  - ${table} (表不存在，跳过)"
    fi
done

# 清理旧表（兼容）
OLD_TABLES=("dws_user_lend_stat_daily" "dws_book_lend_stat_daily" "dws_dept_lend_stat_daily" "dws_subject_lend_stat_daily" "dws_time_lend_stat_daily")
for table in "${OLD_TABLES[@]}"; do
    TABLE_EXISTS=$(hive -S -e "USE library_dws; SHOW TABLES LIKE '${table}';" 2>/dev/null)
    if [ -n "$TABLE_EXISTS" ]; then
        hive -S -e "USE library_dws; DROP TABLE ${table};" 2>/dev/null
        echo "  ✓ ${table} (旧表)"
    fi
done

echo ""
echo "  DWS层清理结果: 成功 ${DWS_SUCCESS}/5, 失败 ${DWS_FAILED}/5"

# =============================================
# 3. 清理Hive ADS层数据（12张表）
# 注意：run.sh 步骤2会 DROP TABLE，这里清理是多余的
# =============================================
echo ""
echo "🔷 [3/4] 清理ADS层数据（12张表）..."

ADS_TABLES=(
    "ads_hot_books" "ads_active_users" "ads_dept_preference" "ads_lend_trend" "ads_operation_dashboard"
    "ads_user_profile" "ads_major_reading_profile" "ads_collection_utilization"
    "ads_overdue_analysis" "ads_time_distribution"
    "ads_user_ranking" "ads_book_recommend_base"
)
ADS_SUCCESS=0
ADS_FAILED=0

for table in "${ADS_TABLES[@]}"; do
    TABLE_EXISTS=$(hive -S -e "USE library_ads; SHOW TABLES LIKE '${table}';" 2>/dev/null)
    
    if [ -n "$TABLE_EXISTS" ]; then
        hive -S -e "USE library_ads; DROP TABLE ${table};" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  ✓ ${table}"
            ((ADS_SUCCESS++))
            ((TOTAL_SUCCESS++))
        else
            echo "  ✗ ${table} (删除失败)"
            ((ADS_FAILED++))
            ((TOTAL_FAILED++))
        fi
    else
        echo "  - ${table} (表不存在，跳过)"
    fi
done

# 清理旧表（兼容）
OLD_ADS_TABLES=("ads_book_recommendation" "ads_data_quality_report")
for table in "${OLD_ADS_TABLES[@]}"; do
    TABLE_EXISTS=$(hive -S -e "USE library_ads; SHOW TABLES LIKE '${table}';" 2>/dev/null)
    if [ -n "$TABLE_EXISTS" ]; then
        hive -S -e "USE library_ads; DROP TABLE ${table};" 2>/dev/null
        echo "  ✓ ${table} (旧表)"
    fi
done

echo ""
echo "  ADS层清理结果: 成功 ${ADS_SUCCESS}/12, 失败 ${ADS_FAILED}/12"

# =============================================
# 4. 清理MySQL数据（28张表，不包括sys_user系统表）
# 注意：run.sh 步骤6-9使用 mode("overwrite") 会覆盖数据
# 但此脚本的TRUNCATE更彻底，适用于故障恢复场景
# =============================================
echo ""
echo "🔷 [4/4] 清理MySQL数据（28张表，不包括sys_user系统表）..."

MYSQL_SUCCESS=0
MYSQL_FAILED=0
MYSQL_SKIPPED=0

# 先测试MySQL连接
mysql -u${MYSQL_USER} -p${MYSQL_PASSWORD} -h${MYSQL_HOST} -e "SELECT 1;" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "  ❌ MySQL连接失败！"
    echo "     主机: ${MYSQL_HOST}"
    echo "     用户: ${MYSQL_USER}"
    echo ""
    echo "  ⚠ 跳过MySQL清理（连接失败）"
    MYSQL_SKIPPED=28
else
    MYSQL_TABLES=(
        "user_dimension"
        "book_dimension"
        "recent_lend_records"
        "user_lend_summary"
        "book_lend_summary"
        "dept_lend_summary"
        "subject_lend_summary"
        "daily_stats"
        "hot_books"
        "active_users"
        "dept_preference"
        "lend_trend"
        "operation_dashboard"
        "book_recommendations"
        "recommendation_stats"
        "user_profile"
        "major_reading_profile"
        "overdue_analysis"
        "collection_utilization_analysis"
        "time_distribution"
        "user_ranking"
        "book_recommend_base"
        "book_association_rules"
        "user_clusters"
        "cluster_summary"
        "overdue_risk_prediction"
        "lend_trend_prediction"
        "book_heat_prediction"
    )
    
    for table in "${MYSQL_TABLES[@]}"; do
        mysql -u${MYSQL_USER} -p${MYSQL_PASSWORD} -h${MYSQL_HOST} -D${MYSQL_DATABASE} -e "TRUNCATE TABLE ${table};" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  ✓ ${table}"
            ((MYSQL_SUCCESS++))
            ((TOTAL_SUCCESS++))
        else
            echo "  ✗ ${table} (表不存在或无权限)"
            ((MYSQL_FAILED++))
            ((TOTAL_FAILED++))
        fi
    done
    
    echo ""
    echo "  MySQL清理结果: 成功 ${MYSQL_SUCCESS}/28, 失败 ${MYSQL_FAILED}/28"
fi

echo ""
echo "========================================"
echo " 清理汇总报告"
echo "========================================"
echo ""
echo " Hive层清理结果："
echo "  DWD层: 成功 ${DWD_SUCCESS}/3, 失败 ${DWD_FAILED}/3"
echo "  DWS层: 成功 ${DWS_SUCCESS}/5, 失败 ${DWS_FAILED}/5"
echo "  ADS层: 成功 ${ADS_SUCCESS}/12, 失败 ${ADS_FAILED}/12"
echo ""
echo "  MySQL清理结果："
if [ $MYSQL_SKIPPED -gt 0 ]; then
    echo "  MySQL: 跳过 ${MYSQL_SKIPPED}/28 (连接失败)"
else
    echo "  MySQL: 成功 ${MYSQL_SUCCESS}/28, 失败 ${MYSQL_FAILED}/28"
fi
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TOTAL_TABLES=48  # 3 + 5 + 12 + 28 (不包括sys_user系统表)
echo "📈 总计: ✓ 成功 ${TOTAL_SUCCESS}/${TOTAL_TABLES}, ✗ 失败 ${TOTAL_FAILED}/${TOTAL_TABLES}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 失败原因分析
if [ $TOTAL_FAILED -gt 0 ] || [ $MYSQL_SKIPPED -gt 0 ]; then
    echo "⚠️  失败原因分析："
    echo ""
    
    if [ $DWD_FAILED -gt 0 ] || [ $DWS_FAILED -gt 0 ] || [ $ADS_FAILED -gt 0 ]; then
        echo "📌 Hive表删除失败可能原因："
        echo "  1. 表正在被其他进程使用（例如正在运行Spark任务）"
        echo "  2. Hive Metastore服务异常"
        echo "  3. HDFS权限不足，无法删除数据文件"
        echo "  4. 表文件已损坏或元数据不一致"
        echo ""
        echo "  解决方案："
        echo "  • 停止所有Spark任务后重试"
        echo "  • 检查Hive Metastore服务: hive --service metastore status"
        echo "  • 手动删除HDFS数据: hdfs dfs -rm -r /user/hive/warehouse/library_xxx.db/"
        echo ""
    fi
    
    if [ $MYSQL_FAILED -gt 0 ]; then
        echo "📌 MySQL表清理失败可能原因："
        echo "  1. 表不存在（未初始化数据库）"
        echo "  2. 用户权限不足，无法执行TRUNCATE"
        echo "  3. 表被锁定（有其他查询正在执行）"
        echo "  4. 存储引擎异常"
        echo ""
        echo "  解决方案："
        echo "  • 初始化数据库: mysql -u${MYSQL_USER} -p${MYSQL_PASSWORD} < bigdata/mysql/init_mysql.sql"
        echo "  • 检查用户权限: GRANT ALL ON library_analysis.* TO '${MYSQL_USER}'@'%';"
        echo "  • 查看锁: SHOW PROCESSLIST; (然后 KILL 阻塞的查询)"
        echo ""
    fi
    
    if [ $MYSQL_SKIPPED -gt 0 ]; then
        echo "📌 MySQL连接失败可能原因："
        echo "  1. MySQL服务未启动"
        echo "  2. 网络不通或防火墙阻止"
        echo "  3. 用户名或密码错误"
        echo "  4. 数据库不存在"
        echo ""
        echo "  解决方案："
        echo "  • 启动MySQL: systemctl start mysqld"
        echo "  • 测试连接: mysql -u${MYSQL_USER} -p${MYSQL_PASSWORD} -h${MYSQL_HOST} -e 'SELECT 1;'"
        echo "  • 创建数据库: CREATE DATABASE IF NOT EXISTS library_analysis;"
        echo ""
    fi
fi

echo "📦 已保留数据："
echo "  ✓ HDFS原始CSV文件 (${HDFS_RAW_PATH})"
echo "  ✓ Hive ODS层表结构"
echo "  ✓ MySQL系统表 (sys_user)"
echo ""

if [ $TOTAL_FAILED -eq 0 ] && [ $MYSQL_SKIPPED -eq 0 ]; then
    echo "✅ 清理完全成功！可以重新执行数据流程"
    echo ""
    echo "📌 后续操作（从步骤2开始）："
    echo "  bash run.sh 2  # 创建Hive表"
    echo "  bash run.sh 3  # 数据清洗（ODS→DWD）"
    echo "  bash run.sh 4  # 数据汇总（DWD→DWS）"
    echo "  bash run.sh 5  # 数据分析（DWS→ADS）"
    echo "  bash run.sh 6  # 导出MySQL（Hive→MySQL）"
    echo "  bash run.sh 7  # 推荐算法【可选】"
    echo "  bash run.sh 8  # 高级挖掘【可选】"
    echo "  bash run.sh 9  # 预测模型【可选】"
    echo ""
    echo "或者一键执行: bash run.sh"
    echo ""
    echo "💡 提示：如果每次都完整运行 run.sh，通常不需要此清理脚本"
    echo "   run.sh 会自动清理并重建所有表"
else
    echo "⚠️  部分清理失败，请解决上述问题后重试"
    echo ""
    echo "  重新清理: bash clean_old_data.sh"
fi
echo ""
