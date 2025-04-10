FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案文件
COPY . .

# 確保資料庫目錄存在
RUN mkdir -p database

# 初始化資料庫
RUN python init_db.py

# 創建supervisord配置文件
RUN echo "[supervisord]\nnodaemon=true\n\n\
[program:webapp]\ncommand=gunicorn --bind 0.0.0.0:8080 --workers 2 --threads 4 --timeout 60 webhook:app\ndirectory=/app\nautostart=true\nautorestart=true\n\n\
[program:scheduler]\ncommand=python -m scheduler.reminder_scheduler\ndirectory=/app\nautostart=true\nautorestart=true" > /etc/supervisor/conf.d/supervisord.conf

# 暴露端口
EXPOSE 8080

# 使用 supervisor 啟動多個進程
CMD ["/usr/bin/supervisord"] 