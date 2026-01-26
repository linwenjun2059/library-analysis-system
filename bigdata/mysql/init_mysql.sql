-- =============================================
-- 图书馆借阅分析系统 - MySQL数据库初始化脚本
-- 包含31张表：维度表(3) + 汇总表(5) + 聚合表(5) + 推荐与功能表(11) + 挖掘表(3) + 预测表(3) + 系统表(1)
-- 用于Spark数据导出
-- =============================================

CREATE DATABASE IF NOT EXISTS library_analysis 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE library_analysis;

-- =============================================
-- 重要说明：Spark写入表的字段约定
-- =============================================
-- 1. 由Spark任务通过 mode("overwrite") 写入的表不包含以下字段：
--    - create_time: 每次覆盖写入无法保留历史创建时间
--    - update_time: 所有记录时间相同，存储冗余，应使用元数据表管理
--    - id（自增主键）：覆盖模式下自增ID会重置
--
-- 2. 如需跟踪数据刷新时间，建议使用单独的 data_refresh_metadata 表
--
-- 3. 仅保留 sys_user 等系统管理表的完整字段结构
-- =============================================

-- =============================================
-- 第一部分：维度表（3张）
-- 从DWD层导出，用于业务系统基础数据
-- =============================================

-- 1. 用户维度表
-- 注意：此表由Spark任务写入，不包含create_time字段
DROP TABLE IF EXISTS user_dimension;

