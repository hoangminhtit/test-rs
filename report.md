# Báo cáo triển khai — Book Recommendation System

**Ngày:** 31/05/2026  
**Tham chiếu:** `plan (1).md`

---

## 1. Review plan

Plan mô tả rõ kiến trúc **Content-Based Filtering**: Databricks xử lý và ghi vector lên Qdrant; FastAPI chỉ đọc Qdrant để khuyến nghị. Luồng 4 bước (book embedding → user weight → user embedding → sync Qdrant) và API `GET /recommend/{user_id}` phù hợp để triển khai theo module.

---

## 2. Đã hoàn thành

### Databricks layer (`databricks/`)

| File | Nội dung |
|------|----------|
| `config/databricks_config.py` | Biến môi trường Databricks, Spark session, tên Delta tables |
| `config/qdrant_config.py` | URL/API key Qdrant, tên collection |
| `create_book_embeddings.py` | Ghép text sách → `SentenceTransformer(paraphrase-multilingual-MiniLM-L12-v2)` → Delta `book_embeddings` |
| `create_user_weight_matrix.py` | Map action (view/click/wishlist/cart/purchase) → weight, group by user/book → Delta `user_book_weights` |
| `create_user_embeddings.py` | Weighted average embedding sách theo công thức trong plan → Delta `user_embeddings` |
| `storage_qdrant.py` | `upsert` vào `book_embeddings` và `user_embeddings` trên Qdrant (payload đúng plan) |
| `recommendation_job.py` | Orchestrator chạy lần lượt 4 bước |
| `utils.py` | Chuyển `book_id` / `user_id` sang ID tương thích Qdrant |
| `requirements.txt` | pyspark, delta-spark, sentence-transformers, qdrant-client |

### FastAPI layer (`fastapi/`)

| File | Nội dung |
|------|----------|
| `config/qdrant_config.py` | Cấu hình Qdrant + `TOP_K=20` |
| `connect_qdrant.py` | Singleton `QdrantClient` |
| `recommend_service.py` | `retrieve` user vector → `search` book collection → Top-K |
| `routes.py` | `GET /recommend/{user_id}` (+ query `top_k`) |
| `main.py` | FastAPI app + `/health` |
| `requirements.txt` | fastapi, uvicorn, qdrant-client |

### Khác

- `README.md` — hướng dẫn cài đặt và chạy
- `.env.example` — mẫu biến môi trường

---

## 3. Cách chạy (tóm tắt)

1. Tạo Delta tables `books`, `user_behaviors` trên Databricks.
2. Cấu hình `.env` (Databricks + Qdrant).
3. `cd databricks && python recommendation_job.py`
4. `cd fastapi && uvicorn main:app --reload`
5. Gọi `GET /recommend/U001`

---

## 4. Lưu ý vận hành

- Pipeline cần **Spark + Delta** (Databricks hoặc local có delta-spark).
- Lần đầu chạy model Sentence Transformer sẽ tải weights (~400MB).
- Schedule 1 giờ: cấu hình trên **Databricks Jobs UI**, không hard-code trong repo.
- `user_id` dạng chuỗi (vd. `U001`) được map sang UUID ổn định để dùng làm point ID trên Qdrant (cùng logic ở Databricks sync và FastAPI retrieve).

---

## 5. Chưa làm trong phạm vi code

- Dữ liệu mẫu / notebook khởi tạo bảng Delta
- Unit test tự động
- Deploy production (Docker, CI/CD)

Các phần trên có thể bổ sung khi có cluster Databricks và Qdrant Cloud thực tế.
