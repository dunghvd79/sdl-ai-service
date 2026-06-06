# 🤖 Smart Digital Library (SDL) — AI Service Context

> **Dự án:** Smart Digital Library (SDL) - Phân hệ AI & RAG Service  
> **Cập nhật lần cuối:** 06/2026  
> **AI Service Production URL:** [https://sdl-ai-service.onrender.com](https://sdl-ai-service.onrender.com)  
> **Backend API URL:** [https://sdl-backend.onrender.com](https://sdl-backend.onrender.com)  
> **Frontend URL:** [https://pigeon-bookstore.netlify.app](https://pigeon-bookstore.netlify.app)

---

## 🎯 Tổng quan repo AI Service
Thư mục này chứa mã nguồn của **AI Service** được thiết kế dưới dạng một microservice độc lập. Service này phụ trách việc tiếp nhận sách kỹ thuật số (tệp tin PDF), trích xuất và băm nhỏ văn bản (Chunking), lưu trữ các vector biểu diễn vào Vector Database, và cung cấp giải pháp hỏi đáp thông minh theo tài liệu (RAG - Retrieval-Augmented Generation) thông qua việc kết hợp cơ sở dữ liệu tri thức local với sức mạnh của mô hình ngôn ngữ lớn Google Gemini.

---

## 🏗️ Kiến trúc & Công nghệ (Tech Stack)

*   **FastAPI v0.136**: Python Web Framework hiệu năng cực cao phục vụ việc xây dựng các API bất đồng bộ (Async API), tự động sinh tài liệu Swagger UI.
*   **Uvicorn v0.47**: Trình chạy server ASGI tốc độ cao cho ứng dụng FastAPI.
*   **Google Generative AI SDK (google-generativeai v0.8)**: Bộ SDK chính thức từ Google dùng để tạo các bản nhúng (Embeddings) và giao tiếp sinh câu trả lời với các model Gemini thế hệ mới.
*   **ChromaDB v1.5**: Vector Database mã nguồn mở dung lượng nhẹ hoạt động ở chế độ lưu trữ file cục bộ (Persistent Storage), tối ưu việc tìm kiếm độ tương đồng cosine giữa các vector.
*   **PyPDF2 v3.0**: Thư viện xử lý và giải nén văn bản trực tiếp từ tệp tin PDF dạng byte trong bộ nhớ.
*   **python-dotenv**: Trình quản lý các biến môi trường cấu hình thông qua file `.env`.

---

## 📁 Cấu trúc mã nguồn

```
sdl-ai-service/
├── chroma_data/         # Thư mục lưu trữ database vector ChromaDB vật lý
├── main.py              # Entry Point: Định nghĩa FastAPI app, xử lý CORS, và các API endpoints
├── rag.py               # Chứa các hàm nghiệp vụ RAG: Đọc PDF, băm văn bản (Chunking) và truy vấn ChromaDB
├── requirements.txt     # Danh sách các thư viện Python cần thiết cho dự án
└── railway.json         # File cấu hình triển khai nhanh trên hạ tầng đám mây Railway
```

---

## 🛠️ Luồng xử lý nghiệp vụ RAG (Retrieval-Augmented Generation)

### 1. Luồng Upload & Indexing (Đọc và ghi nhớ sách)
Khi Curator upload tài liệu PDF của một cuốn sách lên hệ thống:
1.  **FastAPI** nhận tệp tin PDF dưới dạng bytes cùng tham số `book_id`.
2.  `rag.py` dùng **PyPDF2** để trích xuất toàn bộ văn bản chữ trong các trang.
3.  Văn bản được cắt thành các đoạn nhỏ (**Chunk size = 1000 ký tự**).
4.  Mỗi đoạn văn bản sẽ được gán một ID duy nhất dưới dạng `book_<book_id>_chunk_<index>` cùng metadata lưu `book_id`.
5.  Các đoạn văn bản này được đẩy vào ChromaDB Collection `library_books`. ChromaDB sẽ tự động chuyển hóa văn bản thành Vector nhúng (Embeddings) và lưu xuống đĩa.

### 2. Luồng Search & Chat (Hỏi đáp thông tin sách)
Khi Customer gửi câu hỏi trong màn hình đọc sách:
1.  **FastAPI** nhận payload chứa `book_id` và câu hỏi `question`.
2.  Hệ thống truy vấn ChromaDB bằng câu hỏi đó, lọc theo thuộc tính metadata `where={"book_id": book_id}` và lấy ra **3 đoạn văn bản liên quan nhất**.
3.  Gộp 3 đoạn văn bản này lại thành một Context tri thức.
4.  Xây dựng Prompt chi tiết yêu cầu mô hình AI chỉ trả lời dựa trên nội dung Context được trích xuất từ sách.
5.  Gọi **Google Gemini API** sinh câu trả lời và phản hồi lại cho người dùng kèm theo danh sách tham chiếu để đối chiếu.

---

## ⚡ Cơ chế tự động dò tìm Model của Google Gemini
Để tránh lỗi do model cũ bị Google khai tử hoặc thay đổi quyền truy cập, API của service này tích hợp đoạn code đột phá tự động truy vấn danh sách model khả dụng của API Key hiện tại:
*   Hệ thống gọi API `genai.list_models()` để quét tất cả model hỗ trợ phương thức tạo nội dung.
*   Tự động ưu tiên chọn các model tốt nhất theo thứ tự: `gemini-2.5-flash` ➔ `gemini-1.5-flash` ➔ `gemini-1.5-pro` ➔ `gemini-1.0-pro`.
*   Trường hợp có lỗi kết nối mạng, service sẽ tự động dùng model dự phòng mặc định là `gemini-1.5-flash`.

---

## 🔌 API Endpoints Danh sách

| Phương thức | Endpoint | Mô tả |
| :--- | :--- | :--- |
| **GET** | `/api/health` | Kiểm tra trạng thái hoạt động của Service. |
| **POST** | `/api/documents/upload` | Tiếp nhận file PDF sách và tiến hành băm văn bản để đưa vào ChromaDB. |
| **POST** | `/api/chat/search` | Nhận câu hỏi và `book_id`, tìm kiếm dữ liệu liên quan trong ChromaDB, gửi đến Gemini và trả về câu trả lời. |

---

## ⚙️ Cấu hình môi trường Local

Tạo file `.env` tại thư mục gốc của repo AI (`sdl-ai-service/`):

```ini
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 🚀 Hướng dẫn khởi chạy Local

1.  Di chuyển vào thư mục AI:
    ```bash
    cd sdl-ai-service
    ```
2.  Tạo và kích hoạt môi trường ảo Python (Virtual Environment):
    *   **Windows:**
        ```powershell
        python -m venv venv
        .\venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
3.  Cài đặt các gói thư viện phụ thuộc:
    ```bash
    pip install -r requirements.txt
    ```
4.  Chạy ứng dụng bằng Uvicorn với chế độ tự động tải lại (Auto-reload):
    ```bash
    uvicorn main:app --reload
    ```
    *AI Service local sẽ hoạt động tại:* [http://localhost:8000](http://localhost:8000)  
    *Tài liệu hướng dẫn trực quan Swagger UI:* [http://localhost:8000/docs](http://localhost:8000/docs)
