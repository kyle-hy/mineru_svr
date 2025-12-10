# 使用轻量级 Python 镜像（推荐 slim-bullseye 或 alpine，此处用 slim）
FROM python:3.11-alpine

# 设置工作目录
WORKDIR /app

# 安装依赖（先复制 requirements 提升缓存利用率）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install python-multipart

# 复制应用代码
COPY ./app ./app

# 创建非 root 用户（安全加固）
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

# 暴露端口（Uvicorn 默认 8000）
EXPOSE 8000

# 启动命令（生产环境：关闭 reload，workers 建议为 $(nproc)+1 或固定值）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]