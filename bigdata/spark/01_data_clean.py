# -*- coding: utf-8 -*-
"""
步骤1：数据清洗（ODS → DWD层）

功能：
- 从HDFS读取原始CSV数据
- 数据清洗与转换（日期格式、类型转换、字段计算）
- 构建用户维度表、图书维度表、借阅明细事实表
- 写入Hive分区表（按year/month分区）

输出表：
- library_dwd.dwd_user_info：用户维度表
- library_dwd.dwd_book_info：图书维度表
- library_dwd.dwd_lend_detail：借阅明细事实表
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
from datetime import datetime
import sys


class LibraryDataCleaner:
    """图书馆数据清洗"""
    
    def __init__(self, spark):
        self.spark = spark
        if len(sys.argv) > 1:
            self.process_mode = sys.argv[1]  # YYYYMM 或 "all"
        else:
            self.process_mode = "all"
        self.hdfs_input_path = f"/data/library/raw/LENDHIST2019_2020.csv"
        
    def read_raw_data(self):
        """从HDFS读取原始CSV数据"""
        print("=" * 60)
        print("从HDFS读取原始数据...")
        print(f"输入路径: {self.hdfs_input_path}")
        
        schema = StructType([
            StructField("USERID", StringType(), True),
            StructField("BIRTHYEAR", StringType(), True),
            StructField("SEX", StringType(), True),
            StructField("DEPT", StringType(), True),
            StructField("OCCUPATION", StringType(), True),
            StructField("CODE01", StringType(), True),
            StructField("REDR_TYPE_NAME", StringType(), True),
            StructField("LEND_DATE", StringType(), True),
            StructField("RET_DATE", StringType(), True),
            StructField("RENEW_TIMES", StringType(), True),
            StructField("TITLE", StringType(), True),
            StructField("BOOK_ID", StringType(), True),
            StructField("ABSTRACT", StringType(), True),
            StructField("SUB", StringType(), True),
            StructField("CALL_NO", StringType(), True),
            StructField("AUTHOR", StringType(), True),
            StructField("AU", StringType(), True),
            StructField("PUBLISHER", StringType(), True),
            StructField("ISBN", StringType(), True),
            StructField("PUB_YEAR", StringType(), True),
            StructField("LOCATION_NAME", StringType(), True),
            StructField("DOC_TYPE_NAME", StringType(), True)
        ])
        
        # 要求UTF-8编码，GBK需先转换：iconv -f GBK -t UTF-8 input.csv -o output.csv
        df = self.spark.read \
            .option("header", "true") \
            .option("delimiter", ",") \
            .option("quote", "\"") \
            .option("escape", "\"") \
            .option("multiLine", "false") \
            .option("encoding", "UTF-8") \
            .schema(schema) \
            .csv(self.hdfs_input_path)
        
        df = df.toDF(*[col_name.lower() for col_name in df.columns])
        
        print(f"原始数据记录数: {df.count()}")
        df.printSchema()
        df.show(5, truncate=False)
        
        return df
    
    def clean_and_transform(self, raw_df):
        """数据清洗与转换"""
        print("\n" + "=" * 60)
        print("执行数据清洗与转换...")
        
        cleaned_df = raw_df \
            .filter(col("userid").isNotNull()) \
            .filter(col("userid") != "") \
            .filter(col("book_id").isNotNull()) \
            .filter(col("book_id") != "") \
            .filter(col("lend_date").isNotNull()) \
            .filter(col("lend_date") != "")
        
        print(f"清洗后记录数: {cleaned_df.count()}")
        
        # 处理日期时间格式：2020-01-1321:23:17 -> 2020-01-13 21:23:17
        transformed_df = cleaned_df \
            .withColumn(
                "lend_datetime",
                regexp_replace(
                    regexp_replace(trim(col("lend_date")), "\\s+", " "),
                    "([0-9]{4}-[0-9]{2}-[0-9]{2}) ?([0-9]{2}:[0-9]{2}:[0-9]{2})", 
                    "$1 $2"
                )
            ) \
            .withColumn(
                "ret_datetime",
                when(col("ret_date").isNotNull() & (col("ret_date") != ""),
                     regexp_replace(
                         regexp_replace(trim(col("ret_date")), "\\s+", " "),
                         "([0-9]{4}-[0-9]{2}-[0-9]{2}) ?([0-9]{2}:[0-9]{2}:[0-9]{2})", 
                         "$1 $2"
                     )
                ).otherwise(None)
            )
        
        # 3. 类型转换与字段计算
        transformed_df = transformed_df \
            .withColumn("birthyear_int", 
                       when(col("birthyear").rlike("^[0-9]{4}$"), 
                            col("birthyear").cast("int")).otherwise(None)) \
            .withColumn("age", lit(2020) - col("birthyear_int")) \
            .withColumn("renew_times_int", 
                       col("renew_times").cast("int")) \
            .withColumn("pub_year_int", 
                       col("pub_year").cast("int")) \
            .withColumn("subject", 
                       when(col("sub").isNull() | (col("sub") == ""), "未分类")
                       .otherwise(col("sub")))
        
        # 计算借阅天数和逾期标识
        transformed_df = transformed_df \
            .withColumn("lend_ts", 
                       unix_timestamp(col("lend_datetime"), "yyyy-MM-dd HH:mm:ss")) \
            .withColumn("ret_ts", 
                       unix_timestamp(col("ret_datetime"), "yyyy-MM-dd HH:mm:ss")) \
            .withColumn("borrow_days", 
                       when(col("ret_ts").isNotNull(), 
                            datediff(from_unixtime(col("ret_ts")), 
                                   from_unixtime(col("lend_ts"))))
                       .otherwise(None)) \
            .withColumn("is_overdue", 
                       when((col("ret_date").isNotNull()) & (col("borrow_days") > 90), 1).otherwise(0))
        
        # 提取时间维度字段
        transformed_df = transformed_df \
            .withColumn("lend_year", 
                       year(from_unixtime(col("lend_ts")))) \
            .withColumn("lend_month", 
                       month(from_unixtime(col("lend_ts")))) \
            .withColumn("lend_day", 
                       dayofmonth(from_unixtime(col("lend_ts")))) \
            .withColumn("lend_hour", 
                       hour(from_unixtime(col("lend_ts")))) \
            .withColumn("lend_weekday", 
                       dayofweek(from_unixtime(col("lend_ts")))) \
            .withColumn("lend_date_only", 
                       to_date(from_unixtime(col("lend_ts")))) \
            .withColumn("lend_time_only", 
                       date_format(from_unixtime(col("lend_ts")), "HH:mm:ss"))
        
        # 生成唯一借阅记录ID
        transformed_df = transformed_df \
            .withColumn("lend_id", 
                       md5(concat(col("userid"), col("book_id"), col("lend_date"))))
        
        print("数据转换完成")
        return transformed_df
    
    def build_user_dimension(self, cleaned_df):
        """构建用户维度表"""
        print("\n" + "=" * 60)
        print("构建用户维度表...")
        
        user_df = cleaned_df \
            .select(
                "userid",
                "birthyear_int",
                "age",
                "sex",
                "dept",
                "occupation",
                "redr_type_name",
                "lend_year",
                "lend_month"
            ) \
            .withColumn("rank", 
                       row_number().over(Window.partitionBy("userid")
                                       .orderBy(desc("lend_year"), desc("lend_month")))) \
            .filter(col("rank") == 1) \
            .select(
                "userid",
                col("birthyear_int").alias("birthyear"),
                "age",
                "sex",
                "dept",
                "occupation",
                "redr_type_name",
                "lend_year",
                "lend_month"
            ) \
            .withColumn("year", col("lend_year")) \
            .withColumn("month", col("lend_month")) \
            .drop("lend_year", "lend_month")
        
        print(f"用户维度记录数: {user_df.count()}")
        return user_df
    
    def build_book_dimension(self, cleaned_df):
        """构建图书维度表"""
        print("\n" + "=" * 60)
        print("构建图书维度表...")
        
        book_df = cleaned_df \
            .select(
                "book_id",
                "title",
                "author",
                "publisher",
                "isbn",
                "pub_year_int",
                "subject",
                "call_no",
                "location_name",
                "doc_type_name",
                "lend_year",
                "lend_month"
            ) \
            .withColumn("rank", 
                       row_number().over(Window.partitionBy("book_id")
                                       .orderBy(desc("lend_year"), desc("lend_month")))) \
            .filter(col("rank") == 1) \
            .select(
                "book_id",
                "title",
                "author",
                "publisher",
                "isbn",
                col("pub_year_int").alias("pub_year"),
                "subject",
                "call_no",
                "location_name",
                "doc_type_name",
                "lend_year",
                "lend_month"
            ) \
            .withColumn("year", col("lend_year")) \
            .withColumn("month", col("lend_month")) \
            .drop("lend_year", "lend_month")
        
        print(f"图书维度记录数: {book_df.count()}")
        return book_df
    
    def build_lend_detail(self, cleaned_df):
        """构建借阅明细事实表"""
        print("\n" + "=" * 60)
        print("构建借阅明细事实表...")
        
        lend_df = cleaned_df \
            .select(
                "lend_id",
                "userid",
                "book_id",
                col("lend_date_only").alias("lend_date"),
                col("lend_time_only").alias("lend_time"),
                to_date(col("ret_datetime")).alias("ret_date"),
                date_format(col("ret_datetime"), "HH:mm:ss").alias("ret_time"),
                col("renew_times_int").alias("renew_times"),
                "borrow_days",
                "is_overdue",
                "lend_year",
                "lend_month",
                "lend_day",
                "lend_hour",
                "lend_weekday",
                # 添加归还时间解析字段（用于时间分布分析）
                hour(col("ret_datetime")).alias("ret_hour"),
                dayofweek(col("ret_datetime")).alias("ret_weekday"),
                month(col("ret_datetime")).alias("ret_month")
            ) \
            .withColumn("year", col("lend_year")) \
            .withColumn("month", col("lend_month"))
        
        print(f"借阅明细记录数: {lend_df.count()}")
        return lend_df
    
    def write_to_hive(self, df, table_name):
        """写入Hive分区表（按year/month分区）"""
        print(f"\n写入Hive表: {table_name}")
        
        df.write \
            .mode("overwrite") \
            .partitionBy("year", "month") \
            .format("parquet") \
            .option("compression", "snappy") \
            .saveAsTable(table_name)
        
        partitions = df.select("year", "month").distinct().orderBy("year", "month").collect()
        print(f"表 {table_name} 写入完成，分区数: {len(partitions)}")
        for p in partitions:
            print(f"  - year={p.year}, month={p.month}")
    
    def run(self):
        """运行数据清洗流程"""
        print("\n" + "=" * 60)
        print("开始Spark数据清洗任务")
        print(f"处理模式: {self.process_mode}")
        if self.process_mode != "all":
            year = int(self.process_mode[:4])
            month = int(self.process_mode[4:6])
            print(f"处理指定月份: {year}年{month}月")
        else:
            print("处理所有数据 (2019-2020)")
        print("=" * 60)
        
        raw_df = self.read_raw_data()
        cleaned_df = self.clean_and_transform(raw_df)
        
        user_dim = self.build_user_dimension(cleaned_df)
        self.write_to_hive(user_dim, "library_dwd.dwd_user_info")
        
        book_dim = self.build_book_dimension(cleaned_df)
        self.write_to_hive(book_dim, "library_dwd.dwd_book_info")
        
        lend_detail = self.build_lend_detail(cleaned_df)
        self.write_to_hive(lend_detail, "library_dwd.dwd_lend_detail")
        
        print("\n" + "=" * 60)
        print("Spark数据清洗任务完成！")
        print("=" * 60)
        
        self.data_quality_check()
    
    def data_quality_check(self):
        """数据质量检查"""
        print("\n" + "=" * 60)
        print("执行数据质量检查...")
        
        user_count = self.spark.sql(f"""
            SELECT COUNT(*) FROM library_dwd.dwd_user_info
        """).collect()[0][0]
        print(f"✓ 用户维度记录数: {user_count}")
        
        book_count = self.spark.sql(f"""
            SELECT COUNT(*) FROM library_dwd.dwd_book_info
        """).collect()[0][0]
        print(f"✓ 图书维度记录数: {book_count}")
        
        lend_count = self.spark.sql(f"""
            SELECT COUNT(*) FROM library_dwd.dwd_lend_detail
        """).collect()[0][0]
        print(f"✓ 借阅明细记录数: {lend_count}")
        
        partitions = self.spark.sql(f"""
            SELECT year, month, COUNT(*) as cnt 
            FROM library_dwd.dwd_lend_detail 
            GROUP BY year, month 
            ORDER BY year, month
        """).collect()
        print(f"\n✓ 数据分区: {len(partitions)}个月")
        for p in partitions:
            print(f"  - {p.year}年{p.month}月: {p.cnt}条记录")
        
        null_check = self.spark.sql(f"""
            SELECT 
                SUM(CASE WHEN userid IS NULL THEN 1 ELSE 0 END) as null_userid,
                SUM(CASE WHEN book_id IS NULL THEN 1 ELSE 0 END) as null_book_id,
                SUM(CASE WHEN lend_date IS NULL THEN 1 ELSE 0 END) as null_lend_date
            FROM library_dwd.dwd_lend_detail
        """).collect()[0]
        
        print(f"\n✓ 数据完整性检查:")
        print(f"  - NULL userid: {null_check[0]}")
        print(f"  - NULL book_id: {null_check[1]}")
        print(f"  - NULL lend_date: {null_check[2]}")
        
        if null_check[0] == 0 and null_check[1] == 0 and null_check[2] == 0:
            print("✓ 数据质量检查通过！")
        else:
            print("⚠ 警告：存在空值数据")


def main():
    """主函数"""
    spark = SparkSession.builder \
        .appName("Library Data Cleaning") \
        .config("spark.sql.warehouse.dir", "/user/hive/warehouse") \
        .config("hive.metastore.uris", "thrift://master:9083") \
        .config("spark.sql.shuffle.partitions", "10") \
        .config("spark.default.parallelism", "10") \
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic") \
        .enableHiveSupport() \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    try:
        cleaner = LibraryDataCleaner(spark)
        cleaner.run()
    except Exception as e:
        print(f"数据清洗任务失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
