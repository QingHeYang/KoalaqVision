# 快速开始

> 5分钟快速运行 KoalaqVision

## 前置要求

- 已安装 Docker 和 Docker Compose
- 最少 2GB 内存（推荐 8GB）
- 6GB 磁盘空间用于docker解压

## 安装步骤

### 方式一：Docker（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/KoalaqVision.git
cd KoalaqVision

# 2. 启动服务
docker compose -f deploy/docker-compose.yml up -d

# 3. 检查状态
docker compose -f deploy/docker-compose.yml ps
```

### 方式二：本地安装

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 下载模型（见 models.md）

# 3. 启动服务
./start.sh
```

## 第一次测试

打开浏览器访问：

- **Gradio UI**: http://localhost:10770/ui
- **API 文档**: http://localhost:10770/docs

在 Gradio 界面中尝试上传图片！

