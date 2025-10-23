# Configuration Guide

## Overview

KoalaqVision uses environment variables for configuration. You can configure the system in two ways:

**Local Deployment**: Edit the `.env` file in the project root directory
**Docker Deployment**: Add environment variables in `docker-compose.yml`

---

## Application Mode

### APP_MODE
Switch between object recognition and face recognition modes.

**Options**:
- `object` - Object recognition mode (DINOv3, 1024D vectors)
- `face` - Face recognition mode (InsightFace, 512D vectors)

**Default**: `object`

**Docker Example**:
```yaml
environment:
  - APP_MODE=face
```

**Note**: Switching modes requires different vector dimensions. You may need to clear the database when switching.

---

## API Service

### API_PORT
Port number for the API service.

**Default**: `10770`

**Docker Example**:
```yaml
ports:
  - "8080:10770"  # Map host port 8080 to container port 10770
environment:
  - API_PORT=10770
```

### API_HOST
Listening address for the API service.

**Options**:
- `0.0.0.0` - IPv4, accessible from all network interfaces
- `:::` - IPv6 (accepts IPv4 on most systems)

**Default**: `0.0.0.0`

---

## Vector Database

### WEAVIATE_URL
URL of the Weaviate vector database.

**Default**: `http://localhost:10769`

**Docker Example**:
```yaml
environment:
  - WEAVIATE_URL=http://weaviate:8080  # Use service name in Docker network
```

### WEAVIATE_API_KEY
Weaviate API key (optional).

**Default**: Not set

**Docker Example**:
```yaml
environment:
  - WEAVIATE_API_KEY=your_api_key_here
```

---

## File Storage

### UPLOAD_PATH
Directory for storing uploaded images.

**Default**: `data/upload`

### TEMP_PATH
Directory for temporary files.

**Default**: `data/temp`

---

## Object Mode Configuration

### OBJECT_BACKEND
Backend engine for object recognition.
!! This option requires the following conditions:
1. CUDA environment && local deployment only, **NOT** available in Docker
2. Object mode
3. PyTorch version of BiRefNet/DINOv3 models placed in `data/models` directory

**Options**:
- `onnx` - CPU optimized, recommended for production
- `pytorch` - GPU accelerated, requires CUDA

**Default**: `onnx`

### Background Removal Models

#### BG_REMOVAL_MODEL
Select background removal model.

**Options**:
- `u2netp` - Fastest (4.7MB, ~50ms)
- `u2net` - Balanced (168MB, ~100ms) - Recommended
- `birefnet` - Highest quality - Not recommended, too slow

**Default**: `u2net`

**Docker Example**:
```yaml
environment:
  - BG_REMOVAL_MODEL=u2net
```

#### Model Paths (Advanced)
- `BIREFNET_MODEL_PATH` - BiRefNet ONNX model path
- `U2NET_MODEL_PATH` - U2Net ONNX model path
- `U2NETP_MODEL_PATH` - U2Net-P ONNX model path

### Feature Extraction Models

#### DINOV3_MODEL
Select DINOv3 model preset.

**Options**:
- `vits16` - Fast (83MB, ~0.3s, 384D)
- `vitl16` - Best accuracy (185MB, ~1s, 1024D) - Recommended

**Default**: `vitl16`

**Docker Example**:
```yaml
environment:
  - DINOV3_MODEL=vitl16
```

#### DINOV3_MODEL_PATH (Advanced)
Custom DINOv3 ONNX model path. Leave `DINOV3_MODEL` empty to use this option.

**Example**: `data/models/dinov3-vitl16/model_q4.onnx`

### DINOv3 Optimization (PyTorch Backend Only)

#### DINOV3_TEMPERATURE
Temperature scaling for feature discrimination.

**Range**: `0.1 - 1.0`
**Default**: `0.3`
**Note**: Lower values increase discrimination

#### DINOV3_USE_MULTI_SCALE
Enable multi-scale feature fusion (CLS + patch tokens).

**Default**: `true`

#### DINOV3_CLS_WEIGHT
Weight for global features (CLS token).

**Range**: `0.0 - 1.0`
**Default**: `0.7`

#### DINOV3_PATCH_WEIGHT
Weight for local features (patch tokens).

**Range**: `0.0 - 1.0`
**Default**: `0.3`

#### DINOV3_FEATURE_ENHANCEMENT
Apply L2 normalization for feature enhancement.

**Default**: `true`

### PyTorch Backend Paths

#### PYTORCH_BIREFNET_PATH
PyTorch BiRefNet model directory path.

**Default**: `data/models/BiRefNet`

#### PYTORCH_DINOV3_PATH
PyTorch DINOv3 model directory path.

**Default**: `data/models/dinov3-vith16plus-pretrain-lvd1689m`

---

