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
    """Hàm này đọc PDF, băm nhỏ và lưu vào Database Vector"""
    
    # Bước 1: Đọc text từ file PDF
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"

    # Bước 2: Chunking (Băm nhỏ văn bản)
    chunk_size = 1000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    if not chunks:
        raise ValueError("Không tìm thấy chữ trong file PDF này!")

    # Bước 3: Đánh ID và Metadata cho từng đoạn văn
    ids = [f"book_{book_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"book_id": book_id} for _ in range(len(chunks))]

    # Bước 4: Lưu vào ChromaDB
    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )

    return len(chunks)

def search_relevant_chunks(question: str, book_id: str, n_results: int = 3):
    """
    Hàm này nhận câu hỏi, biến nó thành Vector và đi tìm 
    những đoạn văn có Vector giống nhất trong ChromaDB.
    """
    # Dùng hàm query của ChromaDB để tìm kiếm
    results = collection.query(
        query_texts=[question],
        n_results=n_results, # Lấy ra 3 đoạn văn sát nghĩa nhất
        where={"book_id": book_id} # Chỉ tìm trong cuốn sách mà user đang hỏi
    )

    # Trích xuất text từ kết quả trả về
    if not results['documents'] or not results['documents'][0]:
        return []

    return results['documents'][0]