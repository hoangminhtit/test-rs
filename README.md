# Book Recommendation System

Hệ thống khuyến nghị sách **Content-Based Filtering** với Databricks, Sentence Transformer, Qdrant và FastAPI.

## Kiến trúc

- **Databricks**: xử lý dữ liệu, tạo embedding sách/người dùng, đồng bộ lên Qdrant
- **FastAPI**: chỉ đọc vector từ Qdrant và trả về Top-K sách tương tự

## Cấu trúc thư mục

```
recommender-service/
├── databricks/          # Pipeline xử lý & đồng bộ Qdrant
├── fastapi/             # API khuyến nghị
├── .env.example
└── README.md
```

## Cài đặt

### Databricks

```bash
cd databricks
pip install -r requirements.txt
cp ../.env.example ../.env   # điền biến môi trường
```

Chạy toàn bộ pipeline:

```bash
python recommendation_job.py
```

Hoặc từng bước:

```bash
python create_book_embeddings.py
python create_user_weight_matrix.py
python create_user_embeddings.py
python storage_qdrant.py
```

**Lịch Job trên Databricks:** tạo Workflow với 4 task theo thứ tự trên, schedule mỗi 1 giờ.

### FastAPI

```bash
cd fastapi
pip install -r requirements.txt
export QDRANT_URL=...
export QDRANT_API_KEY=...
uvicorn main:app --reload
```

## API

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| GET | `/health` | Health check |
| GET | `/recommend/{user_id}` | Top-K sách gợi ý (mặc định K=20) |
| GET | `/recommend/{user_id}?top_k=10` | Tùy chỉnh số lượng |

Ví dụ:

```http
GET http://localhost:8000/recommend/U001
```

## Delta Tables (Databricks)

| Bảng | Cột chính |
|------|-----------|
| `books` | book_id, title, author, category, description |
| `user_behaviors` | user_id, book_id, action, timestamp |
| `book_embeddings` | book_id, embedding |
| `user_book_weights` | user_id, book_id, weight |
| `user_embeddings` | user_id, embedding |

## Qdrant Collections

- `book_embeddings` — vector sách + payload (title, author, category)
- `user_embeddings` — vector người dùng + payload (user_id)