## Face Mode Configuration

### FACE_MODEL_NAME
InsightFace model pack to use.

**Options**:
- `buffalo_s` - Lightweight (159MB)
- `buffalo_l` - Standard (326MB)
- `antelopev2` - Latest (326MB) - Recommended

**Default**: `antelopev2`

**Docker Example**:
```yaml
environment:
  - FACE_MODEL_NAME=antelopev2
```

### FACE_MODEL_ROOT
Root directory for face models.

**Default**: `data/models`

### FACE_DET_THRESH
Face detection confidence threshold.

**Range**: `0.0 - 1.0`
**Options**:
- `0.3` - Permissive mode (detects more faces) - Recommended
- `0.5` - Default mode (InsightFace standard)
- `0.7` - Strict mode (only high-quality faces)

**Default**: `0.3`

**Docker Example**:
```yaml
environment:
  - FACE_DET_THRESH=0.3
```

### FACE_ENABLE_MULTI_SCALE
Enable multi-scale detection to solve large face/close-up detection failures.

**Default**: `true`

**Note**: SCRFD performs poorly with large faces (>40% of image). Multi-scale detection uses 640x640 for normal scenes and 256x256 for large face scenes.

### Liveness Detection

#### ENABLE_LIVENESS
Enable anti-spoofing liveness detection.

**Default**: `true`

**Docker Example**:
```yaml
environment:
  - ENABLE_LIVENESS=true
```

#### LIVENESS_THRESHOLD
Real person score threshold.

**Range**: `0.0 - 1.0`
**Default**: `0.4`
**Note**: Lower threshold makes it easier to pass validation

#### LIVENESS_PAPER_REJECT_THRESHOLD
Threshold for rejecting paper photos.

**Range**: `0.0 - 1.0`
**Default**: `0.7`
**Note**: Higher threshold means only obvious paper photos are rejected

#### LIVENESS_SCREEN_REJECT_THRESHOLD
Threshold for rejecting electronic screens.

**Range**: `0.0 - 1.0`
**Default**: `0.7`
**Note**: Higher threshold means only obvious screens are rejected

#### MINIFASNET_MODEL_DIR
MiniFASNet liveness detection model directory.

**Default**: `data/models/minifasnet`

---

## Runtime Configuration

### USE_GPU
Enable GPU acceleration (requires CUDA) && NOT available in Docker.

**Default**: `false`

### ONNX_THREAD_MODE
ONNX Runtime thread optimization mode.

**Options**:
- `auto` - Balanced mode (recommended for most scenarios)
- `performance` - Low latency mode (single request, low concurrency)
- `single` - High concurrency mode (high traffic web server)

**Default**: `auto`

**Docker Example**:
```yaml
environment:
  - ONNX_THREAD_MODE=auto
```

---

## SSL/HTTPS

### ENABLE_SSL
Enable HTTPS protocol.

**Default**: `false`

**Docker Example**:
```yaml
environment:
  - ENABLE_SSL=true
volumes:
  - ./certs:/app/data/certs
```

### SSL_CERT_DIR
Directory containing SSL certificates.

**Default**: `./data/certs`

**Supported Formats**:
- `fullchain.pem` / `privkey.pem`
- `cert.pem` / `key.pem`
- `*.crt` / `*.key`

---

## Debugging and Logging

### DEBUG
Enable debug mode.

**Default**: `false`

**Docker Example**:
```yaml
environment:
  - DEBUG=true
```

### RELOAD
Enable automatic code reload on changes (development only).

**Default**: `false`

### LOG_STYLE
Log output style.

**Options**:
- `tree` - Tree format output
- `block` - Block format output

**Default**: `tree`

**Docker Example**:
```yaml
environment:
  - LOG_STYLE=tree
```

---

## Complete Docker Example

Here's a complete `docker-compose.yml` example:

```yaml
services:
  koalaqvision:
    image: 775495797/koalaqvision:latest
    container_name: koalaq-vision
    restart: unless-stopped
    ports:
      - "10770:10770"
    environment:
      # Application mode
      - APP_MODE=face

      # Object Mode configuration
      - DINOV3_MODEL=vitl16
      - BG_REMOVAL_MODEL=u2net
      - ONNX_THREAD_MODE=auto

      # Face Mode configuration
      - FACE_MODEL_NAME=antelopev2
      - FACE_DET_THRESH=0.3
      - ENABLE_LIVENESS=true
      - LIVENESS_THRESHOLD=0.4

      # Weaviate configuration
      - WEAVIATE_URL=http://weaviate:8080

      # Debugging
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

## Configuration Priority

Environment variables have the following priority (highest to lowest):

1. Docker environment variables (in `docker-compose.yml`)
2. `.env` file (local deployment)
3. Default values in `app/config/settings.py`

---