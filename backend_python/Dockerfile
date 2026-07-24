FROM python:3.10-slim
WORKDIR /app

# 系统依赖（pdfplumber / sentence-transformers 等需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 知识库数据卷
VOLUME ["/app/data"]

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
