-- ODS层：原始数据层
CREATE DATABASE IF NOT EXISTS library_ods
COMMENT '图书馆借阅数据-原始数据层'
LOCATION '/user/hive/warehouse/library_ods.db';

USE library_ods;

DROP TABLE IF EXISTS ods_library_lend;

-- 直接映射CSV文件结构，字段类型统一使用STRING
CREATE EXTERNAL TABLE IF NOT EXISTS ods_library_lend(
    userid STRING COMMENT '用户ID（MD5加密）',
    birthyear STRING COMMENT '出生年份',
    sex STRING COMMENT '性别',
    dept STRING COMMENT '院系',
    occupation STRING COMMENT '职业/专业',
    code01 STRING COMMENT '编码（年份）',
    redr_type_name STRING COMMENT '读者类型（本科生/研究生等）',
    lend_date STRING COMMENT '借阅日期时间',
    ret_date STRING COMMENT '归还日期时间',
    renew_times STRING COMMENT '续借次数',
    title STRING COMMENT '图书标题',
    book_id STRING COMMENT '图书ID',
    abstract STRING COMMENT '摘要',
    sub STRING COMMENT '主题分类',
    call_no STRING COMMENT '索书号',
    author STRING COMMENT '作者',
    au STRING COMMENT '作者（简写）',
    publisher STRING COMMENT '出版社',
    isbn STRING COMMENT 'ISBN',
    pub_year STRING COMMENT '出版年份',
    location_name STRING COMMENT '馆藏位置',
    doc_type_name STRING COMMENT '文献类型'
)
COMMENT '图书馆借阅原始数据表'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/data/library/raw'
TBLPROPERTIES (
    'creator'='system',
    'create_time'='2024-12-03',
    'skip.header.line.count'='1'
);

-- 注意：本项目采用Spark直接读取HDFS CSV，ODS表仅作为元数据定义
