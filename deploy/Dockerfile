# KoalaqVision Dockerfile - x86_64 only
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt（先复制依赖文件，利用 Docker 缓存）
COPY requirements.txt .

# 安装系统依赖和 Python 依赖（优化镜像大小）
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 编译 insightface 需要（仅构建时）
    g++ \
    # opencv-python-headless 运行时需要
    libgl1 \
    libglib2.0-0 \
    # 健康检查需要
    curl \
    && rm -rf /var/lib/apt/lists/* \
    # 安装 Python 依赖
    && pip install --no-cache-dir -i https://pypi.mirrors.ustc.edu.cn/simple -r requirements.txt \
    # 清理编译工具（节省空间）
    && apt-get purge -y --auto-remove g++ \
    && rm -rf /root/.cache

# 复制 AI 模型文件（~576MB，不常变动，优先缓存）
COPY data/models/ data/models/

# 创建数据目录
RUN mkdir -p data/upload data/temp data/certs

# 复制应用代码（经常变动，放在最后）
COPY app/ app/
COPY deploy/ deploy/
COPY .env .env

# 设置启动脚本权限
RUN chmod +x /app/deploy/docker-entrypoint.sh

# 暴露端口
EXPOSE 10770

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:10770/health || exit 1

# 启动命令
ENTRYPOINT ["/app/deploy/docker-entrypoint.sh"]
CMD ["python", "-m", "app.main"]