CREATE TABLE user_dimension (
    userid VARCHAR(128) PRIMARY KEY COMMENT '用户ID',
    gender VARCHAR(10) COMMENT '性别',
    dept_name VARCHAR(100) COMMENT '院系名称',
    user_type_name VARCHAR(50) COMMENT '用户类型',
    INDEX idx_dept (dept_name),
    INDEX idx_type (user_type_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户维度表';

-- 2. 图书维度表
-- 注意：此表由Spark任务写入，不包含create_time字段
DROP TABLE IF EXISTS book_dimension;

CREATE TABLE book_dimension (
    book_id VARCHAR(128) PRIMARY KEY COMMENT '图书ID',
    title VARCHAR(500) COMMENT '书名',
    author VARCHAR(200) COMMENT '作者',
    publisher VARCHAR(200) COMMENT '出版社',
    isbn VARCHAR(50) COMMENT 'ISBN',
    pub_year INT COMMENT '出版年份',
    subject VARCHAR(100) COMMENT '主题分类',
    call_no VARCHAR(100) COMMENT '索书号',
    location_name VARCHAR(100) COMMENT '馆藏位置',
    doc_type_name VARCHAR(50) COMMENT '文献类型',
    INDEX idx_title (title(100)),
    INDEX idx_author (author(50)),
    INDEX idx_subject (subject),
    INDEX idx_publisher (publisher(50)),
    FULLTEXT idx_fulltext (title, author)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='图书维度表';

-- 3. 近期借阅记录（最近6个月）
-- 注意：此表由Spark任务写入，不包含create_time字段
DROP TABLE IF EXISTS recent_lend_records;

CREATE TABLE recent_lend_records (
    lend_id VARCHAR(64) PRIMARY KEY COMMENT '借阅记录ID',
    userid VARCHAR(128) NOT NULL COMMENT '用户ID',
    book_id VARCHAR(128) NOT NULL COMMENT '图书ID',
    lend_date DATE NOT NULL COMMENT '借阅日期',
    lend_time VARCHAR(10) COMMENT '借阅时间',
    ret_date DATE COMMENT '归还日期',
    ret_time VARCHAR(10) COMMENT '归还时间',
    renew_times INT DEFAULT 0 COMMENT '续借次数',
    borrow_days INT COMMENT '借阅天数',
    is_overdue TINYINT DEFAULT 0 COMMENT '是否逾期(0:否,1:是)',
    INDEX idx_userid (userid),
    INDEX idx_book (book_id),
    INDEX idx_lend_date (lend_date),
    INDEX idx_ret_date (ret_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='近期借阅记录（最近6个月）';

-- =============================================
-- 第二部分：汇总表（5张）
-- 从DWS层导出，用于统计查询
-- =============================================

-- 4. 用户借阅汇总表
-- 注意：此表由Spark任务写入，不包含create_time字段
DROP TABLE IF EXISTS user_lend_summary;

CREATE TABLE user_lend_summary (
    userid VARCHAR(128) PRIMARY KEY COMMENT '用户ID',
    total_lend_count BIGINT COMMENT '总借阅次数',
    total_borrow_days BIGINT COMMENT '总借阅天数',
    avg_borrow_days DOUBLE COMMENT '平均借阅天数',
    overdue_count BIGINT COMMENT '逾期次数',
    overdue_rate DOUBLE COMMENT '逾期率',
    renew_count BIGINT COMMENT '续借次数',
    favorite_subject VARCHAR(100) COMMENT '最喜欢的主题',
    favorite_location VARCHAR(100) COMMENT '最喜欢的位置',
    first_lend_date DATE COMMENT '首次借阅日期',
    last_lend_date DATE COMMENT '最后借阅日期',
    active_days INT COMMENT '活跃天数',
    INDEX idx_total_lend (total_lend_count DESC),
    INDEX idx_overdue_rate (overdue_rate),
    INDEX idx_last_lend (last_lend_date DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户借阅汇总表';

-- 5. 图书借阅汇总表
-- 注意：此表由Spark任务写入，不包含create_time字段
DROP TABLE IF EXISTS book_lend_summary;

CREATE TABLE book_lend_summary (
    book_id VARCHAR(128) PRIMARY KEY COMMENT '图书ID',
    total_lend_count BIGINT COMMENT '总借阅次数',
    unique_user_count BIGINT COMMENT '借阅用户数',
    avg_borrow_days DOUBLE COMMENT '平均借阅天数',
    total_borrow_days BIGINT COMMENT '总借阅天数',
    overdue_count BIGINT COMMENT '逾期次数',
    overdue_rate DOUBLE COMMENT '逾期率',
    renew_count BIGINT COMMENT '续借次数',
    first_lend_date DATE COMMENT '首次借阅日期',
    last_lend_date DATE COMMENT '最后借阅日期',
    lend_frequency DOUBLE COMMENT '借阅频率',
    INDEX idx_total_lend (total_lend_count DESC),
    INDEX idx_unique_users (unique_user_count DESC),
    INDEX idx_last_lend (last_lend_date DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='图书借阅汇总表';

-- 6. 院系借阅汇总表
-- 注意：此表由Spark任务写入，不包含create_time字段
DROP TABLE IF EXISTS dept_lend_summary;

CREATE TABLE dept_lend_summary (
    dept VARCHAR(100) PRIMARY KEY COMMENT '院系名称',
    total_lend_count BIGINT COMMENT '总借阅次数',
    unique_user_count BIGINT COMMENT '借阅用户数',
    unique_book_count BIGINT COMMENT '借阅图书数',
    avg_lend_per_user DOUBLE COMMENT '人均借阅次数',
    total_borrow_days BIGINT COMMENT '总借阅天数',
    avg_borrow_days DOUBLE COMMENT '平均借阅天数',
    overdue_count BIGINT COMMENT '逾期次数',
    overdue_rate DOUBLE COMMENT '逾期率',
    favorite_subject VARCHAR(100) COMMENT '最喜欢的主题',
    subject_max_count BIGINT COMMENT '最喜欢主题的借阅次数',
    favorite_location VARCHAR(100) COMMENT '最喜欢的位置',
    INDEX idx_total_lend (total_lend_count DESC),
    INDEX idx_avg_lend (avg_lend_per_user DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='院系借阅汇总表';

-- 7. 主题分类汇总表
-- 注意：此表由Spark任务写入，不包含create_time字段
DROP TABLE IF EXISTS subject_lend_summary;

CREATE TABLE subject_lend_summary (
    subject VARCHAR(100) PRIMARY KEY COMMENT '主题分类',
    total_lend_count BIGINT COMMENT '总借阅次数',
    unique_user_count BIGINT COMMENT '借阅用户数',
    unique_book_count BIGINT COMMENT '借阅图书数',
    avg_borrow_days DOUBLE COMMENT '平均借阅天数',
    overdue_rate DOUBLE COMMENT '逾期率',
    popular_dept VARCHAR(100) COMMENT '最受欢迎的院系',
    INDEX idx_total_lend (total_lend_count DESC),
    INDEX idx_unique_users (unique_user_count DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='主题分类汇总表';

-- 8. 每日统计表
-- 注意：此表由Spark任务写入，不包含create_time字段
DROP TABLE IF EXISTS daily_stats;

CREATE TABLE daily_stats (
    stat_date DATE PRIMARY KEY COMMENT '统计日期',
    lend_count INT COMMENT '借阅次数',
    return_count INT COMMENT '归还次数',
    new_user_count INT COMMENT '新增用户数',
    active_user_count INT COMMENT '活跃用户数',
    overdue_count INT COMMENT '逾期次数',
    avg_borrow_days DOUBLE COMMENT '平均借阅天数',
    INDEX idx_stat_date (stat_date DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日统计表';

-- =============================================
-- 第三部分：聚合表（5张）
-- 从ADS层导出，用于Dashboard展示
-- =============================================


-- 9. 热门图书表
DROP TABLE IF EXISTS `hot_books`;
CREATE TABLE `hot_books` (
  `rank_no` INT(11) NOT NULL COMMENT '排名',
  `book_id` VARCHAR(64) NOT NULL COMMENT '图书ID',
  `title` VARCHAR(500) DEFAULT NULL COMMENT '书名',
  `author` VARCHAR(200) DEFAULT NULL COMMENT '作者',
  `subject` VARCHAR(255) DEFAULT NULL COMMENT '主题',
  `borrow_count` BIGINT(20) DEFAULT NULL COMMENT '借阅次数',
  PRIMARY KEY (`rank_no`),
  KEY `idx_book_id` (`book_id`),
  KEY `idx_borrow_count` (`borrow_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='热门图书排行榜(TOP100)';


-- 10. 活跃用户表
DROP TABLE IF EXISTS `active_users`;
CREATE TABLE `active_users` (
  `rank_no` INT(11) NOT NULL COMMENT '排名',
  `userid` VARCHAR(64) NOT NULL COMMENT '用户ID',
  `dept` VARCHAR(255) DEFAULT NULL COMMENT '院系',
  `redr_type_name` VARCHAR(255) DEFAULT NULL COMMENT '读者类型',
  `borrow_count` BIGINT(20) DEFAULT NULL COMMENT '借阅次数',
  PRIMARY KEY (`rank_no`),
  KEY `idx_userid` (`userid`),
  KEY `idx_dept` (`dept`),
  KEY `idx_borrow_count` (`borrow_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='活跃用户排行榜(TOP100)';


-- 11. 院系偏好表
DROP TABLE IF EXISTS `dept_preference`;
CREATE TABLE `dept_preference` (
  `dept` VARCHAR(255) NOT NULL COMMENT '院系',
  `favorite_subject` VARCHAR(255) DEFAULT NULL COMMENT '最喜欢的主题',
  `subject_lend_count` BIGINT(20) DEFAULT NULL COMMENT '主题借阅次数',
  `total_lend_count` BIGINT(20) DEFAULT NULL COMMENT '总借阅次数',
  `preference_rate` DOUBLE DEFAULT NULL COMMENT '偏好率',
  PRIMARY KEY (`dept`(191)),
  KEY `idx_lend_count` (`total_lend_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='院系借阅偏好统计';


-- 12. 借阅趋势表
DROP TABLE IF EXISTS `lend_trend`;
CREATE TABLE `lend_trend` (
  `trend_date` DATE NOT NULL COMMENT '趋势日期',
  `lend_count` BIGINT(20) DEFAULT NULL COMMENT '借阅次数',
  `return_count` BIGINT(20) DEFAULT NULL COMMENT '归还次数',
  `active_user_count` BIGINT(20) DEFAULT NULL COMMENT '活跃用户数',
  `new_user_count` BIGINT(20) DEFAULT NULL COMMENT '新用户数',
  `return_user_count` BIGINT(20) DEFAULT NULL COMMENT '回访用户数（距上次借阅>30天）',
  `avg_lend_per_user` DOUBLE DEFAULT NULL COMMENT '人均借阅次数',
  `trend_type` VARCHAR(20) DEFAULT NULL COMMENT '趋势类型',
  PRIMARY KEY (`trend_date`),
  KEY `idx_lend_count` (`lend_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='借阅趋势统计';


-- 13. 运营看板表
DROP TABLE IF EXISTS `operation_dashboard`;
CREATE TABLE `operation_dashboard` (
  `metric_name` VARCHAR(100) NOT NULL COMMENT '指标名称',
  `metric_value` VARCHAR(500) DEFAULT NULL COMMENT '指标值',
  `compare_yesterday` DOUBLE DEFAULT NULL COMMENT '环比昨日',
  `compare_last_week` DOUBLE DEFAULT NULL COMMENT '环比上周',
  `compare_last_month` DOUBLE DEFAULT NULL COMMENT '环比上月',
  `trend` VARCHAR(20) DEFAULT NULL COMMENT '趋势：上升/下降/持平',
  `category` VARCHAR(50) DEFAULT NULL COMMENT '分类',
  PRIMARY KEY (`metric_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='运营看板数据';


-- =============================================
-- 第四部分：推荐与功能表（11张）
-- 从推荐算法和ADS层导出
-- =============================================

-- 14. 图书推荐表（离线分析版）
-- 注意：此表由Spark任务通过mode("overwrite")写入，不包含id和update_time字段
-- 性能优化：减少索引数量，只保留最常用的查询索引
DROP TABLE IF EXISTS `book_recommendations`;
CREATE TABLE `book_recommendations` (
  `userid` VARCHAR(64) NOT NULL COMMENT '用户ID',
  `book_id` VARCHAR(64) NOT NULL COMMENT '图书ID',
  `title` VARCHAR(500) DEFAULT NULL COMMENT '图书标题',
  `author` VARCHAR(255) DEFAULT NULL COMMENT '作者',
  `subject` VARCHAR(255) DEFAULT NULL COMMENT '主题分类',
  `score` DOUBLE DEFAULT NULL COMMENT '推荐得分(0-10分)',
  `rec_sources` VARCHAR(100) DEFAULT NULL COMMENT '推荐来源组合(cf,content,popularity)',
  `reason` VARCHAR(1000) DEFAULT NULL COMMENT '推荐理由(可包含多个来源的理由)',
  `rank_no` INT(11) DEFAULT NULL COMMENT '推荐排名(1-20)',
  `diversity_score` DOUBLE DEFAULT NULL COMMENT '多样性得分(0-1,越高越多样)',
  `cf_score` DOUBLE DEFAULT NULL COMMENT '协同过滤得分(0-10)',
  `content_score` DOUBLE DEFAULT NULL COMMENT '内容推荐得分(0-10)',
  `popularity_score` DOUBLE DEFAULT NULL COMMENT '热门推荐得分(0-10)',
  PRIMARY KEY (`userid`, `book_id`),
  KEY `idx_userid_rank` (`userid`, `rank_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='个性化图书推荐表-基于历史数据的离线推荐分析';

-- 15. 推荐效果统计表（推荐分析）
DROP TABLE IF EXISTS `recommendation_stats`;
CREATE TABLE `recommendation_stats` (
  `stat_type` VARCHAR(50) NOT NULL COMMENT '统计类型',
  `stat_name` VARCHAR(100) DEFAULT NULL COMMENT '统计名称',
  `stat_value` VARCHAR(500) DEFAULT NULL COMMENT '统计值',
  PRIMARY KEY (`stat_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='推荐效果统计表-记录推荐系统的整体运行指标';

-- 16. 用户画像表（高级管理员）
DROP TABLE IF EXISTS `user_profile`;
CREATE TABLE `user_profile` (
  `userid` VARCHAR(64) NOT NULL COMMENT '用户ID',
  `user_type` VARCHAR(50) DEFAULT NULL COMMENT '用户类型',
  `dept` VARCHAR(255) DEFAULT NULL COMMENT '院系',
  `occupation` VARCHAR(255) DEFAULT NULL COMMENT '专业',
  `gender` VARCHAR(10) DEFAULT NULL COMMENT '性别',
  `age_group` VARCHAR(20) DEFAULT NULL COMMENT '年龄段',
  `borrow_level` VARCHAR(20) DEFAULT NULL COMMENT '借阅等级',
  `total_borrow_count` BIGINT(20) DEFAULT NULL COMMENT '总借阅量',
  `reading_breadth` INT(11) DEFAULT NULL COMMENT '阅读广度',
  `favorite_subjects` TEXT COMMENT '偏好主题TOP3（JSON数组）',
  `favorite_locations` TEXT COMMENT '偏好位置TOP3（JSON数组）',
  `avg_borrow_days` DOUBLE DEFAULT NULL COMMENT '平均借阅天数',
  `overdue_rate` DOUBLE DEFAULT NULL COMMENT '逾期率',
  `last_borrow_date` DATE DEFAULT NULL COMMENT '最后借阅日期',
  `user_tags` TEXT COMMENT '用户标签（JSON数组）',
  PRIMARY KEY (`userid`),
  KEY `idx_dept` (`dept`(100)),
  KEY `idx_borrow_level` (`borrow_level`),
  KEY `idx_total_borrow` (`total_borrow_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户画像分析表';

-- 17. 专业阅读特征表（高级管理员）
DROP TABLE IF EXISTS `major_reading_profile`;
CREATE TABLE `major_reading_profile` (
  `dept` VARCHAR(255) NOT NULL COMMENT '院系',
  `occupation` VARCHAR(255) NOT NULL COMMENT '专业',
  `student_count` BIGINT(20) DEFAULT NULL COMMENT '学生数量',
  `total_borrow_count` BIGINT(20) DEFAULT NULL COMMENT '总借阅量',
  `avg_borrow_per_student` DOUBLE DEFAULT NULL COMMENT '人均借阅量',
  `core_subjects` TEXT COMMENT '核心学科TOP5（JSON数组）',
  `cross_subjects` TEXT COMMENT '跨学科借阅TOP3（JSON数组）',
  `reading_breadth_score` DOUBLE DEFAULT NULL COMMENT '阅读广度得分',
  `popular_books` TEXT COMMENT '热门书目TOP10（JSON数组）',
  PRIMARY KEY (`dept`(100), `occupation`(100)),
  KEY `idx_dept` (`dept`(100)),
  KEY `idx_avg_borrow` (`avg_borrow_per_student`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='专业阅读特征分析表';

-- 18. 逾期分析表（图书管理员）
DROP TABLE IF EXISTS `overdue_analysis`;
CREATE TABLE `overdue_analysis` (
  `analysis_type` VARCHAR(20) NOT NULL COMMENT '分析类型',
  `target_id` VARCHAR(255) NOT NULL COMMENT '目标ID',
  `target_name` VARCHAR(500) DEFAULT NULL COMMENT '目标名称',
  `overdue_count` BIGINT(20) DEFAULT NULL COMMENT '逾期次数',
  `total_borrow_count` BIGINT(20) DEFAULT NULL COMMENT '总借阅次数',
  `overdue_rate` DOUBLE DEFAULT NULL COMMENT '逾期率',
  `avg_overdue_days` DOUBLE DEFAULT NULL COMMENT '平均逾期天数',
  `current_overdue_count` BIGINT(20) DEFAULT NULL COMMENT '当前逾期数量',
  `risk_level` VARCHAR(10) DEFAULT NULL COMMENT '风险等级',
  PRIMARY KEY (`analysis_type`, `target_id`(100)),
  KEY `idx_risk` (`risk_level`),
  KEY `idx_overdue_rate` (`overdue_rate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='逾期分析表';

-- 19. 馆藏利用分析表（高级管理员）
-- 说明：删除流通率字段（数据源限制导致无分析价值），保留周转率等有价值的指标
DROP TABLE IF EXISTS `collection_utilization_analysis`;
CREATE TABLE `collection_utilization_analysis` (
  `dimension_type` VARCHAR(50) NOT NULL COMMENT '维度类型（位置/主题）',
  `dimension_value` VARCHAR(255) NOT NULL COMMENT '维度值（具体位置或主题名称）',
  `total_books` BIGINT(20) DEFAULT NULL COMMENT '馆藏图书总数',
  `borrowed_books` BIGINT(20) DEFAULT NULL COMMENT '被借图书数',
  `total_lend_count` BIGINT(20) DEFAULT NULL COMMENT '总借阅次数',
  `avg_borrow_times` DOUBLE DEFAULT NULL COMMENT '平均借阅次数（次/本）',
  `avg_borrow_days` DOUBLE DEFAULT NULL COMMENT '平均借阅天数',
  `turnover_rate` DOUBLE DEFAULT NULL COMMENT '周转率（次/本/年）= 总借阅次数 / 馆藏总数 / 时间跨度(2年)',
  `high_demand_books` BIGINT(20) DEFAULT NULL COMMENT '高需求图书数（借阅>5次）',
  `medium_demand_books` BIGINT(20) DEFAULT NULL COMMENT '中等需求图书数（2-5次）',
  `low_demand_books` BIGINT(20) DEFAULT NULL COMMENT '低需求图书数（1次）',
  `unique_readers` BIGINT(20) DEFAULT NULL COMMENT '独立读者数',
  `reader_per_book_ratio` DOUBLE DEFAULT NULL COMMENT '读者/图书比 = 独立读者数 / 馆藏总数',
  PRIMARY KEY (`dimension_type`, `dimension_value`(191)),
  KEY `idx_turnover_rate` (`turnover_rate`),
  KEY `idx_avg_borrow_times` (`avg_borrow_times`),
  KEY `idx_reader_ratio` (`reader_per_book_ratio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='馆藏利用分析表（按位置/主题维度，包含周转率、需求分级、读者比等指标）';

-- 20. 出版社分析表（高级管理员）
DROP TABLE IF EXISTS `publisher_analysis`;
CREATE TABLE `publisher_analysis` (
  `publisher` VARCHAR(255) NOT NULL COMMENT '出版社名称',
  `book_count` BIGINT(20) DEFAULT NULL COMMENT '图书数量',
  `total_lend_count` BIGINT(20) DEFAULT NULL COMMENT '总借阅次数',
  `total_user_count` BIGINT(20) DEFAULT NULL COMMENT '总借阅用户数',
  `avg_lend_count` DOUBLE DEFAULT NULL COMMENT '平均借阅次数',
  `rank_no` INT(11) DEFAULT NULL COMMENT '排名',
  PRIMARY KEY (`publisher`(191)),
  KEY `idx_rank` (`rank_no`),
  KEY `idx_total_lend` (`total_lend_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='出版社分析表（高级管理员，TOP50）';

-- 21. 出版年份分析表（高级管理员）
DROP TABLE IF EXISTS `publish_year_analysis`;
CREATE TABLE `publish_year_analysis` (
  `pub_year` INT(11) NOT NULL COMMENT '出版年份',
  `book_count` BIGINT(20) DEFAULT NULL COMMENT '图书数量',
  `total_lend_count` BIGINT(20) DEFAULT NULL COMMENT '总借阅次数',
  `avg_lend_count` DOUBLE DEFAULT NULL COMMENT '平均借阅次数',
  PRIMARY KEY (`pub_year`),
  KEY `idx_total_lend` (`total_lend_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='出版年份分析表（高级管理员）';

-- 22. 时间分布表（图书管理员）
DROP TABLE IF EXISTS `time_distribution`;
CREATE TABLE `time_distribution` (
  `time_type` VARCHAR(20) NOT NULL COMMENT '时间类型',
  `time_value` INT(11) NOT NULL COMMENT '时间值',
  `borrow_count` BIGINT(20) DEFAULT NULL COMMENT '借阅次数',
  `return_count` BIGINT(20) DEFAULT NULL COMMENT '归还次数',
  `active_user_count` BIGINT(20) DEFAULT NULL COMMENT '活跃用户数',
  `percentage` DOUBLE DEFAULT NULL COMMENT '占比',
  PRIMARY KEY (`time_type`, `time_value`),
  KEY `idx_borrow_count` (`borrow_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='时间分布分析表';

-- 23. 用户排名表（普通用户）
DROP TABLE IF EXISTS `user_ranking`;
CREATE TABLE `user_ranking` (
  `userid` VARCHAR(64) NOT NULL COMMENT '用户ID',
  `dept` VARCHAR(255) DEFAULT NULL COMMENT '院系',
  `occupation` VARCHAR(255) DEFAULT NULL COMMENT '专业',
  `user_type` VARCHAR(50) DEFAULT NULL COMMENT '用户类型',
  `total_borrow_count` BIGINT(20) DEFAULT NULL COMMENT '总借阅量',
  `dept_rank` INT(11) DEFAULT NULL COMMENT '院系内排名',
  `occupation_rank` INT(11) DEFAULT NULL COMMENT '专业内排名',
  `dept_total_users` INT(11) DEFAULT NULL COMMENT '院系总用户数',
  `occupation_total_users` INT(11) DEFAULT NULL COMMENT '专业总用户数',
  `percentile_dept` DOUBLE DEFAULT NULL COMMENT '院系百分位',
  `percentile_occupation` DOUBLE DEFAULT NULL COMMENT '专业百分位',
  PRIMARY KEY (`userid`),
  KEY `idx_dept` (`dept`(100)),
  KEY `idx_occupation` (`occupation`(100)),
  KEY `idx_dept_rank` (`dept_rank`),
  KEY `idx_occupation_rank` (`occupation_rank`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户排名表';

-- 24. 图书推荐基础表（普通用户）
DROP TABLE IF EXISTS `book_recommend_base`;
CREATE TABLE `book_recommend_base` (
  `recommend_type` VARCHAR(50) NOT NULL COMMENT '推荐类型',
  `scope` VARCHAR(255) NOT NULL COMMENT '范围',
  `book_id` VARCHAR(64) NOT NULL COMMENT '图书ID',
  `title` VARCHAR(500) DEFAULT NULL COMMENT '书名',
  `author` VARCHAR(255) DEFAULT NULL COMMENT '作者',
  `subject` VARCHAR(255) DEFAULT NULL COMMENT '主题',
  `borrow_count` BIGINT(20) DEFAULT NULL COMMENT '借阅次数',
  `rank_no` INT(11) DEFAULT NULL COMMENT '排名',
  `update_date` DATE DEFAULT NULL COMMENT '更新日期',
  PRIMARY KEY (`recommend_type`, `scope`(100), `book_id`),
  KEY `idx_book_id` (`book_id`),
  KEY `idx_rank` (`rank_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='图书推荐基础表';

-- =============================================
-- 第五部分：高级数据挖掘表（3张）
-- 关联规则分析 + 用户聚类分群
-- =============================================

-- 25. 图书关联规则表（FPGrowth算法）
DROP TABLE IF EXISTS `book_association_rules`;
CREATE TABLE `book_association_rules` (
  `antecedent_books` VARCHAR(500) NOT NULL COMMENT '前项图书ID（逗号分隔）',
  `consequent_books` VARCHAR(500) NOT NULL COMMENT '后项图书ID（逗号分隔）',
  `antecedent_title` VARCHAR(500) DEFAULT NULL COMMENT '前项图书标题',
  `consequent_title` VARCHAR(500) DEFAULT NULL COMMENT '后项图书标题',
  `antecedent_subject` VARCHAR(100) DEFAULT NULL COMMENT '前项图书主题',
  `consequent_subject` VARCHAR(100) DEFAULT NULL COMMENT '后项图书主题',
  `confidence` DOUBLE DEFAULT NULL COMMENT '置信度（0-1）',
  `lift` DOUBLE DEFAULT NULL COMMENT '提升度（>1表示正相关）',
  `support` DOUBLE DEFAULT NULL COMMENT '支持度',
  `rule_description` VARCHAR(500) DEFAULT NULL COMMENT '规则描述',
  `association_type` VARCHAR(50) DEFAULT NULL COMMENT '关联类型（同主题关联/跨主题关联）',
  PRIMARY KEY (`antecedent_books`(200), `consequent_books`(200)),
  KEY `idx_confidence` (`confidence`),
  KEY `idx_lift` (`lift`),
  KEY `idx_association_type` (`association_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='图书关联规则表（FPGrowth算法挖掘结果）';

-- 26. 用户聚类表（K-means算法）
DROP TABLE IF EXISTS `user_clusters`;
CREATE TABLE `user_clusters` (
  `userid` VARCHAR(64) NOT NULL COMMENT '用户ID',
  `dept` VARCHAR(255) DEFAULT NULL COMMENT '院系',
  `user_type` VARCHAR(50) DEFAULT NULL COMMENT '用户类型',
  `occupation` VARCHAR(255) DEFAULT NULL COMMENT '专业',
  `cluster` INT(11) DEFAULT NULL COMMENT '聚类编号',
  `cluster_name` VARCHAR(100) DEFAULT NULL COMMENT '聚类名称（如：考研学习族）',
  `cluster_characteristics` VARCHAR(255) DEFAULT NULL COMMENT '聚类特征描述',
  `borrow_count` BIGINT(20) DEFAULT NULL COMMENT '借阅量',
  `active_days` INT(11) DEFAULT NULL COMMENT '活跃天数',
  `overdue_rate` DOUBLE DEFAULT NULL COMMENT '逾期率',
  `avg_borrow_days` DOUBLE DEFAULT NULL COMMENT '平均借阅天数',
  `reading_breadth` INT(11) DEFAULT NULL COMMENT '阅读广度（涉及主题数）',
  PRIMARY KEY (`userid`),
  KEY `idx_cluster` (`cluster`),
  KEY `idx_cluster_name` (`cluster_name`),
  KEY `idx_dept` (`dept`(100)),
  KEY `idx_borrow_count` (`borrow_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户聚类分群表（K-means算法结果）';

-- 27. 聚类统计摘要表
DROP TABLE IF EXISTS `cluster_summary`;
CREATE TABLE `cluster_summary` (
  `cluster` INT(11) NOT NULL COMMENT '聚类编号',
  `cluster_name` VARCHAR(100) DEFAULT NULL COMMENT '聚类名称',
  `cluster_characteristics` VARCHAR(255) DEFAULT NULL COMMENT '聚类特征描述',
  `user_count` BIGINT(20) DEFAULT NULL COMMENT '用户数量',
  `avg_borrow_count` DOUBLE DEFAULT NULL COMMENT '平均借阅量',
  `avg_active_days` DOUBLE DEFAULT NULL COMMENT '平均活跃天数',
  `avg_overdue_rate` DOUBLE DEFAULT NULL COMMENT '平均逾期率',
  `avg_borrow_days` DOUBLE DEFAULT NULL COMMENT '平均借阅天数',
  `avg_reading_breadth` DOUBLE DEFAULT NULL COMMENT '平均阅读广度',
  PRIMARY KEY (`cluster`),
  KEY `idx_user_count` (`user_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聚类统计摘要表';

-- =============================================
-- 第六部分：预测分析表（3张）
-- 机器学习预测
-- =============================================

-- 28. 用户逾期风险预测表
DROP TABLE IF EXISTS `overdue_risk_prediction`;
CREATE TABLE `overdue_risk_prediction` (
  `userid` VARCHAR(64) NOT NULL COMMENT '用户ID',
  `dept` VARCHAR(255) DEFAULT NULL COMMENT '院系',
  `user_type` VARCHAR(50) DEFAULT NULL COMMENT '用户类型',
  `borrow_count` BIGINT(20) DEFAULT NULL COMMENT '借阅量',
  `historical_overdue_rate` DOUBLE DEFAULT NULL COMMENT '历史逾期率',
  `avg_borrow_days` DOUBLE DEFAULT NULL COMMENT '平均借阅天数',
  `overdue_probability` DOUBLE DEFAULT NULL COMMENT '预测逾期概率（0-1）',
  `risk_level` VARCHAR(20) DEFAULT NULL COMMENT '风险等级（高风险/中风险/低风险/极低风险）',
  `warning_message` VARCHAR(255) DEFAULT NULL COMMENT '预警建议',
  `prediction_date` VARCHAR(20) DEFAULT NULL COMMENT '预测日期',
  PRIMARY KEY (`userid`),
  KEY `idx_risk_level` (`risk_level`),
  KEY `idx_overdue_probability` (`overdue_probability`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户逾期风险预测表';

-- 29. 借阅趋势预测表
DROP TABLE IF EXISTS `lend_trend_prediction`;
CREATE TABLE `lend_trend_prediction` (
  `lend_month` VARCHAR(10) NOT NULL COMMENT '月份（yyyy-MM）',
  `year` INT(11) DEFAULT NULL COMMENT '年份',
  `month` INT(11) DEFAULT NULL COMMENT '月份',
  `lend_count` BIGINT(20) DEFAULT NULL COMMENT '实际借阅量',
  `active_users` BIGINT(20) DEFAULT NULL COMMENT '活跃用户数',
  `unique_books` BIGINT(20) DEFAULT NULL COMMENT '借阅图书种类',
  `predicted_count` BIGINT(20) DEFAULT NULL COMMENT '预测借阅量',
  `data_type` VARCHAR(10) DEFAULT NULL COMMENT '数据类型（历史/预测）',
  `trend` VARCHAR(10) DEFAULT NULL COMMENT '趋势（上升/下降/持平）',
  `prediction_date` VARCHAR(20) DEFAULT NULL COMMENT '预测日期',
  PRIMARY KEY (`lend_month`),
  KEY `idx_data_type` (`data_type`),
  KEY `idx_year_month` (`year`, `month`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='借阅趋势预测表';

-- 30. 图书热度预测表
DROP TABLE IF EXISTS `book_heat_prediction`;
CREATE TABLE `book_heat_prediction` (
  `book_id` VARCHAR(64) NOT NULL COMMENT '图书ID',
  `title` VARCHAR(500) DEFAULT NULL COMMENT '书名',
  `subject` VARCHAR(100) DEFAULT NULL COMMENT '主题分类',
  `author` VARCHAR(255) DEFAULT NULL COMMENT '作者',
  `total_lend_count` BIGINT(20) DEFAULT NULL COMMENT '历史总借阅量',
  `recent_lend_count` BIGINT(20) DEFAULT NULL COMMENT '近期借阅量（3个月）',
  `unique_user_count` BIGINT(20) DEFAULT NULL COMMENT '借阅用户数',
  `heat_score` DOUBLE DEFAULT NULL COMMENT '热度分数（0-100）',
  `heat_level` VARCHAR(20) DEFAULT NULL COMMENT '热度等级（爆款/热门/一般/冷门/极冷）',
  `trend` VARCHAR(10) DEFAULT NULL COMMENT '趋势（上升/稳定/下降）',
  `recommendation` VARCHAR(255) DEFAULT NULL COMMENT '采购建议',
  `prediction_date` VARCHAR(20) DEFAULT NULL COMMENT '预测日期',
  PRIMARY KEY (`book_id`),
  KEY `idx_heat_score` (`heat_score`),
  KEY `idx_heat_level` (`heat_level`),
  KEY `idx_trend` (`trend`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='图书热度预测表';

-- =============================================
-- 表结构说明
-- =============================================

/*
维度表（3张）- 从DWD层导出：
1. user_dimension - 用户维度信息
2. book_dimension - 图书维度信息
3. recent_lend_records - 最近6个月借阅记录

汇总表（5张）- 从DWS层导出：
4. user_lend_summary - 用户借阅汇总
5. book_lend_summary - 图书借阅汇总
6. dept_lend_summary - 院系借阅汇总
7. subject_lend_summary - 主题分类汇总
8. daily_stats - 每日统计

聚合表（5张）- 从ADS层导出：
9. hot_books - 热门图书TOP100
10. active_users - 活跃用户TOP100
11. dept_preference - 院系偏好
12. lend_trend - 借阅趋势
13. operation_dashboard - 运营看板

推荐与功能表（11张）- 从推荐算法和ADS层导出：
14. book_recommendations - 个性化推荐（协同过滤）
15. recommendation_stats - 推荐效果统计表（推荐系统监控）
16. user_profile - 用户画像分析（高级管理员）
17. major_reading_profile - 专业阅读特征（高级管理员）
18. overdue_analysis - 逾期分析（图书管理员）
19. collection_utilization_analysis - 馆藏利用分析（高级管理员）
20. publisher_analysis - 出版社分析（高级管理员）
21. publish_year_analysis - 出版年份分析（高级管理员）
22. time_distribution - 时间分布分析（图书管理员）
23. user_ranking - 用户排名（普通用户）
24. book_recommend_base - 图书推荐基础表（普通用户）

高级数据挖掘表（3张）- 机器学习算法：
25. book_association_rules - 图书关联规则（FPGrowth算法）
26. user_clusters - 用户聚类分群（K-means算法）
27. cluster_summary - 聚类统计摘要

预测分析表（3张）- 机器学习预测：
28. overdue_risk_prediction - 用户逾期风险预测
29. lend_trend_prediction - 借阅趋势预测
30. book_heat_prediction - 图书热度预测

系统用户表（1张）：
31. sys_user - 系统用户表

总计：31张表

角色功能对应：
【高级管理员】- 战略决策层
  - user_profile（用户画像）
  - major_reading_profile（专业特征）
  - collection_utilization_analysis（馆藏利用分析）
  - publisher_analysis（出版社分析）
  - publish_year_analysis（出版年份分析）
  - operation_dashboard（运营看板）
  - book_association_rules（图书关联规则 - FPGrowth算法）
  - user_clusters + cluster_summary（用户聚类分群 - K-means算法）
  - hot_books、active_users、dept_preference、lend_trend

【图书管理员】- 业务执行层
  - overdue_analysis（逾期管理）
  - time_distribution（时间分布）
  - hot_books、dept_preference、book_lend_summary
  - user_lend_summary、recent_lend_records

【普通用户】- 学生/教师
  - user_ranking（我的排名）
  - book_recommend_base（推荐榜单）
  - book_recommendations（个性化推荐）
  - user_lend_summary（个人统计）
  - recent_lend_records（借阅记录）
*/

-- =============================================
-- 第七部分：系统用户表
-- 存储管理员账号
-- =============================================

-- 31. 系统用户表
DROP TABLE IF EXISTS `sys_user`;
CREATE TABLE `sys_user` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `userid` VARCHAR(64) NOT NULL COMMENT '用户ID',
  `username` VARCHAR(50) NOT NULL COMMENT '用户名',
  `password` VARCHAR(255) NOT NULL COMMENT '密码',
  `real_name` VARCHAR(50) DEFAULT NULL COMMENT '真实姓名',
  `birth_year` INT(11) DEFAULT NULL COMMENT '出生年份',
  `sex` VARCHAR(10) DEFAULT NULL COMMENT '性别',
  `dept` VARCHAR(100) DEFAULT NULL COMMENT '院系',
  `occupation` VARCHAR(100) DEFAULT NULL COMMENT '专业',
  `user_type` INT(11) NOT NULL DEFAULT 3 COMMENT '用户类型：1-系统管理员, 2-图书馆管理员, 3-普通用户',
  `reader_type` VARCHAR(50) DEFAULT NULL COMMENT '读者类型',
  `avatar` VARCHAR(255) DEFAULT NULL COMMENT '头像URL',
  `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
  `phone` VARCHAR(20) DEFAULT NULL COMMENT '手机号',
  `status` INT(11) NOT NULL DEFAULT 1 COMMENT '状态：0-禁用, 1-启用',
  `deleted` INT(11) NOT NULL DEFAULT 0 COMMENT '逻辑删除：0-未删除, 1-已删除',
  `create_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `last_login_time` TIMESTAMP NULL DEFAULT NULL COMMENT '最后登录时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_userid` (`userid`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

-- 插入默认管理员账号
INSERT INTO `sys_user` (`userid`, `username`, `password`, `real_name`, `user_type`, `status`) VALUES
('admin', 'admin', '123456', '系统管理员', 1, 1),
('librarian', 'librarian', '123456', '图书馆管理员', 2, 1);

COMMIT;
