"""
Create user profile embeddings via weighted average of book embeddings.
"""

import numpy as np

from config.databricks_config import (
    BOOK_EMBEDDINGS_TABLE,
    USER_BOOK_WEIGHTS_TABLE,
    USER_EMBEDDINGS_TABLE,
    get_spark,
    table_path,
)


def weighted_average(embeddings, weights):
    """UserEmbedding = sum(weight * embedding) / sum(weight)."""
    total_weight = sum(weights)
    if total_weight == 0:
        return None
    stacked = np.array(embeddings, dtype=np.float32)
    weight_arr = np.array(weights, dtype=np.float32).reshape(-1, 1)
    return (stacked * weight_arr).sum(axis=0) / total_weight


def create_user_embeddings():
    spark = get_spark()
    weights_df = spark.table(table_path(USER_BOOK_WEIGHTS_TABLE))
    books_df = spark.table(table_path(BOOK_EMBEDDINGS_TABLE))

    joined_df = weights_df.join(books_df, on="book_id", how="inner")
    rows = joined_df.collect()

    user_data = {}
    for row in rows:
        uid = row.user_id
        if uid not in user_data:
            user_data[uid] = {"embeddings": [], "weights": []}
        user_data[uid]["embeddings"].append(row.embedding)
        user_data[uid]["weights"].append(float(row.weight))

    records = []
    for user_id, data in user_data.items():
        embedding = weighted_average(data["embeddings"], data["weights"])
        if embedding is not None:
            records.append((user_id, embedding.tolist()))

    result_df = spark.createDataFrame(records, schema="user_id string, embedding array<float>")

    (
        result_df.write.format("delta")
        .mode("overwrite")
        .saveAsTable(table_path(USER_EMBEDDINGS_TABLE))
    )

    return result_df.count()


if __name__ == "__main__":
    count = create_user_embeddings()
    print(f"Created embeddings for {count} users.")
