import chromadb
from PyPDF2 import PdfReader
import io

import os

# Khởi tạo Database Vector (ChromaDB)
chroma_data_path = os.getenv("CHROMA_DATA_PATH", "./chroma_data")
chroma_client = chromadb.PersistentClient(path=chroma_data_path)

# Tạo một Collection (Giống như tạo Bảng trong SQL)
collection = chroma_client.get_or_create_collection(name="library_books")

def process_and_index_pdf(file_bytes: bytes, book_id: str):
    """Hàm này đọc PDF, băm nhỏ từng trang và lưu vào Database Vector kèm số trang"""
    
    # Bước 1: Đọc file PDF
    reader = PdfReader(io.BytesIO(file_bytes))
    
    all_chunks = []
    all_ids = []
    all_metadatas = []
    
    chunk_size = 1000
    chunk_idx = 0
    
    for page_idx, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if not page_text or not page_text.strip():
            continue
            
        # Băm nhỏ văn bản của trang này (tránh cắt nửa chừng của trang tiếp theo)
        page_text = page_text.strip()
        page_chunks = [page_text[i:i+chunk_size] for i in range(0, len(page_text), chunk_size)]
        
        for sub_idx, chunk in enumerate(page_chunks):
            all_chunks.append(chunk)
            all_ids.append(f"book_{book_id}_chunk_{chunk_idx}")
            all_metadatas.append({
                "book_id": book_id,
                "page_number": page_idx + 1
            })
            chunk_idx += 1

    if not all_chunks:
        raise ValueError("Không tìm thấy chữ trong file PDF này!")

    # Bước 4: Lưu vào ChromaDB
    collection.add(
        documents=all_chunks,
        metadatas=all_metadatas,
        ids=all_ids
    )

    return len(all_chunks)

def search_relevant_chunks(question: str, book_id: str, n_results: int = 3):
    """
    Hàm này nhận câu hỏi, đi tìm những đoạn văn giống nhất trong ChromaDB
    và trả về thông tin văn bản kèm số trang thực tế.
    """
    # Dùng hàm query của ChromaDB để tìm kiếm
    results = collection.query(
        query_texts=[question],
        n_results=n_results, # Lấy ra 3 đoạn văn sát nghĩa nhất
        where={"book_id": book_id} # Chỉ tìm trong cuốn sách mà user đang hỏi
    )

    # Trích xuất text và metadata từ kết quả trả về
    if not results['documents'] or not results['documents'][0]:
        return []

    formatted_results = []
    for i in range(len(results['documents'][0])):
        snippet = results['documents'][0][i]
        meta = results['metadatas'][0][i] if (results['metadatas'] and len(results['metadatas'][0]) > i) else {}
        page_num = meta.get("page_number", i + 1)
        
        formatted_results.append({
            "page_number": page_num,
            "snippet": snippet
        })

    return formatted_results