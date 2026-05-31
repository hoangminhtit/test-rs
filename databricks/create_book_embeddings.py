"""
Create book embeddings from Gold Layer dim_books → Delta book_embeddings.

Plan input: book_id, title, author, category_name, seller_username, price, rating_avg, purchase_count
"""

from sentence_transformers import SentenceTransformer

from config.databricks_config import (
    BOOK_EMBEDDINGS_TABLE,
    DIM_BOOKS_TABLE,
    ensure_output_schema,
    get_spark,
    gold_table_path,
    output_table_path,
)

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


def build_book_text(
    title: str,
    author: str,
    category_name: str,
    seller_username: str,
    price,
    rating_avg,
    purchase_count,
) -> str:
    """Text construction per plan section 5."""
    return f"""
Title: {title}
Author: {author}
Category: {category_name}
Seller: {seller_username}
Price: {price}
Rating: {rating_avg}
Purchase count: {purchase_count}
""".strip()


def create_book_embeddings() -> int:
    spark = get_spark()
    ensure_output_schema(spark)
    books_df = spark.table(gold_table_path(DIM_BOOKS_TABLE))
    model = SentenceTransformer(EMBEDDING_MODEL)

    records = []
    for row in books_df.collect():
        text = build_book_text(
            title=row.title,
            author=row.author,
            category_name=row.category_name,
            seller_username=row.seller_username,
            price=row.price,
            rating_avg=row.rating_avg,
            purchase_count=row.purchase_count,
        )
        records.append((int(row.book_id), model.encode(text).tolist()))

    result_df = spark.createDataFrame(
        records, schema="book_id int, embedding array<float>"
    )
    (
        result_df.write.format("delta")
        .mode("overwrite")
        .saveAsTable(output_table_path(BOOK_EMBEDDINGS_TABLE))
    )
    return result_df.count()


if __name__ == "__main__":
    print(f"Created embeddings for {create_book_embeddings()} books.")
