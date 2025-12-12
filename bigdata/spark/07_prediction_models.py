#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
预测模型分析脚本
================
1. 逾期风险预测 - 使用随机森林预测用户逾期概率
2. 借阅趋势预测 - 使用时间序列预测未来借阅量
3. 图书热度预测 - 预测图书未来热度

输出表：
- Hive: library_ads.ads_overdue_prediction, ads_lend_trend_prediction, ads_book_heat_prediction
- MySQL: overdue_risk_prediction, lend_trend_prediction, book_heat_prediction
"""

import os
import sys
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import col, lit, when, count, avg, sum as spark_sum, max as spark_max, min as spark_min
from pyspark.sql.functions import datediff, to_date, date_sub, date_add, month, year, dayofweek
from pyspark.sql.functions import lag, lead, round as spark_round, expr
from pyspark.sql.window import Window
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, DateType, LongType
from pyspark.ml.feature import VectorAssembler, StringIndexer, StandardScaler
from pyspark.ml.classification import RandomForestClassifier, GBTClassifier
from pyspark.ml.regression import RandomForestRegressor, GBTRegressor
from pyspark.ml.evaluation import BinaryClassificationEvaluator, RegressionEvaluator
from pyspark.ml import Pipeline
import builtins


class PredictionModels:
    """预测模型分析类"""
    
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("PredictionModels") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .enableHiveSupport() \
            .getOrCreate()
        
        # MySQL连接配置
        self.mysql_url = "jdbc:mysql://{}:{}/{}".format(
            os.getenv("MYSQL_HOST", "master"),
            os.getenv("MYSQL_PORT", "3306"),
            os.getenv("MYSQL_DATABASE", "library_analysis")
        )
        self.mysql_properties = {
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", "123456"),
            "driver": "com.mysql.cj.jdbc.Driver"
        }
        
        print(f"MySQL连接: {os.getenv('MYSQL_HOST', 'master')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DATABASE', 'library_analysis')}")
        
        # 数据集
        self.lend_detail = None
        self.user_summary = None
        self.book_summary = None
        self.user_info = None
        self.book_info = None
        self.latest_date = None
    
    def load_data(self):
        """加载数据"""
        print("\n" + "=" * 60)
        print("加载数据...")
        
        # 加载DWD层数据
        self.lend_detail = self.spark.table("library_dwd.dwd_lend_detail")
        self.user_info = self.spark.table("library_dwd.dwd_user_info")
        self.book_info = self.spark.table("library_dwd.dwd_book_info")
        
        # 加载DWS层汇总数据
        self.user_summary = self.spark.table("library_dws.dws_user_lend_summary")
        self.book_summary = self.spark.table("library_dws.dws_book_lend_summary")
        
        # 获取数据集最新日期（转换为字符串格式）
        latest_date_result = self.lend_detail.agg(spark_max("lend_date")).collect()
        latest_date_value = latest_date_result[0][0] if latest_date_result else None
        if latest_date_value is None:
            self.latest_date = "2020-12-31"
        elif isinstance(latest_date_value, str):
            self.latest_date = latest_date_value
        else:
            # datetime.date 类型转换为字符串
            self.latest_date = latest_date_value.strftime("%Y-%m-%d")
        
        print(f"借阅记录数: {self.lend_detail.count():,}")
        print(f"用户汇总数: {self.user_summary.count():,}")
        print(f"图书汇总数: {self.book_summary.count():,}")
        print(f"数据集最新日期: {self.latest_date}")
    
    def predict_overdue_risk(self):
        """
        逾期风险预测 - 使用随机森林预测用户逾期概率
        
        核心思路：基于用户前期行为特征预测其近期逾期倾向
        
        时间划分：
        - 前期（特征）：6个月前的借阅行为
        - 近期（标签）：最近6个月是否逾期
        
        这样模型学习的是"什么样的前期行为模式会导致近期逾期"
        """
        print("\n" + "=" * 60)
        print("[1/3] 逾期风险预测（随机森林）...")
        
        # 1. 时间划分：前期特征 vs 近期标签
        split_date = (datetime.strptime(self.latest_date, "%Y-%m-%d") - timedelta(days=180)).strftime("%Y-%m-%d")
        print(f"  时间划分点: {split_date}")
        
        # 2. 计算前期特征（6个月前的借阅行为）
        # 显式转换日期类型确保比较正确
        early_lend = self.lend_detail.filter(col("lend_date") < to_date(lit(split_date)))
        
        early_user_stats = early_lend.groupBy("userid").agg(
            count("*").alias("early_borrow_count"),
            F.countDistinct("lend_date").alias("early_active_days"),
            avg("borrow_days").alias("early_avg_borrow_days"),
            spark_sum(when(col("renew_times") > 0, 1).otherwise(0)).alias("early_renew_count")
        )
        
        # 3. 计算近期标签（最近6个月是否逾期）
        recent_lend = self.lend_detail.filter(col("lend_date") >= to_date(lit(split_date)))
        
        recent_overdue = recent_lend.groupBy("userid").agg(
            spark_sum(when(col("is_overdue") == 1, 1).otherwise(0)).alias("recent_overdue_count")
        )
        
        # 4. 合并特征和标签
        # 使用left join保留所有前期有借阅的用户，近期无借阅的视为无逾期
        user_features = early_user_stats \
            .join(recent_overdue, "userid", "left") \
            .join(
                self.user_info.groupBy("userid").agg(
                    F.first("dept").alias("dept"),
                    F.first("redr_type_name").alias("user_type")
                ),
                "userid",
                "left"
            ) \
            .na.fill(0, ["recent_overdue_count"])  # 只填充数值字段
        
        # 5. 计算行为特征
        user_features = user_features \
            .withColumn(
                "borrow_frequency",
                when(col("early_active_days") > 0, 
                     col("early_borrow_count") / col("early_active_days")).otherwise(0.0)
            ) \
            .withColumn(
                "renew_ratio",
                when(col("early_borrow_count") > 0, 
                     col("early_renew_count") / col("early_borrow_count")).otherwise(0.0)
            ) \
            .withColumn(
                "early_avg_borrow_days",
                F.coalesce(col("early_avg_borrow_days"), lit(0.0))
            )
        
        # 6. 创建标签：近期是否有逾期记录
        user_features = user_features.withColumn(
            "is_high_risk",
            when(col("recent_overdue_count") > 0, 1.0).otherwise(0.0)
        )
        
        # 过滤有效数据（前期至少有借阅记录）
        user_features = user_features.filter(col("early_borrow_count") > 0)
        
        print(f"  训练样本数: {user_features.count():,}")
        
        # 统计正负样本比例
        label_dist = user_features.groupBy("is_high_risk").count().collect()
        for row in label_dist:
            label = "有逾期" if row["is_high_risk"] == 1.0 else "无逾期"
            print(f"    {label}: {row['count']:,}人")
        
        # 7. 特征工程 - 只使用前期行为特征
        feature_cols = ["early_borrow_count", "early_avg_borrow_days", "early_renew_count", 
                        "early_active_days", "borrow_frequency", "renew_ratio"]
        
        assembler = VectorAssembler(
            inputCols=feature_cols,
            outputCol="features_raw"
        )
        
        scaler = StandardScaler(
            inputCol="features_raw",
            outputCol="features",
            withStd=True,
            withMean=True
        )
        
        # 5. 随机森林分类器
        rf = RandomForestClassifier(
            featuresCol="features",
            labelCol="is_high_risk",
            predictionCol="prediction",
            probabilityCol="probability",
            numTrees=50,
            maxDepth=5,
            seed=42
        )
        
        # 6. 构建Pipeline
        pipeline = Pipeline(stages=[assembler, scaler, rf])
        
        # 7. 训练模型
        model = pipeline.fit(user_features)
        
        # 8. 预测
        predictions = model.transform(user_features)
        
        # 9. 提取逾期概率（probability列的第二个元素是正类概率）
        # 在Driver端用Pandas提取Vector类型的概率值
        print("  正在提取预测概率...")
        prob_pdf = predictions.select("userid", "probability").toPandas()
        prob_pdf["overdue_probability"] = prob_pdf["probability"].apply(
            lambda x: float(x[1]) if x is not None and len(x) > 1 else 0.0
        )
        
        # 转换回Spark DataFrame
        prob_schema = StructType([
            StructField("userid", StringType(), True),
            StructField("overdue_probability", DoubleType(), True)
        ])
        prob_df = self.spark.createDataFrame(
            prob_pdf[["userid", "overdue_probability"]].values.tolist(),
            schema=prob_schema
        )
        
        # 合并概率数据回原DataFrame，去除ML中间列
        result = predictions.drop("features_raw", "features", "rawPrediction", "probability", "prediction") \
            .join(prob_df, "userid", "inner")
        
        # 10. 生成风险等级
        result = result.withColumn(
            "risk_level",
            when(col("overdue_probability") >= 0.7, "高风险")
            .when(col("overdue_probability") >= 0.4, "中风险")
            .when(col("overdue_probability") >= 0.2, "低风险")
            .otherwise("极低风险")
        )
        
        # 11. 生成预警建议
        result = result.withColumn(
            "warning_message",
            when(col("risk_level") == "高风险", "建议加强逾期提醒，考虑限制借阅数量")
            .when(col("risk_level") == "中风险", "建议定期发送还书提醒")
            .when(col("risk_level") == "低风险", "正常借阅，偶尔提醒即可")
            .otherwise("优质读者，无需特别关注")
        )
        
        # 12. 计算历史逾期率（用于展示，非特征）
        user_history = self.user_summary.select(
            col("userid"),
            col("total_lend_count").alias("total_borrow_count"),
            col("overdue_rate").alias("historical_overdue_rate"),
            col("avg_borrow_days").alias("history_avg_borrow_days")
        )
        
        result = result.join(user_history, "userid", "left")
        
        # 13. 选择输出字段
        output = result.select(
            col("userid"),
            col("dept"),
            col("user_type"),
            F.coalesce(col("total_borrow_count"), col("early_borrow_count")).cast("long").alias("borrow_count"),
            spark_round(F.coalesce(col("historical_overdue_rate"), lit(0.0)), 4).cast("double").alias("historical_overdue_rate"),
            spark_round(F.coalesce(col("history_avg_borrow_days"), col("early_avg_borrow_days")), 2).cast("double").alias("avg_borrow_days"),
            spark_round(col("overdue_probability"), 4).cast("double").alias("overdue_probability"),
            col("risk_level"),
            col("warning_message"),
            lit(self.latest_date).alias("prediction_date")
        )
        
        # 14. 保存到Hive
        output.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_overdue_prediction")
        
        # 15. 保存到MySQL
        output.write \
            .mode("overwrite") \
            .jdbc(self.mysql_url, "overdue_risk_prediction", properties=self.mysql_properties)
        
        # 统计风险分布
        risk_stats = output.groupBy("risk_level").count().collect()
        print(f"✓ 逾期风险预测完成: {output.count():,} 个用户")
        print("\n  风险分布：")
        for row in risk_stats:
            print(f"    {row['risk_level']}: {row['count']:,}人")
        
        return output
    
    def predict_lend_trend(self):
        """
        借阅趋势预测 - 基于历史数据预测未来借阅量
        
        使用月度借阅数据，通过回归模型预测未来趋势
        """
        print("\n" + "=" * 60)
        print("[2/3] 借阅趋势预测（时间序列回归）...")
        
        # 1. 按月统计借阅量
        monthly_lend = self.lend_detail \
            .withColumn("lend_month", F.date_format(to_date(col("lend_date")), "yyyy-MM")) \
            .groupBy("lend_month") \
            .agg(
                count("*").alias("lend_count"),
                F.countDistinct("userid").alias("active_users"),
                F.countDistinct("book_id").alias("unique_books")
            ) \
            .orderBy("lend_month")
        
        # 2. 添加时间特征
        monthly_lend = monthly_lend \
            .withColumn("year", F.substring("lend_month", 1, 4).cast("int")) \
            .withColumn("month", F.substring("lend_month", 6, 2).cast("int"))
        
        # 创建时间索引（从第一个月开始的月数）
        min_year = monthly_lend.agg(spark_min("year")).collect()[0][0]
        monthly_lend = monthly_lend.withColumn(
            "month_index",
            ((col("year") - min_year) * 12 + col("month")).cast("double")
        )
        
        # 添加季节性特征
        monthly_lend = monthly_lend \
            .withColumn("is_semester_start", when(col("month").isin([3, 9]), 1.0).otherwise(0.0)) \
            .withColumn("is_exam_period", when(col("month").isin([1, 6, 7, 12]), 1.0).otherwise(0.0)) \
            .withColumn("is_vacation", when(col("month").isin([2, 7, 8]), 1.0).otherwise(0.0))
        
        print(f"  历史月份数: {monthly_lend.count()}")
        
        # 3. 准备特征
        feature_cols = ["month_index", "month", "is_semester_start", "is_exam_period", "is_vacation"]
        
        assembler = VectorAssembler(
            inputCols=feature_cols,
            outputCol="features"
        )
        
        # 4. 随机森林回归
        rf_regressor = RandomForestRegressor(
            featuresCol="features",
            labelCol="lend_count",
            predictionCol="predicted_count",
            numTrees=30,
            maxDepth=5,
            seed=42
        )
        
        pipeline = Pipeline(stages=[assembler, rf_regressor])
        
        # 5. 训练模型
        model = pipeline.fit(monthly_lend)
        
        # 6. 对历史数据进行拟合
        fitted = model.transform(monthly_lend)
        
        # 7. 生成未来6个月的预测
        # 获取最后一个月的信息
        last_row = monthly_lend.orderBy(col("month_index").desc()).first()
        last_month_index = last_row["month_index"]
        last_year = last_row["year"]
        last_month = last_row["month"]
        
        # 创建未来月份数据
        future_data = []
        current_year = last_year
        current_month = last_month
        
        for i in range(1, 7):  # 预测未来6个月
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
            
            future_data.append({
                "lend_month": f"{current_year}-{current_month:02d}",
                "year": current_year,
                "month": current_month,
                "month_index": float(last_month_index + i),
                "is_semester_start": 1.0 if current_month in [3, 9] else 0.0,
                "is_exam_period": 1.0 if current_month in [1, 6, 7, 12] else 0.0,
                "is_vacation": 1.0 if current_month in [2, 7, 8] else 0.0,
                "lend_count": 0,  # 占位
                "active_users": 0,
                "unique_books": 0
            })
        
        future_df = self.spark.createDataFrame(future_data)
        
        # 8. 预测未来
        future_predictions = model.transform(future_df)
        
        # 9. 合并历史和预测数据
        historical = fitted.select(
            col("lend_month"),
            col("year").cast("int"),
            col("month").cast("int"),
            col("lend_count").cast("long"),
            col("active_users").cast("long"),
            col("unique_books").cast("long"),
            spark_round(col("predicted_count"), 0).cast("long").alias("predicted_count"),
            lit("历史").alias("data_type")
        )
        
        future = future_predictions.select(
            col("lend_month"),
            col("year").cast("int"),
            col("month").cast("int"),
            lit(0).cast("long").alias("lend_count"),
            lit(0).cast("long").alias("active_users"),
            lit(0).cast("long").alias("unique_books"),
            spark_round(col("predicted_count"), 0).cast("long").alias("predicted_count"),
            lit("预测").alias("data_type")
        )
        
        result = historical.union(future).orderBy("lend_month")
        
        # 添加趋势判断
        window = Window.orderBy("lend_month")
        result = result.withColumn(
            "prev_predicted",
            lag("predicted_count", 1).over(window)
        ).withColumn(
            "trend",
            when(col("prev_predicted").isNull(), "持平")
            .when(col("predicted_count") > col("prev_predicted") * 1.1, "上升")
            .when(col("predicted_count") < col("prev_predicted") * 0.9, "下降")
            .otherwise("持平")
        ).drop("prev_predicted")
        
        # 添加预测日期
        result = result.withColumn("prediction_date", lit(self.latest_date))
        
        # 10. 保存到Hive
        result.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_lend_trend_prediction")
        
        # 11. 保存到MySQL
        result.write \
            .mode("overwrite") \
            .jdbc(self.mysql_url, "lend_trend_prediction", properties=self.mysql_properties)
        
        print(f"✓ 借阅趋势预测完成: {result.count()} 个月份（含6个月预测）")
        
        # 显示预测结果
        print("\n  未来6个月预测：")
        future_result = result.filter(col("data_type") == "预测").collect()
        for row in future_result:
            print(f"    {row['lend_month']}: 预测借阅量 {row['predicted_count']:,} ({row['trend']})")
        
        return result
    
    def predict_book_heat(self):
        """
        图书热度预测 - 预测图书未来的借阅热度
        
        核心思路：用前期特征预测近期热度
        特征：早期借阅量、借阅用户数、平均借阅天数、续借次数
        标签：近期借阅量（作为热度指标）
        
        注意：特征不包含近期数据，避免数据泄露
        """
        print("\n" + "=" * 60)
        print("[3/3] 图书热度预测（随机森林回归）...")
        
        # 1. 计算图书特征
        # 将数据分为前期（特征）和近期（标签）
        recent_date = (datetime.strptime(self.latest_date, "%Y-%m-%d") - timedelta(days=90)).strftime("%Y-%m-%d")
        early_date = (datetime.strptime(self.latest_date, "%Y-%m-%d") - timedelta(days=180)).strftime("%Y-%m-%d")
        print(f"  时间窗口: 历史(<{early_date}) | 前期({early_date}~{recent_date}) | 近期(>={recent_date})")
        
        # 近期借阅量（最近3个月）- 作为标签
        recent_lend = self.lend_detail \
            .filter(col("lend_date") >= to_date(lit(recent_date))) \
            .groupBy("book_id") \
            .agg(
                count("*").alias("recent_lend_count"),
                F.countDistinct("userid").alias("recent_user_count")
            )
        
        # 前期借阅量（3-6个月前）- 作为特征
        early_lend = self.lend_detail \
            .filter((col("lend_date") >= to_date(lit(early_date))) & (col("lend_date") < to_date(lit(recent_date)))) \
            .groupBy("book_id") \
            .agg(
                count("*").alias("early_lend_count"),
                F.countDistinct("userid").alias("early_user_count")
            )
        
        # 历史总借阅量（排除近期）
        historical_lend = self.lend_detail \
            .filter(col("lend_date") < to_date(lit(recent_date))) \
            .groupBy("book_id") \
            .agg(
                count("*").alias("historical_lend_count"),
                F.countDistinct("userid").alias("historical_user_count")
            )
        
        # 合并图书基本信息
        book_features = self.book_info.select("book_id", "title", "subject", "author") \
            .join(self.book_summary.select(
                "book_id", 
                col("total_lend_count").alias("all_time_lend_count"),
                col("unique_user_count").alias("all_time_user_count"),
                "avg_borrow_days", 
                "renew_count"
            ), "book_id", "left") \
            .join(historical_lend, "book_id", "left") \
            .join(early_lend, "book_id", "left") \
            .join(recent_lend, "book_id", "left") \
            .select(
                col("book_id"),
                col("title"),
                col("subject"),
                col("author"),
                F.coalesce(col("all_time_lend_count"), lit(0)).cast("double").alias("total_lend_count"),
                F.coalesce(col("all_time_user_count"), lit(0)).cast("double").alias("unique_user_count"),
                F.coalesce(col("avg_borrow_days"), lit(0)).cast("double").alias("avg_borrow_days"),
                F.coalesce(col("renew_count"), lit(0)).cast("double").alias("renew_count"),
                F.coalesce(col("historical_lend_count"), lit(0)).cast("double").alias("historical_lend_count"),
                F.coalesce(col("historical_user_count"), lit(0)).cast("double").alias("historical_user_count"),
                F.coalesce(col("early_lend_count"), lit(0)).cast("double").alias("early_lend_count"),
                F.coalesce(col("early_user_count"), lit(0)).cast("double").alias("early_user_count"),
                F.coalesce(col("recent_lend_count"), lit(0)).cast("double").alias("recent_lend_count"),
                F.coalesce(col("recent_user_count"), lit(0)).cast("double").alias("recent_user_count")
            ) \
            .na.fill(0)
        
        # 计算趋势特征（前期增长率）
        book_features = book_features.withColumn(
            "early_growth_rate",
            when(col("historical_lend_count") > 0, 
                 col("early_lend_count") / col("historical_lend_count"))
            .otherwise(0.0)
        )
        
        # 过滤有借阅记录的图书
        book_features = book_features.filter(col("total_lend_count") > 0)
        
        print(f"  图书样本数: {book_features.count():,}")
        
        # 2. 特征工程 - 只使用前期数据，不包含近期数据
        feature_cols = ["historical_lend_count", "historical_user_count", 
                        "avg_borrow_days", "renew_count", 
                        "early_lend_count", "early_user_count", "early_growth_rate"]
        
        assembler = VectorAssembler(
            inputCols=feature_cols,
            outputCol="features"
        )
        
        # 3. 使用近期借阅量作为目标变量（特征不包含近期数据）
        rf_regressor = RandomForestRegressor(
            featuresCol="features",
            labelCol="recent_lend_count",
            predictionCol="predicted_heat",
            numTrees=30,
            maxDepth=5,
            seed=42
        )
        
        pipeline = Pipeline(stages=[assembler, rf_regressor])
        
        # 4. 训练模型
        model = pipeline.fit(book_features)
        
        # 5. 预测
        predictions = model.transform(book_features)
        
        # 6. 计算热度分数（归一化到0-100）
        max_heat = predictions.agg(spark_max("predicted_heat")).collect()[0][0]
        min_heat = predictions.agg(spark_min("predicted_heat")).collect()[0][0]
        
        # 处理边界情况：热度值相同或为空时设置默认分数
        if max_heat == min_heat or max_heat is None or min_heat is None:
            predictions = predictions.withColumn("heat_score", lit(50.0))
        else:
            predictions = predictions.withColumn(
                "heat_score",
                spark_round((col("predicted_heat") - lit(min_heat)) / lit(max_heat - min_heat) * 100, 2)
            )
        
        # 7. 生成热度等级
        predictions = predictions.withColumn(
            "heat_level",
            when(col("heat_score") >= 80, "爆款")
            .when(col("heat_score") >= 60, "热门")
            .when(col("heat_score") >= 40, "一般")
            .when(col("heat_score") >= 20, "冷门")
            .otherwise("极冷")
        )
        
        # 8. 生成趋势判断（比较近期与前期）
        predictions = predictions.withColumn(
            "trend",
            when(col("early_lend_count") == 0, "稳定")  # 无前期数据
            .when(col("recent_lend_count") > col("early_lend_count") * 1.2, "上升")
            .when(col("recent_lend_count") < col("early_lend_count") * 0.8, "下降")
            .otherwise("稳定")
        )
        
        # 9. 生成采购建议
        predictions = predictions.withColumn(
            "recommendation",
            when((col("heat_level") == "爆款") & (col("trend") == "上升"), "强烈建议增加馆藏")
            .when((col("heat_level") == "热门") & (col("trend") == "上升"), "建议适当增加馆藏")
            .when((col("heat_level").isin("爆款", "热门")) & (col("trend") == "稳定"), "维持现有馆藏")
            .when(col("heat_level") == "极冷", "考虑下架或剔旧")
            .otherwise("正常管理")
        )
        
        # 10. 选择输出字段
        output = predictions.select(
            col("book_id"),
            col("title"),
            col("subject"),
            col("author"),
            col("total_lend_count").cast("long"),
            col("recent_lend_count").cast("long").alias("recent_lend_count"),
            col("unique_user_count").cast("long"),
            spark_round(col("heat_score"), 2).cast("double").alias("heat_score"),
            col("heat_level"),
            col("trend"),
            col("recommendation"),
            lit(self.latest_date).alias("prediction_date")
        ).orderBy(col("heat_score").desc())
        
        # 11. 保存到Hive
        output.write \
            .mode("overwrite") \
            .format("parquet") \
            .saveAsTable("library_ads.ads_book_heat_prediction")
        
        # 12. 保存到MySQL
        output.write \
            .mode("overwrite") \
            .jdbc(self.mysql_url, "book_heat_prediction", properties=self.mysql_properties)
        
        # 统计热度分布
        heat_stats = output.groupBy("heat_level").count().orderBy(col("count").desc()).collect()
        print(f"✓ 图书热度预测完成: {output.count():,} 本图书")
        print("\n  热度分布：")
        for row in heat_stats:
            print(f"    {row['heat_level']}: {row['count']:,}本")
        
        # 显示TOP10热门图书
        print("\n  预测热门TOP10：")
        top10 = output.limit(10).collect()
        for i, row in enumerate(top10, 1):
            title = row['title'] if row['title'] else "未知书名"
            title_display = title[:20] if len(title) > 20 else title
            print(f"    {i}. 《{title_display}》 热度:{row['heat_score']:.1f} ({row['trend']})")
        
        return output
    
    def run(self):
        """运行所有预测模型"""
        print("\n" + "█" * 60)
        print("开始预测模型分析")
        print("█" * 60)
        
        try:
            # 加载数据
            self.load_data()
            
            # 1. 逾期风险预测
            self.predict_overdue_risk()
            
            # 2. 借阅趋势预测
            self.predict_lend_trend()
            
            # 3. 图书热度预测
            self.predict_book_heat()
            
            print("\n" + "█" * 60)
            print("✅ 预测模型分析完成")
            print("█" * 60)
            print("生成的预测表：")
            print("  1. ads_overdue_prediction      - 用户逾期风险预测")
            print("  2. ads_lend_trend_prediction   - 借阅趋势预测")
            print("  3. ads_book_heat_prediction    - 图书热度预测")
            print("\nMySQL表：")
            print("  1. overdue_risk_prediction  - 用户逾期风险")
            print("  2. lend_trend_prediction    - 借阅趋势")
            print("  3. book_heat_prediction     - 图书热度")
            print("█" * 60)
            
        except Exception as e:
            print(f"\n❌ 预测分析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            self.spark.stop()


if __name__ == "__main__":
    predictor = PredictionModels()
    predictor.run()
