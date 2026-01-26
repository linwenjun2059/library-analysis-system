-- 优化 book_recommendations 表结构
-- 删除不必要的索引，提升写入性能

USE library_analysis;

-- 删除多余的索引（保留主键和最常用的查询索引）
ALTER TABLE book_recommendations DROP INDEX IF EXISTS idx_book_id;
ALTER TABLE book_recommendations DROP INDEX IF EXISTS idx_score;
ALTER TABLE book_recommendations DROP INDEX IF EXISTS idx_rec_sources;

-- 只保留：
-- 1. PRIMARY KEY (userid, book_id) - 主键
-- 2. idx_userid_rank (userid, rank_no) - 查询用户推荐列表时使用
