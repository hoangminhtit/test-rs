# Book Recommendation System
## Databricks + Qdrant + FastAPI

---

## 1. Project Goal

Xây dựng hệ thống khuyến nghị sách theo phương pháp **Content-Based Filtering**.

**Tech Stack:**
- **Databricks** — Data Processing
- **Sentence Transformer** — Embedding
- **Qdrant** — Vector Database
- **FastAPI** — Recommendation Service

**Nguyên tắc hoạt động:**
- Databricks xử lý dữ liệu
- Databricks tạo Book Embeddings
- Databricks tạo User Embeddings
- Databricks cập nhật dữ liệu vào Qdrant
- FastAPI chỉ đọc dữ liệu từ Qdrant để khuyến nghị

---

## 2. Project Architecture

```
Databricks

Books Data
    ↓
create_book_embeddings.py
    ↓
Qdrant (book_embeddings)


User Behaviors
    ↓
create_user_weight_matrix.py
    ↓
create_user_embeddings.py
    ↓
Qdrant (user_embeddings)


FastAPI (Local)

connect_qdrant.py
    ↓
recommend_service.py
    ↓
Top-K Book Recommendations
```

---

## 3. Folder Structure

```
project/
├── databricks/
│   ├── config/
│   │   ├── databricks_config.py 
│   │   └── qdrant_config.py
│   ├── create_book_embeddings.py
│   ├── create_user_weight_matrix.py
│   ├── create_user_embeddings.py
│   ├── storage_qdrant.py
│   └── recommendation_job.py
|   └── requirements.txt
│
├── fastapi/
│   ├── config/
│   │   └── qdrant_config.py
│   ├── connect_qdrant.py
│   ├── recommend_service.py
│   ├── routes.py
│   └── main.py
│
└── README.md
```

---

## 4. Databricks Layer

### `databricks_config.py`

Kết nối Databricks Workspace.

```python
DATABRICKS_URL
DATABRICKS_HTTP_PATH
DATABRICKS_TOKEN
DATABRICKS_HOST
DATABRICKS_CATALOG_NAME
DATABRICKS_SCHEMA_NAME
```

Dùng cho: SQL Warehouse, Delta Tables, Databricks Jobs.

---

### `qdrant_config.py`

Kết nối Qdrant Cloud.

```python
QDRANT_URL
QDRANT_API_KEY
BOOK_COLLECTION  = "book_embeddings"
USER_COLLECTION  = "user_embeddings"
```

---

## 5. `create_book_embeddings.py`

Tạo embedding cho sách.

**Input — Books Table:**
```
book_id | title | author | category | description
```

**Text Construction:**
```python
text = f"""
Title: {title}
Author: {author}
Category: {category}
Description: {description}
"""
```

**Embedding Model:**
```python
SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
```

**Output → Delta Table `book_embeddings`:**
```
book_id | embedding
```

---

## 6. `create_user_weight_matrix.py`

Tính trọng số tương tác người dùng - sách.

**Input — User Behaviors:**
```
user_id | book_id | action | timestamp
```

**Weight Mapping:**
```python
{
    "view":      1,
    "click":     2,
    "wishlist":  3,
    "cart":      5,
    "purchase": 10
}
```

**Aggregation:** Group by `(user_id, book_id)` → `sum(weight)`

**Output → Delta Table `user_book_weights`:**
```
user_id | book_id | weight
```

---

## 7. `create_user_embeddings.py`

Tạo embedding profile cho người dùng.

**Input:** `user_book_weights` JOIN `book_embeddings`

**Formula — Weighted Average:**
```
UserEmbedding = Σ(weight × embedding) / Σ(weight)
```

**Output → Delta Table `user_embeddings`:**
```
user_id | embedding
```

---

## 8. `storage_qdrant.py`

Đẩy vectors vào Qdrant.

**Collection `book_embeddings`:**
```python
id      = book_id
vector  = embedding
payload = { title, category, author }
```

**Collection `user_embeddings`:**
```python
id      = user_id
vector  = embedding
payload = { user_id }
```

**Method:** `client.upsert(...)` — tự động Insert hoặc Update.

---

## 9. `recommendation_job.py`

Master Databricks Workflow — điều phối toàn bộ pipeline.

**Execution Order:**
```
Step 1: create_book_embeddings
    ↓
Step 2: create_user_weight_matrix
    ↓
Step 3: create_user_embeddings
    ↓
Step 4: storage_qdrant
```

**Schedule:** Mỗi 1 giờ → Qdrant luôn được cập nhật.

---

## 10. FastAPI Layer

### `connect_qdrant.py`

Tạo Qdrant connection.

```python
QDRANT_URL
QDRANT_API_KEY
# → trả về QdrantClient
```

---

## 11. `recommend_service.py`

Sinh danh sách khuyến nghị.

**Input:** `user_id`

**Step 1 — Load User Vector:**
```python
retrieve(
    collection_name="user_embeddings",
    ids=[user_id]
)
```

**Step 2 — Search Books:**
```python
search(
    collection_name="book_embeddings",
    query_vector=user_vector
)
```

**Step 3:** Sort by Cosine Similarity Score

**Step 4:** Return Top-K (`TOP_K = 20`)

**Output:**
```json
{
  "user_id": "U001",
  "recommendations": [
    { "book_id": 101, "score": 0.96 },
    { "book_id": 205, "score": 0.93 }
  ]
}
```

---

## 12. `routes.py`

```http
GET /recommend/{user_id}
```

**Example:**
```http
GET /recommend/U001
```

---

## 13. `main.py`

```bash
uvicorn main:app --reload
```

---

## 14. Recommendation Flow

```
User Opens Website
    ↓
Frontend
    ↓
GET /recommend/{user_id}
    ↓
FastAPI
    ↓
Qdrant — Load User Embedding
    ↓
Search Book Embeddings
    ↓
Top-K Similar Books
    ↓
Response → Frontend
```

---

## 15. Final Workflow Summary

```
Databricks                          FastAPI
──────────────────────────          ──────────────────────
Books → Book Embedding → Qdrant     Load User Embedding
                                        ↓
Behaviors                           Search Book Embedding
  → User Weight Matrix                  ↓
  → User Embedding    → Qdrant      Top-K Recommendations
```
