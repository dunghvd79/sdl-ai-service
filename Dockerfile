# Sử dụng base image Python chính thức bản Slim để tối ưu dung lượng
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết (như build-essential nếu cần biên dịch thư viện C/C++)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Sao chép file requirements.txt trước để tận dụng cache của Docker layer
COPY requirements.txt .

# Cài đặt các thư viện python
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn ứng dụng
COPY . .

# Expose cổng chạy mặc định của uvicorn FastAPI
EXPOSE 8000

# Khởi chạy FastAPI sử dụng Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
