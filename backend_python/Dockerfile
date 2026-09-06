FROM python:3.10-slim
WORKDIR /app

# 系统依赖（pdfplumber / RapidOCR(opencv) / sentence-transformers 等需要：
# gcc libc-dev 编译、libgl1/libglib2.0-0/libgomp1/libsm6/libxext6/libxrender1 供 OCR 渲染链路）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc-dev libgl1 libglib2.0-0 libgomp1 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# 知识库数据卷
VOLUME ["/app/data"]

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
