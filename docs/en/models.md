# Model Download Guide

## Docker Deployment

Docker images have all models built-in, **no download required**.

```bash
docker pull 775495797/koalaqvision:latest
docker compose -f deploy/docker-compose.yml up -d
```

### Docker Built-in Model List (Total Size: 955MB)

> **Note**: Docker images include models for both Object and Face modes, because...I'm lazy. If you want to slim down the image to only include models for a specific mode, please check `deploy/Dockerfile` to build your own.

#### Face Mode Models
| Model Name | Size | Files | Purpose |
|------------|------|-------|---------|
| **antelopev2** | 381MB | glintr100.onnx (249MB)<br>scrfd_10g_bnkps.onnx (17MB)<br>Other auxiliary files | Face recognition (latest) |
| **buffalo_s** | 132MB | w600k_mbf.onnx (13MB)<br>det_500m.onnx (2.5MB)<br>Other auxiliary files | Face recognition (lightweight) |
| **minifasnet** | 3.4MB | 2.7_80x80_MiniFASNetV2.onnx (1.7MB)<br>4_0_0_80x80_MiniFASNetV1SE.onnx (1.7MB) | Liveness detection |

#### Object Mode Models
| Model Name | Size | Files | Purpose |
|------------|------|-------|---------|
| **dinov3-vits16** | 83MB | model.onnx + model.onnx_data | Feature extraction (fast, 384D) |
| **dinov3-vitl16** | 185MB | model_q4.onnx + model_q4.onnx_data<br>(INT4 quantized) | Feature extraction (recommended, 1024D) |
| **U2Net** | 173MB | u2net.onnx (168MB)<br>u2netp.onnx (4.4MB) | Background removal |

---

## Local Deployment

### Download Links

To be added

### Directory Structure

After extraction, place in `data/models/` directory:

```
data/models/
├── dinov3-vits16/      # Object: Feature extraction (fast)
├── dinov3-vitl16/      # Object: Feature extraction (recommended)
├── U2Net/              # Object: Background removal
├── buffalo_s/          # Face: Face recognition (lightweight)
├── antelopev2/         # Face: Face recognition (recommended)
└── minifasnet/         # Face: Liveness detection
```

### Start

```bash
pip install -r requirements.txt
./start.sh
```

---

## Model Selection

Edit `.env` to configure models:

```bash
# Object Mode
DINOV3_MODEL=vitl16        # vits16 (fast) | vitl16 (recommended)
BG_REMOVAL_MODEL=u2net     # u2netp (fast) | u2net (recommended)

# Face Mode
FACE_MODEL_NAME=antelopev2  # buffalo_s (lightweight) | antelopev2 (recommended)
ENABLE_LIVENESS=true        # Liveness detection
```

---

## License Information

- **DINOv3**: DINOv3's own license
- **InsightFace**: For academic research only
- **MiniFASNet**: MIT