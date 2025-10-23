# 配置指南

## 概述

KoalaqVision 使用环境变量进行配置。您可以通过两种方式配置系统：

**本地部署**：编辑项目根目录的 `.env` 文件
**Docker 部署**：在 `docker-compose.yml` 中添加环境变量

---

## 应用模式

### APP_MODE
在物品识别和人脸识别模式之间切换。

**选项**：
- `object` - 物品识别模式（DINOv3，1024维向量）
- `face` - 人脸识别模式（InsightFace，512维向量）

**默认值**：`object`

**Docker 示例**：
```yaml
environment:
  - APP_MODE=face
```

**注意**：切换模式需要不同的向量维度。切换时可能需要清空数据库。

---

## API 服务

### API_PORT
API 服务的端口号。

**默认值**：`10770`

**Docker 示例**：
```yaml
ports:
  - "8080:10770"  # 将主机端口 8080 映射到容器端口 10770
environment:
  - API_PORT=10770
```

### API_HOST
API 服务的监听地址。

**选项**：
- `0.0.0.0` - IPv4，所有网络接口可访问
- `:::` - IPv6（大多数系统也接受 IPv4）

**默认值**：`0.0.0.0`

---

## 向量数据库

### WEAVIATE_URL
Weaviate 向量数据库的 URL。

**默认值**：`http://localhost:10769`

**Docker 示例**：
```yaml
environment:
  - WEAVIATE_URL=http://weaviate:8080  # Docker 网络中使用服务名
```

### WEAVIATE_API_KEY
Weaviate 的 API 密钥（可选）。

**默认值**：未设置

**Docker 示例**：
```yaml
environment:
  - WEAVIATE_API_KEY=your_api_key_here
```

---

## 文件存储

### UPLOAD_PATH
上传图片的存储目录。

**默认值**：`data/upload`

### TEMP_PATH
临时文件的存储目录。

**默认值**：`data/temp`

---

## Object Mode 配置（物品模式）

### OBJECT_BACKEND
物品识别的后端引擎。
!!此选项需要如下条件开启：  
1. 具有cuda环境 && 并且使用本地部署，docker**无法使用**此字段
2. object模式  
3. 具有pytroch版本的Brefnet/Dinov3系列模型放置在`data/models`目录下放  

**选项**：
- `onnx` - CPU 优化，生产环境推荐
- `pytorch` - GPU 加速，需要 CUDA

**默认值**：`onnx`

### 背景去除模型

#### BG_REMOVAL_MODEL
选择背景去除模型。

**选项**：
- `u2netp` - 最快（4.7MB，~50ms）
- `u2net` - 平衡（168MB，~100ms）- 推荐
- `birefnet` - 最高质量 - 不推荐，速度过慢

**默认值**：`u2net`

**Docker 示例**：
```yaml
environment:
  - BG_REMOVAL_MODEL=u2net
```

#### 模型路径（高级）
- `BIREFNET_MODEL_PATH` - BiRefNet ONNX 模型路径
- `U2NET_MODEL_PATH` - U2Net ONNX 模型路径
- `U2NETP_MODEL_PATH` - U2Net-P ONNX 模型路径

### 特征提取模型

#### DINOV3_MODEL
选择 DINOv3 模型预设。

**选项**：
- `vits16` - 快速（83MB，~0.3秒，384维）
- `vitl16` - 最佳精度（185MB，~1秒，1024维）- 推荐

**默认值**：`vitl16`

**Docker 示例**：
```yaml
environment:
  - DINOV3_MODEL=vitl16
```

#### DINOV3_MODEL_PATH（高级）
自定义 DINOv3 ONNX 模型路径。留空 `DINOV3_MODEL` 以使用此选项。

**示例**：`data/models/dinov3-vitl16/model_q4.onnx`

### DINOv3 优化（仅 PyTorch 后端）

#### DINOV3_TEMPERATURE
特征区分度的温度缩放。

**范围**：`0.1 - 1.0`
**默认值**：`0.3`
**说明**：值越低，区分度越高

#### DINOV3_USE_MULTI_SCALE
启用多尺度特征融合（CLS + patch tokens）。

**默认值**：`true`

#### DINOV3_CLS_WEIGHT
全局特征（CLS token）的权重。

**范围**：`0.0 - 1.0`
**默认值**：`0.7`

#### DINOV3_PATCH_WEIGHT
局部特征（patch tokens）的权重。

**范围**：`0.0 - 1.0`
**默认值**：`0.3`

#### DINOV3_FEATURE_ENHANCEMENT
应用 L2 归一化进行特征增强。

**默认值**：`true`

### PyTorch 后端路径

#### PYTORCH_BIREFNET_PATH
PyTorch BiRefNet 模型目录路径。

**默认值**：`data/models/BiRefNet`

#### PYTORCH_DINOV3_PATH
PyTorch DINOv3 模型目录路径。

**默认值**：`data/models/dinov3-vith16plus-pretrain-lvd1689m`

---

## Face Mode 配置（人脸模式）

### FACE_MODEL_NAME
使用的 InsightFace 模型包。

**选项**：
- `buffalo_s` - 轻量级（159MB）
- `buffalo_l` - 标准（326MB）
- `antelopev2` - 最新（326MB）- 推荐

**默认值**：`antelopev2`

**Docker 示例**：
```yaml
environment:
  - FACE_MODEL_NAME=antelopev2
```

