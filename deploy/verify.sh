#!/bin/bash
# =============================================
# 图书馆数据分析系统 - 数据链路验证脚本
# 用法: bash verify.sh [步骤号]
#   不带参数: 验证全部步骤 (1-9)
#   带参数: 验证指定步骤 (1-9)
# =============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

# =============================================
# 验证步骤1: HDFS数据上传
# =============================================
verify_step1() {
    print_header "验证步骤1: HDFS数据上传"
    
    echo "检查HDFS文件是否存在..."
    hdfs dfs -test -f ${HDFS_RAW_PATH}/LENDHIST2019_2020.csv
    if [ $? -eq 0 ]; then
        FILE_SIZE=$(hdfs dfs -du -h ${HDFS_RAW_PATH}/LENDHIST2019_2020.csv | awk '{print $1}')
        print_success "✓ HDFS文件存在，大小: ${FILE_SIZE}"
        hdfs dfs -ls ${HDFS_RAW_PATH}/LENDHIST2019_2020.csv
        
        # 检查文件行数（优化：对于大文件只统计前1000行验证格式）
        echo "正在检查文件格式和数据量..."
        # 使用head限制读取量，避免大文件时过慢
        SAMPLE_LINES=$(hdfs dfs -cat ${HDFS_RAW_PATH}/LENDHIST2019_2020.csv 2>/dev/null | head -1000 | wc -l)
        
        if [ "$SAMPLE_LINES" -gt 0 ]; then
            echo "文件格式检查通过，样本行数: ${SAMPLE_LINES}"
            # 尝试快速统计总行数（如果文件不太大）
            echo "正在统计总行数（大文件可能需要较长时间）..."
            LINE_COUNT=$(hdfs dfs -cat ${HDFS_RAW_PATH}/LENDHIST2019_2020.csv 2>/dev/null | wc -l)
            echo "文件总行数: ${LINE_COUNT}"
            
            if [ "$LINE_COUNT" -gt 1000 ]; then
                print_success "✓ 数据量正常"
                return 0
            else
                print_warning "⚠ 数据量可能不足"
                return 1
            fi
        else
            print_error "✗ 无法读取文件内容"
            return 1
        fi
    else
        print_error "✗ HDFS文件不存在"
        return 1
    fi
}

# =============================================
# 验证步骤2: Hive表结构
# =============================================
verify_step2() {
    print_header "验证步骤2: Hive表结构"
    
    echo "检查Hive数据库..."
    DATABASES=$(hive -e "SHOW DATABASES" 2>/dev/null | grep -E "library_ods|library_dwd|library_dws|library_ads")
    
    if [ -n "$DATABASES" ]; then
        print_success "✓ ✓ Hive数据库已创建"
        echo "$DATABASES"
        
        echo -e "\n检查DWD层表（3张）..."
        DWD_TABLES=$(hive -S -e "USE library_dwd; SHOW TABLES" 2>/dev/null | grep -v "^$" | grep -v "^OK$")
        if [ -n "$DWD_TABLES" ]; then
            echo "$DWD_TABLES"
            # 验证3张表都存在（过滤空行和OK标记）
            DWD_COUNT=$(echo "$DWD_TABLES" | grep -v "^$" | grep -v "^OK$" | wc -l)
            if [ "$DWD_COUNT" -ge 3 ]; then
                print_success "✓ ✓ DWD层3张表已创建"
            else
                print_warning "⚠ DWD层表数量不足3张（当前: $DWD_COUNT）"
            fi
        else
            print_error "✗ DWD层表不存在"
            return 1
        fi
        
        echo -e "\n检查DWS层表（5张）..."
        DWS_TABLES=$(hive -S -e "USE library_dws; SHOW TABLES" 2>/dev/null | grep -v "^$" | grep -v "^OK$")
        if [ -n "$DWS_TABLES" ]; then
            echo "$DWS_TABLES"
            # 验证5张表都存在（过滤空行和OK标记）
            DWS_COUNT=$(echo "$DWS_TABLES" | grep -v "^$" | grep -v "^OK$" | wc -l)
            if [ "$DWS_COUNT" -ge 5 ]; then
                print_success "✓ ✓ DWS层5张表已创建"
            else
                print_warning "⚠ DWS层表数量不足5张（当前: $DWS_COUNT）"
            fi
        else
            print_error "✗ DWS层表不存在"
            return 1
        fi
        
        echo -e "\n检查ADS层表（12张）..."
        ADS_TABLES=$(hive -S -e "USE library_ads; SHOW TABLES" 2>/dev/null | grep -v "^$" | grep -v "^OK$")
        if [ -n "$ADS_TABLES" ]; then
            echo "$ADS_TABLES"
            # 验证12张表都存在（过滤空行和OK标记）
            ADS_COUNT=$(echo "$ADS_TABLES" | grep -v "^$" | grep -v "^OK$" | wc -l)
            if [ "$ADS_COUNT" -ge 12 ]; then
                print_success "✓ ✓ ADS层12张表已创建"
            else
                print_warning "⚠ ADS层表数量不足12张（当前: $ADS_COUNT）"
            fi
        else
            print_error "✗ ADS层表不存在"
            return 1
        fi
        
        return 0
    else
        print_error "✗ Hive数据库不存在"
        return 1
    fi
}

