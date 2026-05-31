"""
Aggregate user-book interaction weights from user behaviors.
"""

from pyspark.sql import functions as F

from config.databricks_config import (
    USER_BEHAVIORS_TABLE,
    USER_BOOK_WEIGHTS_TABLE,
    get_spark,
    table_path,
)

ACTION_WEIGHTS = {
    "view": 1,
    "click": 2,
    "wishlist": 3,
    "cart": 5,
    "purchase": 10,
}


def create_user_weight_matrix():
    spark = get_spark()
    behaviors_df = spark.table(table_path(USER_BEHAVIORS_TABLE))

    mapping_expr = F.create_map(
        *[item for pair in ACTION_WEIGHTS.items() for item in (F.lit(pair[0]), F.lit(pair[1]))]
    )

    weighted_df = behaviors_df.withColumn("weight", mapping_expr[F.col("action")])

    result_df = (
        weighted_df.groupBy("user_id", "book_id")
        .agg(F.sum("weight").alias("weight"))
        .filter(F.col("weight").isNotNull())
    )

    (
        result_df.write.format("delta")
        .mode("overwrite")
        .saveAsTable(table_path(USER_BOOK_WEIGHTS_TABLE))
    )

    return result_df.count()


if __name__ == "__main__":
    count = create_user_weight_matrix()
    print(f"Created {count} user-book weight rows.")
