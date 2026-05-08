# ================================
# Final image
# ================================
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

RUN pip install --no-cache-dir gunicorn uvicorn[standard] -i https://mirrors.aliyun.com/pypi/simple/

COPY backend/ ./backend/
COPY app/ ./app/

COPY start.sh ./start.sh
RUN chmod +x ./start.sh

EXPOSE 7860

CMD ["./start.sh"]
