#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""步骤3：数据分析（DWS → ADS层）"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
import sys

class DataAnalyzer:
    """数据分析：DWS → ADS"""
    
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("Data Analysis - DWS to ADS") \
            .enableHiveSupport() \
            .getOrCreate()
    
    def load_dws_data(self):
        """加载DWS层数据"""
        print("\n" + "=" * 60)
        print("加载DWS层数据...")
        
        self.user_summary = self.spark.table("library_dws.dws_user_lend_summary")
        self.book_summary = self.spark.table("library_dws.dws_book_lend_summary")
        self.dept_summary = self.spark.table("library_dws.dws_dept_lend_summary")
        self.subject_summary = self.spark.table("library_dws.dws_subject_lend_summary")
        self.daily_stats = self.spark.table("library_dws.dws_daily_stats")
        
        self.book_info = self.spark.table("library_dwd.dwd_book_info")
        self.user_info = self.spark.table("library_dwd.dwd_user_info")
        
        print("✓ DWS层数据加载完成")
    
    def build_hot_books(self):
        """构建热门图书排行（TOP 100）"""
        print("\n" + "=" * 60)
        print("[1/5] 构建热门图书排行...")
        
        book_info_latest = self.book_info.groupBy("book_id").agg(
            first("title").alias("title"),
            first("author").alias("author"),
            first("subject").alias("subject")
        )
        
        hot_books = self.book_summary \
            .join(book_info_latest, "book_id") \
            .select(
                col("book_id"),
                col("title"),
                col("author"),
                col("subject"),
                col("total_lend_count").alias("borrow_count")
            ) \
            .orderBy(desc("borrow_count")) \
            .limit(100) \
            .withColumn("rank_no", row_number().over(Window.orderBy(desc("borrow_count"))))
        
        hot_books.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_hot_books")
        
        print(f"✓ 热门图书TOP100")
    
    def build_active_users(self):
        """构建活跃用户排行（TOP 100）"""
        print("\n" + "=" * 60)
        print("[2/5] 构建活跃用户排行...")
        
        user_info_latest = self.user_info.groupBy("userid").agg(
            first("dept").alias("dept"),
            first("redr_type_name").alias("redr_type_name")
        )
        
        active_users = self.user_summary \
            .join(user_info_latest, "userid") \
            .select(
                col("userid"),
                col("dept"),
                col("redr_type_name"),
                col("total_lend_count").alias("borrow_count")
            ) \
            .orderBy(desc("borrow_count")) \
            .limit(100) \
            .withColumn("rank_no", row_number().over(Window.orderBy(desc("borrow_count"))))
        
        active_users.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_active_users")
        
        print(f"✓ 活跃用户TOP100")
    
    def build_dept_preference(self):
        """构建院系偏好分析"""
        print("\n" + "=" * 60)
        print("[3/5] 构建院系偏好分析...")
        
        dept_preference = self.dept_summary.select(
            col("dept"),
            col("favorite_subject"),
            col("subject_max_count").alias("subject_lend_count"),
            col("total_lend_count"),
            round(col("subject_max_count") / col("total_lend_count"), 2).alias("preference_rate")
        )
        
        dept_preference.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_dept_preference")
        
        print(f"✓ 院系偏好分析完成: {dept_preference.count():,} 个院系")
    
    def build_lend_trend(self):
        """构建借阅趋势"""
        print("\n" + "=" * 60)
        print("[4/5] 构建借阅趋势...")
        
        lend_detail = self.spark.table("library_dwd.dwd_lend_detail")
        
        user_window = Window.partitionBy("userid").orderBy("lend_date")
        
        user_daily_lend = lend_detail.select(
            "userid",
            "lend_date"
        ).distinct().withColumn(
            "prev_lend_date",
            lag("lend_date", 1).over(user_window)
        ).withColumn(
            "days_since_last",
            when(col("prev_lend_date").isNotNull(),
                 datediff(col("lend_date"), col("prev_lend_date"))
            ).otherwise(None)
        )
        
        daily_return_users = user_daily_lend.filter(
            col("days_since_last") > 30
        ).groupBy("lend_date").agg(
            countDistinct("userid").alias("return_user_count")
        ).withColumnRenamed("lend_date", "stat_date")
        
        lend_trend = self.daily_stats.join(
            daily_return_users, 
            "stat_date", 
            "left"
        ).select(
            col("stat_date").alias("trend_date"),
            col("lend_count"),
            col("return_count"),
            col("active_user_count"),
            col("new_user_count"),
            coalesce(col("return_user_count"), lit(0)).alias("return_user_count"),
            round(col("lend_count") / col("active_user_count"), 2).alias("avg_lend_per_user"),
            lit("daily").alias("trend_type")
        ).orderBy("trend_date")
        
        lend_trend.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_lend_trend")
        
        print(f"✓ 借阅趋势完成: {lend_trend.count():,} 天")
    
    def build_operation_dashboard(self):
        """构建运营看板"""
        print("\n" + "=" * 60)
        print("[5/13] 构建运营看板...")
        
        total_users = self.user_summary.count()
        total_books = self.book_summary.count()
        total_lends = self.user_summary.agg(sum("total_lend_count")).collect()[0][0]
        total_overdues = self.user_summary.agg(sum("overdue_count")).collect()[0][0]
        avg_borrow_days = self.book_summary.agg(avg("avg_borrow_days")).collect()[0][0]
        
        sorted_stats = self.daily_stats.orderBy(desc("stat_date"))
        recent_stats = sorted_stats.limit(30).collect()
        
        def calc_compare(current, previous):
            if previous is None or previous == 0:
                return 0.0
            # 注意：不能直接用round()，因为from pyspark.sql.functions import * 会覆盖Python的round()
            return float(f"{(current - previous) / previous * 100:.2f}")
        
        # 辅助函数：获取历史数据
        def get_historical_value(days_ago, field):
            if len(recent_stats) > days_ago:
                return recent_stats[days_ago][field]
            return None
        
        # 今日数据（最新一天）
        today_lends = recent_stats[0]["lend_count"] if recent_stats else 0
        today_active_users = recent_stats[0]["active_user_count"] if recent_stats else 0
        
        # 昨日数据
        yesterday_lends = get_historical_value(1, "lend_count")
        yesterday_active = get_historical_value(1, "active_user_count")
        
        # 上周同期数据（7天前）
        lastweek_lends = get_historical_value(7, "lend_count")
        lastweek_active = get_historical_value(7, "active_user_count")
        
        # 上月同期数据（30天前）
        lastmonth_lends = get_historical_value(30, "lend_count")
        lastmonth_active = get_historical_value(30, "active_user_count")
        
        # 计算环比
        lends_vs_yesterday = calc_compare(today_lends, yesterday_lends)
        lends_vs_lastweek = calc_compare(today_lends, lastweek_lends)
        lends_vs_lastmonth = calc_compare(today_lends, lastmonth_lends)
        
        active_vs_yesterday = calc_compare(today_active_users, yesterday_active)
        active_vs_lastweek = calc_compare(today_active_users, lastweek_active)
        active_vs_lastmonth = calc_compare(today_active_users, lastmonth_active)
        
        # 判断趋势
        def get_trend(compare_yesterday):
            if compare_yesterday > 5:
                return "up"
            elif compare_yesterday < -5:
                return "down"
            else:
                return "stable"
        
        # 构建指标数据
        # 注意：不能直接用round()，因为from pyspark.sql.functions import * 会覆盖Python的round()
        avg_days_value = float(f"{float(avg_borrow_days):.2f}") if avg_borrow_days else 0.0
        avg_days_str = f"{avg_days_value:.2f}"
        
        metrics = [
            ("total_users", str(total_users), 0.0, 0.0, 0.0, "stable", "user"),
            ("total_books", str(total_books), 0.0, 0.0, 0.0, "stable", "book"),
            ("total_lends", str(total_lends), 0.0, 0.0, 0.0, "stable", "lend"),
            ("today_lends", str(today_lends), lends_vs_yesterday, lends_vs_lastweek, lends_vs_lastmonth, get_trend(lends_vs_yesterday), "daily"),
            ("today_active_users", str(today_active_users), active_vs_yesterday, active_vs_lastweek, active_vs_lastmonth, get_trend(active_vs_yesterday), "daily"),
            ("total_overdues", str(total_overdues), 0.0, 0.0, 0.0, "stable", "overdue"),
            ("avg_borrow_days", avg_days_str, 0.0, 0.0, 0.0, "stable", "stat")
        ]
        
        dashboard = self.spark.createDataFrame(metrics, [
            "metric_name", "metric_value", "compare_yesterday",
            "compare_last_week", "compare_last_month", "trend", "category"
        ])
        
        dashboard.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_operation_dashboard")
        
        print(f"✓ 运营看板完成: {dashboard.count():,} 个指标")
        print(f"  今日借阅: {today_lends} (环比昨日: {lends_vs_yesterday:+.2f}%)")
        print(f"  活跃用户: {today_active_users} (环比昨日: {active_vs_yesterday:+.2f}%)")
    
    def build_user_profile(self):
        """构建用户画像分析（高级管理员）"""
        print("\n" + "=" * 60)
        print("[6/13] 构建用户画像分析...")
        
        from pyspark.sql import functions as F
        
        # 加载明细数据用于计算阅读广度
        lend_detail = self.spark.table("library_dwd.dwd_lend_detail")
        
        # 计算每个用户的阅读广度（涉及主题数）
        user_breadth = lend_detail.join(self.book_info, "book_id") \
            .groupBy("userid") \
            .agg(countDistinct("subject").alias("reading_breadth"))
        
        # 计算用户偏好主题TOP3和位置TOP3
        user_subject_top = lend_detail.join(self.book_info, "book_id") \
            .groupBy("userid", "subject") \
            .agg(count("*").alias("cnt")) \
            .withColumn("rn", row_number().over(Window.partitionBy("userid").orderBy(desc("cnt")))) \
            .filter(col("rn") <= 3) \
            .groupBy("userid") \
            .agg(collect_list("subject").alias("favorite_subjects"))
        
        user_location_top = lend_detail.join(self.book_info, "book_id") \
            .groupBy("userid", "location_name") \
            .agg(count("*").alias("cnt")) \
            .withColumn("rn", row_number().over(Window.partitionBy("userid").orderBy(desc("cnt")))) \
            .filter(col("rn") <= 3) \
            .groupBy("userid") \
            .agg(collect_list("location_name").alias("favorite_locations"))
        
        # 获取用户基本信息
        user_info_agg = self.user_info.groupBy("userid").agg(
            first("redr_type_name").alias("user_type"),
            first("dept").alias("dept"),
            first("occupation").alias("occupation"),
            first("sex").alias("gender"),
            first("age").alias("age")
        )
        
        # 构建用户画像
        user_profile = self.user_summary \
            .join(user_info_agg, "userid", "left") \
            .join(user_breadth, "userid", "left") \
            .join(user_subject_top, "userid", "left") \
            .join(user_location_top, "userid", "left") \
            .select(
                col("userid"),
                col("user_type"),
                col("dept"),
                col("occupation"),
                col("gender"),
                when(col("age") < 20, "20以下")
                    .when(col("age") < 25, "20-24岁")
                    .when(col("age") < 30, "25-29岁")
                    .when(col("age") < 40, "30-39岁")
                    .otherwise("40岁以上").alias("age_group"),
                when(col("total_lend_count") >= 20, "活跃")
                    .when(col("total_lend_count") >= 5, "一般")
                    .otherwise("不活跃").alias("borrow_level"),
                col("total_lend_count").alias("total_borrow_count"),
                coalesce(col("reading_breadth"), lit(0)).alias("reading_breadth"),
                col("favorite_subjects"),
                col("favorite_locations"),
                col("avg_borrow_days"),
                col("overdue_rate"),
                col("last_lend_date").alias("last_borrow_date"),
                # 生成用户标签（基于用户行为特征）
                array_distinct(
                    array_union(
                        array_union(
                            array_union(
                                # 1. 借阅频率标签（基于total_lend_count）
                                when(col("total_lend_count") >= 100, array(lit("骨灰级读者")))
                                .when(col("total_lend_count") >= 50, array(lit("超级读者")))
                                .when(col("total_lend_count") >= 20, array(lit("活跃读者")))
                                .when(col("total_lend_count") >= 5, array(lit("普通读者")))
                                .otherwise(array(lit("新用户"))),
                                
                                # 2. 逾期行为标签（基于overdue_rate）
                                when(col("overdue_rate") == 0, array(lit("守时借阅")))
                                .when(col("overdue_rate") < 0.05, array(lit("极少逾期")))
                                .when(col("overdue_rate") < 0.2, array(lit("偶尔逾期")))
                                .when(col("overdue_rate") >= 0.5, array(lit("高频逾期")))
                                .otherwise(array())
                            ),
                            array_union(
                                # 3. 阅读广度标签（基于reading_breadth）
                                when(coalesce(col("reading_breadth"), lit(0)) >= 15, array(lit("博览群书")))
                                .when(coalesce(col("reading_breadth"), lit(0)) >= 10, array(lit("跨学科阅读")))
                                .when(coalesce(col("reading_breadth"), lit(0)) >= 5, array(lit("涉猎广泛")))
                                .when(coalesce(col("reading_breadth"), lit(0)) >= 2, array(lit("专注阅读")))
                                .otherwise(array()),
                                
                                # 4. 借阅时长标签（基于avg_borrow_days）
                                when(col("avg_borrow_days") >= 30, array(lit("长期保留")))
                                .when(col("avg_borrow_days") >= 20, array(lit("深度阅读")))
                                .when(col("avg_borrow_days") < 7, array(lit("快速阅读")))
                                .otherwise(array())
                            )
                        ),
                        array_union(
                            array_union(
                                # 5. 活跃状态标签（基于last_lend_date，使用数据集截止日期而非当前日期）
                                when(datediff(lit("2020-12-31"), col("last_lend_date")) <= 30, array(lit("当前活跃")))
                                .when(datediff(lit("2020-12-31"), col("last_lend_date")) <= 90, array(lit("近期活跃")))
                                .when(datediff(lit("2020-12-31"), col("last_lend_date")) >= 180, array(lit("沉睡用户")))
                                .otherwise(array()),
                                
                                # 6. 续借行为标签（基于renew_count和total_lend_count的比例）
                                when(col("total_lend_count") > 0,
                                    when((col("renew_count") / col("total_lend_count")) >= 0.5, array(lit("常续借")))
                                    .when((col("renew_count") / col("total_lend_count")) >= 0.2, array(lit("偶尔续借")))
                                    .otherwise(array())
                                ).otherwise(array())
                            ),
                            array_union(
                                # 7. 用户忠诚度标签（基于active_days和总时长）
                                when(col("active_days") >= 100, array(lit("高频使用")))
                                .when(col("active_days") >= 30, array(lit("持续借阅")))
                                .otherwise(array()),
                                
                                # 8. 用户类型标签（基于user_type）
                                when(col("user_type").isNotNull(),
                                    when(col("user_type").contains("教师") | col("user_type").contains("老师"), array(lit("教师用户")))
                                    .when(col("user_type").contains("学生") | col("user_type").contains("本科") | col("user_type").contains("研究生"), array(lit("学生用户")))
                                    .when(col("user_type").contains("教职工") | col("user_type").contains("员工"), array(lit("教职工用户")))
                                    .otherwise(array())
                                ).otherwise(array())
                            )
                        )
                    )
                ).alias("user_tags")
            )
        
        user_profile.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_user_profile")
        
        print(f"✓ 用户画像完成: {user_profile.count():,} 个用户")
    
    def build_resource_optimization(self):
        """构建资源优化建议（高级管理员）"""
        print("\n" + "=" * 60)
        print("[7/13] 构建资源优化建议...")
        
        # 获取图书信息
        book_info_agg = self.book_info.groupBy("book_id").agg(
            first("title").alias("title"),
            first("author").alias("author"),
            first("subject").alias("subject")
        )
        
        # 1. 超级热门图书（借阅次数>=30，紧急需要增加复本）
        super_hot_books = self.book_summary \
            .filter(col("total_lend_count") >= 30) \
            .join(book_info_agg, "book_id") \
            .select(
                lit("超级热门").alias("optimization_type"),
                col("book_id"),
                col("title"),
                col("author"),
                col("subject"),
                col("total_lend_count").alias("borrow_count"),
                col("last_lend_date"),
                concat(lit("紧急增加复本（当前借阅"), col("total_lend_count"), lit("次）")).alias("recommendation"),
                lit(10).alias("priority")
            )
        
        # 2. 热门图书（借阅次数10-29，建议增加复本）
        hot_books = self.book_summary \
            .filter((col("total_lend_count") >= 10) & (col("total_lend_count") < 30)) \
            .join(book_info_agg, "book_id") \
            .select(
                lit("热门图书").alias("optimization_type"),
                col("book_id"),
                col("title"),
                col("author"),
                col("subject"),
                col("total_lend_count").alias("borrow_count"),
                col("last_lend_date"),
                concat(lit("建议增加复本（当前借阅"), col("total_lend_count"), lit("次）")).alias("recommendation"),
                lit(5).alias("priority")
            )
        
        # 3. 冷门图书（借阅次数<3且超过180天未借，使用数据集截止日期）
        cold_books = self.book_summary \
            .filter((col("total_lend_count") < 3) & (datediff(lit("2020-12-31"), col("last_lend_date")) > 180)) \
            .join(book_info_agg, "book_id") \
            .select(
                lit("冷门图书").alias("optimization_type"),
                col("book_id"),
                col("title"),
                col("author"),
                col("subject"),
                col("total_lend_count").alias("borrow_count"),
                col("last_lend_date"),
                concat(
                    lit("建议调整位置或剔旧（借阅"), 
                    col("total_lend_count"), 
                    lit("次，最后借阅"),
                    datediff(lit("2020-12-31"), col("last_lend_date")),
                    lit("天前）")
                ).alias("recommendation"),
                lit(2).alias("priority")
            )
        
        # 4. 僵尸图书（从未被借阅，优先级最低）
        # 关键修复：从book_info中找出不在book_summary中的图书（即从未被借阅的）
        borrowed_book_ids = self.book_summary.select("book_id")
        zombie_books = book_info_agg \
            .join(borrowed_book_ids, "book_id", "left_anti") \
            .select(
                lit("僵尸图书").alias("optimization_type"),
                col("book_id"),
                col("title"),
                col("author"),
                col("subject"),
                lit(0).alias("borrow_count"),
                lit(None).cast("string").alias("last_lend_date"),
                lit("从未被借阅，建议评估是否保留").alias("recommendation"),
                lit(1).alias("priority")
            )
        
        # 合并所有优化建议
        optimization = super_hot_books.union(hot_books).union(cold_books).union(zombie_books)
        
        optimization.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_resource_optimization")
        
        print(f"✓ 资源优化建议完成: {optimization.count():,} 条建议")
    
    def build_major_reading_profile(self):
        """构建专业阅读特征分析（高级管理员）"""
        print("\n" + "=" * 60)
        print("[8/13] 构建专业阅读特征分析...")
        
        # 加载明细数据
        lend_detail = self.spark.table("library_dwd.dwd_lend_detail")
        
        # 按院系专业统计
        user_info_agg = self.user_info.groupBy("userid").agg(
            first("dept").alias("dept"),
            first("occupation").alias("occupation")
        )
        
        lend_with_user = lend_detail.join(user_info_agg, "userid")
        lend_with_book = lend_with_user.join(
            self.book_info.groupBy("book_id").agg(
                first("subject").alias("subject"),
                first("title").alias("title")
            ),
            "book_id"
        )
        
        # 1. 所有学科借阅统计（基础数据，只计算一次）
        all_subjects = lend_with_book.groupBy("dept", "occupation", "subject") \
            .agg(count("*").alias("cnt"))
        
        # 2. 核心学科TOP5（从all_subjects中筛选）
        major_subjects_detail = all_subjects \
            .withColumn("rn", row_number().over(Window.partitionBy("dept", "occupation").orderBy(desc("cnt")))) \
            .filter(col("rn") <= 5)
        
        major_subjects = major_subjects_detail \
            .groupBy("dept", "occupation") \
            .agg(collect_list("subject").alias("core_subjects"))
        
        # 3. 跨学科借阅TOP3（从all_subjects中排除核心学科）
        # 先获取每个专业的核心学科集合
        core_subjects_set = major_subjects_detail \
            .groupBy("dept", "occupation") \
            .agg(collect_set("subject").alias("core_set"))
        
        # 从all_subjects中过滤掉核心学科，找出跨学科借阅TOP3
        cross_subjects = all_subjects.join(core_subjects_set, ["dept", "occupation"]) \
            .filter(~array_contains(col("core_set"), col("subject"))) \
            .withColumn("rn", row_number().over(Window.partitionBy("dept", "occupation").orderBy(desc("cnt")))) \
            .filter(col("rn") <= 3) \
            .groupBy("dept", "occupation") \
            .agg(collect_list("subject").alias("cross_subjects"))
        
        # 4. 热门书目TOP10
        major_books = lend_with_book.groupBy("dept", "occupation", "title") \
            .agg(count("*").alias("cnt")) \
            .withColumn("rn", row_number().over(Window.partitionBy("dept", "occupation").orderBy(desc("cnt")))) \
            .filter(col("rn") <= 10) \
            .groupBy("dept", "occupation") \
            .agg(collect_list("title").alias("popular_books"))
        
        # 5. 基础统计
        major_stats = lend_with_user.groupBy("dept", "occupation") \
            .agg(
                countDistinct("userid").alias("student_count"),
                count("*").alias("total_borrow_count")
            ) \
            .withColumn("avg_borrow_per_student", 
                       round(col("total_borrow_count") / col("student_count"), 2))
        
        # 6. 计算阅读广度得分（涉及主题数/10，最高1.0分）
        breadth_score = lend_with_book.groupBy("dept", "occupation") \
            .agg(countDistinct("subject").alias("breadth")) \
            .withColumn("reading_breadth_score", 
                       when(col("breadth") >= 10, 1.0).otherwise(round(col("breadth") / 10.0, 2)))
        
        # 7. 合并所有数据
        major_profile = major_stats \
            .join(major_subjects, ["dept", "occupation"], "left") \
            .join(cross_subjects, ["dept", "occupation"], "left") \
            .join(major_books, ["dept", "occupation"], "left") \
            .join(breadth_score.select("dept", "occupation", "reading_breadth_score"), 
                  ["dept", "occupation"], "left") \
            .select(
                col("dept"),
                col("occupation"),
                col("student_count"),
                col("total_borrow_count"),
                col("avg_borrow_per_student"),
                col("core_subjects"),
                coalesce(col("cross_subjects"), array().cast("array<string>")).alias("cross_subjects"),
                coalesce(col("reading_breadth_score"), lit(0.0)).alias("reading_breadth_score"),
                col("popular_books")
            )
        
        major_profile.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_major_reading_profile")
        
        print(f"✓ 专业阅读特征完成: {major_profile.count():,} 个专业")
    
    def build_overdue_analysis(self):
        """构建逾期分析（图书管理员）"""
        print("\n" + "=" * 60)
        print("[9/13] 构建逾期分析...")
        
        # 加载明细数据，计算真实的逾期天数和当前逾期状态
        lend_detail = self.spark.table("library_dwd.dwd_lend_detail")
        
        # 1. 计算每个用户的平均逾期天数（只统计逾期的记录）
        user_overdue_days = lend_detail \
            .filter(col("is_overdue") == 1) \
            .withColumn("overdue_days", col("borrow_days") - 30) \
            .groupBy("userid") \
            .agg(avg("overdue_days").alias("avg_overdue_days"))
        
        # 2. 计算当前逾期数量（ret_date为空且borrow_days>30）
        current_overdue_count_user = lend_detail \
            .filter((col("ret_date").isNull()) & (datediff(lit("2020-12-31"), col("lend_date")) > 30)) \
            .groupBy("userid") \
            .agg(count("*").alias("current_overdue_count"))
        
        # 3. 用户维度逾期分析
        user_overdue = self.user_summary \
            .join(self.user_info.groupBy("userid").agg(
                first("dept").alias("dept")
            ), "userid") \
            .filter(col("overdue_count") > 0) \
            .join(user_overdue_days, "userid", "left") \
            .join(current_overdue_count_user, "userid", "left") \
            .select(
                lit("用户").alias("analysis_type"),
                col("userid").alias("target_id"),
                col("dept").alias("target_name"),
                col("overdue_count"),
                col("total_lend_count").alias("total_borrow_count"),
                col("overdue_rate"),
                round(coalesce(col("avg_overdue_days"), lit(0.0)), 2).alias("avg_overdue_days"),
                coalesce(col("current_overdue_count"), lit(0)).alias("current_overdue_count"),
                when(col("overdue_rate") > 0.3, "高")
                    .when(col("overdue_rate") > 0.1, "中")
                    .otherwise("低").alias("risk_level")
            )
        
        # 4. 院系维度逾期分析
        # 先关联用户院系信息到借阅明细
        lend_with_dept = lend_detail.join(
            self.user_info.groupBy("userid").agg(first("dept").alias("dept")),
            "userid"
        )
        
        # 计算各院系的平均逾期天数
        dept_overdue_days = lend_with_dept \
            .filter(col("is_overdue") == 1) \
            .withColumn("overdue_days", col("borrow_days") - 30) \
            .groupBy("dept") \
            .agg(avg("overdue_days").alias("avg_overdue_days"))
        
        # 计算各院系的当前逾期数量
        current_overdue_count_dept = lend_with_dept \
            .filter((col("ret_date").isNull()) & (datediff(lit("2020-12-31"), col("lend_date")) > 30)) \
            .groupBy("dept") \
            .agg(count("*").alias("current_overdue_count"))
        
        dept_overdue = self.dept_summary \
            .filter(col("overdue_count") > 0) \
            .join(dept_overdue_days, "dept", "left") \
            .join(current_overdue_count_dept, "dept", "left") \
            .select(
                lit("院系").alias("analysis_type"),
                col("dept").alias("target_id"),
                col("dept").alias("target_name"),
                col("overdue_count"),
                col("total_lend_count").alias("total_borrow_count"),
                col("overdue_rate"),
                round(coalesce(col("avg_overdue_days"), lit(0.0)), 2).alias("avg_overdue_days"),
                coalesce(col("current_overdue_count"), lit(0)).alias("current_overdue_count"),
                when(col("overdue_rate") > 0.2, "高")
                    .when(col("overdue_rate") > 0.1, "中")
                    .otherwise("低").alias("risk_level")
            )
        
        # 5. 合并所有维度的逾期分析
        overdue_analysis = user_overdue.union(dept_overdue)
        
        overdue_analysis.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_overdue_analysis")
        
        print(f"✓ 逾期分析完成: {overdue_analysis.count():,} 条记录")
    
    def build_circulation_rate(self):
        """构建馆藏流通率分析（高级管理员）"""
        print("\n" + "=" * 60)
        print("[10/13] 构建馆藏流通率分析...")
        
        # 按位置统计
        # 第1步：统计每个位置的馆藏总数
        location_total = self.book_info.groupBy("location_name").agg(
            countDistinct("book_id").alias("total_books")
        )
        
        # 第2步：从book_info获取每本书的位置，然后与book_summary关联
        book_with_location = self.book_info.select("book_id", "location_name").distinct()
        
        # 第3步：统计每个位置被借阅的图书情况
        location_borrowed = self.book_summary.join(
            book_with_location,
            "book_id",
            "inner"  # 只统计被借过的
        ).groupBy("location_name").agg(
            countDistinct("book_id").alias("borrowed_books"),  # 被借的不同图书数
            sum("total_lend_count").alias("total_lend_sum"),
            avg("total_lend_count").alias("avg_borrow_times"),
            sum(when(col("total_lend_count") > 5, 1).otherwise(0)).alias("high_demand_books"),
            sum(when(col("total_lend_count") == 0, 1).otherwise(0)).alias("zero_borrow_books")
        )
        
        # 第4步：合并统计
        location_stats = location_total.join(
            location_borrowed,
            "location_name",
            "left"
        ).select(
            lit("位置").alias("dimension_type"),
            col("location_name").alias("dimension_value"),
            col("total_books"),
            coalesce(col("borrowed_books"), lit(0)).alias("borrowed_books"),
            round(coalesce(col("borrowed_books"), lit(0)) / col("total_books"), 2).alias("circulation_rate"),
            round(coalesce(col("avg_borrow_times"), lit(0.0)), 2).alias("avg_borrow_times"),
            coalesce(col("high_demand_books"), lit(0)).alias("high_demand_books"),
            coalesce(col("zero_borrow_books"), lit(0)).alias("zero_borrow_books"),
            # 周转率 = 总借阅次数 / 馆藏总数 / 时间跨度(2年)
            round(coalesce(col("total_lend_sum"), lit(0)) / col("total_books") / lit(2.0), 2).alias("turnover_rate")
        )
        
        # 按主题统计
        # 第1步：统计每个主题的馆藏总数
        subject_total = self.book_info.groupBy("subject").agg(
            countDistinct("book_id").alias("total_books")
        )
        
        # 第2步：从book_info获取每本书的主题，然后与book_summary关联
        book_with_subject = self.book_info.select("book_id", "subject").distinct()
        
        # 第3步：统计每个主题被借阅的图书情况
        subject_borrowed = self.book_summary.join(
            book_with_subject,
            "book_id",
            "inner"  # 只统计被借过的
        ).groupBy("subject").agg(
            countDistinct("book_id").alias("borrowed_books"),  # 被借的不同图书数
            sum("total_lend_count").alias("total_lend_sum"),
            avg("total_lend_count").alias("avg_borrow_times"),
            sum(when(col("total_lend_count") > 5, 1).otherwise(0)).alias("high_demand_books"),
            sum(when(col("total_lend_count") == 0, 1).otherwise(0)).alias("zero_borrow_books")
        )
        
        # 第4步：合并统计
        subject_stats = subject_total.join(
            subject_borrowed,
            "subject",
            "left"
        ).select(
            lit("主题").alias("dimension_type"),
            col("subject").alias("dimension_value"),
            col("total_books"),
            coalesce(col("borrowed_books"), lit(0)).alias("borrowed_books"),
            round(coalesce(col("borrowed_books"), lit(0)) / col("total_books"), 2).alias("circulation_rate"),
            round(coalesce(col("avg_borrow_times"), lit(0.0)), 2).alias("avg_borrow_times"),
            coalesce(col("high_demand_books"), lit(0)).alias("high_demand_books"),
            coalesce(col("zero_borrow_books"), lit(0)).alias("zero_borrow_books"),
            # 周转率 = 总借阅次数 / 馆藏总数 / 时间跨度(2年)
            round(coalesce(col("total_lend_sum"), lit(0)) / col("total_books") / lit(2.0), 2).alias("turnover_rate")
        )
        
        # 合并
        circulation = location_stats.union(subject_stats)
        
        circulation.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_circulation_rate")
        
        print(f"✓ 馆藏流通率完成: {circulation.count():,} 条记录")
    
    def build_time_distribution(self):
        """构建时间分布分析（图书管理员）"""
        print("\n" + "=" * 60)
        print("[11/13] 构建时间分布分析...")
        
        lend_detail = self.spark.table("library_dwd.dwd_lend_detail")
        
        # 1. 按小时统计借阅
        hour_borrow = lend_detail.groupBy("lend_hour").agg(
            count("*").alias("borrow_count"),
            countDistinct("userid").alias("active_user_count")
        )
        
        # 按小时统计归还（只统计已归还的记录）
        hour_return = lend_detail.filter(col("ret_date").isNotNull()) \
            .groupBy("ret_hour").agg(
                count("*").alias("return_count")
            )
        
        # 计算小时总借阅量用于占比
        total_borrow_hour = lend_detail.count()
        
        hour_dist = hour_borrow \
            .join(hour_return, hour_borrow["lend_hour"] == hour_return["ret_hour"], "left") \
            .select(
                lit("小时").alias("time_type"),
                col("lend_hour").alias("time_value"),
                col("borrow_count"),
                coalesce(col("return_count"), lit(0)).alias("return_count"),
                col("active_user_count"),
                round(col("borrow_count") / lit(total_borrow_hour), 2).alias("percentage")
            )
        
        # 2. 按星期统计借阅
        weekday_borrow = lend_detail.groupBy("lend_weekday").agg(
            count("*").alias("borrow_count"),
            countDistinct("userid").alias("active_user_count")
        )
        
        # 按星期统计归还
        weekday_return = lend_detail.filter(col("ret_date").isNotNull()) \
            .groupBy("ret_weekday").agg(
                count("*").alias("return_count")
            )
        
        total_borrow_weekday = lend_detail.count()
        
        weekday_dist = weekday_borrow \
            .join(weekday_return, weekday_borrow["lend_weekday"] == weekday_return["ret_weekday"], "left") \
            .select(
                lit("星期").alias("time_type"),
                col("lend_weekday").alias("time_value"),
                col("borrow_count"),
                coalesce(col("return_count"), lit(0)).alias("return_count"),
                col("active_user_count"),
                round(col("borrow_count") / lit(total_borrow_weekday), 2).alias("percentage")
            )
        
        # 3. 按月份统计借阅
        month_borrow = lend_detail.groupBy("lend_month").agg(
            count("*").alias("borrow_count"),
            countDistinct("userid").alias("active_user_count")
        )
        
        # 按月份统计归还
        month_return = lend_detail.filter(col("ret_date").isNotNull()) \
            .groupBy("ret_month").agg(
                count("*").alias("return_count")
            )
        
        total_borrow_month = lend_detail.count()
        
        month_dist = month_borrow \
            .join(month_return, month_borrow["lend_month"] == month_return["ret_month"], "left") \
            .select(
                lit("月份").alias("time_type"),
                col("lend_month").alias("time_value"),
                col("borrow_count"),
                coalesce(col("return_count"), lit(0)).alias("return_count"),
                col("active_user_count"),
                round(col("borrow_count") / lit(total_borrow_month), 2).alias("percentage")
            )
        
        # 4. 合并所有维度
        time_dist = hour_dist.union(weekday_dist).union(month_dist)
        
        time_dist.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_time_distribution")
        
        print(f"✓ 时间分布分析完成: {time_dist.count():,} 条记录")
    
    def build_user_ranking(self):
        """构建用户排名（普通用户）"""
        print("\n" + "=" * 60)
        print("[12/13] 构建用户排名...")
        
        # 获取用户信息
        user_info_agg = self.user_info.groupBy("userid").agg(
            first("dept").alias("dept"),
            first("occupation").alias("occupation"),
            first("redr_type_name").alias("user_type")
        )
        
        user_with_info = self.user_summary \
            .join(user_info_agg, "userid") \
            .select(
                col("userid"),
                col("dept"),
                col("occupation"),
                col("user_type"),
                col("total_lend_count").alias("total_borrow_count")
            )
        
        # 院系内排名
        user_with_dept_rank = user_with_info.withColumn(
            "dept_rank",
            row_number().over(Window.partitionBy("dept").orderBy(desc("total_borrow_count")))
        )
        
        # 专业内排名
        user_with_ranks = user_with_dept_rank.withColumn(
            "occupation_rank",
            row_number().over(Window.partitionBy("dept", "occupation").orderBy(desc("total_borrow_count")))
        )
        
        # 计算总数和百分位
        dept_counts = user_with_info.groupBy("dept").agg(
            count("userid").alias("dept_total_users")
        )
        
        occupation_counts = user_with_info.groupBy("dept", "occupation").agg(
            count("userid").alias("occupation_total_users")
        )
        
        user_ranking = user_with_ranks \
            .join(dept_counts, "dept") \
            .join(occupation_counts, ["dept", "occupation"]) \
            .withColumn("percentile_dept", 
                       round((1 - col("dept_rank") / col("dept_total_users")) * 100, 2)) \
            .withColumn("percentile_occupation",
                       round((1 - col("occupation_rank") / col("occupation_total_users")) * 100, 2))
        
        user_ranking.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_user_ranking")
        
        print(f"✓ 用户排名完成: {user_ranking.count():,} 个用户")
    
    def build_book_recommend_base(self):
        """构建图书推荐基础表（普通用户）"""
        print("\n" + "=" * 60)
        print("[13/13] 构建图书推荐基础表...")
        
        book_info_agg = self.book_info.groupBy("book_id").agg(
            first("title").alias("title"),
            first("author").alias("author"),
            first("subject").alias("subject")
        )
        
        # 全校热门榜TOP50（一次排序，避免重复）
        global_hot = self.book_summary \
            .join(book_info_agg, "book_id") \
            .withColumn("rank_no", row_number().over(Window.orderBy(desc("total_lend_count")))) \
            .filter(col("rank_no") <= 50) \
            .select(
                lit("热门榜").alias("recommend_type"),
                lit("全校").alias("scope"),
                col("book_id"),
                col("title"),
                col("author"),
                col("subject"),
                col("total_lend_count").alias("borrow_count"),
                col("rank_no"),
                current_date().alias("update_date")
            )
        
        # 按院系热门榜TOP30
        lend_detail = self.spark.table("library_dwd.dwd_lend_detail")
        user_info_agg = self.user_info.groupBy("userid").agg(
            first("dept").alias("dept")
        )
        
        dept_hot = lend_detail \
            .join(user_info_agg, "userid") \
            .groupBy("dept", "book_id").agg(count("*").alias("borrow_count")) \
            .withColumn("rank_no", row_number().over(Window.partitionBy("dept").orderBy(desc("borrow_count")))) \
            .filter(col("rank_no") <= 30) \
            .join(book_info_agg, "book_id") \
            .select(
                lit("院系榜").alias("recommend_type"),
                col("dept").alias("scope"),
                col("book_id"),
                col("title"),
                col("author"),
                col("subject"),
                col("borrow_count"),
                col("rank_no"),
                current_date().alias("update_date")
            )
        
        # 合并
        recommend_base = global_hot.union(dept_hot)
        
        recommend_base.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_book_recommend_base")
        
        print(f"✓ 图书推荐基础表完成: {recommend_base.count():,} 条推荐")
    
    def run(self):
        """运行分析流程"""
        print("\n" + "█" * 60)
        print("开始数据分析：DWS → ADS")
        print("█" * 60)
        
        try:
            self.load_dws_data()
            
            # 基础分析表（原有5张）
            self.build_hot_books()
            self.build_active_users()
            self.build_dept_preference()
            self.build_lend_trend()
            self.build_operation_dashboard()
            
            # 高级管理员功能表（新增4张）
            self.build_user_profile()
            self.build_resource_optimization()
            self.build_major_reading_profile()
            self.build_circulation_rate()
            
            # 图书管理员功能表（新增2张）
            self.build_overdue_analysis()
            self.build_time_distribution()
            
            # 普通用户功能表（新增2张）
            self.build_user_ranking()
            self.build_book_recommend_base()
            
            print("\n" + "█" * 60)
            print("✅ ADS层构建完成（13张分析表）")
            print("█" * 60)
            print("基础分析表（5张）：")
            print("  1. ads_hot_books           - 热门图书TOP100")
            print("  2. ads_active_users        - 活跃用户TOP100")
            print("  3. ads_dept_preference     - 院系偏好分析")
            print("  4. ads_lend_trend          - 借阅趋势")
            print("  5. ads_operation_dashboard - 运营看板")
            print("\n高级管理员功能表（4张）：")
            print("  6. ads_user_profile        - 用户画像分析")
            print("  7. ads_resource_optimization - 资源优化建议")
            print("  8. ads_major_reading_profile - 专业阅读特征")
            print("  9. ads_circulation_rate    - 馆藏流通率分析")
            print("\n图书管理员功能表（2张）：")
            print(" 10. ads_overdue_analysis    - 逾期分析")
            print(" 11. ads_time_distribution   - 时间分布分析")
            print("\n普通用户功能表（2张）：")
            print(" 12. ads_user_ranking        - 用户排名")
            print(" 13. ads_book_recommend_base - 图书推荐基础表")
            print("█" * 60)
            
        except Exception as e:
            print(f"\n❌ 分析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            self.spark.stop()

if __name__ == "__main__":
    analyzer = DataAnalyzer()
    analyzer.run()
