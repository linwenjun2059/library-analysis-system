#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""步骤2：数据汇总（DWD → DWS层）"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
import sys

class DataAggregator:
    """数据汇总：DWD → DWS"""
    
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("Data Aggregation - DWD to DWS") \
            .enableHiveSupport() \
            .getOrCreate()
        
        if len(sys.argv) > 1 and sys.argv[1] != "all":
            self.year = int(sys.argv[1][:4])
            self.month = int(sys.argv[1][4:6])
            self.where_clause = f"WHERE year = {self.year} AND month = {self.month}"
            print(f"处理指定月份: {self.year}年{self.month}月")
        else:
            self.where_clause = ""
            print("处理所有数据 (2019-2020)")
    
    def load_dwd_data(self):
        """加载DWD层数据"""
        print("\n" + "=" * 60)
        print("加载DWD层数据...")
        
        self.lend_detail = self.spark.sql(f"""
            SELECT * FROM library_dwd.dwd_lend_detail
            {self.where_clause}
        """)
        
        self.book_info = self.spark.sql("""
            SELECT * FROM library_dwd.dwd_book_info
        """)
        
        self.user_info = self.spark.sql("""
            SELECT * FROM library_dwd.dwd_user_info
        """)
        
        print(f"✓ 借阅明细: {self.lend_detail.count():,} 条")
        print(f"✓ 图书信息: {self.book_info.count():,} 条")
        print(f"✓ 用户信息: {self.user_info.count():,} 条")
    
    def build_user_lend_summary(self):
        """构建用户借阅汇总表"""
        print("\n" + "=" * 60)
        print("[1/5] 构建用户借阅汇总表...")
        
        user_summary = self.lend_detail.groupBy("userid").agg(
            count("*").alias("total_lend_count"),
            sum("borrow_days").alias("total_borrow_days"),
            round(avg("borrow_days"), 2).alias("avg_borrow_days"),
            sum(when(col("is_overdue") == 1, 1).otherwise(0)).alias("overdue_count"),
            sum("renew_times").alias("renew_count"),
            min("lend_date").alias("first_lend_date"),
            max("lend_date").alias("last_lend_date"),
            countDistinct("lend_date").alias("active_days")
        )
        
        user_summary = user_summary.withColumn(
            "overdue_rate",
            round(col("overdue_count") / col("total_lend_count"), 2)
        )
        
        favorite_subject = self.lend_detail \
            .join(self.book_info, "book_id") \
            .groupBy("userid", "subject") \
            .count() \
            .withColumn("rank", row_number().over(Window.partitionBy("userid").orderBy(desc("count")))) \
            .filter(col("rank") == 1) \
            .select("userid", col("subject").alias("favorite_subject"))
        
        favorite_location = self.lend_detail \
            .join(self.book_info, "book_id") \
            .groupBy("userid", "location_name") \
            .count() \
            .withColumn("rank", row_number().over(Window.partitionBy("userid").orderBy(desc("count")))) \
            .filter(col("rank") == 1) \
            .select("userid", col("location_name").alias("favorite_location"))
        
        user_summary = user_summary \
            .join(favorite_subject, "userid", "left") \
            .join(favorite_location, "userid", "left")
        
        user_summary.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_dws.dws_user_lend_summary")
        
        print(f"✓ 用户借阅汇总完成: {user_summary.count():,} 个用户")
    
    def build_book_lend_summary(self):
        """构建图书借阅汇总表"""
        print("\n" + "=" * 60)
        print("[2/5] 构建图书借阅汇总表...")
        
        book_summary = self.lend_detail.groupBy("book_id").agg(
            count("*").alias("total_lend_count"),
            countDistinct("userid").alias("unique_user_count"),
            round(avg("borrow_days"), 2).alias("avg_borrow_days"),
            sum("borrow_days").alias("total_borrow_days"),
            sum(when(col("is_overdue") == 1, 1).otherwise(0)).alias("overdue_count"),
            sum("renew_times").alias("renew_count"),
            min("lend_date").alias("first_lend_date"),
            max("lend_date").alias("last_lend_date")
        )
        
        book_summary = book_summary \
            .withColumn("overdue_rate", round(col("overdue_count") / col("total_lend_count"), 2)) \
            .withColumn("lend_frequency", round(col("total_lend_count") / col("unique_user_count"), 2))
        
        book_summary.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_dws.dws_book_lend_summary")
        
        print(f"✓ 图书借阅汇总完成: {book_summary.count():,} 本图书")
    
    def build_dept_lend_summary(self):
        """构建院系借阅汇总表"""
        print("\n" + "=" * 60)
        print("[3/5] 构建院系借阅汇总表...")
        
        dept_summary = self.lend_detail \
            .join(self.user_info, "userid") \
            .groupBy("dept").agg(
                count("*").alias("total_lend_count"),
                countDistinct("userid").alias("unique_user_count"),
                countDistinct("book_id").alias("unique_book_count"),
                sum("borrow_days").alias("total_borrow_days"),
                round(avg("borrow_days"), 2).alias("avg_borrow_days"),
                sum(when(col("is_overdue") == 1, 1).otherwise(0)).alias("overdue_count")
            )
        
        dept_summary = dept_summary \
            .withColumn("avg_lend_per_user", round(col("total_lend_count") / col("unique_user_count"), 2)) \
            .withColumn("overdue_rate", round(col("overdue_count") / col("total_lend_count"), 2))
        
        favorite_subject = self.lend_detail \
            .join(self.user_info, "userid") \
            .join(self.book_info, "book_id") \
            .groupBy("dept", "subject") \
            .count() \
            .withColumn("rank", row_number().over(Window.partitionBy("dept").orderBy(desc("count")))) \
            .filter(col("rank") == 1) \
            .select("dept", 
                   col("subject").alias("favorite_subject"),
                   col("count").alias("subject_max_count"))
        
        favorite_location = self.lend_detail \
            .join(self.user_info, "userid") \
            .join(self.book_info, "book_id") \
            .groupBy("dept", "location_name") \
            .count() \
            .withColumn("rank", row_number().over(Window.partitionBy("dept").orderBy(desc("count")))) \
            .filter(col("rank") == 1) \
            .select("dept", col("location_name").alias("favorite_location"))
        
        dept_summary = dept_summary \
            .join(favorite_subject, "dept", "left") \
            .join(favorite_location, "dept", "left")
        
        dept_summary.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_dws.dws_dept_lend_summary")
        
        print(f"✓ 院系借阅汇总完成: {dept_summary.count():,} 个院系")
    
    def build_subject_lend_summary(self):
        """构建主题分类汇总表"""
        print("\n" + "=" * 60)
        print("[4/5] 构建主题分类汇总表...")
        
        subject_summary = self.lend_detail \
            .join(self.book_info, "book_id") \
            .groupBy("subject").agg(
                count("*").alias("total_lend_count"),
                countDistinct("userid").alias("unique_user_count"),
                countDistinct("book_id").alias("unique_book_count"),
                round(avg("borrow_days"), 2).alias("avg_borrow_days"),
                sum(when(col("is_overdue") == 1, 1).otherwise(0)).alias("overdue_count")
            )
        
        subject_summary = subject_summary.withColumn(
            "overdue_rate",
            round(col("overdue_count") / col("total_lend_count"), 2)
        )
        
        # 获取最受欢迎的院系
        popular_dept = self.lend_detail \
            .join(self.book_info, "book_id") \
            .join(self.user_info, "userid") \
            .groupBy("subject", "dept") \
            .count() \
            .withColumn("rank", row_number().over(Window.partitionBy("subject").orderBy(desc("count")))) \
            .filter(col("rank") == 1) \
            .select("subject", col("dept").alias("popular_dept"))
        
        subject_summary = subject_summary.join(popular_dept, "subject", "left")
        
        subject_summary.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_dws.dws_subject_lend_summary")
        
        print(f"✓ 主题分类汇总完成: {subject_summary.count():,} 个主题")
    
    def build_daily_stats(self):
        """构建每日统计表"""
        print("\n" + "=" * 60)
        print("[5/5] 构建每日统计表...")
        
        daily_lend = self.lend_detail.groupBy("lend_date").agg(
            count("*").alias("lend_count"),
            countDistinct("userid").alias("active_user_count")
        ).withColumnRenamed("lend_date", "stat_date")
        
        daily_return = self.lend_detail.filter(col("ret_date").isNotNull()).groupBy("ret_date").agg(
            count("*").alias("return_count")
        ).withColumnRenamed("ret_date", "stat_date")
        
        user_first_lend = self.lend_detail.groupBy("userid").agg(
            min("lend_date").alias("first_lend_date")
        )
        
        daily_new_users = user_first_lend.groupBy("first_lend_date").agg(
            count("*").alias("new_user_count")
        ).withColumnRenamed("first_lend_date", "stat_date")
        
        daily_overdue = self.lend_detail.filter(col("is_overdue") == 1).groupBy("lend_date").agg(
            count("*").alias("overdue_count")
        ).withColumnRenamed("lend_date", "stat_date")
        
        daily_avg_days = self.lend_detail.groupBy("lend_date").agg(
            round(avg("borrow_days"), 2).alias("avg_borrow_days")
        ).withColumnRenamed("lend_date", "stat_date")
        
        daily_stats = daily_lend \
            .join(daily_return, "stat_date", "full_outer") \
            .join(daily_new_users, "stat_date", "full_outer") \
            .join(daily_overdue, "stat_date", "full_outer") \
            .join(daily_avg_days, "stat_date", "full_outer") \
            .fillna(0)
        
        daily_stats.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_dws.dws_daily_stats")
        
        print(f"✓ 每日统计完成: {daily_stats.count():,} 天")
    
    def run(self):
        """运行汇总流程"""
        print("\n" + "█" * 60)
        print("开始数据汇总：DWD → DWS")
        print("█" * 60)
        
        try:
            self.load_dwd_data()
            self.build_user_lend_summary()
            self.build_book_lend_summary()
            self.build_dept_lend_summary()
            self.build_subject_lend_summary()
            self.build_daily_stats()
            
            print("\n" + "█" * 60)
            print("✅ DWS层构建完成（5张汇总表）")
            print("█" * 60)
            print("输出表：")
            print("  1. dws_user_lend_summary     - 用户借阅汇总")
            print("  2. dws_book_lend_summary     - 图书借阅汇总")
            print("  3. dws_dept_lend_summary     - 院系借阅汇总")
            print("  4. dws_subject_lend_summary  - 主题分类汇总")
            print("  5. dws_daily_stats           - 每日统计")
            print("█" * 60)
            
        except Exception as e:
            print(f"\n❌ 汇总失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            self.spark.stop()

if __name__ == "__main__":
    aggregator = DataAggregator()
    aggregator.run()
