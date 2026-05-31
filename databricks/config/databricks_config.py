"""Databricks workspace and Spark configuration."""

import os

DATABRICKS_URL = os.getenv("DATABRICKS_URL", "")
DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "")
DATABRICKS_CATALOG_NAME = os.getenv("DATABRICKS_CATALOG_NAME", "main")
DATABRICKS_SCHEMA_NAME = os.getenv("DATABRICKS_SCHEMA_NAME", "default")

BOOKS_TABLE = os.getenv("BOOKS_TABLE", "books")
USER_BEHAVIORS_TABLE = os.getenv("USER_BEHAVIORS_TABLE", "user_behaviors")
BOOK_EMBEDDINGS_TABLE = os.getenv("BOOK_EMBEDDINGS_TABLE", "book_embeddings")
USER_BOOK_WEIGHTS_TABLE = os.getenv("USER_BOOK_WEIGHTS_TABLE", "user_book_weights")
USER_EMBEDDINGS_TABLE = os.getenv("USER_EMBEDDINGS_TABLE", "user_embeddings")


def get_spark():
    """Return active SparkSession (Databricks) or create a local session."""
    from pyspark.sql import SparkSession

    spark = SparkSession.getActiveSession()
    if spark is None:
        spark = (
            SparkSession.builder.appName("recommender-service")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config(
                "spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.delta.catalog.DeltaCatalog",
            )
            .getOrCreate()
        )
    return spark


def table_path(table_name: str) -> str:
    """Fully qualified Delta table name: catalog.schema.table."""
    return f"{DATABRICKS_CATALOG_NAME}.{DATABRICKS_SCHEMA_NAME}.{table_name}"