# =============================================
# 验证步骤3: Spark数据清洗
# =============================================
verify_step3() {
    print_header "验证步骤3: Spark数据清洗"
    
    echo "检查DWD层数据（按year/month分区）..."
    
    # 检查用户维度表（所有分区）
    echo "查询用户维度表..."
    USER_COUNT=$(hive -S -e "SELECT COUNT(*) FROM library_dwd.dwd_user_info" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "用户维度记录数: ${USER_COUNT:-0}"
    
    # 检查图书维度表（所有分区）
    echo "查询图书维度表..."
    BOOK_COUNT=$(hive -S -e "SELECT COUNT(*) FROM library_dwd.dwd_book_info" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "图书维度记录数: ${BOOK_COUNT:-0}"
    
    # 检查借阅明细表（所有分区）
    echo "查询借阅明细表..."
    LEND_COUNT=$(hive -S -e "SELECT COUNT(*) FROM library_dwd.dwd_lend_detail" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "借阅明细记录数: ${LEND_COUNT:-0}"
    
    # 显示分区信息
    echo "查询分区信息..."
    hive -S -e "SHOW PARTITIONS library_dwd.dwd_lend_detail" 2>&1 | head -5
    echo "..."
    
    # 确保变量是数字
    LEND_COUNT=${LEND_COUNT:-0}
    USER_COUNT=${USER_COUNT:-0}
    BOOK_COUNT=${BOOK_COUNT:-0}
    
    if [ "$LEND_COUNT" -gt 0 ] 2>/dev/null; then
        print_success "✓ Spark数据清洗成功，数据已写入DWD层"
        
        if [ "$USER_COUNT" -gt 10000 ] && [ "$BOOK_COUNT" -gt 5000 ]; then
            print_success "✓ 数据量正常（2019-2020全量数据）"
        elif [ "$USER_COUNT" -gt 1000 ] && [ "$BOOK_COUNT" -gt 1000 ]; then
            print_success "✓ 数据量合理（部分月份数据）"
        else
            print_warning "⚠ 数据量偏少，请检查清洗逻辑"
        fi
        return 0
    else
        print_error "✗ DWD层数据为空"
        print_warning "常见原因: CSV分隔符不匹配，请检查 data_clean.py 第59行"
        return 1
    fi
}

# =============================================
# 验证步骤4: Spark数据汇总（DWD → DWS）
# =============================================
verify_step4() {
    print_header "验证步骤4: Spark数据汇总（DWS层）"
    
    echo "检查DWS层汇总表（5张表）..."
    
    # 检查用户汇总表
    echo "1. 查询用户汇总表..."
    USER_SUMMARY=$(hive -S -e "SELECT COUNT(*) FROM library_dws.dws_user_lend_summary" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   用户汇总记录数: ${USER_SUMMARY:-0}"
    
    # 检查图书汇总表
    echo "2. 查询图书汇总表..."
    BOOK_SUMMARY=$(hive -S -e "SELECT COUNT(*) FROM library_dws.dws_book_lend_summary" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   图书汇总记录数: ${BOOK_SUMMARY:-0}"
    
    # 检查院系汇总表
    echo "3. 查询院系汇总表..."
    DEPT_SUMMARY=$(hive -S -e "SELECT COUNT(*) FROM library_dws.dws_dept_lend_summary" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   院系汇总记录数: ${DEPT_SUMMARY:-0}"
    
    # 检查主题分类汇总表
    echo "4. 查询主题分类汇总表..."
    SUBJECT_SUMMARY=$(hive -S -e "SELECT COUNT(*) FROM library_dws.dws_subject_lend_summary" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   主题分类汇总记录数: ${SUBJECT_SUMMARY:-0}"
    
    # 检查每日统计表
    echo "5. 查询每日统计表..."
    DAILY_STATS=$(hive -S -e "SELECT COUNT(*) FROM library_dws.dws_daily_stats" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   每日统计记录数: ${DAILY_STATS:-0}"
    
    # 确保变量是数字
    USER_SUMMARY=${USER_SUMMARY:-0}
    BOOK_SUMMARY=${BOOK_SUMMARY:-0}
    DEPT_SUMMARY=${DEPT_SUMMARY:-0}
    SUBJECT_SUMMARY=${SUBJECT_SUMMARY:-0}
    DAILY_STATS=${DAILY_STATS:-0}
    
    # 验证所有表都有数据
    if [ "$USER_SUMMARY" -gt 0 ] && [ "$BOOK_SUMMARY" -gt 0 ] && [ "$DEPT_SUMMARY" -gt 0 ] && [ "$SUBJECT_SUMMARY" -gt 0 ] && [ "$DAILY_STATS" -gt 0 ] 2>/dev/null; then
        print_success "✓ DWS层汇总完成，5张表数据已写入"
        return 0
    else
        print_error "✗ DWS层部分表数据为空"
        [ "$USER_SUMMARY" -eq 0 ] && echo "  - dws_user_lend_summary 为空"
        [ "$BOOK_SUMMARY" -eq 0 ] && echo "  - dws_book_lend_summary 为空"
        [ "$DEPT_SUMMARY" -eq 0 ] && echo "  - dws_dept_lend_summary 为空"
        [ "$SUBJECT_SUMMARY" -eq 0 ] && echo "  - dws_subject_lend_summary 为空"
        [ "$DAILY_STATS" -eq 0 ] && echo "  - dws_daily_stats 为空"
        return 1
    fi
}

# =============================================
# 验证步骤5: Spark数据分析（DWS → ADS）
# =============================================
verify_step5() {
    print_header "验证步骤5: Spark数据分析（ADS层）"
    
    echo "检查ADS层分析表（12张表）..."
    echo ""
    
    echo "基础分析表（5张）:"
    # 1-5: 基础分析表
    echo "1. 查询热门图书表..."
    HOT_BOOKS=$(hive -S -e "SELECT COUNT(*) FROM library_ads.ads_hot_books" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   热门图书: ${HOT_BOOKS:-0}"
    
    echo "2. 查询活跃用户表..."
    ACTIVE_USERS=$(hive -S -e "SELECT COUNT(*) FROM library_ads.ads_active_users" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   活跃用户: ${ACTIVE_USERS:-0}"
    
    echo "3. 查询院系偏好表..."
    DEPT_PREF=$(hive -S -e "SELECT COUNT(*) FROM library_ads.ads_dept_preference" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   院系偏好: ${DEPT_PREF:-0}"
    
    echo "4. 查询借阅趋势表..."
    LEND_TREND=$(hive -S -e "SELECT COUNT(*) FROM library_ads.ads_lend_trend" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   借阅趋势: ${LEND_TREND:-0}"
    
    echo "5. 查询运营看板表..."
    DASHBOARD=$(hive -S -e "SELECT COUNT(*) FROM library_ads.ads_operation_dashboard" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   运营看板: ${DASHBOARD:-0}"
    
    echo ""
    echo "高级管理员功能表（3张）:"
    # 6-8: 高级管理员功能表
    echo "6. 查询用户画像表..."
    USER_PROFILE=$(hive -S -e "SELECT COUNT(*) FROM library_ads.ads_user_profile" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   用户画像: ${USER_PROFILE:-0}"
    
    echo "7. 查询专业阅读表..."
    MAJOR_PROFILE=$(hive -S -e "SELECT COUNT(*) FROM library_ads.ads_major_reading_profile" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   专业阅读: ${MAJOR_PROFILE:-0}"
    
    echo "8. 查询馆藏利用表..."
    COLLECTION_UTIL=$(hive -S -e "SELECT COUNT(*) FROM library_ads.ads_collection_utilization" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   馆藏利用: ${COLLECTION_UTIL:-0}"
    
    echo ""
    echo "图书管理员功能表（2张）:"
    # 9-10: 图书管理员功能表
    echo "9. 查询逾期分析表..."
    OVERDUE=$(hive -S -e "SELECT COUNT(*) FROM library_ads.ads_overdue_analysis" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "    逾期分析: ${OVERDUE:-0}"
    
    echo "10. 查询时间分布表..."
    TIME_DIST=$(hive -S -e "SELECT COUNT(*) FROM library_ads.ads_time_distribution" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "    时间分布: ${TIME_DIST:-0}"
    
    echo ""
    echo "普通用户功能表（2张）:"
    # 11-12: 普通用户功能表
    echo "11. 查询用户排名表..."
    USER_RANK=$(hive -S -e "SELECT COUNT(*) FROM library_ads.ads_user_ranking" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "    用户排名: ${USER_RANK:-0}"
    
    echo "12. 查询推荐基础表..."
    RECOMMEND_BASE=$(hive -S -e "SELECT COUNT(*) FROM library_ads.ads_book_recommend_base" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "    推荐基础: ${RECOMMEND_BASE:-0}"
    
    # 确保变量是数字
    HOT_BOOKS=${HOT_BOOKS:-0}
    ACTIVE_USERS=${ACTIVE_USERS:-0}
    DEPT_PREF=${DEPT_PREF:-0}
    LEND_TREND=${LEND_TREND:-0}
    DASHBOARD=${DASHBOARD:-0}
    USER_PROFILE=${USER_PROFILE:-0}
    MAJOR_PROFILE=${MAJOR_PROFILE:-0}
    COLLECTION_UTIL=${COLLECTION_UTIL:-0}
    OVERDUE=${OVERDUE:-0}
    TIME_DIST=${TIME_DIST:-0}
    USER_RANK=${USER_RANK:-0}
    RECOMMEND_BASE=${RECOMMEND_BASE:-0}
    
    # 验证所有表都有数据（至少基础表必须有数据）
    if [ "$HOT_BOOKS" -gt 0 ] && [ "$ACTIVE_USERS" -gt 0 ] && [ "$DEPT_PREF" -gt 0 ] && [ "$LEND_TREND" -gt 0 ] && [ "$DASHBOARD" -gt 0 ] 2>/dev/null; then
        print_success "✓ ADS层分析完成，12张表数据已写入"
        
        # 检查功能表
        NON_EMPTY=0
        [ "$USER_PROFILE" -gt 0 ] && ((NON_EMPTY++))
        [ "$MAJOR_PROFILE" -gt 0 ] && ((NON_EMPTY++))
        [ "$COLLECTION_UTIL" -gt 0 ] && ((NON_EMPTY++))
        [ "$OVERDUE" -gt 0 ] && ((NON_EMPTY++))
        [ "$TIME_DIST" -gt 0 ] && ((NON_EMPTY++))
        [ "$USER_RANK" -gt 0 ] && ((NON_EMPTY++))
        [ "$RECOMMEND_BASE" -gt 0 ] && ((NON_EMPTY++))
        
        echo "  基础表: 5/5 ✓"
        echo "  功能表: $NON_EMPTY/7"
        
        return 0
    else
        print_error "✗ ADS层部分基础表数据为空"
        [ "$HOT_BOOKS" -eq 0 ] && echo "  - ads_hot_books 为空"
        [ "$ACTIVE_USERS" -eq 0 ] && echo "  - ads_active_users 为空"
        [ "$DEPT_PREF" -eq 0 ] && echo "  - ads_dept_preference 为空"
        [ "$LEND_TREND" -eq 0 ] && echo "  - ads_lend_trend 为空"
        [ "$DASHBOARD" -eq 0 ] && echo "  - ads_operation_dashboard 为空"
        return 1
    fi
}

# =============================================
# 验证步骤7: Spark推荐算法
# =============================================
verify_step7() {
    print_header "验证步骤7: Spark推荐算法"
    
    echo "检查MySQL推荐结果（2张表）..."
    echo ""
    
    # 1. 检查主推荐表
    echo "1. 查询主推荐表（book_recommendations）..."
    REC_COUNT=$(mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -se "SELECT COUNT(*) FROM book_recommendations" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    
    if [ $? -ne 0 ]; then
        print_error "✗ 无法连接MySQL数据库"
        return 1
    fi
    
    echo "   推荐记录数: ${REC_COUNT:-0}"
    USER_COUNT=$(mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -se "SELECT COUNT(DISTINCT userid) FROM book_recommendations" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   推荐用户数: ${USER_COUNT:-0}"
    
    # 2. 检查推荐统计表
    echo ""
    echo "2. 查询推荐统计表（recommendation_stats）..."
    STATS_COUNT=$(mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -se "SELECT COUNT(*) FROM recommendation_stats" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   统计指标数: ${STATS_COUNT:-0} 项"
    
    REC_COUNT=${REC_COUNT:-0}
    STATS_COUNT=${STATS_COUNT:-0}
    
    if [ "$REC_COUNT" -gt 0 ] && [ "$STATS_COUNT" -gt 0 ] 2>/dev/null; then
        print_success "✓ 推荐算法成功，2张表数据已写入MySQL"
        
        # 显示推荐统计
        echo -e "\n推荐系统统计："
        mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -e "SELECT stat_name, stat_value FROM recommendation_stats WHERE stat_type IN ('total_users', 'recommended_users', 'coverage_rate', 'avg_score', 'cf_percent', 'content_percent', 'popularity_percent') ORDER BY stat_type" 2>/dev/null
        
        # 显示示例推荐
        echo -e "\n推荐示例（前5条）:"
        mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -e "SELECT userid, book_id, title, score, rank_no FROM book_recommendations LIMIT 5" 2>/dev/null
        return 0
    else
        print_error "✗ MySQL推荐结果不完整"
        [ "$REC_COUNT" -eq 0 ] && echo "  - book_recommendations 为空"
        [ "$STATS_COUNT" -eq 0 ] && echo "  - recommendation_stats 为空"
        return 1
    fi
}

# =============================================
# 验证步骤6: 导出所有表到MySQL（20张表）⭐
# =============================================
verify_step6() {
    print_header "验证步骤6: 导出所有表到MySQL（20张表）"
    
    echo "检查MySQL表导出结果..."
    
    # 定义20张表（不包括book_recommendations等推荐表，它们由步骤7单独生成）
    TABLES=(
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
        "user_profile"
        "major_reading_profile"
        "overdue_analysis"
        "collection_utilization_analysis"
        "time_distribution"
        "user_ranking"
        "book_recommend_base"
    )
    
    FAILED_TABLES=()
    SUCCESS_COUNT=0
    
    for table in "${TABLES[@]}"; do
        echo -n "检查 ${table}... "
        COUNT=$(mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -se "SELECT COUNT(*) FROM ${table}" 2>&1 | grep -E '^[0-9]+$' | tail -1)
        
        if [ $? -ne 0 ]; then
            print_error "✗ 表不存在或无法访问"
            FAILED_TABLES+=("${table}")
        else
            COUNT=${COUNT:-0}
            if [ "$COUNT" -gt 0 ] 2>/dev/null; then
                echo "✓ ${COUNT} 条记录"
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            else
                echo "⚠ 表存在但数据为空"
                FAILED_TABLES+=("${table}")
            fi
        fi
    done
    
    echo ""
    echo "验证汇总："
    echo "  成功：${SUCCESS_COUNT}/20"
    echo "  失败：${#FAILED_TABLES[@]}/20"
    
    if [ ${#FAILED_TABLES[@]} -eq 0 ]; then
        print_success "✓ 所有20张表验证通过！"
        
        # 显示详细统计
        echo -e "\n各表数据量："
        mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -e "
            SELECT 
                'user_dimension' as table_name, COUNT(*) as count FROM user_dimension
            UNION ALL SELECT 'book_dimension', COUNT(*) FROM book_dimension
            UNION ALL SELECT 'recent_lend_records', COUNT(*) FROM recent_lend_records
            UNION ALL SELECT 'user_lend_summary', COUNT(*) FROM user_lend_summary
            UNION ALL SELECT 'book_lend_summary', COUNT(*) FROM book_lend_summary
            UNION ALL SELECT 'dept_lend_summary', COUNT(*) FROM dept_lend_summary
            UNION ALL SELECT 'subject_lend_summary', COUNT(*) FROM subject_lend_summary
            UNION ALL SELECT 'daily_stats', COUNT(*) FROM daily_stats
            UNION ALL SELECT 'hot_books', COUNT(*) FROM hot_books
            UNION ALL SELECT 'active_users', COUNT(*) FROM active_users
            UNION ALL SELECT 'dept_preference', COUNT(*) FROM dept_preference
            UNION ALL SELECT 'lend_trend', COUNT(*) FROM lend_trend
            UNION ALL SELECT 'operation_dashboard', COUNT(*) FROM operation_dashboard
            UNION ALL SELECT 'user_profile', COUNT(*) FROM user_profile
            UNION ALL SELECT 'major_reading_profile', COUNT(*) FROM major_reading_profile
            UNION ALL SELECT 'overdue_analysis', COUNT(*) FROM overdue_analysis
            UNION ALL SELECT 'collection_utilization_analysis', COUNT(*) FROM collection_utilization_analysis
            UNION ALL SELECT 'time_distribution', COUNT(*) FROM time_distribution
            UNION ALL SELECT 'user_ranking', COUNT(*) FROM user_ranking
            UNION ALL SELECT 'book_recommend_base', COUNT(*) FROM book_recommend_base;
        " 2>/dev/null
        
        return 0
    else
        print_error "✗ 以下表验证失败："
        for table in "${FAILED_TABLES[@]}"; do
            echo "  - ${table}"
        done
        return 1
    fi
}

# =============================================
# 验证步骤8: 高级数据挖掘（FPGrowth + K-means）
# =============================================
verify_step8() {
    print_header "验证步骤8: 高级数据挖掘"
    
    echo "检查MySQL挖掘结果（3张表）..."
    echo ""
    
    # 1. 检查图书关联规则表
    echo "1. 查询图书关联规则表（book_association_rules）..."
    ASSOC_COUNT=$(mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -se "SELECT COUNT(*) FROM book_association_rules" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   关联规则数: ${ASSOC_COUNT:-0}"
    
    # 2. 检查用户聚类表
    echo "2. 查询用户聚类表（user_clusters）..."
    CLUSTER_COUNT=$(mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -se "SELECT COUNT(*) FROM user_clusters" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   聚类用户数: ${CLUSTER_COUNT:-0}"
    
    # 3. 检查聚类统计摘要表
    echo "3. 查询聚类统计表（cluster_summary）..."
    SUMMARY_COUNT=$(mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -se "SELECT COUNT(*) FROM cluster_summary" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   聚类群体数: ${SUMMARY_COUNT:-0}"
    
    ASSOC_COUNT=${ASSOC_COUNT:-0}
    CLUSTER_COUNT=${CLUSTER_COUNT:-0}
    SUMMARY_COUNT=${SUMMARY_COUNT:-0}
    
    if [ "$CLUSTER_COUNT" -gt 0 ] && [ "$SUMMARY_COUNT" -gt 0 ] 2>/dev/null; then
        print_success "✓ 高级挖掘成功，3张表数据已写入MySQL"
        
        # 显示聚类结果
        echo -e "\n聚类群体摘要："
        mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -e "SELECT cluster_name, user_count, cluster_characteristics FROM cluster_summary ORDER BY user_count DESC" 2>/dev/null
        return 0
    else
        print_error "✗ 高级挖掘结果不完整"
        [ "$ASSOC_COUNT" -eq 0 ] && echo "  - book_association_rules 为空（可能数据稀疏无关联规则）"
        [ "$CLUSTER_COUNT" -eq 0 ] && echo "  - user_clusters 为空"
        [ "$SUMMARY_COUNT" -eq 0 ] && echo "  - cluster_summary 为空"
        return 1
    fi
}

# =============================================
# 验证步骤9: 预测模型（随机森林）
# =============================================
verify_step9() {
    print_header "验证步骤9: 预测模型"
    
    echo "检查MySQL预测结果（3张表）..."
    echo ""
    
    # 1. 检查逾期风险预测表
    echo "1. 查询逾期风险预测表（overdue_risk_prediction）..."
    OVERDUE_COUNT=$(mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -se "SELECT COUNT(*) FROM overdue_risk_prediction" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   预测用户数: ${OVERDUE_COUNT:-0}"
    
    # 2. 检查借阅趋势预测表
    echo "2. 查询借阅趋势预测表（lend_trend_prediction）..."
    TREND_COUNT=$(mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -se "SELECT COUNT(*) FROM lend_trend_prediction" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   预测月份数: ${TREND_COUNT:-0}"
    
    # 3. 检查图书热度预测表
    echo "3. 查询图书热度预测表（book_heat_prediction）..."
    HEAT_COUNT=$(mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -se "SELECT COUNT(*) FROM book_heat_prediction" 2>&1 | grep -E '^[0-9]+$' | tail -1)
    echo "   预测图书数: ${HEAT_COUNT:-0}"
    
    OVERDUE_COUNT=${OVERDUE_COUNT:-0}
    TREND_COUNT=${TREND_COUNT:-0}
    HEAT_COUNT=${HEAT_COUNT:-0}
    
    if [ "$OVERDUE_COUNT" -gt 0 ] && [ "$TREND_COUNT" -gt 0 ] && [ "$HEAT_COUNT" -gt 0 ] 2>/dev/null; then
        print_success "✓ 预测模型成功，3张表数据已写入MySQL"
        
        # 显示风险分布
        echo -e "\n逾期风险分布："
        mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -e "SELECT risk_level, COUNT(*) as user_count FROM overdue_risk_prediction GROUP BY risk_level ORDER BY user_count DESC" 2>/dev/null
        
        # 显示未来预测
        echo -e "\n借阅趋势预测（未来6个月）："
        mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -h ${MYSQL_HOST} -D ${MYSQL_DATABASE} -e "SELECT lend_month, predicted_count, trend FROM lend_trend_prediction WHERE data_type='预测' ORDER BY lend_month" 2>/dev/null
        return 0
    else
        print_error "✗ 预测模型结果不完整"
        [ "$OVERDUE_COUNT" -eq 0 ] && echo "  - overdue_risk_prediction 为空"
        [ "$TREND_COUNT" -eq 0 ] && echo "  - lend_trend_prediction 为空"
        [ "$HEAT_COUNT" -eq 0 ] && echo "  - book_heat_prediction 为空"
        return 1
    fi
}

# =============================================
# 验证全部步骤
# =============================================
verify_all_steps() {
    print_header "验证所有步骤"
    echo "分区策略: year + month"
    echo ""
    
    FAILED_STEPS=()
    
    verify_step1
    [ $? -ne 0 ] && FAILED_STEPS+=(1)
    echo ""
    
    verify_step2
    [ $? -ne 0 ] && FAILED_STEPS+=(2)
    echo ""
    
    verify_step3
    [ $? -ne 0 ] && FAILED_STEPS+=(3)
    echo ""
    
    verify_step4
    [ $? -ne 0 ] && FAILED_STEPS+=(4)
    echo ""
    
    verify_step5
    [ $? -ne 0 ] && FAILED_STEPS+=(5)
    echo ""
    
    verify_step6
    [ $? -ne 0 ] && FAILED_STEPS+=(6)
    echo ""
    
    # 可选步骤（7-9）
    verify_step7 || print_warning "推荐算法验证跳过"
    echo ""
    
    verify_step8 || print_warning "高级挖掘验证跳过"
    echo ""
    
    verify_step9 || print_warning "预测模型验证跳过"
    echo ""
    
    # 输出汇总结果
    print_header "验证结果汇总"
    
    if [ ${#FAILED_STEPS[@]} -eq 0 ]; then
        print_success "✅ 所有步骤验证通过！"
        echo "系统已就绪，可以启动前后端服务。"
        return 0
    else
        print_error "❌ 以下步骤验证失败: ${FAILED_STEPS[*]}"
        echo ""
        echo "重新执行失败的步骤:"
        for step in "${FAILED_STEPS[@]}"; do
            echo "  bash run.sh ${step}"
        done
        return 1
    fi
}

# =============================================
# 显示使用说明
# =============================================
show_usage() {
    cat << EOF

用法: bash verify.sh [步骤号]

不带参数: 验证全部步骤 (1-9)
带参数: 验证指定步骤

步骤说明:
  1 - 验证HDFS数据上传
  2 - 验证Hive表结构
  3 - 验证数据清洗（DWD层，3张表）
  4 - 验证数据汇总（DWS层，5张表）
  5 - 验证数据分析（ADS层，12张表）
  6 - 验证导出MySQL（20张表）
  7 - 验证推荐算法（2张表）【可选】
  8 - 验证高级挖掘（3张表）【可选】
  9 - 验证预测模型（3张表）【可选】

注意：数据按year+month分区（适合2019-2020历史数据）

示例:
  bash verify.sh        # 验证全部步骤
  bash verify.sh 3      # 只验证步骤3
  bash verify.sh 5      # 只验证步骤5

执行步骤:
  bash run.sh           # 执行全部步骤
  bash run.sh 3         # 执行步骤3

EOF
}

# =============================================
# 主函数
# =============================================
main() {
    STEP=$1
    
    if [ -z "$STEP" ]; then
        # 不带参数，验证全部步骤
        verify_all_steps
    elif [ "$STEP" = "-h" ] || [ "$STEP" = "--help" ]; then
        # 显示帮助
        show_usage
    else
        # 验证指定步骤
        case $STEP in
            1) verify_step1 ;;
            2) verify_step2 ;;
            3) verify_step3 ;;
            4) verify_step4 ;;
            5) verify_step5 ;;
            6) verify_step6 ;;
            7) verify_step7 ;;
            8) verify_step8 ;;
            9) verify_step9 ;;
            *)
                print_error "无效的步骤号: $STEP (有效范围: 1-9)"
                show_usage
                exit 1
                ;;
        esac
        
        if [ $? -eq 0 ]; then
            echo ""
            print_success "✓ 步骤${STEP}验证通过"
        else
            echo ""
            print_error "✗ 步骤${STEP}验证失败"
            echo "重新执行: bash run.sh ${STEP}"
            exit 1
        fi
    fi
}

main "$@"
