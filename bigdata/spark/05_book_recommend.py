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
        
        # 加载借阅明细（用于训练ALS模型 - 可以是特定时间范围）
        self.lend_detail = self.spark.sql(f"""
            SELECT userid, book_id, lend_date
            FROM library_dwd.dwd_lend_detail
            {where_clause}
        """)
        
        # 关键修复：加载所有历史借阅记录（用于计算用户偏好和热门度）
        # 用户偏好和热门度应该基于长期历史，而不是单月数据
        self.lend_detail_all = self.spark.sql("""
            SELECT userid, book_id, lend_date
            FROM library_dwd.dwd_lend_detail
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
        
        # 用户已借阅图书列表（所有历史）
        self.user_borrowed_books = self.spark.sql("""
            SELECT userid, collect_set(book_id) as borrowed_books
            FROM library_dwd.dwd_lend_detail
            GROUP BY userid
        """)
        
        # 缓存常用数据以提升性能
        self.lend_detail_all.cache()
        self.book_info.cache()
        self.user_borrowed_books.cache()
        
        # 只打印关键统计（减少count操作）
        print(f"数据加载完成")
        
    def collaborative_filtering(self):
        """协同过滤推荐 - 使用ALS算法"""
        print("\n" + "=" * 60)
        print("执行协同过滤推荐（ALS）...")
        
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
        
        # 关键修改：推荐更多候选（50本），然后过滤已借图书，确保最终有足够的推荐
        user_recs = model.recommendForAllUsers(50)
        
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
                    ).otherwise(5.0),
                    2
                )
            ) \
            .join(book_indexer, "book_index") \
            .join(self.book_info, "book_id") \
            .join(self.user_borrowed_books, "userid", "left") \
            .filter(
                (col("borrowed_books").isNull()) | 
                (~array_contains(col("borrowed_books"), col("book_id")))
            ) \
            .withColumn(
                "rank",
                row_number().over(Window.partitionBy("userid").orderBy(desc("cf_score")))
            ) \
            .filter(col("rank") <= 20) \
            .select(
                "userid", "book_id", "title", "author", "subject",
                col("cf_score").alias("score")
            )
        
        # 缓存结果供后续使用
        cf_recommendations.cache()
        print(f"协同过滤推荐完成")
        return cf_recommendations
    
    def content_based_recommend(self):
        """基于内容的推荐 - 根据用户历史借阅的主题和作者"""
        print("\n" + "=" * 60)
        print("执行基于内容的推荐...")
        
        # 获取所有用户
        all_users = self.user_info.select("userid")
        
        # 关键修复：用户偏好应该基于所有历史数据，而不是当前处理月份
        user_subject_pref = self.lend_detail_all \
            .join(self.book_info, "book_id") \
            .groupBy("userid", "subject") \
            .agg(count("*").alias("subject_count")) \
            .withColumn(
                "rank",
                row_number().over(Window.partitionBy("userid").orderBy(desc("subject_count")))
            ) \
            .filter(col("rank") <= 5) \
            .groupBy("userid") \
            .agg(collect_list("subject").alias("preferred_subjects"))
        
        # 用户历史借阅的作者偏好（扩展到TOP5）
        user_author_pref = self.lend_detail_all \
            .join(self.book_info, "book_id") \
            .filter(col("author").isNotNull()) \
            .groupBy("userid", "author") \
            .agg(count("*").alias("author_count")) \
            .withColumn(
                "rank",
                row_number().over(Window.partitionBy("userid").orderBy(desc("author_count")))
            ) \
            .filter(col("rank") <= 5) \
            .groupBy("userid") \
            .agg(collect_list("author").alias("preferred_authors"))
        
        # 合并用户偏好
        user_preferences = all_users \
            .join(user_subject_pref, "userid", "left") \
            .join(user_author_pref, "userid", "left") \
            .join(self.user_borrowed_books, "userid", "left") \
            .withColumn("preferred_subjects", when(col("preferred_subjects").isNull(), array()).otherwise(col("preferred_subjects"))) \
            .withColumn("preferred_authors", when(col("preferred_authors").isNull(), array()).otherwise(col("preferred_authors"))) \
            .withColumn("borrowed_books", when(col("borrowed_books").isNull(), array()).otherwise(col("borrowed_books")))
        
        # 只为有历史偏好的用户生成内容推荐
        users_with_pref = user_preferences.filter(
            (size(col("preferred_subjects")) > 0) | (size(col("preferred_authors")) > 0)
        )
        
        # 关键优化：避免crossJoin，改用explode + join
        # 将用户偏好展开，然后与图书进行匹配
        user_subject_exploded = users_with_pref \
            .select("userid", "borrowed_books", explode("preferred_subjects").alias("pref_subject"))
        
        user_author_exploded = users_with_pref \
            .select("userid", "borrowed_books", explode("preferred_authors").alias("pref_author"))
        
        # 按主题匹配图书
        subject_matches = user_subject_exploded \
            .join(
                self.book_info.select("book_id", "title", "author", "subject"),
                user_subject_exploded.pref_subject == self.book_info.subject
            ) \
            .filter(~array_contains(col("borrowed_books"), col("book_id"))) \
            .select("userid", "book_id", "title", "author", "subject", lit(6.0).alias("subject_score"))
        
        # 按作者匹配图书
        author_matches = user_author_exploded \
            .join(
                self.book_info.select("book_id", "title", "author", "subject"),
                user_author_exploded.pref_author == self.book_info.author
            ) \
            .filter(~array_contains(col("borrowed_books"), col("book_id"))) \
            .select("userid", "book_id", "title", "author", "subject", lit(4.0).alias("author_score"))
        
        # 合并主题和作者匹配，计算总分
        content_recommendations = subject_matches \
            .join(author_matches, ["userid", "book_id", "title", "author", "subject"], "full_outer") \
            .withColumn(
                "content_score",
                round(coalesce(col("subject_score"), lit(0.0)) + coalesce(col("author_score"), lit(0.0)), 2)
            ) \
            .withColumn(
                "rank",
                row_number().over(Window.partitionBy("userid").orderBy(desc("content_score")))
            ) \
            .filter(col("rank") <= 30) \
            .select("userid", "book_id", "title", "author", "subject", col("content_score").alias("score"))
        
        content_recommendations.cache()
        print(f"基于内容推荐完成")
        return content_recommendations
    
    def popularity_based_recommend(self):
        """基于热门度的推荐 - 按主题分类的热门图书（个性化）"""
        print("\n" + "=" * 60)
        print("执行基于热门度的推荐...")
        
        # 关键修复：热门度应该基于所有历史数据，而不是当前处理月份
        hot_books_by_subject = self.lend_detail_all \
            .join(self.book_info, "book_id") \
            .groupBy("subject", "book_id") \
            .agg(
                count("*").alias("lend_count"),
                countDistinct("userid").alias("reader_count")
            ) \
            .withColumn(
                "raw_score",
                col("lend_count") * 0.6 + col("reader_count") * 0.4
            )
        
        # 按主题归一化得分到0-10分，并为每个主题选TOP10热门图书
        from pyspark.sql.functions import min as spark_min, max as spark_max
        subject_window = Window.partitionBy("subject")
        
        hot_books_normalized = hot_books_by_subject \
            .withColumn("min_score", spark_min("raw_score").over(subject_window)) \
            .withColumn("max_score", spark_max("raw_score").over(subject_window)) \
            .withColumn(
                "popularity_score",
                round(
                    when(col("max_score") > col("min_score"),
                         ((col("raw_score") - col("min_score")) / (col("max_score") - col("min_score"))) * 10
                    ).otherwise(5.0),
                    2
                )
            ) \
            .withColumn(
                "subject_rank",
                row_number().over(Window.partitionBy("subject").orderBy(desc("popularity_score")))
            ) \
            .filter(col("subject_rank") <= 10) \
            .select("subject", "book_id", "popularity_score") \
            .join(self.book_info.select("book_id", "title", "author"), "book_id") \
            .select("book_id", "title", "author", "subject", "popularity_score")
        
        # 关键修复：用户偏好应该基于所有历史数据
        user_subject_pref = self.lend_detail_all \
            .join(self.book_info, "book_id") \
            .groupBy("userid", "subject") \
            .agg(count("*").alias("subject_count")) \
            .withColumn(
                "rank",
                row_number().over(Window.partitionBy("userid").orderBy(desc("subject_count")))
            ) \
            .filter(col("rank") <= 5)  # 取TOP5偏好主题
        
        # 为有历史的用户推荐其偏好主题的热门图书
        # 关键修改：每个主题只取TOP10，5个主题最多50本候选
        users_with_history = user_subject_pref.select("userid").distinct()
        
        popularity_recs_with_pref = user_subject_pref \
            .join(hot_books_normalized, "subject") \
            .join(self.user_borrowed_books, "userid", "left") \
            .filter(
                (col("borrowed_books").isNull()) | 
                (~array_contains(col("borrowed_books"), col("book_id")))
            ) \
            .withColumn(
                "rank",
                row_number().over(Window.partitionBy("userid").orderBy(desc("popularity_score")))
            ) \
            .filter(col("rank") <= 30) \
            .select("userid", "book_id", "title", "author", "subject", col("popularity_score").alias("score"))
        
        # 为没有历史的用户推荐全局热门（多样化）
        all_users = self.user_info.select("userid")
        users_without_history = all_users.join(users_with_history, "userid", "left_anti")
        
        # 优化：为没有历史的用户，直接复制全局TOP30热门图书
        global_hot_books = hot_books_normalized \
            .withColumn(
                "global_rank",
                row_number().over(Window.orderBy(desc("popularity_score")))
            ) \
            .filter(col("global_rank") <= 30) \
            .select("book_id", "title", "author", "subject", "popularity_score")
        
        # 使用broadcast join优化小表关联
        from pyspark.sql.functions import broadcast
        popularity_recs_without_pref = users_without_history \
            .crossJoin(broadcast(global_hot_books)) \
            .join(self.user_borrowed_books, "userid", "left") \
            .filter(
                (col("borrowed_books").isNull()) | 
                (~array_contains(col("borrowed_books"), col("book_id")))
            ) \
            .withColumn(
                "rank",
                row_number().over(Window.partitionBy("userid").orderBy(desc("popularity_score")))
            ) \
            .filter(col("rank") <= 30) \
            .select("userid", "book_id", "title", "author", "subject", col("popularity_score").alias("score"))
        
        # 合并两种推荐
        popularity_recommendations = popularity_recs_with_pref.union(popularity_recs_without_pref)
        
        popularity_recommendations.cache()
        print(f"热门推荐完成")
        return popularity_recommendations
    
    def hybrid_recommend(self, cf_recs, content_recs, popularity_recs):
        """混合推荐 - 融合多种推荐策略，并确保多样性"""
        print("\n" + "=" * 60)
        print("执行混合推荐...")
        
        # 关键优化：先按 userid+book_id 聚合（减少 shuffle 数据量），再关联图书信息
        # 为三种推荐结果添加标识和权重
        cf_recs_weighted = cf_recs.select(
            "userid", "book_id", "subject",
            (col("score") * 0.5).alias("weighted_score"),
            lit(0.5).alias("weight"),
            col("score").alias("cf_score"),
            lit(None).cast("double").alias("content_score"),
            lit(None).cast("double").alias("popularity_score"),
            lit("cf").alias("rec_type")
        )
        
        content_recs_weighted = content_recs.select(
            "userid", "book_id", "subject",
            (col("score") * 0.3).alias("weighted_score"),
            lit(0.3).alias("weight"),
            lit(None).cast("double").alias("cf_score"),
            col("score").alias("content_score"),
            lit(None).cast("double").alias("popularity_score"),
            lit("content").alias("rec_type")
        )
        
        popularity_recs_weighted = popularity_recs.select(
            "userid", "book_id", "subject",
            (col("score") * 0.2).alias("weighted_score"),
            lit(0.2).alias("weight"),
            lit(None).cast("double").alias("cf_score"),
            lit(None).cast("double").alias("content_score"),
            col("score").alias("popularity_score"),
            lit("popularity").alias("rec_type")
        )
        
        # 合并并聚合（只按 userid, book_id, subject 聚合，减少 shuffle）
        all_recs = cf_recs_weighted.union(content_recs_weighted).union(popularity_recs_weighted)
        
        hybrid_recs_agg = all_recs.groupBy("userid", "book_id", "subject") \
            .agg(
                sum("weighted_score").alias("weighted_score"),
                sum("weight").alias("total_weight"),
                max("cf_score").alias("cf_score"),
                max("content_score").alias("content_score"),
                max("popularity_score").alias("popularity_score"),
                collect_set("rec_type").alias("rec_types")
            ) \
            .withColumn(
                "final_score",
                round(col("weighted_score") / col("total_weight"), 2)
            )
        
        # 多样性约束：每个主题最多6本
        MAX_PER_SUBJECT = 6
        subject_window = Window.partitionBy("userid", "subject").orderBy(desc("final_score"))
        
        subject_limited = hybrid_recs_agg \
            .withColumn("subject_rank", row_number().over(subject_window)) \
            .filter(col("subject_rank") <= MAX_PER_SUBJECT)
        
        # 最终排序取TOP20
        final_window = Window.partitionBy("userid").orderBy(desc("final_score"))
        
        diverse_recs_core = subject_limited \
            .withColumn("rank", row_number().over(final_window)) \
            .filter(col("rank") <= 20) \
            .withColumn("rec_sources", concat_ws(",", col("rec_types")))
        
        # 最后关联图书信息（title, author）
        diverse_recs = diverse_recs_core \
            .join(
                self.book_info.select("book_id", "title", "author"),
                "book_id"
            ) \
            .withColumn(
                "reason",
                when(
                    size(col("rec_types")) >= 2,
                    concat(
                        lit("综合推荐："),
                        when(array_contains(col("rec_types"), "cf"), lit("相似借阅者也喜欢；")).otherwise(lit("")),
                        when(array_contains(col("rec_types"), "content"), lit("符合你的阅读偏好；")).otherwise(lit("")),
                        when(array_contains(col("rec_types"), "popularity"), lit("热门图书")).otherwise(lit(""))
                    )
                ).when(
                    array_contains(col("rec_types"), "cf"),
                    lit("基于相似用户的借阅偏好推荐")
                ).when(
                    array_contains(col("rec_types"), "content"),
                    lit("基于你的历史阅读偏好推荐")
                ).otherwise(
                    lit("热门图书推荐")
                )
            ) \
            .select(
                "userid", "book_id", "title", "author", "subject",
                "final_score", "cf_score", "content_score", "popularity_score",
                "rec_sources", "rec_types", "reason", "rank"
            )
        
        diverse_recs.cache()
        print(f"混合推荐完成（含多样性约束）")
        return diverse_recs
    
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
        print("  [1/3] 保存混合推荐结果到MySQL...")
        
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
                col("cf_score"),
                col("content_score"),
                col("popularity_score")
            )
        
        # 关键优化1：减少分区数，提升写入并行度
        # 将数据重新分区到4个分区（平衡并行度和开销）
        recommend_flat_optimized = recommend_flat.repartition(4)
        
        # 关键优化2：缓存后再写入，避免重复计算
        recommend_flat_optimized.cache()
        total_count = recommend_flat_optimized.count()  # 触发缓存并获取总数
        print(f"    准备写入 {total_count} 条推荐记录...")
        
        # 关键优化3：写入MySQL（使用更大的批量和并行写入）
        recommend_flat_optimized.write \
            .mode("overwrite") \
            .option("batchsize", "50000") \
            .option("isolationLevel", "NONE") \
            .option("numPartitions", "4") \
            .option("rewriteBatchedStatements", "true") \
            .jdbc(mysql_url, "book_recommendations", properties=mysql_properties)
        
        print(f"    ✓ MySQL推荐结果已保存 ({total_count} 条)")
        
        # 后续使用优化后的DataFrame
        recommend_flat = recommend_flat_optimized
        
        # 2. 保存推荐效果统计
        print("  [2/3] 保存推荐效果统计到MySQL...")
        
        # 优化：缓存user_info避免重复扫描
        self.user_info.cache()
        total_users = self.user_info.count()
        
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
        
        print(f"    ✓ MySQL统计数据已保存: {len(stats_data)} 项指标")
        
        # 3. 保存到Hive ADS层（扁平结构，快速写入）
        print("  [3/3] 保存到Hive ADS层...")
        
        # 优化：从缓存的lend_detail获取最新日期，避免重复扫描
        latest_date_result = self.lend_detail.agg(max("lend_date")).collect()
        if latest_date_result and latest_date_result[0][0]:
            dataset_latest_date = latest_date_result[0][0]
            dataset_latest_date_str = dataset_latest_date.strftime("%Y-%m-%d")
            dataset_year = dataset_latest_date.year
            dataset_month = dataset_latest_date.month
        else:
            dataset_latest_date_str = "2020-12-31"
            dataset_year = 2020
            dataset_month = 12
        
        # 直接保存扁平结构（比嵌套结构快很多）
        recommend_hive = recommend_flat \
            .withColumn("recommend_date", lit(dataset_latest_date_str)) \
            .withColumn("algorithm_type", lit("hybrid")) \
            .withColumn("year", lit(dataset_year)) \
            .withColumn("month", lit(dataset_month)) \
            .select(
                "userid", "book_id", "title", "author", "subject",
                "score", "rec_sources", "reason", "rank_no",
                "recommend_date", "algorithm_type", "year", "month"
            )
        
        # 优化：使用更少的分区数加速写入
        recommend_hive.coalesce(2).write \
            .mode("overwrite") \
            .partitionBy("year", "month") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_book_recommendation")
        
        print("    ✓ Hive ADS层已保存")
        
        # 释放缓存
        recommend_flat.unpersist()
        
        print("\n推荐结果保存完成！")
        print(f"  - MySQL推荐记录: {total_recs} 条")
        print(f"  - 覆盖用户: {recommended_users} 人")
        print(f"  - 平均得分: {avg_score:.2f} 分")
    
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
