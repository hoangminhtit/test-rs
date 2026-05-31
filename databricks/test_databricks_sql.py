"""Quick Databricks SQL connectivity test for all configured tables."""

from databricks import sql

from config.databricks_config import (
    DATABRICKS_HOST,
    DATABRICKS_HTTP_PATH,
    DATABRICKS_TOKEN,
    DATABRICKS_CATALOG_NAME,
    DATABRICKS_SCHEMA_NAME,
    DIM_BOOKS_TABLE,
    DIM_USERS_TABLE,
    DIM_DATE_TABLE,
    FACT_CART_TABLE,
    FACT_REVIEWS_TABLE,
    FACT_SALES_TABLE,
)

TABLES = [
    DIM_BOOKS_TABLE,
    DIM_USERS_TABLE,
    DIM_DATE_TABLE,
    FACT_CART_TABLE,
    FACT_REVIEWS_TABLE,
    FACT_SALES_TABLE,
]


def _full_table_name(table: str) -> str:
    return f"{DATABRICKS_CATALOG_NAME}.{DATABRICKS_SCHEMA_NAME}.{table}"


def main() -> None:
    if not (DATABRICKS_HOST and DATABRICKS_HTTP_PATH and DATABRICKS_TOKEN):
        raise RuntimeError(
            "Missing Databricks SQL credentials. Set DATABRICKS_HOST, "
            "DATABRICKS_HTTP_PATH, and DATABRICKS_TOKEN."
        )

    with sql.connect(
        server_hostname=DATABRICKS_HOST,
        http_path=DATABRICKS_HTTP_PATH,
        access_token=DATABRICKS_TOKEN,
    ) as connection:
        with connection.cursor() as cursor:
            for table in TABLES:
                full_name = _full_table_name(table)
                query = f"SELECT COUNT(*) AS row_count FROM {full_name}"
                cursor.execute(query)
                row = cursor.fetchone()
                print(f"{full_name}: {row[0] if row else 'no result'}")


if __name__ == "__main__":
    main()
