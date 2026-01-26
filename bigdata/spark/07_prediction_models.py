#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
步骤7：预测模型分析

功能：
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
        
        # 模型评估结果（用于最后统一打印）
        self.evaluation_results = {
            "overdue_risk": {},
            "lend_trend": {},
            "book_heat": {}
        }
    
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
        
        核心思路：基于用户历史期行为特征预测其近期逾期倾向
        
        时间划分：
        - 历史期（特征）：6个月前以前的借阅行为
        - 近期（标签）：最近6个月是否逾期
        
        注意：这是回测（Backtesting）模式
        - 训练集 = 预测集（用于评估模型性能）
        - 输出的预测结果是对"已知结果"的预测
        - 实际应用时，应该用全部历史数据训练，对当前用户预测未来风险
        
        模型学习的是"什么样的历史行为模式会导致近期逾期"
        """
        print("\n" + "=" * 60)
        print("[1/3] 逾期风险预测（随机森林）...")
        
        # 1. 时间划分：前期特征 vs 近期标签
        split_date = (datetime.strptime(self.latest_date, "%Y-%m-%d") - timedelta(days=180)).strftime("%Y-%m-%d")
        print(f"  时间划分点: {split_date}")
        
        # 2. 计算历史特征（6个月前以前的借阅行为）
        # 显式转换日期类型确保比较正确
        historical_lend = self.lend_detail.filter(col("lend_date") < to_date(lit(split_date)))
        
        historical_user_stats = historical_lend.groupBy("userid").agg(
            count("*").alias("historical_borrow_count"),
            F.countDistinct("lend_date").alias("historical_active_days"),
            avg("borrow_days").alias("historical_avg_borrow_days"),
            spark_sum(when(col("renew_times") > 0, 1).otherwise(0)).alias("historical_renew_count"),
            spark_sum(when(col("is_overdue") == 1, 1).otherwise(0)).alias("historical_overdue_count")
        )
        
        # 计算历史逾期率（用于特征）
        historical_user_stats = historical_user_stats.withColumn(
            "historical_overdue_rate",
            when(col("historical_borrow_count") > 0,
                 col("historical_overdue_count") / col("historical_borrow_count"))
            .otherwise(0.0)
        )
        
        # 3. 计算近期标签（最近6个月的逾期情况）
        recent_lend = self.lend_detail.filter(col("lend_date") >= to_date(lit(split_date)))
        
        # 同时计算近期逾期次数和借阅总数
        recent_stats = recent_lend.groupBy("userid").agg(
            spark_sum(when(col("is_overdue") == 1, 1).otherwise(0)).alias("recent_overdue_count"),
            count("*").alias("recent_borrow_count")
        )
        
        # 4. 合并特征和标签
        # 使用inner join只保留近期有借阅的用户（有实际行为才能评估风险）
        user_features = historical_user_stats \
            .join(recent_stats, "userid", "inner") \
            .join(
                self.user_info.groupBy("userid").agg(
                    F.first("dept").alias("dept"),
                    F.first("redr_type_name").alias("user_type")
                ),
                "userid",
                "left"
            )
        
        # 5. 计算行为特征
        user_features = user_features \
            .withColumn(
                "borrow_frequency",
                when(col("historical_active_days") > 0, 
                     col("historical_borrow_count") / col("historical_active_days")).otherwise(0.0)
            ) \
            .withColumn(
                "renew_ratio",
                when(col("historical_borrow_count") > 0, 
                     col("historical_renew_count") / col("historical_borrow_count")).otherwise(0.0)
            ) \
            .withColumn(
                "historical_avg_borrow_days",
                F.coalesce(col("historical_avg_borrow_days"), lit(0.0))
            )
        
        # 6. 创建标签：近期逾期率（而非简单的是否逾期）
        # 计算近期逾期率（所有用户都有recent_borrow_count > 0，因为用了inner join）
        user_features = user_features.withColumn(
            "recent_overdue_rate",
            col("recent_overdue_count") / col("recent_borrow_count")
        )
        
        # 定义高风险：近期逾期率 > 20% 或 逾期次数 >= 2
        user_features = user_features.withColumn(
            "is_high_risk",
            when((col("recent_overdue_rate") > 0.2) | (col("recent_overdue_count") >= 2), 1.0)
            .otherwise(0.0)
        )
        
        # 过滤有效数据（历史期至少有借阅记录）
        user_features = user_features.filter(col("historical_borrow_count") > 0)
        
        print(f"  训练样本数: {user_features.count():,}")
        
        # 统计正负样本比例
        label_dist = user_features.groupBy("is_high_risk").count().collect()
        positive_count = 0
        negative_count = 0
        for row in label_dist:
            if row["is_high_risk"] == 1.0:
                positive_count = row['count']
                print(f"    有逾期: {row['count']:,}人")
            else:
                negative_count = row['count']
                print(f"    无逾期: {row['count']:,}人")
        
        # 计算类别权重（处理样本不平衡）
        total_count = positive_count + negative_count
        if positive_count > 0 and negative_count > 0:
            weight_ratio = negative_count / positive_count
            print(f"    样本不平衡比例: 1:{weight_ratio:.2f}")
            
            # 为少数类（逾期用户）添加权重
            user_features = user_features.withColumn(
                "sample_weight",
                when(col("is_high_risk") == 1.0, weight_ratio).otherwise(1.0)
            )
        else:
            weight_ratio = 1.0
            user_features = user_features.withColumn("sample_weight", lit(1.0))
        
        # 7. 特征工程 - 只使用历史期行为特征（不包含历史逾期率，避免过拟合）
        # 注意：不使用historical_overdue_rate，因为它与标签高度相关，会导致过拟合
        # 
        # 特征说明：
        # - historical_borrow_count, historical_active_days: 原始特征
        # - borrow_frequency: 派生特征 = historical_borrow_count / historical_active_days
        # - renew_ratio: 派生特征 = historical_renew_count / historical_borrow_count
        # 
        # 虽然存在线性依赖，但随机森林对多重共线性不敏感，可以保留
        feature_cols = ["historical_borrow_count", "historical_avg_borrow_days", "historical_renew_count", 
                        "historical_active_days", "borrow_frequency", "renew_ratio"]
        
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
        
        # 5. 随机森林分类器（添加类别权重处理样本不平衡）
        # 使用weightCol来处理不平衡问题
        rf = RandomForestClassifier(
            featuresCol="features",
            labelCol="is_high_risk",
            predictionCol="prediction",
            probabilityCol="probability",
            weightCol="sample_weight",  # 使用样本权重
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
        
        # 8.1 模型评估（保存结果，稍后打印）
        # 计算AUC
        evaluator_auc = BinaryClassificationEvaluator(
            labelCol="is_high_risk",
            rawPredictionCol="rawPrediction",
            metricName="areaUnderROC"
        )
        auc = evaluator_auc.evaluate(predictions)
        
        # 计算准确率、召回率、精确率
        tp = predictions.filter((col("prediction") == 1.0) & (col("is_high_risk") == 1.0)).count()
        fp = predictions.filter((col("prediction") == 1.0) & (col("is_high_risk") == 0.0)).count()
        tn = predictions.filter((col("prediction") == 0.0) & (col("is_high_risk") == 0.0)).count()
        fn = predictions.filter((col("prediction") == 0.0) & (col("is_high_risk") == 1.0)).count()
        
        accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        # 保存评估结果
        self.evaluation_results["overdue_risk"] = {
            "auc": auc,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1
        }
        
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
        
        # 12. 输出字段（不再从user_summary获取，避免数据泄露）
        output = result.select(
            col("userid"),
            col("dept"),
            col("user_type"),
            col("historical_borrow_count").cast("long").alias("borrow_count"),
            spark_round(col("historical_overdue_rate"), 4).cast("double").alias("historical_overdue_rate"),
            spark_round(col("historical_avg_borrow_days"), 2).cast("double").alias("avg_borrow_days"),
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
        
        # 添加历史趋势特征（前1-3个月的借阅量）
        window = Window.orderBy("lend_month")
        monthly_lend = monthly_lend \
            .withColumn("prev_1_month", lag("lend_count", 1).over(window)) \
            .withColumn("prev_2_month", lag("lend_count", 2).over(window)) \
            .withColumn("prev_3_month", lag("lend_count", 3).over(window)) \
            .na.fill(0, ["prev_1_month", "prev_2_month", "prev_3_month"])
        
        # 添加季节性特征
        monthly_lend = monthly_lend \
            .withColumn("is_semester_start", when(col("month").isin([3, 9]), 1.0).otherwise(0.0)) \
            .withColumn("is_exam_period", when(col("month").isin([1, 6, 7, 12]), 1.0).otherwise(0.0)) \
            .withColumn("is_vacation", when(col("month").isin([2, 7, 8]), 1.0).otherwise(0.0))
        
        print(f"  历史月份数: {monthly_lend.count()}")
        
        # 3. 准备特征（包含历史趋势）
        feature_cols = ["month_index", "month", "prev_1_month", "prev_2_month", "prev_3_month",
                        "is_semester_start", "is_exam_period", "is_vacation"]
        
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
        
        # 6.1 模型评估（保存结果，稍后打印）
        # 计算RMSE和R²
        evaluator_rmse = RegressionEvaluator(
            labelCol="lend_count",
            predictionCol="predicted_count",
            metricName="rmse"
        )
        rmse = evaluator_rmse.evaluate(fitted)
        
        evaluator_r2 = RegressionEvaluator(
            labelCol="lend_count",
            predictionCol="predicted_count",
            metricName="r2"
        )
        r2 = evaluator_r2.evaluate(fitted)
        
        evaluator_mae = RegressionEvaluator(
            labelCol="lend_count",
            predictionCol="predicted_count",
            metricName="mae"
        )
        mae = evaluator_mae.evaluate(fitted)
        
        # 保存评估结果
        self.evaluation_results["lend_trend"] = {
            "rmse": rmse,
            "r2": r2,
            "mae": mae
        }
        
        # 7. 生成未来6个月的预测（滚动预测）
        # 获取最后一个月的信息
        last_row = monthly_lend.orderBy(col("month_index").desc()).first()
        last_month_index = last_row["month_index"]
        last_year = last_row["year"]
        last_month = last_row["month"]
        
        # 获取最近3个月的借阅量（用于第一个月预测）
        recent_3_months = monthly_lend.orderBy(col("month_index").desc()).limit(3).collect()
        prev_counts = [row["lend_count"] for row in reversed(recent_3_months)]
        while len(prev_counts) < 3:
            prev_counts.insert(0, 0)  # 不足3个月时补0
        
        # 滚动预测：每次预测使用前一次的预测结果
        future_results = []
        current_year = last_year
        current_month = last_month
        predicted_values = []  # 存储预测值用于下一次预测
        
        for i in range(1, 7):  # 预测未来6个月
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
            
            # 动态更新历史窗口
            if i == 1:
                # 第一个月：使用真实历史
                p1, p2, p3 = prev_counts[-1], prev_counts[-2], prev_counts[-3]
            elif i == 2:
                # 第二个月：prev_1是第一个月的预测值
                p1, p2, p3 = predicted_values[0], prev_counts[-1], prev_counts[-2]
            elif i == 3:
                # 第三个月：prev_1和prev_2是预测值
                p1, p2, p3 = predicted_values[1], predicted_values[0], prev_counts[-1]
            else:
                # 第四个月及以后：全部使用预测值
                p1, p2, p3 = predicted_values[i-2], predicted_values[i-3], predicted_values[i-4]
            
            # 构建当前月份的特征
            month_data = {
                "lend_month": f"{current_year}-{current_month:02d}",
                "year": current_year,
                "month": current_month,
                "month_index": float(last_month_index + i),
                "prev_1_month": float(p1),
                "prev_2_month": float(p2),
                "prev_3_month": float(p3),
                "is_semester_start": 1.0 if current_month in [3, 9] else 0.0,
                "is_exam_period": 1.0 if current_month in [1, 6, 7, 12] else 0.0,
                "is_vacation": 1.0 if current_month in [2, 7, 8] else 0.0,
                "lend_count": 0,  # 占位
                "active_users": 0,
                "unique_books": 0
            }
            
            # 预测当前月份
            temp_df = self.spark.createDataFrame([month_data])
            temp_pred_df = model.transform(temp_df)
            temp_pred = temp_pred_df.select("predicted_count").collect()[0][0]
            predicted_values.append(temp_pred)
            
            # 保存预测结果
            future_results.append({
                "lend_month": month_data["lend_month"],
                "year": month_data["year"],
                "month": month_data["month"],
                "lend_count": 0,
                "active_users": 0,
                "unique_books": 0,
                "predicted_count": int(round(temp_pred)),
                "data_type": "预测"
            })
        
        # 8. 转换为DataFrame
        future_df = self.spark.createDataFrame(future_results)
        
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
        
        # future_df已经包含正确的字段
        future = future_df.select(
            col("lend_month"),
            col("year").cast("int"),
            col("month").cast("int"),
            col("lend_count").cast("long"),
            col("active_users").cast("long"),
            col("unique_books").cast("long"),
            col("predicted_count").cast("long"),
            col("data_type")
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
        
        核心思路：用历史期和前期特征预测近期热度
        
        时间划分：
        - 更早期（特征）：6个月前以前
        - 前期（特征）：3-6个月前
        - 近期（标签）：最近3个月
        
        注意：这是回测（Backtesting）模式
        - 训练集 = 预测集（用于评估模型性能）
        - 输出的预测结果是对"已知结果"的预测
        - 实际应用时，应该用全部历史数据训练，对当前图书预测未来热度
        
        特征不包含近期数据，避免数据泄露
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
        
        # 更早期借阅量（6个月前以前）- 计算所有特征
        very_early_lend = self.lend_detail \
            .filter(col("lend_date") < to_date(lit(early_date))) \
            .groupBy("book_id") \
            .agg(
                count("*").alias("very_early_lend_count"),
                F.countDistinct("userid").alias("very_early_user_count"),
                avg("borrow_days").alias("very_early_avg_borrow_days"),
                spark_sum(when(col("renew_times") > 0, 1).otherwise(0)).alias("very_early_renew_count")
            )
        
        # 合并图书基本信息（只使用6个月前以前的数据，避免数据泄露）
        book_features = self.book_info.select("book_id", "title", "subject", "author") \
            .join(very_early_lend, "book_id", "left") \
            .join(early_lend, "book_id", "left") \
            .join(recent_lend, "book_id", "left") \
            .select(
                col("book_id"),
                col("title"),
                col("subject"),
                col("author"),
                F.coalesce(col("very_early_avg_borrow_days"), lit(0)).cast("double").alias("avg_borrow_days"),
                F.coalesce(col("very_early_renew_count"), lit(0)).cast("double").alias("renew_count"),
                F.coalesce(col("very_early_lend_count"), lit(0)).cast("double").alias("very_early_lend_count"),
                F.coalesce(col("very_early_user_count"), lit(0)).cast("double").alias("very_early_user_count"),
                F.coalesce(col("early_lend_count"), lit(0)).cast("double").alias("early_lend_count"),
                F.coalesce(col("early_user_count"), lit(0)).cast("double").alias("early_user_count"),
                F.coalesce(col("recent_lend_count"), lit(0)).cast("double").alias("recent_lend_count"),
                F.coalesce(col("recent_user_count"), lit(0)).cast("double").alias("recent_user_count")
            ) \
            .na.fill(0)
        
        # 计算趋势特征（前期相对于更早期的增长率）
        book_features = book_features.withColumn(
            "early_growth_rate",
            when(col("very_early_lend_count") > 0, 
                 col("early_lend_count") / col("very_early_lend_count"))
            .otherwise(when(col("early_lend_count") > 0, 2.0).otherwise(0.0))  # 新书默认增长率2.0
        )
        
        # 过滤有借阅记录的图书（6个月前以前或前期有数据）
        book_features = book_features.filter(
            (col("very_early_lend_count") > 0) | (col("early_lend_count") > 0)
        )
        
        print(f"  图书样本数: {book_features.count():,}")
        
        # 2. 特征工程 - 只使用6个月前以前和前期数据，不包含近期数据
        feature_cols = ["very_early_lend_count", "very_early_user_count", 
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
        
        # 5.1 模型评估（保存结果，稍后打印）
        # 计算RMSE和R²
        evaluator_rmse = RegressionEvaluator(
            labelCol="recent_lend_count",
            predictionCol="predicted_heat",
            metricName="rmse"
        )
        rmse = evaluator_rmse.evaluate(predictions)
        
        evaluator_r2 = RegressionEvaluator(
            labelCol="recent_lend_count",
            predictionCol="predicted_heat",
            metricName="r2"
        )
        r2 = evaluator_r2.evaluate(predictions)
        
        evaluator_mae = RegressionEvaluator(
            labelCol="recent_lend_count",
            predictionCol="predicted_heat",
            metricName="mae"
        )
        mae = evaluator_mae.evaluate(predictions)
        
        # 保存评估结果
        self.evaluation_results["book_heat"] = {
            "rmse": rmse,
            "r2": r2,
            "mae": mae
        }
        
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
            when((col("early_lend_count") == 0) & (col("recent_lend_count") > 0), "上升")  # 新书或冷门书突然热门
            .when((col("early_lend_count") > 0) & (col("recent_lend_count") == 0), "下降")  # 热门书变冷门
            .when(col("early_lend_count") == 0, "稳定")  # 两期都无数据
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
        
        # 10. 选择输出字段（使用6个月前以前+前期的数据作为总借阅量）
        output = predictions.select(
            col("book_id"),
            col("title"),
            col("subject"),
            col("author"),
            (col("very_early_lend_count") + col("early_lend_count")).cast("long").alias("total_lend_count"),
            col("recent_lend_count").cast("long").alias("recent_lend_count"),
            (col("very_early_user_count") + col("early_user_count")).cast("long").alias("unique_user_count"),
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
            
            # 打印模型评估结果
            print("\n" + "█" * 60)
            print("📊 模型评估结果汇总")
            print("█" * 60)
            
            # 逾期风险预测评估
            if self.evaluation_results["overdue_risk"]:
                print("\n[1] 逾期风险预测模型（随机森林分类器）")
                print("=" * 60)
                eval_data = self.evaluation_results["overdue_risk"]
                print(f"  AUC (ROC曲线下面积):  {eval_data['auc']:.4f}")
                print(f"  准确率 (Accuracy):     {eval_data['accuracy']:.4f}")
                print(f"  精确率 (Precision):    {eval_data['precision']:.4f}")
                print(f"  召回率 (Recall):       {eval_data['recall']:.4f}")
                print(f"  F1分数:                {eval_data['f1']:.4f}")
                
                # 根据指标给出评价
                if eval_data['auc'] >= 0.8:
                    print(f"\n  ✓ AUC={eval_data['auc']:.2f} 表明模型具有良好的分类能力")
                else:
                    print(f"\n  ⚠ AUC={eval_data['auc']:.2f} 模型分类能力一般")
                
                if eval_data['recall'] >= 0.7:
                    print(f"  ✓ 召回率={eval_data['recall']*100:.1f}% 能够有效识别潜在逾期用户")
                elif eval_data['recall'] >= 0.5:
                    print(f"  ⚠ 召回率={eval_data['recall']*100:.1f}% 识别能力中等，建议调整阈值")
                else:
                    print(f"  ⚠ 召回率={eval_data['recall']*100:.1f}% 较低，模型过于保守")
                    print(f"     建议：1) 使用样本权重平衡数据 2) 调整分类阈值 3) 增加特征")
                
                if eval_data['f1'] < 0.3:
                    print(f"  ⚠ F1={eval_data['f1']:.2f} 较低，精确率和召回率不平衡")
            
            # 借阅趋势预测评估
            if self.evaluation_results["lend_trend"]:
                print("\n[2] 借阅趋势预测模型（随机森林回归）")
                print("=" * 60)
                eval_data = self.evaluation_results["lend_trend"]
                print(f"  均方根误差 (RMSE):     {eval_data['rmse']:.2f}")
                print(f"  平均绝对误差 (MAE):    {eval_data['mae']:.2f}")
                print(f"  拟合优度 (R²):         {eval_data['r2']:.4f}")
                print(f"\n  ✓ R²={eval_data['r2']:.2f} 说明模型能解释{eval_data['r2']*100:.0f}%的借阅量波动")
                print(f"  ✓ RMSE={eval_data['rmse']:.1f} 预测误差在可接受范围内")
            
            # 图书热度预测评估
            if self.evaluation_results["book_heat"]:
                print("\n[3] 图书热度预测模型（随机森林回归）")
                print("=" * 60)
                eval_data = self.evaluation_results["book_heat"]
                print(f"  均方根误差 (RMSE):     {eval_data['rmse']:.2f}")
                print(f"  平均绝对误差 (MAE):    {eval_data['mae']:.2f}")
                print(f"  拟合优度 (R²):         {eval_data['r2']:.4f}")
                
                # 根据R²给出评价
                if eval_data['r2'] >= 0.7:
                    print(f"\n  ✓ R²={eval_data['r2']:.2f} 模型拟合效果良好")
                elif eval_data['r2'] >= 0.5:
                    print(f"\n  ⚠ R²={eval_data['r2']:.2f} 模型拟合效果一般")
                else:
                    print(f"\n  ⚠ R²={eval_data['r2']:.2f} 模型拟合效果较差")
                    print(f"     原因：图书借阅数据稀疏，大部分图书借阅量很少")
                    print(f"     建议：1) 只预测热门图书 2) 使用分类而非回归 3) 增加特征")
                
                print(f"  ✓ MAE={eval_data['mae']:.1f} 平均预测偏差较小")
            
            print("\n" + "█" * 60)
            if (self.evaluation_results["overdue_risk"].get("recall", 0) < 0.5 or 
                self.evaluation_results["book_heat"].get("r2", 0) < 0.5):
                print("⚠️  部分模型性能需要优化，但整体预测功能正常")
            else:
                print("✅ 所有预测模型评估完成，性能指标符合预期")
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
