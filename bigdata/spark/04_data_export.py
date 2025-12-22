#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
步骤4：数据导出（Hive → MySQL）
统一导出22张表到MySQL供业务系统使用

表分类：
- 维度表（3张）：用户维度、图书维度、近期借阅记录
- 汇总表（5张）：用户汇总、图书汇总、院系汇总、主题汇总、每日统计
- 聚合表（5张）：热门图书、活跃用户、院系偏好、借阅趋势、运营看板
- 功能表（9张）：用户画像、专业阅读、馆藏利用、出版社分析、出版年份分析、逾期分析、时间分布、用户排名、推荐基础表

注：推荐结果表（2张MySQL + 1张Hive）由05_book_recommend.py单独导出
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
import sys

class DataExporter:
    """数据导出：Hive → MySQL（22张表）"""
    
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("Data Export - Hive to MySQL") \
            .enableHiveSupport() \
            .getOrCreate()
        
        # MySQL连接配置（从环境变量读取，支持灵活配置）
        import os
        mysql_host = os.getenv("MYSQL_HOST", "master")
        mysql_port = os.getenv("MYSQL_PORT", "3306")
        mysql_user = os.getenv("MYSQL_USER", "root")
        mysql_password = os.getenv("MYSQL_PASSWORD", "780122")
        mysql_database = os.getenv("MYSQL_DATABASE", "library_analysis")
        
        self.mysql_url = f"jdbc:mysql://{mysql_host}:{mysql_port}/{mysql_database}?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai"
        self.mysql_properties = {
            "user": mysql_user,
            "password": mysql_password,
            "driver": "com.mysql.cj.jdbc.Driver"
        }
        
        print(f"MySQL连接: {mysql_host}:{mysql_port}/{mysql_database}")
        
        self.exported_count = 0
    
    # =============================================
    # 第一部分：维度表（3张）
    # =============================================
    
    def export_dimension_tables(self):
        """导出维度表（3张）"""
        print("\n" + "█" * 60)
        print("第一部分：导出维度表（3张）")
        print("█" * 60)
        
        self._export_user_dimension()
        self._export_book_dimension()
        self._export_recent_lend_records()
    
    def _export_user_dimension(self):
        """导出用户维度表"""
        print("\n" + "=" * 60)
        print(f"[{self.exported_count + 1}/22] 导出用户维度表...")
        
        user_df = self.spark.sql("""
            SELECT 
                userid, sex as gender, dept as dept_name, redr_type_name as user_type_name,
                CAST(CONCAT(year, '-', LPAD(month, 2, '0'), '-01') AS DATE) as import_date
            FROM library_dwd.dwd_user_info
        """)
        
        # 获取每个用户的最新记录
        latest_user = user_df.groupBy("userid").agg(max("import_date").alias("latest_date"))
        final_user = user_df.join(latest_user, 
            ["userid"], "inner"
        ).where(user_df.import_date == latest_user.latest_date
        ).select("userid", "gender", "dept_name", "user_type_name").distinct()
        
        count = final_user.count()
        print(f"   📊 用户数量: {count:,}")
        
        final_user.write.mode("overwrite").jdbc(self.mysql_url, "user_dimension", properties=self.mysql_properties)
        print("   ✅ user_dimension")
        self.exported_count += 1
    
    def _export_book_dimension(self):
        """导出图书维度表"""
        print("\n" + "=" * 60)
        print(f"[{self.exported_count + 1}/22] 导出图书维度表...")
        
        book_df = self.spark.sql("""
            SELECT book_id, title, author, publisher, isbn, pub_year, subject, 
                   call_no, location_name, doc_type_name,
                   CAST(CONCAT(year, '-', LPAD(month, 2, '0'), '-01') AS DATE) as import_date
            FROM library_dwd.dwd_book_info
        """)
        
        latest_book = book_df.groupBy("book_id").agg(max("import_date").alias("latest_date"))
        final_book = book_df.join(latest_book,
            ["book_id"], "inner"
        ).where(book_df.import_date == latest_book.latest_date
        ).select("book_id", "title", "author", "publisher",
                 "isbn", "pub_year", "subject", "call_no",
                 "location_name", "doc_type_name").distinct()
        
        count = final_book.count()
        print(f"   📊 图书数量: {count:,}")
        
        final_book.write.mode("overwrite").jdbc(self.mysql_url, "book_dimension", properties=self.mysql_properties)
        print("   ✅ book_dimension")
        self.exported_count += 1
    
    def _export_recent_lend_records(self):
        """导出近期借阅记录（数据中最近6个月）"""
        print("\n" + "=" * 60)
        print(f"[{self.exported_count + 1}/22] 导出近期借阅记录（数据中最近6个月）...")
        
        # 动态相对时间：基于数据中的最新日期往前推180天
        recent_df = self.spark.sql("""
            WITH max_date AS (
                SELECT MAX(lend_date) as latest_date
                FROM library_dwd.dwd_lend_detail
            )
            SELECT lend_id, userid, book_id, lend_date, lend_time,
                   ret_date, ret_time, renew_times, borrow_days, is_overdue
            FROM library_dwd.dwd_lend_detail
            WHERE lend_date >= DATE_SUB((SELECT latest_date FROM max_date), 180)
        """)
        
        count = recent_df.count()
        print(f"   📊 近期借阅数: {count:,}")
        
        recent_df.write.mode("overwrite").jdbc(self.mysql_url, "recent_lend_records", properties=self.mysql_properties)
        print("   ✅ recent_lend_records")
        self.exported_count += 1
    
    # =============================================
    # 第二部分：汇总表（5张）
    # =============================================
    
    def export_summary_tables(self):
        """导出汇总表（5张）"""
        print("\n" + "█" * 60)
        print("第二部分：导出汇总表（5张）")
        print("█" * 60)
        
        self._export_table("user_lend_summary", "library_dws.dws_user_lend_summary", "用户借阅汇总")
        self._export_table("book_lend_summary", "library_dws.dws_book_lend_summary", "图书借阅汇总")
        self._export_table("dept_lend_summary", "library_dws.dws_dept_lend_summary", "院系借阅汇总")
        self._export_table("subject_lend_summary", "library_dws.dws_subject_lend_summary", "主题分类汇总")
        
        # 每日统计（数据中最近1年）
        print("\n" + "=" * 60)
        print(f"[{self.exported_count + 1}/22] 导出每日统计（数据中最近1年）...")
        
        # 动态相对时间：基于数据中的最新日期往前推365天
        daily_df = self.spark.sql("""
            WITH max_date AS (
                SELECT MAX(stat_date) as latest_date
                FROM library_dws.dws_daily_stats
            )
            SELECT stat_date, lend_count, return_count, new_user_count,
                   active_user_count, overdue_count, avg_borrow_days
            FROM library_dws.dws_daily_stats
            WHERE stat_date >= DATE_SUB((SELECT latest_date FROM max_date), 365)
        """)
        
        count = daily_df.count()
        print(f"   📊 统计天数: {count:,}")
        
        daily_df.write.mode("overwrite").jdbc(self.mysql_url, "daily_stats", properties=self.mysql_properties)
        print("   ✅ daily_stats")
        self.exported_count += 1
    
    # =============================================
    # 第三部分：聚合表（5张）
    # =============================================
    
    def export_aggregation_tables(self):
        """导出聚合表（5张）"""
        print("\n" + "█" * 60)
        print("第三部分：导出聚合表（5张）")
        print("█" * 60)
        
        self._export_table("hot_books", "library_ads.ads_hot_books", "热门图书排行")
        self._export_table("active_users", "library_ads.ads_active_users", "活跃用户排行")
        self._export_table("dept_preference", "library_ads.ads_dept_preference", "院系偏好分析")
        self._export_table("lend_trend", "library_ads.ads_lend_trend", "借阅趋势")
        self._export_table("operation_dashboard", "library_ads.ads_operation_dashboard", "运营看板")
    
    # =============================================
    # 第四部分：功能表（9张）
    # =============================================
    
    def export_feature_tables(self):
        """导出功能表（9张）- 支持高级管理员、图书管理员、普通用户功能"""
        print("\n" + "█" * 60)
        print("第四部分：导出功能表（9张）")
        print("█" * 60)
        
        # 高级管理员功能表（5张）
        self._export_user_profile()
        self._export_major_reading_profile()
        self._export_table("collection_utilization_analysis", "library_ads.ads_collection_utilization", "馆藏利用分析")
        self._export_table("publisher_analysis", "library_ads.ads_publisher_analysis", "出版社分析")
        self._export_table("publish_year_analysis", "library_ads.ads_publish_year_analysis", "出版年份分析")
        
        # 图书管理员功能表（2张）
        self._export_table("overdue_analysis", "library_ads.ads_overdue_analysis", "逾期分析")
        self._export_table("time_distribution", "library_ads.ads_time_distribution", "时间分布")
        
        # 普通用户功能表（2张）
        self._export_table("user_ranking", "library_ads.ads_user_ranking", "用户排名")
        self._export_table("book_recommend_base", "library_ads.ads_book_recommend_base", "图书推荐基础表")
    
    def _export_user_profile(self):
        """导出用户画像表（需要处理ARRAY类型转JSON）"""
        print("\n" + "=" * 60)
        print(f"[{self.exported_count + 1}/22] 导出用户画像分析...")
        
        # 读取Hive表，将ARRAY转为JSON字符串
        df = self.spark.sql("""
            SELECT 
                userid,
                user_type,
                dept,
                occupation,
                gender,
                age_group,
                borrow_level,
                total_borrow_count,
                reading_breadth,
                to_json(favorite_subjects) as favorite_subjects,
                to_json(favorite_locations) as favorite_locations,
                avg_borrow_days,
                overdue_rate,
                last_borrow_date,
                to_json(user_tags) as user_tags
            FROM library_ads.ads_user_profile
        """)
        
        count = df.count()
        print(f"   📊 记录数: {count:,}")
        
        df.write.mode("overwrite").jdbc(self.mysql_url, "user_profile", properties=self.mysql_properties)
        print(f"   ✅ user_profile")
        self.exported_count += 1
    
    def _export_major_reading_profile(self):
        """导出专业阅读特征表（需要处理ARRAY类型转JSON）"""
        print("\n" + "=" * 60)
        print(f"[{self.exported_count + 1}/22] 导出专业阅读特征...")
        
        # 读取Hive表，将ARRAY转为JSON字符串
        df = self.spark.sql("""
            SELECT 
                dept,
                occupation,
                student_count,
                total_borrow_count,
                avg_borrow_per_student,
                to_json(core_subjects) as core_subjects,
                to_json(cross_subjects) as cross_subjects,
                reading_breadth_score,
                to_json(popular_books) as popular_books
            FROM library_ads.ads_major_reading_profile
        """)
        
        count = df.count()
        print(f"   📊 记录数: {count:,}")
        
        df.write.mode("overwrite").jdbc(self.mysql_url, "major_reading_profile", properties=self.mysql_properties)
        print(f"   ✅ major_reading_profile")
        self.exported_count += 1
    
    def _export_table(self, mysql_table, hive_table, desc):
        """通用导出方法"""
        print("\n" + "=" * 60)
        print(f"[{self.exported_count + 1}/22] 导出{desc}...")
        
        df = self.spark.sql(f"SELECT * FROM {hive_table}")
        count = df.count()
        print(f"   📊 记录数: {count:,}")
        
        df.write.mode("overwrite").jdbc(self.mysql_url, mysql_table, properties=self.mysql_properties)
        print(f"   ✅ {mysql_table}")
        self.exported_count += 1
    
    # =============================================
    # 主流程
    # =============================================
    
    def run(self):
        """运行完整导出流程"""
        print("\n" + "█" * 60)
        print("🚀 开始导出数据到MySQL")
        print("█" * 60)
        print("📋 总计：22张表")
        print("   - 维度表：3张（用户/图书/近期借阅）")
        print("   - 汇总表：5张（用户/图书/院系/主题/每日统计）")
        print("   - 聚合表：5张（热门图书/活跃用户/院系偏好/借阅趋势/运营看板）")
        print("   - 功能表：9张（用户画像/专业阅读/逾期分析/馆藏利用/时间分布/用户排名/出版社分析/出版年份分析/推荐基础）")
        print("💡 推荐结果表：2张MySQL + 1张Hive由05_book_recommend.py单独导出")
        print("█" * 60)
        
        try:
            import time
            start_time = time.time()
            
            # 第一部分：维度表
            self.export_dimension_tables()
            
            # 第二部分：汇总表
            self.export_summary_tables()
            
            # 第三部分：聚合表
            self.export_aggregation_tables()
            
            # 第四部分：推荐与功能表
            self.export_feature_tables()
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            print("\n" + "█" * 60)
            print(f"✅ 导出完成！共导出 {self.exported_count} 张表")
            print(f"⏱️  耗时: {elapsed:.2f} 秒")
            print("█" * 60)
            print("\n💡 提示：")
            print("   - 维度表：用于用户登录、图书搜索等基础业务")
            print("   - 汇总表：用于快速统计查询和数据分析")
            print("   - 聚合表：用于Dashboard可视化展示")
            print("   - 功能表：支持三大角色功能（高级管理员/图书管理员/普通用户）")
            print("   - 出版分析表：优化页面加载速度")
            print("   - 推荐表：由05_book_recommend.py生成（2张：推荐主表+统计表）")
            print("   - 历史借阅明细保留在Hive，按需查询")
            print("█" * 60)
            
        except Exception as e:
            print(f"\n❌ 导出失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            self.spark.stop()

if __name__ == "__main__":
    exporter = DataExporter()
    exporter.run()
