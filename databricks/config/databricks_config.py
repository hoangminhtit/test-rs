"""Databricks workspace, Spark, and Gold Layer table configuration."""

import os

from dotenv import load_dotenv

load_dotenv()

DATABRICKS_URL = os.getenv("DATABRICKS_URL", "")
DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "")
DATABRICKS_CATALOG_NAME = os.getenv(
    "DATABRICKS_CATALOG_NAME", "ecommerce_analyst_agent_catalog"
)
# Gold = read-only foreign schema (dim_*, fact_*)
DATABRICKS_SCHEMA_NAME = os.getenv("DATABRICKS_SCHEMA_NAME", "gold")
# Pipeline outputs: writable catalog/schema (NOT the foreign Gold catalog)
# Default "main" — change in Job env if your workspace uses another catalog
DATABRICKS_OUTPUT_CATALOG_NAME = os.getenv("DATABRICKS_OUTPUT_CATALOG_NAME", "main")
DATABRICKS_OUTPUT_SCHEMA_NAME = os.getenv(
    "DATABRICKS_OUTPUT_SCHEMA_NAME", "recommender"
)
DATABRICKS_CONNECT_ENABLED = os.getenv("DATABRICKS_CONNECT_ENABLED", "").lower() in {
    "1",
    "true",
    "yes",
}

# Gold Layer — source tables (read from gold schema)
DIM_BOOKS_TABLE = os.getenv("DIM_BOOKS_TABLE", "dim_books")
DIM_USERS_TABLE = os.getenv("DIM_USERS_TABLE", "dim_users")
DIM_DATE_TABLE = os.getenv("DIM_DATE_TABLE", "dim_date")
FACT_CART_TABLE = os.getenv("FACT_CART_TABLE", "fact_cart")
FACT_REVIEWS_TABLE = os.getenv("FACT_REVIEWS_TABLE", "fact_reviews")
FACT_SALES_TABLE = os.getenv("FACT_SALES_TABLE", "fact_sales")

# Pipeline output tables (write to output schema)
BOOK_EMBEDDINGS_TABLE = os.getenv("BOOK_EMBEDDINGS_TABLE", "book_embeddings")
USER_BOOK_WEIGHTS_TABLE = os.getenv("USER_BOOK_WEIGHTS_TABLE", "user_book_weights")
USER_EMBEDDINGS_TABLE = os.getenv("USER_EMBEDDINGS_TABLE", "user_embeddings")

SALES_PAYMENT_STATUSES = os.getenv("SALES_PAYMENT_STATUSES", "paid,completed,success").split(",")


def gold_table_path(table_name: str) -> str:
    """Read-only Gold Layer: catalog.gold.table"""
    return f"{DATABRICKS_CATALOG_NAME}.{DATABRICKS_SCHEMA_NAME}.{table_name}"


def output_table_path(table_name: str) -> str:
    """Writable pipeline tables: catalog.recommender.table"""
    return (
        f"{DATABRICKS_OUTPUT_CATALOG_NAME}.{DATABRICKS_OUTPUT_SCHEMA_NAME}.{table_name}"
    )


def table_path(table_name: str) -> str:
    """Deprecated alias — use gold_table_path or output_table_path."""
    return gold_table_path(table_name)


def validate_output_location() -> None:
    """Fail fast when output is pointed at the read-only foreign catalog."""
    if (
        DATABRICKS_OUTPUT_CATALOG_NAME.strip().lower()
        == DATABRICKS_CATALOG_NAME.strip().lower()
    ):
        raise RuntimeError(
            f"DATABRICKS_OUTPUT_CATALOG_NAME must not be the foreign source catalog "
            f"'{DATABRICKS_CATALOG_NAME}'. "
            f"Set DATABRICKS_OUTPUT_CATALOG_NAME to a writable catalog (e.g. 'main') "
            f"on the cluster/job environment, then create schema "
            f"'{DATABRICKS_OUTPUT_CATALOG_NAME}.{DATABRICKS_OUTPUT_SCHEMA_NAME}' in SQL."
        )


def ensure_output_schema(spark) -> None:
    """Create output schema in a writable catalog (requires CREATE SCHEMA)."""
    validate_output_location()
    qualified = (
        f"{DATABRICKS_OUTPUT_CATALOG_NAME}.{DATABRICKS_OUTPUT_SCHEMA_NAME}"
    )
    try:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {qualified}")
    except Exception as exc:
        err = str(exc)
        if "FOREIGN" in err or "CHILD_CREATION_FORBIDDEN" in err:
            raise RuntimeError(
                f"Cannot create schema '{qualified}': catalog "
                f"'{DATABRICKS_OUTPUT_CATALOG_NAME}' is foreign or read-only. "
                f"Use a native/writable catalog (commonly 'main') via "
                f"DATABRICKS_OUTPUT_CATALOG_NAME."
            ) from exc
        raise


def _is_databricks_runtime() -> bool:
    if os.getenv("DATABRICKS_RUNTIME_VERSION"):
        return True
    if os.getenv("DATABRICKS_CLUSTER_ID") or os.getenv("DB_IS_DRIVER"):
        return True
    if os.getenv("DATABRICKS_ROOT_VIRTUALENV_ENV") or os.getenv("DB_HOME"):
        return True
    if os.getenv("SPARK_REMOTE"):
        return True
    try:
        from pyspark.dbutils import DBUtils  # noqa: F401

        return True
    except Exception:
        pass
    return False


def get_spark():
    from pyspark.sql import SparkSession

    spark = SparkSession.getActiveSession()
    if spark is not None:
        return spark

    if _is_databricks_runtime():
        return SparkSession.builder.appName("recommender-service").getOrCreate()

    try:
        return SparkSession.builder.appName("recommender-service").getOrCreate()
    except Exception:
        pass

    if (
        DATABRICKS_CONNECT_ENABLED
        and DATABRICKS_HOST
        and DATABRICKS_TOKEN
        and DATABRICKS_HTTP_PATH
    ):
        try:
            from databricks.connect import DatabricksSession
        except Exception as exc:
            raise RuntimeError(
                "Databricks Connect is required for remote Spark sessions. "
                "Install databricks-connect and configure the environment."
            ) from exc

        return (
            DatabricksSession.builder.remote(
                host=DATABRICKS_HOST,
                token=DATABRICKS_TOKEN,
                http_path=DATABRICKS_HTTP_PATH,
            )
            .appName("recommender-service")
            .getOrCreate()
        )

    raise RuntimeError(
        "No active Spark session found. Run this on a Databricks cluster with "
        "an attached Spark runtime, or enable Databricks Connect locally "
        "(DATABRICKS_CONNECT_ENABLED=true + HOST/TOKEN/HTTP_PATH)."
    )
