# -*- coding: utf-8 -*-
"""
步骤6：高级数据挖掘分析

功能：
1. 关联规则分析（FPGrowth算法）- 挖掘图书之间的隐性关联
2. 读者聚类分群（K-means算法）- 识别不同阅读偏好群体

输出：
- book_association_rules（MySQL）：图书关联规则（如"借了A也借B"）
- user_clusters（MySQL）：用户聚类分群结果
- cluster_summary（MySQL）：聚类统计摘要
- library_ads.ads_book_association（Hive）：图书关联规则
- library_ads.ads_user_cluster（Hive）：用户聚类结果

Author: Library Analysis System
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import col, lit, when, count, avg, sum as spark_sum, max as spark_max, min as spark_min, first, round, desc, size, collect_set, countDistinct, concat, concat_ws, element_at
from pyspark.sql.types import *
from pyspark.sql.window import Window
from pyspark.ml.fpm import FPGrowth
from pyspark.ml.clustering import KMeans
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.evaluation import ClusteringEvaluator
from datetime import datetime


class AdvancedAnalyzer:
    """高级数据挖掘分析"""
    
    def __init__(self, spark):
        self.spark = spark
        
        # MySQL连接配置（从环境变量读取，与04_data_export.py保持一致）
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
        
    def load_data(self):
        """加载数据"""
        print("=" * 60)
        print("加载数据...")
        
        # 加载借阅明细
        self.lend_detail = self.spark.table("library_dwd.dwd_lend_detail")
        
        # 加载图书信息并缓存（小表，频繁使用）
        self.book_info = self.spark.table("library_dwd.dwd_book_info").cache()
        
        # 加载用户信息
        self.user_info = self.spark.table("library_dwd.dwd_user_info")
        
        # 加载用户汇总（用于聚类特征）
        self.user_summary = self.spark.table("library_dws.dws_user_lend_summary")
        
        # 获取数据集最新日期（lend_date是STRING类型）
        latest_date_result = self.lend_detail.agg(spark_max("lend_date")).collect()
        if latest_date_result and latest_date_result[0][0]:
            # lend_date是STRING类型，直接使用
            self.dataset_latest_date = str(latest_date_result[0][0])
        else:
            self.dataset_latest_date = "2020-12-31"
        
        # 优化：使用采样估算数据量，避免全表扫描（仅用于日志输出）
        sample_fraction = 0.01  # 1%采样
        lend_sample_count = self.lend_detail.sample(False, sample_fraction).count()
        estimated_lend_count = int(lend_sample_count / sample_fraction)
        
        print(f"借阅记录数（估算）: ~{estimated_lend_count:,}")
        print(f"数据集最新日期: {self.dataset_latest_date}")
    
    # ==================== 关联规则分析 ====================
    
    def build_book_association(self):
        """
        关联规则分析 - 使用FPGrowth算法挖掘图书关联
        
        输出示例：借阅《三体》和《孤独深处》的读者80%会借《流浪地球》
        """
        print("\n" + "=" * 60)
        print("[1/2] 关联规则分析（FPGrowth）...")
        
        # 1. 构建用户借阅的图书集合（事务数据）
        # 每个用户的借阅记录作为一个"购物篮"
        user_books = self.lend_detail \
            .groupBy("userid") \
            .agg(collect_set("book_id").alias("items"))
        
        # 过滤：只保留借阅2本及以上的用户（否则无法产生关联规则）
        user_books_filtered = user_books.filter(size(col("items")) >= 2)
        
        # 缓存以避免重复计算
        user_books_filtered.cache()
        user_count = user_books_filtered.count()
        print(f"  有效用户数（借阅>=2本）: {user_count:,}")
        
        # 2. FPGrowth模型训练
        # minSupport: 最小支持度（项集出现的最小频率）
        # minConfidence: 最小置信度（规则的可靠程度）
        # 注意：图书借阅数据通常很稀疏，需要较低的支持度
        
        # 计算合理的最小支持度（至少3个用户借阅过）
        import builtins
        min_support_value = builtins.max(3.0 / user_count, 0.0003)  # 至少3人，或0.03%
        print(f"  计算的最小支持度: {min_support_value:.6f} (约{int(min_support_value * user_count)}人)")
        
        fp_growth = FPGrowth(
            itemsCol="items",
            minSupport=min_support_value,
            minConfidence=0.2     # 20%的置信度（与后续过滤保持一致）
        )
        
        model = fp_growth.fit(user_books_filtered)
        
        # 3. 获取频繁项集
        freq_itemsets = model.freqItemsets
        freq_count = freq_itemsets.count()
        print(f"  频繁项集数量: {freq_count:,}")
        
        # 4. 获取关联规则
        association_rules = model.associationRules
        rules_count = association_rules.count()
        print(f"  关联规则数量: {rules_count:,}")
        
        if rules_count == 0 and freq_count == 0:
            print("  ⚠ 未发现频繁项集，尝试进一步降低阈值...")
            # 进一步降低阈值（至少2个用户）
            min_support_retry = builtins.max(2.0 / user_count, 0.0002)
            fp_growth_retry = FPGrowth(
                itemsCol="items",
                minSupport=min_support_retry,
                minConfidence=0.05  # 5%置信度
            )
            model = fp_growth_retry.fit(user_books_filtered)
            freq_itemsets = model.freqItemsets
            association_rules = model.associationRules
            rules_count = association_rules.count()
            print(f"  重试后频繁项集数量: {freq_itemsets.count():,}")
            print(f"  重试后关联规则数量: {rules_count:,}")
        
        # 5. 构建图书关联结果表
        # 获取图书标题映射（去重，确保每个book_id只有一条记录）
        book_titles = self.book_info \
            .select("book_id", "title", "author", "subject") \
            .dropDuplicates(["book_id"])
        
        # 缓存图书信息以提升性能（小表，使用broadcast）
        book_titles.cache()
        
        # 提前准备两个别名的DataFrame，避免重复select
        book_titles_ant = book_titles.select(
            col("book_id").alias("ant_book_id"),
            col("title").alias("antecedent_title"),
            col("subject").alias("antecedent_subject")
        )
        book_titles_con = book_titles.select(
            col("book_id").alias("con_book_id"),
            col("title").alias("consequent_title"),
            col("subject").alias("consequent_subject")
        )
        
        # 定义空表schema（复用）
        empty_schema = StructType([
            StructField("antecedent", ArrayType(StringType()), True),
            StructField("consequent", ArrayType(StringType()), True),
            StructField("antecedent_title", StringType(), True),
            StructField("consequent_title", StringType(), True),
            StructField("antecedent_subject", StringType(), True),
            StructField("consequent_subject", StringType(), True),
            StructField("confidence", DoubleType(), True),
            StructField("lift", DoubleType(), True),
            StructField("support", DoubleType(), True),
            StructField("rule_description", StringType(), True),
            StructField("association_type", StringType(), True)
        ])
        
        # 解析关联规则，转换book_id为标题
        # antecedent: 前项（如果借了这些书）
        # consequent: 后项（则可能借这本书）
        # confidence: 置信度
        # lift: 提升度（>1表示正相关）
        # support: 支持度
        
        if rules_count > 0:
            # 先统计原始规则的分布情况（诊断信息）
            print("  分析原始规则分布...")
            single_item_rules = association_rules \
                .filter(size(col("antecedent")) == 1) \
                .filter(size(col("consequent")) == 1)
            single_item_count = single_item_rules.count()
            print(f"  单项规则数量: {single_item_count:,} / {rules_count:,}")
            
            # 计算最小支持度阈值
            # 对于极度稀疏的图书数据，直接使用FPGrowth的minSupport
            # 不再额外提高阈值，避免过度过滤
            min_support_threshold = min_support_value
            
            print(f"  应用过滤条件：支持度>={min_support_threshold:.6f}, 置信度>=25%, 提升度>1.0")
            
            # 过滤条件：
            # 1. 单项规则
            # 2. 非自关联
            # 3. 支持度>=阈值
            # 4. 置信度>=25%（略低于FPGrowth的20%，保留更多规则）
            # 5. 提升度>1（不设上限）
            rules_filtered = association_rules \
                .filter(size(col("antecedent")) == 1) \
                .filter(size(col("consequent")) == 1) \
                .withColumn("antecedent_book", element_at(col("antecedent"), 1)) \
                .withColumn("consequent_book", element_at(col("consequent"), 1)) \
                .filter(col("antecedent_book") != col("consequent_book")) \
                .filter(col("support") >= min_support_threshold) \
                .filter(col("confidence") >= 0.25) \
                .filter(col("lift") > 1.0)
            
            # 检查过滤后是否还有规则（优化：使用take(1)判断是否为空，避免全量count）
            has_rules = len(rules_filtered.take(1)) > 0
            
            if not has_rules:
                print("  ⚠ 过滤后无有效规则，放宽条件...")
                # 放宽条件：降低置信度到20%，降低支持度到3人
                min_support_relaxed = builtins.max(3.0 / user_count, min_support_value)
                rules_filtered = association_rules \
                    .filter(size(col("antecedent")) == 1) \
                    .filter(size(col("consequent")) == 1) \
                    .withColumn("antecedent_book", element_at(col("antecedent"), 1)) \
                    .withColumn("consequent_book", element_at(col("consequent"), 1)) \
                    .filter(col("antecedent_book") != col("consequent_book")) \
                    .filter(col("support") >= min_support_relaxed) \
                    .filter(col("confidence") >= 0.2) \
                    .filter(col("lift") > 1.0)
                has_rules = len(rules_filtered.take(1)) > 0
                if has_rules:
                    print(f"  放宽后有有效规则（支持度>={min_support_relaxed:.6f}, 置信度>=20%）")
                else:
                    print(f"  放宽后仍无有效规则")
            else:
                print(f"  过滤后有有效规则")
            
            if has_rules:
                # 去除完全重复的规则（相同的前项、后项）
                rules_unique = rules_filtered.dropDuplicates(["antecedent_book", "consequent_book"])
                
                # 注意：不做对称去重（A→B 和 B→A 都保留）
                # 因为在图书推荐场景中，两个方向可能都有意义
                # 例如：借了A的人会借B（置信度80%），借了B的人会借A（置信度60%）
                # 这两条规则提供了不同的信息
                
                # 关联图书信息（使用broadcast join优化）
                book_association = rules_unique \
                    .join(
                        F.broadcast(book_titles_ant),
                        col("antecedent_book") == col("ant_book_id"),
                        "left"
                    ) \
                    .join(
                        F.broadcast(book_titles_con),
                        col("consequent_book") == col("con_book_id"),
                        "left"
                    ) \
                    .filter(col("antecedent_title").isNotNull()) \
                    .filter(col("consequent_title").isNotNull()) \
                    .select(
                        col("antecedent"),
                        col("consequent"),
                        col("antecedent_title"),
                        col("consequent_title"),
                        col("antecedent_subject"),
                        col("consequent_subject"),
                        round(col("confidence"), 4).alias("confidence"),
                        round(col("lift"), 4).alias("lift"),
                        round(col("support"), 6).alias("support"),
                        # 生成可读的规则描述
                        concat(
                            lit("借阅《"), col("antecedent_title"), lit("》的读者"),
                            round(col("confidence") * 100, 1), lit("%会借《"),
                            col("consequent_title"), lit("》")
                        ).alias("rule_description"),
                        # 判断是否同主题关联
                        when(
                            col("antecedent_subject") == col("consequent_subject"),
                            lit("同主题关联")
                        ).otherwise(lit("跨主题关联")).alias("association_type")
                    )
                
                # 排序策略：平衡提升度和支持度
                # 1. 先按关联类型排序（跨主题关联优先，更有价值）
                # 2. 再按支持度*提升度的综合得分排序（平衡流行度和关联强度）
                # 3. 最后按置信度排序
                book_association = book_association \
                    .withColumn("score", col("support") * col("lift")) \
                    .orderBy(
                        when(col("association_type") == "跨主题关联", 1).otherwise(2),
                        desc("score"),
                        desc("confidence")
                    ) \
                    .drop("score") \
                    .limit(1000)  # 保留TOP1000规则（增加容量）
                
                # 缓存结果以便后续统计和写入
                book_association.cache()
            else:
                # 过滤后无规则，创建空表
                print("  ⚠ 放宽条件后仍无有效规则")
                book_association = self.spark.createDataFrame([], empty_schema)
        else:
            # 如果没有规则，创建空表
            print("  ⚠ FPGrowth未生成任何关联规则")
            book_association = self.spark.createDataFrame([], empty_schema)
        
        # 6. 保存到Hive
        book_association.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_book_association")
        
        # 统计规则数量（在写入后，利用缓存）
        final_count = book_association.count()
        
        # 7. 保存到MySQL
        # 转换数组为字符串以便MySQL存储
        book_association_mysql = book_association \
            .withColumn("antecedent_books", concat_ws(",", col("antecedent"))) \
            .withColumn("consequent_books", concat_ws(",", col("consequent"))) \
            .select(
                "antecedent_books",
                "consequent_books",
                "antecedent_title",
                "consequent_title",
                "antecedent_subject",
                "consequent_subject",
                "confidence",
                "lift",
                "support",
                "rule_description",
                "association_type"
            )
        
        book_association_mysql.write \
            .mode("overwrite") \
            .jdbc(self.mysql_url, "book_association_rules", properties=self.mysql_properties)
        
        # 释放book_association缓存
        if 'book_association' in locals():
            book_association.unpersist()
        
        # 释放其他缓存
        user_books_filtered.unpersist()
        book_titles.unpersist()
        # 注意：book_info在load_data中缓存，在run()结束时统一释放
        
        print(f"✓ 图书关联规则完成: {final_count:,} 条规则")
        
        # 打印示例规则
        if final_count > 0:
            print("\n  示例关联规则（TOP 5）：")
            top_rules = book_association.select("rule_description", "confidence", "lift").limit(5).collect()
            for i, rule in enumerate(top_rules, 1):
                print(f"    {i}. {rule['rule_description']} (置信度:{rule['confidence']:.2%}, 提升度:{rule['lift']:.2f})")
        
        return book_association
    
    # ==================== 读者聚类分群 ====================
    
    def build_user_clustering(self):
        """
        读者聚类分群 - 使用K-means算法识别不同阅读偏好群体
        
        输出示例：考研族、文学爱好者、科研群体等
        """
        print("\n" + "=" * 60)
        print("[2/2] 读者聚类分群（K-means）...")
        
        # 1. 合并用户汇总数据（从 DWS 层获取用户统计特征）
        # 获取用户最新信息（按分区排序，取最新的）
        user_info_latest = self.user_info \
            .withColumn("partition_key", concat(col("year"), lit("-"), col("month"))) \
            .withColumn("rank", F.row_number().over(
                Window.partitionBy("userid").orderBy(desc("year"), desc("month"))
            )) \
            .filter(col("rank") == 1) \
            .select("userid", "dept", "redr_type_name", "occupation")
        
        user_features = self.user_summary \
            .join(user_info_latest, "userid", "left") \
            .select(
                "userid",
                "dept",
                col("redr_type_name").alias("user_type"),
                "occupation",
                col("total_lend_count").cast("long").alias("borrow_count"),
                col("active_days").cast("int").alias("active_days"),
                col("overdue_rate").cast("double").alias("overdue_rate"),
                col("avg_borrow_days").cast("double").alias("avg_borrow_days"),
                col("renew_count").cast("long").alias("renew_count")
            )
        
        # 2. 计算阅读广度（涉及主题数）
        # 使用broadcast join优化（book_info已缓存）
        book_subject = self.book_info.select("book_id", "subject")
        user_breadth = self.lend_detail \
            .join(F.broadcast(book_subject), "book_id") \
            .groupBy("userid") \
            .agg(countDistinct("subject").cast("int").alias("reading_breadth"))
        
        user_features = user_features.join(user_breadth, "userid", "left") \
            .na.fill(0, ["reading_breadth"])
        
        # 3. 准备聚类特征（数值型）
        # 注意：移除overdue_rate和renew_count，它们的区分度不够
        # 聚焦于借阅行为的核心特征
        feature_cols = [
            "borrow_count",      # 借阅数量（核心特征）
            "active_days",       # 活跃天数（核心特征）
            "avg_borrow_days",   # 平均借阅天数（反映阅读深度）
            "reading_breadth"    # 阅读广度（反映兴趣范围）
        ]
        
        # 过滤有效数据
        user_features_clean = user_features \
            .na.fill(0, feature_cols) \
            .filter(col("borrow_count") > 0)  # 至少有借阅记录
        
        clustering_user_count = user_features_clean.count()
        print(f"  聚类用户数: {clustering_user_count:,}")
        
        # 边界检查：用户数必须足够多才能聚类
        if clustering_user_count < 20:
            print(f"  ⚠ 用户数太少（<20），跳过聚类分析")
            return None
        
        # 4. 特征向量化
        assembler = VectorAssembler(
            inputCols=feature_cols,
            outputCol="features_raw"
        )
        user_vectors = assembler.transform(user_features_clean)
        
        # 5. 特征标准化（重要！K-means对尺度敏感）
        scaler = StandardScaler(
            inputCol="features_raw",
            outputCol="features",
            withStd=True,
            withMean=True
        )
        scaler_model = scaler.fit(user_vectors)
        user_vectors_scaled = scaler_model.transform(user_vectors)
        
        # 6. 确定最佳K值（使用轮廓系数）
        print("  评估最佳聚类数...")
        silhouette_scores = []
        # 动态调整K的范围：最大不超过用户数的1/10，最小为3
        max_k = min(7, clustering_user_count // 10)
        k_range = range(3, max_k + 1) if max_k >= 3 else [3]
        
        # 缓存标准化后的向量，避免重复计算
        user_vectors_scaled.cache()
        
        for k in k_range:
            kmeans = KMeans(k=k, seed=42, featuresCol="features", predictionCol="cluster")
            model = kmeans.fit(user_vectors_scaled)
            predictions = model.transform(user_vectors_scaled)
            
            evaluator = ClusteringEvaluator(
                featuresCol="features",
                predictionCol="cluster",
                metricName="silhouette"
            )
            silhouette = evaluator.evaluate(predictions)
            silhouette_scores.append((k, silhouette))
            print(f"    K={k}: 轮廓系数={silhouette:.4f}")
        
        # 选择轮廓系数最高的K（使用Python内置max，不是PySpark的max）
        import builtins
        best_k, best_silhouette = builtins.max(silhouette_scores, key=lambda x: x[1])
        print(f"  最佳聚类数: K={best_k} (轮廓系数={best_silhouette:.4f})")
        
        # 如果最佳轮廓系数太低（<0.2），说明聚类效果不好
        if best_silhouette < 0.2:
            print(f"  ⚠ 轮廓系数过低（{best_silhouette:.4f}），聚类效果可能不理想")
        
        # 7. 使用最佳K训练最终模型
        kmeans_final = KMeans(k=best_k, seed=42, featuresCol="features", predictionCol="cluster")
        final_model = kmeans_final.fit(user_vectors_scaled)
        user_clustered = final_model.transform(user_vectors_scaled)
        
        # 8. 分析每个聚类的特征，生成聚类标签
        cluster_stats = user_clustered.groupBy("cluster").agg(
            count("*").alias("user_count"),
            avg("borrow_count").alias("avg_borrow"),
            avg("active_days").alias("avg_active_days"),
            avg("overdue_rate").alias("avg_overdue_rate"),
            avg("avg_borrow_days").alias("avg_borrow_days"),
            avg("reading_breadth").alias("avg_breadth")
        ).orderBy("cluster")
        
        # 收集聚类统计用于标签生成
        cluster_stats_list = cluster_stats.collect()
        
        # 计算全局平均值用于比较
        global_stats = user_clustered.agg(
            avg("borrow_count").alias("global_borrow"),
            avg("active_days").alias("global_active"),
            avg("reading_breadth").alias("global_breadth"),
            avg("overdue_rate").alias("global_overdue"),
            avg("avg_borrow_days").alias("global_borrow_days")
        ).collect()[0]
        
        # 9. 为每个聚类生成描述性标签
        def generate_cluster_label(stats, global_stats):
            """根据聚类特征生成标签"""
            labels = []
            
            # 借阅量判断
            if stats["avg_borrow"] > global_stats["global_borrow"] * 1.5:
                labels.append("高频借阅")
            elif stats["avg_borrow"] < global_stats["global_borrow"] * 0.5:
                labels.append("低频借阅")
            
            # 阅读广度判断
            if stats["avg_breadth"] > global_stats["global_breadth"] * 1.3:
                labels.append("博览群书")
            elif stats["avg_breadth"] < global_stats["global_breadth"] * 0.7:
                labels.append("专注阅读")
            
            # 活跃度判断（基于全局平均值的倍数，更符合实际）
            if stats["avg_active_days"] > global_stats["global_active"] * 2:
                labels.append("持续活跃")
            
            # 逾期率判断（基于全局平均值）
            if stats["avg_overdue_rate"] > global_stats["global_overdue"] * 1.5:
                labels.append("易逾期")
            elif stats["avg_overdue_rate"] < global_stats["global_overdue"] * 0.5:
                labels.append("守时借阅")
            
            # 借阅时长判断（基于全局平均值）
            if stats["avg_borrow_days"] > global_stats["global_borrow_days"] * 1.3:
                labels.append("深度阅读")
            elif stats["avg_borrow_days"] < global_stats["global_borrow_days"] * 0.7:
                labels.append("快速阅读")
            
            if not labels:
                labels.append("普通读者")
            
            return "、".join(labels[:3])  # 最多3个标签
        
        # 生成聚类标签映射
        cluster_labels = {}
        cluster_descriptions = {}
        used_names = set()  # 记录已使用的名称，避免重复
        
        # 按用户数量排序，优先给大群体分配更好的名称
        sorted_stats = sorted(cluster_stats_list, key=lambda x: x["user_count"], reverse=True)
        
        for stats in sorted_stats:
            cluster_id = stats["cluster"]
            label = generate_cluster_label(stats, global_stats)
            
            # 根据特征分配名称（优先级从高到低，避免重复）
            # 标签设计原则：符合高校图书馆实际场景，中性描述
            name = None
            
            # 高借阅量 + 窄阅读面 = 专业深耕型（专注某一领域深入学习）
            if name is None and "专业深耕型" not in used_names:
                if stats["avg_borrow"] > global_stats["global_borrow"] * 1.5 and stats["avg_breadth"] < global_stats["global_breadth"]:
                    name = "专业深耕型"
            
            # 高借阅量 + 宽阅读面 = 博览群书型（跨学科广泛阅读）
            if name is None and "博览群书型" not in used_names:
                if stats["avg_breadth"] > global_stats["global_breadth"] * 1.5 and stats["avg_borrow"] > global_stats["global_borrow"]:
                    name = "博览群书型"
            
            # 高借阅量 + 高活跃度 = 学术活跃型（持续高频使用图书馆）
            if name is None and "学术活跃型" not in used_names:
                if stats["avg_borrow"] > global_stats["global_borrow"] * 1.2 and stats["avg_active_days"] > global_stats["global_active"] * 2:
                    name = "学术活跃型"
            
            # 高逾期率 = 长期借阅型（借阅周期较长，需关注提醒）
            if name is None and "长期借阅型" not in used_names:
                if stats["avg_overdue_rate"] > global_stats["global_overdue"] * 1.5:
                    name = "长期借阅型"
            
            # 宽阅读面 = 兴趣广泛型（涉猎多个学科领域）
            if name is None and "兴趣广泛型" not in used_names:
                if stats["avg_breadth"] > global_stats["global_breadth"] * 1.3:
                    name = "兴趣广泛型"
            
            # 低借阅量 + 低逾期 = 轻度使用型（偶尔借阅，按时归还）
            if name is None and "轻度使用型" not in used_names:
                if stats["avg_borrow"] < global_stats["global_borrow"] * 0.7 and stats["avg_overdue_rate"] <= global_stats["global_overdue"]:
                    name = "轻度使用型"
            
            # 低借阅量 = 低频借阅型
            if name is None and "低频借阅型" not in used_names:
                if stats["avg_borrow"] < global_stats["global_borrow"] * 0.5:
                    name = "低频借阅型"
            
            # 默认名称
            if name is None:
                # 根据最显著特征命名
                if stats["avg_borrow"] > global_stats["global_borrow"]:
                    name = f"活跃用户群{cluster_id + 1}"
                else:
                    name = f"普通用户群{cluster_id + 1}"
            
            used_names.add(name)
            cluster_labels[cluster_id] = name
            cluster_descriptions[cluster_id] = label
        
        # 10. 添加聚类标签到用户数据
        # 创建标签映射DataFrame
        label_schema = StructType([
            StructField("cluster", IntegerType(), False),
            StructField("cluster_name", StringType(), True),
            StructField("cluster_characteristics", StringType(), True)
        ])
        label_data = [(int(k), v, cluster_descriptions[k]) for k, v in cluster_labels.items()]
        label_df = self.spark.createDataFrame(label_data, label_schema)
        
        # 转换cluster字段类型后进行join（使用broadcast join，label_df很小）
        user_clustered_typed = user_clustered.withColumn("cluster", col("cluster").cast("int"))
        
        user_cluster_result = user_clustered_typed \
            .join(F.broadcast(label_df), "cluster") \
            .select(
                col("userid"),
                col("dept"),
                col("user_type"),
                col("occupation"),
                col("cluster"),
                col("cluster_name"),
                col("cluster_characteristics"),
                col("borrow_count").cast("long"),
                col("active_days").cast("int"),
                col("overdue_rate").cast("double"),
                col("avg_borrow_days").cast("double"),
                col("reading_breadth").cast("int")
            )
        
        # 11. 保存到Hive
        user_cluster_result.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_user_cluster")
        
        # 12. 保存聚类统计到MySQL
        # 用户聚类结果
        user_cluster_result.write \
            .mode("overwrite") \
            .jdbc(self.mysql_url, "user_clusters", properties=self.mysql_properties)
        
        # 聚类统计摘要（使用broadcast join）
        cluster_stats_typed = cluster_stats.withColumn("cluster", col("cluster").cast("int"))
        cluster_summary = cluster_stats_typed.join(F.broadcast(label_df), "cluster") \
            .select(
                col("cluster").cast("int"),
                col("cluster_name"),
                col("cluster_characteristics"),
                col("user_count").cast("long"),
                round(col("avg_borrow"), 2).cast("double").alias("avg_borrow_count"),
                round(col("avg_active_days"), 2).cast("double").alias("avg_active_days"),
                round(col("avg_overdue_rate"), 4).cast("double").alias("avg_overdue_rate"),
                round(col("avg_borrow_days"), 2).cast("double").alias("avg_borrow_days"),
                round(col("avg_breadth"), 2).cast("double").alias("avg_reading_breadth")
            )
        
        cluster_summary.write \
            .mode("overwrite") \
            .jdbc(self.mysql_url, "cluster_summary", properties=self.mysql_properties)
        
        print(f"✓ 用户聚类完成: {user_cluster_result.count():,} 个用户，{best_k} 个群体")
        
        # 打印聚类摘要
        print("\n  聚类群体摘要：")
        for row in cluster_summary.collect():
            print(f"    {row['cluster_name']}（{row['user_count']:,}人）: {row['cluster_characteristics']}")
            print(f"      - 平均借阅: {row['avg_borrow_count']:.1f}本, 活跃天数: {row['avg_active_days']:.1f}天, 阅读广度: {row['avg_reading_breadth']:.1f}类")
        
        # 释放缓存
        user_vectors_scaled.unpersist()
        
        return user_cluster_result
    
    def run(self):
        """运行高级分析流程"""
        print("\n" + "█" * 60)
        print("开始高级数据挖掘分析")
        print("█" * 60)
        
        try:
            # 加载数据
            self.load_data()
            
            # 1. 关联规则分析
            self.build_book_association()
            
            # 2. 读者聚类分群
            self.build_user_clustering()
            
            print("\n" + "█" * 60)
            print("✅ 高级数据挖掘分析完成")
            print("█" * 60)
            print("生成的分析表：")
            print("  1. ads_book_association  - 图书关联规则（FPGrowth）")
            print("  2. ads_user_cluster      - 用户聚类分群（K-means）")
            print("\nMySQL表：")
            print("  1. book_association_rules - 图书关联规则")
            print("  2. user_clusters          - 用户聚类结果")
            print("  3. cluster_summary        - 聚类统计摘要")
            print("█" * 60)
            
            # 释放全局缓存
            if hasattr(self, 'book_info'):
                self.book_info.unpersist()
            
        except Exception as e:
            print(f"\n❌ 分析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise


def main():
    """主函数"""
    spark = SparkSession.builder \
        .appName("Advanced Data Mining Analysis") \
        .config("spark.sql.warehouse.dir", "/user/hive/warehouse") \
        .config("hive.metastore.uris", "thrift://master:9083") \
        .config("spark.sql.shuffle.partitions", "10") \
        .config("spark.default.parallelism", "10") \
        .enableHiveSupport() \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    try:
        analyzer = AdvancedAnalyzer(spark)
        analyzer.run()
    except Exception as e:
        print(f"高级分析任务执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
