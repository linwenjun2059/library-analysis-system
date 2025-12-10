-- ADS层：应用数据层
CREATE DATABASE IF NOT EXISTS library_ads
COMMENT '图书馆借阅数据-应用数据层'
LOCATION '/user/hive/warehouse/library_ads.db';

USE library_ads;

-- 热门图书TOP100
DROP TABLE IF EXISTS ads_hot_books;

CREATE TABLE IF NOT EXISTS ads_hot_books(
    rank_no INT COMMENT '排名',
    book_id STRING COMMENT '图书ID',
    title STRING COMMENT '图书标题',
    author STRING COMMENT '作者',
    subject STRING COMMENT '主题分类',
    borrow_count BIGINT COMMENT '借阅次数'
)
COMMENT '热门图书TOP100'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 活跃用户TOP100
DROP TABLE IF EXISTS ads_active_users;

CREATE TABLE IF NOT EXISTS ads_active_users(
    rank_no INT COMMENT '排名',
    userid STRING COMMENT '用户ID',
    dept STRING COMMENT '院系',
    redr_type_name STRING COMMENT '读者类型',
    borrow_count BIGINT COMMENT '借阅次数'
)
COMMENT '活跃用户TOP100'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 院系偏好分析
DROP TABLE IF EXISTS ads_dept_preference;

CREATE TABLE IF NOT EXISTS ads_dept_preference(
    dept STRING COMMENT '院系',
    favorite_subject STRING COMMENT '最喜欢的主题',
    subject_lend_count BIGINT COMMENT '主题借阅次数',
    total_lend_count BIGINT COMMENT '总借阅次数',
    preference_rate DOUBLE COMMENT '偏好率'
)
COMMENT '院系偏好分析表'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);
-- 借阅趋势
DROP TABLE IF EXISTS ads_lend_trend;

CREATE TABLE IF NOT EXISTS ads_lend_trend(
    trend_date DATE COMMENT '趋势日期',
    lend_count BIGINT COMMENT '借阅次数',
    return_count BIGINT COMMENT '归还次数',
    active_user_count BIGINT COMMENT '活跃用户数',
    new_user_count BIGINT COMMENT '新增用户数',
    return_user_count BIGINT COMMENT '回流用户数',
    avg_lend_per_user DOUBLE COMMENT '人均借阅次数',
    trend_type STRING COMMENT '趋势类型'
)
COMMENT '借阅趋势表'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 运营看板
DROP TABLE IF EXISTS ads_operation_dashboard;

CREATE TABLE IF NOT EXISTS ads_operation_dashboard(
    metric_name STRING COMMENT '指标名称',
    metric_value DOUBLE COMMENT '指标值',
    compare_yesterday DOUBLE COMMENT '环比昨日',
    compare_last_week DOUBLE COMMENT '环比上周',
    compare_last_month DOUBLE COMMENT '环比上月',
    trend STRING COMMENT '趋势',
    category STRING COMMENT '指标分类'
)
COMMENT '运营看板'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 用户画像分析（高级管理员）
DROP TABLE IF EXISTS ads_user_profile;

CREATE TABLE IF NOT EXISTS ads_user_profile(
    userid STRING COMMENT '用户ID',
    user_type STRING COMMENT '用户类型',
    dept STRING COMMENT '院系',
    occupation STRING COMMENT '专业',
    gender STRING COMMENT '性别',
    age_group STRING COMMENT '年龄段',
    borrow_level STRING COMMENT '借阅等级（活跃/一般/不活跃）',
    total_borrow_count BIGINT COMMENT '总借阅量',
    reading_breadth INT COMMENT '阅读广度（涉及主题数）',
    favorite_subjects ARRAY<STRING> COMMENT '偏好主题TOP3',
    favorite_locations ARRAY<STRING> COMMENT '偏好位置TOP3',
    avg_borrow_days DOUBLE COMMENT '平均借阅天数',
    overdue_rate DOUBLE COMMENT '逾期率',
    last_borrow_date DATE COMMENT '最后借阅日期',
    user_tags ARRAY<STRING> COMMENT '用户标签'
)
COMMENT '用户画像分析表'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 资源优化建议（高级管理员）
DROP TABLE IF EXISTS ads_resource_optimization;

CREATE TABLE IF NOT EXISTS ads_resource_optimization(
    optimization_type STRING COMMENT '优化类型（热门图书/冷门图书/采购建议）',
    book_id STRING COMMENT '图书ID',
    title STRING COMMENT '图书标题',
    author STRING COMMENT '作者',
    subject STRING COMMENT '主题分类',
    borrow_count BIGINT COMMENT '借阅次数',
    last_borrow_date DATE COMMENT '最后借阅日期',
    recommendation STRING COMMENT '优化建议',
    priority INT COMMENT '优先级（1-5）'
)
COMMENT '资源优化建议表'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 专业阅读特征分析（高级管理员）
DROP TABLE IF EXISTS ads_major_reading_profile;

