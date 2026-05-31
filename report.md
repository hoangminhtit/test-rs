# Báo cáo — Book Recommendation System

**Cập nhật theo:** `plan (1).md` (Gold Layer schema đầy đủ)

---

## Đã viết lại theo plan

### Databricks

| Module | Khớp plan |
|--------|-----------|
| `create_book_embeddings.py` | Input `dim_books`; text đúng mẫu section 5; output `book_id \| embedding` |
| `create_user_weight_matrix.py` | `fact_cart` + `fact_sales` only; **bỏ `fact_reviews`**; ACTION_WEIGHTS; groupBy sum(weight) |
| `create_user_embeddings.py` | Weighted average; output `user_id \| embedding` |
| `storage_books_qdrant.py` / `storage_users_qdrant.py` | Batch upsert; payload sách có `book_id` |
| `recommendation_job.py` | 4 bước tuần tự |
| `databricks_config.py` | Spark session cho Databricks cluster + Connect |

### FastAPI

| Module | Khớp plan |
|--------|-----------|
| `recommend_service.py` | retrieve user → search books → Top-K; response `{book_id, score}` |
| `routes.py` | `GET /recommend/{user_id}` |

### Schema `fact_reviews`

Chỉ còn: `book_id`, `score`, `total_reviews_at_snapshot`, `snapshot_date` — không map được `user_id`, nên pipeline **không đọc** bảng này (đúng ghi chú plan).

---

## Chạy trên Databricks

1. Sync repo lên Workspace.
2. Job/notebook gắn **cluster Spark**.
3. `python recommendation_job.py` hoặc từng file riêng.

---

## Unity Catalog — foreign catalog

- **Đọc:** `ecommerce_analyst_agent_catalog.gold.*`
- **Ghi:** `main.recommender.*` (mặc định) — **không** dùng foreign catalog làm `DATABRICKS_OUTPUT_CATALOG_NAME`

---

## Qdrant sync (tách pipeline + batch)

- `storage_books_qdrant.py` / `storage_users_qdrant.py` — không dùng `.collect()`
- Upsert theo batch (`QDRANT_BATCH_SIZE=1000`, `toLocalIterator()`)
- Payload sách có thêm `book_id` để debug

---

## Lưu ý Qdrant

Point ID = `book_id` / `user_id` (integer). Re-run `storage_books_qdrant` / `storage_users_qdrant` sau khi đổi embedding hoặc ID scheme.
