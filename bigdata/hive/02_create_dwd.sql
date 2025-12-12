-- DWD层：明细数据层
CREATE DATABASE IF NOT EXISTS library_dwd
COMMENT '图书馆借阅数据-明细数据层'
LOCATION '/user/hive/warehouse/library_dwd.db';

USE library_dwd;

-- 用户维度表
DROP TABLE IF EXISTS dwd_user_info;

CREATE TABLE IF NOT EXISTS dwd_user_info(
    userid STRING COMMENT '用户ID',
    birthyear INT COMMENT '出生年份',
    age INT COMMENT '年龄',
    sex STRING COMMENT '性别',
    dept STRING COMMENT '院系',
    occupation STRING COMMENT '职业/专业',
    redr_type_name STRING COMMENT '读者类型'
)
COMMENT '用户维度表'
PARTITIONED BY (
    year INT COMMENT '年份',
    month INT COMMENT '月份'
)
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 图书维度表
DROP TABLE IF EXISTS dwd_book_info;

CREATE TABLE IF NOT EXISTS dwd_book_info(
    book_id STRING COMMENT '图书ID',
    title STRING COMMENT '图书标题',
    author STRING COMMENT '作者',
    publisher STRING COMMENT '出版社',
    isbn STRING COMMENT 'ISBN',
    pub_year INT COMMENT '出版年份',
    subject STRING COMMENT '主题分类',
    call_no STRING COMMENT '索书号',
    location_name STRING COMMENT '馆藏位置',
    doc_type_name STRING COMMENT '文献类型'
)
COMMENT '图书维度表'
PARTITIONED BY (
    year INT COMMENT '年份',
    month INT COMMENT '月份'
)
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

-- 借阅明细事实表
DROP TABLE IF EXISTS dwd_lend_detail;

CREATE TABLE IF NOT EXISTS dwd_lend_detail(
    lend_id STRING COMMENT '借阅记录ID（MD5生成）',
    userid STRING COMMENT '用户ID',
    book_id STRING COMMENT '图书ID',
    lend_date STRING COMMENT '借阅日期',
    lend_time STRING COMMENT '借阅时间',
    ret_date STRING COMMENT '归还日期',
    ret_time STRING COMMENT '归还时间',
    renew_times INT COMMENT '续借次数',
    borrow_days INT COMMENT '借阅天数',
    is_overdue INT COMMENT '是否逾期(0:否,1:是)',
    lend_year INT COMMENT '借阅年份',
    lend_month INT COMMENT '借阅月份',
    lend_day INT COMMENT '借阅日（月中的天）',
    lend_hour INT COMMENT '借阅小时',
    lend_weekday INT COMMENT '借阅星期(1-7)',
    ret_hour INT COMMENT '归还小时',
    ret_weekday INT COMMENT '归还星期(1-7)',
    ret_month INT COMMENT '归还月份'
)
COMMENT '借阅明细事实表'
PARTITIONED BY (
    year INT COMMENT '年份',
    month INT COMMENT '月份'
)
STORED AS PARQUET
TBLPROPERTIES (
    'parquet.compression'='SNAPPY'
);

