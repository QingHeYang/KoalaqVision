#!/bin/bash
set -e

echo "================================================"
echo "  KoalaqVision Docker Entrypoint"
echo "================================================"
echo ""

# 读取 APP_MODE（从环境变量或 .env 文件）
APP_MODE=${APP_MODE:-object}
echo "→ App Mode: $APP_MODE"
echo ""

# 配置 Weaviate 地址
# 如果外部没传入 WEAVIATE_URL，使用 Docker 网络中的 weaviate 服务
if [ -z "$WEAVIATE_URL" ]; then
    export WEAVIATE_URL="http://weaviate:8080"
    echo "→ Weaviate URL: $WEAVIATE_URL (auto-configured)"
else
    echo "→ Weaviate URL: $WEAVIATE_URL (from environment)"
fi
echo ""

# 检查模型文件
echo "→ Checking model files..."
MODELS_OK=true

if [ "$APP_MODE" = "object" ]; then
    echo "  Checking Object Recognition models..."

    # 检查 DINOv3 模型目录（支持任意版本：vits16/vitb16/vitl16/vith16plus）
    DINOV3_COUNT=$(find data/models/dinov3-* -name "*.onnx" 2>/dev/null | wc -l)
    if [ "$DINOV3_COUNT" -gt 0 ]; then
        DINOV3_FOUND_FILE=$(find data/models/dinov3-* -name "*.onnx" 2>/dev/null | head -1)
        DINOV3_DIR=$(basename $(dirname "$DINOV3_FOUND_FILE"))
        echo "  ✓ DINOv3 model found ($DINOV3_DIR)"
    else
        echo "  ✗ DINOv3 model NOT FOUND (need dinov3-vits16/vitb16/vitl16/vith16plus)"
        MODELS_OK=false
    fi

    # 检查背景去除模型（支持 U2Net 或 BiRefNet）
    BG_COUNT=$(find data/models/U2Net data/models/birefnet -name "*.onnx" 2>/dev/null | wc -l)
    if [ "$BG_COUNT" -gt 0 ]; then
        BG_FOUND_FILE=$(find data/models/U2Net data/models/birefnet -name "*.onnx" 2>/dev/null | head -1)
        BG_DIR=$(basename $(dirname "$BG_FOUND_FILE"))
        echo "  ✓ Background removal model found ($BG_DIR)"
    else
        echo "  ✗ Background removal model NOT FOUND (need U2Net or birefnet)"
        MODELS_OK=false
    fi

elif [ "$APP_MODE" = "face" ]; then
    echo "  Checking Face Recognition models..."

    # 检查 InsightFace 模型目录（支持任意版本）
    FACE_COUNT=$(find data/models/buffalo_* -name "*.onnx" 2>/dev/null | wc -l)
    if [ "$FACE_COUNT" -ge 2 ]; then
        FACE_DIR=$(basename $(dirname $(find data/models/buffalo_* -name "*.onnx" 2>/dev/null | head -1)))
        echo "  ✓ InsightFace model found ($FACE_DIR)"
    else
        echo "  ✗ InsightFace model NOT FOUND (need buffalo_s/buffalo_l)"
        MODELS_OK=false
    fi

    # 检查活体检测模型
    LIVENESS_COUNT=$(find data/models/minifasnet -name "*.onnx" 2>/dev/null | wc -l)
    if [ "$LIVENESS_COUNT" -gt 0 ]; then
        echo "  ✓ Liveness detection model found (minifasnet)"
    else
        echo "  ✗ Liveness detection model NOT FOUND (need minifasnet)"
        MODELS_OK=false
    fi
else
    echo "  ⚠️  Unknown APP_MODE: $APP_MODE"
fi

echo ""

# 如果模型缺失，显示警告
if [ "$MODELS_OK" = false ]; then
    echo "⚠️  MODELS MISSING!"
    echo ""
    echo "Solutions:"
    echo "  1. Mount models volume: -v ./data/models:/app/data/models"
    echo "  2. Copy models to data/models/ directory"
    echo "  3. Download from: https://github.com/YourRepo/models"
    echo ""
    echo "⚠️  Service will start but may fail on first request..."
    echo ""
fi

# 等待 Weaviate 服务就绪（最多等待 30 秒）
echo "→ Waiting for Weaviate to be ready..."
MAX_WAIT=30
WAIT_COUNT=0

while ! curl -sf "$WEAVIATE_URL/v1/.well-known/ready" > /dev/null 2>&1; do
    if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
        echo "  ⚠️  Weaviate not ready after ${MAX_WAIT}s, continuing anyway..."
        break
    fi
    echo "  Waiting for Weaviate... (${WAIT_COUNT}/${MAX_WAIT}s)"
    sleep 2
    WAIT_COUNT=$((WAIT_COUNT + 2))
done

if [ $WAIT_COUNT -lt $MAX_WAIT ]; then
    echo "  ✓ Weaviate is ready"
fi
echo ""

echo "================================================"
echo "  Starting KoalaqVision..."
echo "================================================"
echo ""

# 执行传入的命令
exec "$@"
