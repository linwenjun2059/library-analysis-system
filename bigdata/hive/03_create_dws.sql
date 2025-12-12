-- DWS层：汇总数据层
CREATE DATABASE IF NOT EXISTS library_dws
COMMENT '图书馆借阅数据-汇总数据层'
LOCATION '/user/hive/warehouse/library_dws.db';

USE library_dws;

-- 用户借阅汇总表
DROP TABLE IF EXISTS dws_user_lend_summary;

CREATE TABLE IF NOT EXISTS dws_user_lend_summary(
    userid STRING COMMENT '用户ID',
    total_lend_count BIGINT COMMENT '总借阅次数',
    total_borrow_days BIGINT COMMENT '总借阅天数',
    avg_borrow_days DOUBLE COMMENT '平均借阅天数',
    overdue_count BIGINT COMMENT '逾期次数',
    overdue_rate DOUBLE COMMENT '逾期率',
    renew_count BIGINT COMMENT '续借总次数',
    first_lend_date DATE COMMENT '首次借阅日期',
    last_lend_date DATE COMMENT '最后借阅日期',
    active_days BIGINT COMMENT '活跃天数',
    favorite_subject STRING COMMENT '最喜欢的主题分类',
    favorite_location STRING COMMENT '最常借阅的位置'
)
COMMENT '用户借阅汇总表'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 图书借阅汇总表
DROP TABLE IF EXISTS dws_book_lend_summary;

CREATE TABLE IF NOT EXISTS dws_book_lend_summary(
    book_id STRING COMMENT '图书ID',
    total_lend_count BIGINT COMMENT '总借阅次数',
    unique_user_count BIGINT COMMENT '借阅用户数',
    avg_borrow_days DOUBLE COMMENT '平均借阅天数',
    total_borrow_days BIGINT COMMENT '总借阅天数',
    overdue_count BIGINT COMMENT '逾期次数',
    overdue_rate DOUBLE COMMENT '逾期率',
    renew_count BIGINT COMMENT '续借总次数',
    first_lend_date DATE COMMENT '首次借阅日期',
    last_lend_date DATE COMMENT '最后借阅日期',
    lend_frequency DOUBLE COMMENT '借阅频率（总借阅次数/借阅人数）'
)
COMMENT '图书借阅汇总表'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 院系借阅汇总表
DROP TABLE IF EXISTS dws_dept_lend_summary;

CREATE TABLE IF NOT EXISTS dws_dept_lend_summary(
    dept STRING COMMENT '院系',
    total_lend_count BIGINT COMMENT '总借阅次数',
    unique_user_count BIGINT COMMENT '借阅用户数',
    unique_book_count BIGINT COMMENT '借阅图书数',
    total_borrow_days BIGINT COMMENT '总借阅天数',
    avg_borrow_days DOUBLE COMMENT '平均借阅天数',
    overdue_count BIGINT COMMENT '逾期次数',
    avg_lend_per_user DOUBLE COMMENT '人均借阅次数',
    overdue_rate DOUBLE COMMENT '逾期率',
    favorite_subject STRING COMMENT '最喜欢的主题分类',
    subject_max_count BIGINT COMMENT '最喜欢主题的借阅次数',
    favorite_location STRING COMMENT '最常借阅的位置'
)
COMMENT '院系借阅汇总表'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 主题分类汇总表
DROP TABLE IF EXISTS dws_subject_lend_summary;

CREATE TABLE IF NOT EXISTS dws_subject_lend_summary(
    subject STRING COMMENT '主题分类',
    total_lend_count BIGINT COMMENT '总借阅次数',
    unique_user_count BIGINT COMMENT '借阅用户数',
    unique_book_count BIGINT COMMENT '借阅图书数',
    avg_borrow_days DOUBLE COMMENT '平均借阅天数',
    overdue_count BIGINT COMMENT '逾期次数',
    overdue_rate DOUBLE COMMENT '逾期率',
    popular_dept STRING COMMENT '最受欢迎的院系'
)
COMMENT '主题分类汇总表'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 每日统计表
DROP TABLE IF EXISTS dws_daily_stats;

CREATE TABLE IF NOT EXISTS dws_daily_stats(
    stat_date DATE COMMENT '统计日期',
    lend_count BIGINT COMMENT '借阅次数',
    active_user_count BIGINT COMMENT '活跃用户数',
    return_count BIGINT COMMENT '归还次数',
    new_user_count BIGINT COMMENT '新增用户数',
    overdue_count BIGINT COMMENT '逾期次数',
    avg_borrow_days DOUBLE COMMENT '平均借阅天数'
)
COMMENT '每日统计表'
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