CREATE TABLE IF NOT EXISTS ads_major_reading_profile(
    dept STRING COMMENT '院系',
    occupation STRING COMMENT '专业',
    student_count BIGINT COMMENT '学生数量',
    total_borrow_count BIGINT COMMENT '总借阅量',
    avg_borrow_per_student DOUBLE COMMENT '人均借阅量',
    core_subjects ARRAY<STRING> COMMENT '核心学科TOP5',
    cross_subjects ARRAY<STRING> COMMENT '跨学科借阅TOP3',
    reading_breadth_score DOUBLE COMMENT '阅读广度得分',
    popular_books ARRAY<STRING> COMMENT '热门书目TOP10（书名）'
)
COMMENT '专业阅读特征分析表'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 逾期分析（图书管理员）
DROP TABLE IF EXISTS ads_overdue_analysis;

CREATE TABLE IF NOT EXISTS ads_overdue_analysis(
    analysis_type STRING COMMENT '分析类型（用户/图书/院系）',
    target_id STRING COMMENT '目标ID',
    target_name STRING COMMENT '目标名称',
    overdue_count BIGINT COMMENT '逾期次数',
    total_borrow_count BIGINT COMMENT '总借阅次数',
    overdue_rate DOUBLE COMMENT '逾期率',
    avg_overdue_days DOUBLE COMMENT '平均逾期天数',
    current_overdue_count BIGINT COMMENT '当前逾期数量',
    risk_level STRING COMMENT '风险等级（高/中/低）'
)
COMMENT '逾期分析表'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 馆藏流通率分析（高级管理员）
DROP TABLE IF EXISTS ads_circulation_rate;

CREATE TABLE IF NOT EXISTS ads_circulation_rate(
    dimension_type STRING COMMENT '维度类型（位置/主题/文献类型）',
    dimension_value STRING COMMENT '维度值',
    total_books BIGINT COMMENT '馆藏图书总数',
    borrowed_books BIGINT COMMENT '被借图书数',
    circulation_rate DOUBLE COMMENT '流通率',
    avg_borrow_times DOUBLE COMMENT '平均借阅次数',
    high_demand_books BIGINT COMMENT '高需求图书数（借阅>5次）',
    zero_borrow_books BIGINT COMMENT '零借阅图书数',
    turnover_rate DOUBLE COMMENT '周转率'
)
COMMENT '馆藏流通率分析表'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 时间分布分析（图书管理员）
DROP TABLE IF EXISTS ads_time_distribution;

CREATE TABLE IF NOT EXISTS ads_time_distribution(
    time_type STRING COMMENT '时间类型（小时/星期/月份）',
    time_value INT COMMENT '时间值',
    borrow_count BIGINT COMMENT '借阅次数',
    return_count BIGINT COMMENT '归还次数',
    active_user_count BIGINT COMMENT '活跃用户数',
    percentage DOUBLE COMMENT '占比'
)
COMMENT '时间分布分析表'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 用户排名（按院系/专业）（普通用户）
DROP TABLE IF EXISTS ads_user_ranking;

CREATE TABLE IF NOT EXISTS ads_user_ranking(
    userid STRING COMMENT '用户ID',
    dept STRING COMMENT '院系',
    occupation STRING COMMENT '专业',
    user_type STRING COMMENT '用户类型',
    total_borrow_count BIGINT COMMENT '总借阅量',
    dept_rank INT COMMENT '院系内排名',
    occupation_rank INT COMMENT '专业内排名',
    dept_total_users INT COMMENT '院系总用户数',
    occupation_total_users INT COMMENT '专业总用户数',
    percentile_dept DOUBLE COMMENT '院系百分位',
    percentile_occupation DOUBLE COMMENT '专业百分位'
)
COMMENT '用户排名表（按院系/专业）'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 个性化推荐基础表（普通用户）
DROP TABLE IF EXISTS ads_book_recommend_base;

CREATE TABLE IF NOT EXISTS ads_book_recommend_base(
    recommend_type STRING COMMENT '推荐类型（热门榜/院系榜/专业榜/新书）',
    scope STRING COMMENT '范围（全校/院系名/专业名）',
    book_id STRING COMMENT '图书ID',
    title STRING COMMENT '书名',
    author STRING COMMENT '作者',
    subject STRING COMMENT '主题',
    borrow_count BIGINT COMMENT '借阅次数',
    rank_no INT COMMENT '排名',
    update_date DATE COMMENT '更新日期'
)
COMMENT '图书推荐基础表'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

