"""
Build user-book weights from Gold Layer facts → Delta user_book_weights.

Behaviors (plan): user_id | book_id | action | timestamp
  fact_cart  → cart (5)
  fact_sales → purchase (10)

fact_reviews: no buyer_id in catalog — skipped (plan note).
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, StringType, StructField, StructType, TimestampType

from config.databricks_config import (
    FACT_CART_TABLE,
    FACT_SALES_TABLE,
    SALES_PAYMENT_STATUSES,
    USER_BOOK_WEIGHTS_TABLE,
    ensure_output_schema,
    get_spark,
    gold_table_path,
    output_table_path,
)

ACTION_WEIGHTS = {
    "view": 1,
    "click": 2,
    "wishlist": 3,
    "cart": 5,
    "purchase": 10,
}

BEHAVIOR_SCHEMA = StructType(
    [
        StructField("user_id", IntegerType(), False),
        StructField("book_id", IntegerType(), False),
        StructField("action", StringType(), False),
        StructField("timestamp", TimestampType(), True),
        StructField("quantity", IntegerType(), False),
    ]
)


def _empty_behaviors(spark) -> DataFrame:
    return spark.createDataFrame([], BEHAVIOR_SCHEMA)


def _cart_timestamp():
    """fact_cart.added_at is TIMESTAMP in Gold schema."""
    return F.col("added_at").cast("timestamp").alias("timestamp")


def _sales_timestamp():
    """fact_sales.order_date is BIGINT epoch (seconds or milliseconds)."""
    epoch = F.col("order_date").cast("long")
    return (
        F.when(
            epoch > F.lit(1_000_000_000_000),
            F.from_unixtime(epoch / F.lit(1000)),
        )
        .otherwise(F.from_unixtime(epoch))
        .alias("timestamp")
    )


def _behaviors_from_fact_cart(spark) -> DataFrame:
    df = spark.table(gold_table_path(FACT_CART_TABLE))
    required = ["buyer_id", "book_id", "added_at"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[WARN] {FACT_CART_TABLE} missing {missing}; skip cart.")
        return _empty_behaviors(spark)

    qty = (
        F.coalesce(F.col("quantity"), F.lit(1)).cast("int")
        if "quantity" in df.columns
        else F.lit(1)
    )
    return df.select(
        F.col("buyer_id").cast("int").alias("user_id"),
        F.col("book_id").cast("int"),
        F.lit("cart").alias("action"),
        _cart_timestamp(),
        qty.alias("quantity"),
    )


def _behaviors_from_fact_sales(spark) -> DataFrame:
    df = spark.table(gold_table_path(FACT_SALES_TABLE))
    required = ["buyer_id", "book_id", "order_date"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[WARN] {FACT_SALES_TABLE} missing {missing}; skip sales.")
        return _empty_behaviors(spark)

    paid = [s.strip().lower() for s in SALES_PAYMENT_STATUSES if s.strip()]
    if paid and "payment_status" in df.columns:
        df = df.filter(
            F.lower(F.col("payment_status")).isin(paid)
            | F.col("payment_status").isNull()
        )

    qty = (
        F.coalesce(F.col("quantity"), F.lit(1)).cast("int")
        if "quantity" in df.columns
        else F.lit(1)
    )
    return df.select(
        F.col("buyer_id").cast("int").alias("user_id"),
        F.col("book_id").cast("int"),
        F.lit("purchase").alias("action"),
        _sales_timestamp(),
        qty.alias("quantity"),
    )


def build_user_behaviors(spark) -> DataFrame:
    return _behaviors_from_fact_cart(spark).unionByName(
        _behaviors_from_fact_sales(spark)
    )


def create_user_weight_matrix() -> int:
    spark = get_spark()
    ensure_output_schema(spark)
    behaviors_df = build_user_behaviors(spark)

    weight_map = F.create_map(
        *[x for pair in ACTION_WEIGHTS.items() for x in (F.lit(pair[0]), F.lit(pair[1]))]
    )

    result_df = (
        behaviors_df.withColumn("unit_weight", weight_map[F.col("action")])
        .withColumn("weight", F.col("unit_weight") * F.col("quantity"))
        .groupBy("user_id", "book_id")
        .agg(F.sum("weight").alias("weight"))
        .filter(F.col("weight") > 0)
    )

    (
        result_df.write.format("delta")
        .mode("overwrite")
        .saveAsTable(output_table_path(USER_BOOK_WEIGHTS_TABLE))
    )
    return result_df.count()


if __name__ == "__main__":
    print(f"Created {create_user_weight_matrix()} user-book weight rows.")
