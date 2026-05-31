"""
Create book embeddings from books catalog and write to Delta table book_embeddings.
"""

from sentence_transformers import SentenceTransformer

from config.databricks_config import (
    BOOK_EMBEDDINGS_TABLE,
    BOOKS_TABLE,
    get_spark,
    table_path,
)

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


def build_book_text(title: str, author: str, category: str, description: str) -> str:
    return f"""
Title: {title}
Author: {author}
Category: {category}
Description: {description}
""".strip()


def create_book_embeddings():
    spark = get_spark()
    books_df = spark.table(table_path(BOOKS_TABLE))

    model = SentenceTransformer(EMBEDDING_MODEL)
    rows = books_df.collect()

    records = []
    for row in rows:
        text = build_book_text(
            row.title, row.author, row.category, row.description
        )
        embedding = model.encode(text).tolist()
        records.append((row.book_id, embedding))

    result_df = spark.createDataFrame(
        records, schema="book_id long, embedding array<float>"
    )

    (
        result_df.write.format("delta")
        .mode("overwrite")
        .saveAsTable(table_path(BOOK_EMBEDDINGS_TABLE))
    )

    return result_df.count()


if __name__ == "__main__":
    count = create_book_embeddings()
    print(f"Created embeddings for {count} books.")
