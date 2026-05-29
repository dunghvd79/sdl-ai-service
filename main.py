import os
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# Import các hàm từ file rag.py của bạn (vẫn giữ nguyên file rag.py nhé)
from rag import process_and_index_pdf, search_relevant_chunks

# 1. Tải biến môi trường từ file .env
load_dotenv()

# 2. Khởi tạo cấu hình cho Google Gemini AI
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# --- BƯỚC ĐỘT PHÁ: TỰ ĐỘNG DÒ TÌM MODEL ĐƯỢC HỖ TRỢ ---
print("[AI] Dang do tim cac model AI duoc ho tro cho API Key...")
try:
    # Lấy danh sách tất cả model có khả năng tạo text (generateContent)
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    print(f"[AI] Cac model kha dung: {available_models}")
    
    # Ưu tiên chọn model đời mới, nếu không có thì lấy đại cái đầu tiên
    selected_model = available_models[0] 
    for m in ['models/gemini-2.5-flash', 'models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-1.0-pro']:
        if m in available_models:
            selected_model = m
            break
            
    # Khởi tạo AI với model vừa tìm được (cắt bỏ chữ 'models/' ở đầu)
    model_name_clean = selected_model.replace('models/', '')
    print(f"[AI] Da tu dong chon model xuat sac nhat: {model_name_clean}")
    model = genai.GenerativeModel(model_name_clean)
    
except Exception as e:
    print("[AI] Loi khi do tim model:", e)
    # Fallback mặc định nếu có lỗi kết nối lúc khởi động
    model = genai.GenerativeModel('gemini-1.5-flash')
# --------------------------------------------------------

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SDL AI Service", version="1.0")

# Cấu hình CORS cho phép Backend Render kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    book_id: str
    question: str

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "AI Service đang chạy ngon lành!"}

@app.post("/api/documents/upload")
async def upload_document(book_id: str = Form(...), file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        num_chunks = process_and_index_pdf(file_bytes, book_id)
        return {
            "message": f"Thành công! AI đã đọc và ghi nhớ xong cuốn sách ID: {book_id}",
            "chunks_processed": num_chunks
        }
    except Exception as e:
        return {"error": str(e)}

# API: TÍCH HỢP GEMINI ĐỂ TRẢ LỜI CÂU HỎI
@app.post("/api/chat/search")
async def search_document(request: SearchRequest):
    try:
        # BƯỚC 1: TÌM KIẾM (Lật sách)
        contexts = search_relevant_chunks(request.question, request.book_id)
        
        if not contexts:
            return {"answer": "Xin lỗi, tôi không tìm thấy thông tin này trong sách."}

        # BƯỚC 2: TỔNG HỢP (Gom đoạn văn)
        context_text = "\n---\n".join(contexts)

        # BƯỚC 3: TẠO PROMPT (Ra lệnh cho Gemini)
        prompt = f"""
        Bạn là một trợ lý thư viện thông minh và thân thiện.
        Dựa vào Nội dung sách được trích xuất dưới đây, hãy trả lời câu hỏi của người dùng.
        Lưu ý: Chỉ trả lời dựa trên nội dung sách cung cấp. Nếu trong sách không có, hãy nói "Tôi không tìm thấy thông tin trong cuốn sách này".
        
        NỘI DUNG SÁCH:
        {context_text}
        
        CÂU HỎI CỦA NGƯỜI DÙNG: {request.question}
        """

        # BƯỚC 4: SINH CÂU TRẢ LỜI (Gemini xử lý)
        response = model.generate_content(prompt)
        
        return {
            "answer": response.text, # Câu trả lời mượt mà như con người
            "references": contexts   # Trả về luôn đoạn text gốc để user tin tưởng
        }
    except Exception as e:
        return {"error": str(e)}