# Book Recommendation System

Content-Based Filtering — **Databricks** + **Sentence Transformer** + **Qdrant** + **FastAPI**.

## Unity Catalog

| Vị trí | Vai trò |
|--------|---------|
| `ecommerce_analyst_agent_catalog.gold` | **Chỉ đọc** (CATALOG_FOREIGN + SCHEMA_FOREIGN) |
| `main.recommender` (mặc định) | **Ghi** pipeline outputs |

**Không** tạo schema/bảng trong `ecommerce_analyst_agent_catalog` — catalog này là foreign.

Trên Databricks Job, set biến môi trường:

```bash
DATABRICKS_OUTPUT_CATALOG_NAME=main
DATABRICKS_OUTPUT_SCHEMA_NAME=recommender
```

Tạo schema ghi (catalog **writable** của workspace bạn, thường là `main`):

```sql
CREATE SCHEMA IF NOT EXISTS main.recommender;
```

Bảng output: `main.recommender.book_embeddings`, `user_book_weights`, `user_embeddings`.

| Bảng Gold | Pipeline |
|-----------|----------|
| `dim_books` | → book embeddings |
| `fact_cart`, `fact_sales` | → user weights |
| `fact_reviews` | Không dùng (không có `buyer_id`) |

## Pipeline Databricks

```bash
cd databricks
pip install -r requirements.txt
python recommendation_job.py
```

**Pipeline 1 (sách):** `create_book_embeddings` → `storage_books_qdrant`

**Pipeline 2 (user):** `create_user_weight_matrix` → `create_user_embeddings` → `storage_users_qdrant`

**Full:** `python recommendation_job.py` (cả hai pipeline)

Qdrant sync dùng `toLocalIterator()` + batch 1000 (tránh OOM driver khi catalog lớn).

## FastAPI

```bash
cd fastapi
pip install -r requirements.txt
uvicorn main:app --reload
```

```http
GET /recommend/42
GET /recommend/42?top_k=10
```

Response (theo plan):

```json
{
  "user_id": 42,
  "recommendations": [
    { "book_id": 101, "score": 0.96 }
  ]
}
```

## Cấu hình

Copy `.env.example` → `.env` (Databricks + Qdrant).