### FACE_MODEL_ROOT
人脸模型的根目录。

**默认值**：`data/models`

### FACE_DET_THRESH
人脸检测置信度阈值。

**范围**：`0.0 - 1.0`
**选项**：
- `0.3` - 宽松模式（检测更多人脸）- 推荐
- `0.5` - 默认模式（InsightFace 标准）
- `0.7` - 严格模式（仅高质量人脸）

**默认值**：`0.3`

**Docker 示例**：
```yaml
environment:
  - FACE_DET_THRESH=0.3
```

### FACE_ENABLE_MULTI_SCALE
启用多尺度检测，解决大脸/特写检测失败问题。

**默认值**：`true`

**说明**：SCRFD 对大脸（>40% 图像）表现不佳。多尺度检测使用 640x640 处理正常场景，256x256 处理大脸场景。

### 活体检测

#### ENABLE_LIVENESS
启用防翻拍活体检测。

**默认值**：`true`

**Docker 示例**：
```yaml
environment:
  - ENABLE_LIVENESS=true
```

#### LIVENESS_THRESHOLD
真人分数阈值。

**范围**：`0.0 - 1.0`
**默认值**：`0.4`
**说明**：阈值越低，越容易通过验证

#### LIVENESS_PAPER_REJECT_THRESHOLD
拒绝纸质照片的阈值。

**范围**：`0.0 - 1.0`
**默认值**：`0.7`
**说明**：阈值越高，只有明显的纸质照片才会被拒绝

#### LIVENESS_SCREEN_REJECT_THRESHOLD
拒绝电子屏幕的阈值。

**范围**：`0.0 - 1.0`
**默认值**：`0.7`
**说明**：阈值越高，只有明显的屏幕才会被拒绝

#### MINIFASNET_MODEL_DIR
MiniFASNet 活体检测模型目录。

**默认值**：`data/models/minifasnet`

---

## 运行时配置

### USE_GPU
启用 GPU 加速（需要 CUDA）&& docker 无法使用此字段。

**默认值**：`false`

### ONNX_THREAD_MODE
ONNX Runtime 的线程优化模式。

**选项**：
- `auto` - 平衡模式（大多数场景推荐）
- `performance` - 低延迟模式（单请求、低并发）
- `single` - 高并发模式（高流量 Web 服务器）

**默认值**：`auto`

**Docker 示例**：
```yaml
environment:
  - ONNX_THREAD_MODE=auto
```

---

## SSL/HTTPS

### ENABLE_SSL
启用 HTTPS 协议。

**默认值**：`false`

**Docker 示例**：
```yaml
environment:
  - ENABLE_SSL=true
volumes:
  - ./certs:/app/data/certs
```

### SSL_CERT_DIR
包含 SSL 证书的目录。

**默认值**：`./data/certs`

**支持的格式**：
- `fullchain.pem` / `privkey.pem`
- `cert.pem` / `key.pem`
- `*.crt` / `*.key`

---

## 调试和日志

### DEBUG
启用调试模式。

**默认值**：`false`

**Docker 示例**：
```yaml
environment:
  - DEBUG=true
```

### RELOAD
启用代码变更自动重载（仅开发环境）。

**默认值**：`false`

### LOG_STYLE
日志输出样式。

**选项**：
- `tree` - 树形输出
- `block` - 块状输出

**默认值**：`tree`

**Docker 示例**：
```yaml
environment:
  - LOG_STYLE=tree
```

---

## 完整 Docker 示例

以下是 `docker-compose.yml` 的完整示例：

```yaml
services:
  koalaqvision:
    image: 775495797/koalaqvision:latest
    container_name: koalaq-vision
    restart: unless-stopped
    ports:
      - "10770:10770"
    environment:
      # 应用模式
      - APP_MODE=face

      # Object Mode 配置
      - DINOV3_MODEL=vitl16
      - BG_REMOVAL_MODEL=u2net
      - ONNX_THREAD_MODE=auto

      # Face Mode 配置
      - FACE_MODEL_NAME=antelopev2
      - FACE_DET_THRESH=0.3
      - ENABLE_LIVENESS=true
      - LIVENESS_THRESHOLD=0.4

      # Weaviate 配置
      - WEAVIATE_URL=http://weaviate:8080

      # 调试
      - DEBUG=false
      - LOG_STYLE=tree
    volumes:
      - ./data/upload:/app/data/upload
      - ./data/temp:/app/data/temp
    networks:
      - koalaq-network
    depends_on:
      - weaviate

  weaviate:
    image: semitechnologies/weaviate:1.24.1
    container_name: koalaq-weaviate
    restart: unless-stopped
    ports:
      - "10769:8080"
    volumes:
      - ./weaviate:/var/lib/weaviate
    environment:
      - QUERY_DEFAULTS_LIMIT=25
      - AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true
      - PERSISTENCE_DATA_PATH=/var/lib/weaviate
      - DEFAULT_VECTORIZER_MODULE=none
      - ENABLE_MODULES=
    networks:
      - koalaq-network

networks:
  koalaq-network:
    driver: bridge
```

---

## 配置优先级

环境变量具有以下优先级（从高到低）：

1. Docker 环境变量（在 `docker-compose.yml` 中）
2. `.env` 文件（本地部署）
3. `app/config/settings.py` 中的默认值

---
