# -*- coding: utf-8 -*-
"""
步骤5：图书推荐算法 - 基于协同过滤和内容的混合推荐

功能：
1. ALS协同过滤推荐（基于用户借阅历史的相似度）
2. 内容过滤推荐（基于图书主题的相似度）
3. 热门推荐（基于借阅热度）
4. 混合推荐（加权融合三种算法）

输出：
- book_recommendations（主表）：个性化推荐结果（每用户TOP20）
- recommendation_stats（统计表）：推荐系统整体效果指标（22项）
- library_ads.ads_book_recommendation（Hive）：推荐结果存档

Author: Library Analysis System
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
from pyspark.ml.recommendation import ALS
from pyspark.ml.feature import HashingTF, IDF, Tokenizer
from datetime import datetime
import sys


class BookRecommender:
    """图书推荐系统"""
    
    def __init__(self, spark):
        self.spark = spark
        # 支持指定年月或处理所有数据
        if len(sys.argv) > 1:
            self.process_mode = sys.argv[1]  # "all" 或 "YYYYMM"
            if self.process_mode != "all":
                self.year = int(self.process_mode[:4])
                self.month = int(self.process_mode[4:6])
        else:
            self.process_mode = "all"
        
    def load_data(self):
        """加载数据（从DWD层）"""
        print("=" * 60)
        print("加载数据...")
        
        if self.process_mode == "all":
            print("加载所有数据 (2019-2020)")
            where_clause = ""
        else:
            print(f"加载指定月份: {self.year}年{self.month}月")
            where_clause = f"WHERE year = {self.year} AND month = {self.month}"
        
        # 加载借阅明细
        self.lend_detail = self.spark.sql(f"""
            SELECT userid, book_id, lend_date
            FROM library_dwd.dwd_lend_detail
            {where_clause}
        """)
        
        # 加载图书信息（所有）
        self.book_info = self.spark.sql("""
            SELECT book_id, title, author, subject, publisher
            FROM library_dwd.dwd_book_info
        """)
        
        # 加载用户信息（所有）
        self.user_info = self.spark.sql("""
            SELECT userid, dept, redr_type_name, occupation
            FROM library_dwd.dwd_user_info
        """)
        
        print(f"借阅记录数: {self.lend_detail.count()}")
        print(f"图书数量: {self.book_info.count()}")
        print(f"用户数量: {self.user_info.count()}")
        
    def collaborative_filtering(self):
        """协同过滤推荐 - 使用ALS算法"""
        print("\n" + "=" * 60)
        print("执行协同过滤推荐（ALS）...")
        
        # 记录用户已借阅的图书（用于后续过滤）
        self.user_borrowed_books = self.lend_detail \
            .groupBy("userid") \
            .agg(collect_set("book_id").alias("borrowed_books"))
        
        # 构建用户-图书评分矩阵（隐式反馈）
        user_book_matrix = self.lend_detail \
            .groupBy("userid", "book_id") \
            .agg(count("*").alias("rating"))
        
        # 用户和图书ID转换为数值型（ALS要求Integer类型），使用索引映射提升性能
        user_list = user_book_matrix.select("userid").distinct().rdd.map(lambda row: row[0]).collect()
        user_indexer = self.spark.createDataFrame(
            [(user_id, idx) for idx, user_id in enumerate(sorted(user_list))],
            ["userid", "user_index"]
        )
        
        book_list = user_book_matrix.select("book_id").distinct().rdd.map(lambda row: row[0]).collect()
        book_indexer = self.spark.createDataFrame(
            [(book_id, idx) for idx, book_id in enumerate(sorted(book_list))],
            ["book_id", "book_index"]
        )
        
        # 关联索引
        matrix_indexed = user_book_matrix \
            .join(user_indexer, "userid") \
            .join(book_indexer, "book_id")
        
        # ALS模型训练
        als = ALS(
            maxIter=10,
            regParam=0.1,
            userCol="user_index",
            itemCol="book_index",
            ratingCol="rating",
            coldStartStrategy="drop",
            implicitPrefs=True,
            nonnegative=True
        )
        
        model = als.fit(matrix_indexed)
        
        # 为每个用户推荐TOP20图书
        user_recs = model.recommendForAllUsers(20)
        
        # 解析推荐结果
        cf_recs_raw = user_recs \
            .join(user_indexer, user_recs.user_index == user_indexer.user_index) \
            .select(
                col("userid"),
                explode(col("recommendations")).alias("rec")
            ) \
            .select(
                col("userid"),
                col("rec.book_index").alias("book_index"),
                col("rec.rating").alias("raw_cf_score")
            )
        
        # 归一化CF得分到0-10范围（按用户分组归一化）
        from pyspark.sql.functions import min as spark_min, max as spark_max
        user_cf_window = Window.partitionBy("userid")
        
        cf_recommendations = cf_recs_raw \
            .withColumn("min_score", spark_min("raw_cf_score").over(user_cf_window)) \
            .withColumn("max_score", spark_max("raw_cf_score").over(user_cf_window)) \
            .withColumn(
                "cf_score",
                round(
                    when(col("max_score") > col("min_score"),
                         ((col("raw_cf_score") - col("min_score")) / (col("max_score") - col("min_score"))) * 10
                    ).otherwise(5.0),  # 如果用户所有推荐得分相同，给中间值
                    2
                )
            ) \
            .join(book_indexer, "book_index") \
            .join(self.book_info, "book_id") \
            .select(
                "userid", "book_id", "title", "author", "subject",
                col("cf_score").alias("score")
            )
        
        print(f"协同过滤推荐完成，推荐记录数: {cf_recommendations.count()}")
        return cf_recommendations
    
    def content_based_recommend(self):
        """基于内容的推荐 - 根据用户历史借阅的主题和作者"""
        print("\n" + "=" * 60)
        print("执行基于内容的推荐...")
        
        # 获取所有用户（包括没有历史记录的用户）
        all_users = self.user_info.select("userid")
        
        # 用户历史借阅的主题偏好
        user_subject_pref = self.lend_detail \
            .join(self.book_info, "book_id") \
            .groupBy("userid", "subject") \
            .agg(count("*").alias("subject_count")) \
            .withColumn(
                "rank",
                row_number().over(Window.partitionBy("userid").orderBy(desc("subject_count")))
            ) \
            .filter(col("rank") <= 3) \
            .groupBy("userid") \
            .agg(collect_list("subject").alias("preferred_subjects"))
        
        # 用户历史借阅的作者偏好
        user_author_pref = self.lend_detail \
            .join(self.book_info, "book_id") \
            .filter(col("author").isNotNull()) \
            .groupBy("userid", "author") \
            .agg(count("*").alias("author_count")) \
            .withColumn(
                "rank",
                row_number().over(Window.partitionBy("userid").orderBy(desc("author_count")))
            ) \
            .filter(col("rank") <= 3) \
            .groupBy("userid") \
            .agg(collect_list("author").alias("preferred_authors"))
        
        # 用户已借阅的图书
        user_borrowed_books = self.lend_detail \
            .groupBy("userid") \
            .agg(collect_set("book_id").alias("borrowed_books"))
        
        # 合并用户偏好（使用left join确保所有用户都有记录）
        user_preferences = all_users \
            .join(user_subject_pref, "userid", "left") \
            .join(user_author_pref, "userid", "left") \
            .join(user_borrowed_books, "userid", "left") \
            .withColumn("preferred_subjects", when(col("preferred_subjects").isNull(), array()).otherwise(col("preferred_subjects"))) \
            .withColumn("preferred_authors", when(col("preferred_authors").isNull(), array()).otherwise(col("preferred_authors"))) \
            .withColumn("borrowed_books", when(col("borrowed_books").isNull(), array()).otherwise(col("borrowed_books")))
        
        # 为每个用户推荐符合偏好的图书
        content_recs = user_preferences.crossJoin(
            self.book_info.select("book_id", "title", "author", "subject")
        )
        
        # 过滤已借阅的图书，计算内容相似度得分
        content_recommendations = content_recs \
            .filter(~array_contains(col("borrowed_books"), col("book_id"))) \
            .withColumn(
                "subject_match",
                when(
                    (size(col("preferred_subjects")) > 0) & array_contains(col("preferred_subjects"), col("subject")), 
                    1.0
                ).otherwise(0.0)
            ) \
            .withColumn(
                "author_match",
                when(
                    (size(col("preferred_authors")) > 0) & array_contains(col("preferred_authors"), col("author")), 
                    1.0
                ).otherwise(0.0)
            ) \
            .withColumn(
                "raw_score",
                col("subject_match") * 0.6 + col("author_match") * 0.4
            ) \
            .filter(col("raw_score") > 0) \
            .withColumn(
                "content_score",
                round(col("raw_score") * 10, 2)  # 归一化：0.4-1.0 -> 4-10分，保留2位
            ) \
            .withColumn(
                "rank",
                row_number().over(Window.partitionBy("userid").orderBy(desc("content_score")))
            ) \
            .filter(col("rank") <= 20) \
            .select("userid", "book_id", "title", "author", "subject", col("content_score").alias("score"))
        
        print(f"基于内容推荐完成，推荐记录数: {content_recommendations.count()}")
        return content_recommendations
    
    def popularity_based_recommend(self):
        """基于热门度的推荐 - 全局热门图书"""
        print("\n" + "=" * 60)
        print("执行基于热门度的推荐...")
        
        # 计算图书热度
        hot_books_raw = self.lend_detail \
            .groupBy("book_id") \
            .agg(
                count("*").alias("lend_count"),
                countDistinct("userid").alias("reader_count")
            ) \
            .withColumn(
                "raw_score",
                col("lend_count") * 0.6 + col("reader_count") * 0.4
            )
        
        # 归一化到0-10分范围
        from pyspark.sql.functions import min as spark_min, max as spark_max
        stats = hot_books_raw.agg(
            spark_min("raw_score").alias("min_score"),
            spark_max("raw_score").alias("max_score")
        ).collect()[0]
        
        min_score = stats["min_score"]
        max_score = stats["max_score"]
        
        # 在Python层面判断边界条件
        if max_score > min_score:
            hot_books = hot_books_raw \
                .withColumn(
                    "popularity_score",
                    round(((col("raw_score") - lit(min_score)) / (lit(max_score) - lit(min_score))) * 10, 2)
                ) \
                .join(self.book_info, "book_id") \
                .select("book_id", "title", "author", "subject", "popularity_score") \
                .orderBy(desc("popularity_score")) \
                .limit(50)
        else:
            # 如果所有得分相同，给固定分数
            hot_books = hot_books_raw \
                .withColumn("popularity_score", lit(5.0)) \
                .join(self.book_info, "book_id") \
                .select("book_id", "title", "author", "subject", "popularity_score") \
                .orderBy(desc("lend_count")) \
                .limit(50)
        
        # 为没有历史记录的新用户推荐热门图书
        all_users = self.user_info.select("userid")
        
        popularity_recommendations = all_users.crossJoin(hot_books) \
            .select(
                "userid", "book_id", "title", "author", "subject",
                col("popularity_score").alias("score")
            )
        
        print(f"热门推荐完成，推荐记录数: {popularity_recommendations.count()}")
        return popularity_recommendations
    
    def hybrid_recommend(self, cf_recs, content_recs, popularity_recs):
        """混合推荐 - 融合多种推荐策略"""
        print("\n" + "=" * 60)
        print("执行混合推荐...")
        
        # 为三种推荐结果添加标识（保持统一的列名以便union）
        cf_recs_marked = cf_recs.withColumn("rec_type", lit("cf"))
        content_recs_marked = content_recs.withColumn("rec_type", lit("content"))
        popularity_recs_marked = popularity_recs.withColumn("rec_type", lit("popularity"))
        
        # 合并推荐结果（列名: userid, book_id, title, author, subject, score, rec_type）
        all_recs = cf_recs_marked.union(content_recs_marked).union(popularity_recs_marked)
        
        # 过滤已借图书
        all_recs_filtered = all_recs.join(self.user_borrowed_books, "userid", "left") \
            .filter(
                ~array_contains(col("borrowed_books"), col("book_id")) |
                col("borrowed_books").isNull()
            )
        
        # 按用户+图书聚合，使用加权平均（不同算法权重不同）
        # 同时保留各算法的分项得分用于离线分析
        hybrid_recs = all_recs_filtered.groupBy("userid", "book_id", "title", "author", "subject") \
            .agg(
                # 加权得分计算
                sum(
                    when(col("rec_type") == "cf", col("score") * 0.5)  # 协同过滤权重50%
                    .when(col("rec_type") == "content", col("score") * 0.3)  # 内容推荐权重30%
                    .when(col("rec_type") == "popularity", col("score") * 0.2)  # 热门推荐权重20%
                ).alias("weighted_score"),
                sum(
                    when(col("rec_type") == "cf", 0.5)
                    .when(col("rec_type") == "content", 0.3)
                    .when(col("rec_type") == "popularity", 0.2)
                ).alias("total_weight"),
                # 保留各算法的分项得分（用于离线分析），使用max()聚合获取各算法分数
                max(when(col("rec_type") == "cf", col("score"))).alias("cf_score"),
                max(when(col("rec_type") == "content", col("score"))).alias("content_score"),
                max(when(col("rec_type") == "popularity", col("score"))).alias("popularity_score"),
                collect_set("rec_type").alias("rec_types")
            ) \
            .withColumn(
                "final_score",
                round(col("weighted_score") / col("total_weight"), 2)  # 加权平均，保留2位小数
            ) \
            .withColumn(
                "rank",
                row_number().over(Window.partitionBy("userid").orderBy(desc("final_score")))
            ) \
            .filter(col("rank") <= 20) \
            .withColumn(
                "rec_sources",
                concat_ws(",", col("rec_types"))  # 记录推荐来源组合
            ) \
            .withColumn(
                "reason",
                when(
                    size(col("rec_types")) >= 2,
                    concat(
                        lit("综合推荐："),
                        when(array_contains(col("rec_types"), "cf"), lit("相似借阅者也喜欢；")).otherwise(lit("")),
                        when(array_contains(col("rec_types"), "content"), concat(lit("符合你的"), col("subject"), lit("偏好；"))).otherwise(lit("")),
                        when(array_contains(col("rec_types"), "popularity"), lit("热门图书")).otherwise(lit(""))
                    )
                ).when(
                    array_contains(col("rec_types"), "cf"),
                    concat(lit("与你借阅过《"), col("title"), lit("》相似"))
                ).when(
                    array_contains(col("rec_types"), "content"),
                    concat(lit("基于你的"), col("subject"), lit("阅读偏好"))
                ).otherwise(
                    lit("热门图书推荐")
                )
            )
        
        print(f"混合推荐完成，推荐记录数: {hybrid_recs.count()}")
        return hybrid_recs
    
    def save_recommendations(self, recommendations, cf_recs, content_recs, popularity_recs):
        """保存推荐结果到ADS层和MySQL"""
        print("\n" + "=" * 60)
        print("保存推荐结果...")
        
        # 配置MySQL连接
        mysql_url = "jdbc:mysql://master:3306/library_analysis"
        mysql_properties = {
            "user": "root",
            "password": "780122",
            "driver": "com.mysql.cj.jdbc.Driver"
        }
        
        # 1. 保存混合推荐结果（主表）
        print("  [1/3] 保存混合推荐结果...")
        
        # 计算多样性得分（推荐列表中不同主题/作者的比例）
        user_diversity = recommendations.groupBy("userid").agg(
            countDistinct("subject").alias("subject_count"),
            countDistinct("author").alias("author_count"),
            count("*").alias("total_count")
        ).withColumn(
            "diversity_score",
            round((col("subject_count") / col("total_count") + col("author_count") / col("total_count")) / 2, 2)
        ).select("userid", "diversity_score")
        
        recommend_flat = recommendations.join(user_diversity, "userid") \
            .select(
                "userid",
                "book_id",
                "title",
                "author",
                "subject",
                col("final_score").alias("score"),
                col("rec_sources"),
                "reason",
                col("rank").alias("rank_no"),
                col("diversity_score"),
                col("cf_score"),           # 协同过滤分项得分
                col("content_score"),      # 内容推荐分项得分
                col("popularity_score")    # 热门推荐分项得分
            )
        
        recommend_flat.write \
            .mode("overwrite") \
            .jdbc(mysql_url, "book_recommendations", properties=mysql_properties)
        
        print(f"    ✓ 混合推荐已保存: {recommend_flat.count()} 条")
        
        # 2. 保存推荐效果统计
        print("  [2/3] 保存推荐效果统计...")
        
        # 缓存DataFrame以复用
        recommend_flat.cache()
        
        # 合并多个聚合操作到一次扫描
        from pyspark.sql.functions import sum as spark_sum, when
        
        stats_agg = recommend_flat.agg(
            count("*").alias("total_recs"),
            countDistinct("userid").alias("recommended_users"),
            avg("score").alias("avg_score"),
            avg("diversity_score").alias("avg_diversity"),
            spark_sum(when(size(split(col("rec_sources"), ",")) >= 2, 1).otherwise(0)).alias("multi_source_count"),
            spark_sum(when(col("rec_sources").contains("cf"), 1).otherwise(0)).alias("cf_count"),
            spark_sum(when(col("rec_sources").contains("content"), 1).otherwise(0)).alias("content_count"),
            spark_sum(when(col("rec_sources").contains("popularity"), 1).otherwise(0)).alias("popularity_count"),
            countDistinct(when(col("cf_score").isNotNull(), col("userid"))).alias("cf_users"),
            countDistinct(when(col("content_score").isNotNull(), col("userid"))).alias("content_users"),
            countDistinct(when(col("popularity_score").isNotNull(), col("userid"))).alias("popularity_users"),
            avg(when(col("cf_score").isNotNull(), col("cf_score"))).alias("avg_cf"),
            avg(when(col("content_score").isNotNull(), col("content_score"))).alias("avg_content"),
            avg(when(col("popularity_score").isNotNull(), col("popularity_score"))).alias("avg_pop")
        ).collect()[0]
        
        total_users = self.user_info.count()
        recommended_users = stats_agg["recommended_users"]
        total_recs = stats_agg["total_recs"]
        avg_score = stats_agg["avg_score"]
        avg_diversity = stats_agg["avg_diversity"]
        multi_source_count = stats_agg["multi_source_count"]
        multi_source_rate = multi_source_count / total_recs * 100 if total_recs > 0 else 0
        cf_users = stats_agg["cf_users"]
        content_users = stats_agg["content_users"]
        popularity_users = stats_agg["popularity_users"]
        cf_count = stats_agg["cf_count"]
        content_count = stats_agg["content_count"]
        popularity_count = stats_agg["popularity_count"]
        avg_cf = stats_agg["avg_cf"] or 0
        avg_content = stats_agg["avg_content"] or 0
        avg_pop = stats_agg["avg_pop"] or 0
        
        stats_data = [
            ("total_users", "系统用户总数", str(total_users)),
            ("recommended_users", "获得推荐的用户数", str(recommended_users)),
            ("coverage_rate", "推荐覆盖率", f"{recommended_users/total_users*100:.2f}%"),
            ("total_recommendations", "推荐总数", str(total_recs)),
            ("avg_recommendations_per_user", "人均推荐数", f"{total_recs/recommended_users:.1f}"),
            ("avg_score", "平均推荐得分(0-10分)", f"{avg_score:.2f}"),
            ("avg_diversity", "平均多样性得分(0-1)", f"{avg_diversity:.3f}"),
            ("multi_source_count", "多来源推荐数量", str(multi_source_count)),
            ("multi_source_rate", "多来源推荐占比", f"{multi_source_rate:.2f}%"),
            ("cf_user_count", "协同过滤覆盖用户数", str(cf_users)),
            ("content_user_count", "内容推荐覆盖用户数", str(content_users)),
            ("popularity_user_count", "热门推荐覆盖用户数", str(popularity_users)),
            ("cf_rec_count", "协同过滤推荐数", str(cf_count)),
            ("content_rec_count", "内容推荐数", str(content_count)),
            ("popularity_rec_count", "热门推荐数", str(popularity_count)),
            ("avg_cf_score", "协同过滤平均得分", f"{avg_cf:.2f}"),
            ("avg_content_score", "内容推荐平均得分", f"{avg_content:.2f}"),
            ("avg_popularity_score", "热门推荐平均得分", f"{avg_pop:.2f}"),
            ("algorithm_weights", "推荐权重配置", "CF:50%, Content:30%, Popularity:20%"),
            ("score_normalization", "得分归一化", "所有算法统一归一化到0-10分"),
            ("algorithm_type", "推荐算法", "ALS协同过滤 + 内容过滤 + 热门度加权混合"),
            ("last_update", "最后更新时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ]
        
        stats_df = self.spark.createDataFrame(stats_data, ["stat_type", "stat_name", "stat_value"])
        
        stats_df.write \
            .mode("overwrite") \
            .jdbc(mysql_url, "recommendation_stats", properties=mysql_properties)
        
        print(f"    ✓ 推荐统计已保存: {len(stats_data)} 项指标")
        
        # 3. 保存到Hive ADS层（按year/month分区）
        print("  [3/3] 保存到Hive ADS层...")
        
        # 获取数据集最新日期（离线分析，不使用系统当前时间）
        latest_date_result = self.lend_detail.agg(max("lend_date")).collect()
        if latest_date_result and latest_date_result[0][0]:
            dataset_latest_date = latest_date_result[0][0]
            dataset_latest_date_str = dataset_latest_date.strftime("%Y-%m-%d")
            dataset_year = dataset_latest_date.year
            dataset_month = dataset_latest_date.month
        else:
            # 默认值
            dataset_latest_date_str = "2020-12-31"
            dataset_year = 2020
            dataset_month = 12
        
        recommend_struct = recommendations.groupBy("userid") \
            .agg(
                collect_list(
                    struct(
                        col("book_id"),
                        col("title"),
                        col("author"),
                        col("subject"),
                        col("final_score").alias("score"),
                        col("reason")
                    )
                ).alias("recommend_books")
            ) \
            .withColumn("recommend_date", lit(dataset_latest_date_str)) \
            .withColumn("algorithm_type", lit("hybrid")) \
            .withColumn("year", lit(dataset_year)) \
            .withColumn("month", lit(dataset_month))
        
        recommend_struct.write \
            .mode("overwrite") \
            .partitionBy("year", "month") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_book_recommendation")
        
        print("    ✓ Hive ADS层已保存")
        
        print("\n推荐结果保存完成！")
    
    def run(self):
        """运行推荐流程"""
        print("\n" + "=" * 60)
        print("开始图书推荐任务")
        print("=" * 60)
        
        # 1. 加载数据
        self.load_data()
        
        # 2. 协同过滤推荐
        cf_recs = self.collaborative_filtering()
        
        # 3. 基于内容的推荐
        content_recs = self.content_based_recommend()
        
        # 4. 基于热门度的推荐
        popularity_recs = self.popularity_based_recommend()
        
        # 5. 混合推荐
        hybrid_recs = self.hybrid_recommend(cf_recs, content_recs, popularity_recs)
        
        # 6. 保存推荐结果（包含分策略明细和统计）
        self.save_recommendations(hybrid_recs, cf_recs, content_recs, popularity_recs)
        
        print("\n" + "=" * 60)
        print("图书推荐任务完成！")
        print("=" * 60)


def main():
    """主函数"""
    # 创建Spark会话
    spark = SparkSession.builder \
        .appName("Library Book Recommendation") \
        .config("spark.sql.warehouse.dir", "/user/hive/warehouse") \
        .config("hive.metastore.uris", "thrift://master:9083") \
        .config("spark.sql.shuffle.partitions", "10") \
        .config("spark.default.parallelism", "10") \
        .enableHiveSupport() \
        .getOrCreate()
    
    # 设置日志级别
    spark.sparkContext.setLogLevel("WARN")
    
    try:
        # 运行推荐系统
        recommender = BookRecommender(spark)
        recommender.run()
    except Exception as e:
        print(f"推荐任务执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
