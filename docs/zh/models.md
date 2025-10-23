# 模型下载指南

## Docker 部署

Docker 镜像已内置所有模型，**无需下载**。

```bash
docker pull 775495797/koalaqvision:latest
docker compose -f deploy/docker-compose.yml up -d
```

### Docker 内置模型列表（总大小: 955MB）

> **注意**: Docker 镜像同时包含了 Object 和 Face 两种模式的模型，因为...我懒。如果想精简镜像只包含特定模式的模型，请查看 `deploy/Dockerfile` 自行构建。

#### Face Mode 模型
| 模型名称 | 大小 | 文件 | 用途 |
|---------|------|------|------|
| **antelopev2** | 381MB | glintr100.onnx (249MB)<br>scrfd_10g_bnkps.onnx (17MB)<br>其他辅助文件 | 人脸识别（最新） |
| **buffalo_s** | 132MB | w600k_mbf.onnx (13MB)<br>det_500m.onnx (2.5MB)<br>其他辅助文件 | 人脸识别（轻量） |
| **minifasnet** | 3.4MB | 2.7_80x80_MiniFASNetV2.onnx (1.7MB)<br>4_0_0_80x80_MiniFASNetV1SE.onnx (1.7MB) | 活体检测 |

#### Object Mode 模型
| 模型名称 | 大小 | 文件 | 用途 |
|---------|------|------|------|
| **dinov3-vits16** | 83MB | model.onnx + model.onnx_data | 特征提取（快速，384维） |
| **dinov3-vitl16** | 185MB | model_q4.onnx + model_q4.onnx_data<br>（INT4量化版） | 特征提取（推荐，1024维） |
| **U2Net** | 173MB | u2net.onnx (168MB)<br>u2netp.onnx (4.4MB) | 背景去除 |

---

## 本地部署

### 下载地址

待补充  

### 目录结构

解压后放置到 `data/models/` 目录：

```
data/models/
├── dinov3-vits16/      # Object: 特征提取（快速）
├── dinov3-vitl16/      # Object: 特征提取（推荐）
├── U2Net/              # Object: 背景去除
├── buffalo_s/          # Face: 人脸识别（轻量）
├── antelopev2/         # Face: 人脸识别（推荐）
└── minifasnet/         # Face: 活体检测
```

### 启动

```bash
pip install -r requirements.txt
./start.sh
```

---

## 模型选择

编辑 `.env` 配置使用的模型：

```bash
# Object Mode
DINOV3_MODEL=vitl16        # vits16 (快) | vitl16 (推荐)
BG_REMOVAL_MODEL=u2net     # u2netp (快) | u2net (推荐)

# Face Mode
FACE_MODEL_NAME=antelopev2  # buffalo_s (轻量) | antelopev2 (推荐)
ENABLE_LIVENESS=true        # 活体检测
```

---  


## 许可说明

- **DINOv3**: DINOv3 自有许可
- **InsightFace**: 仅供学术研究使用
- **MiniFASNet**: MIT
