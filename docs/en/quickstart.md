# Quick Start

> Get KoalaqVision running in 5 minutes

## Prerequisites

- Docker and Docker Compose installed
- Minimum 2GB RAM (8GB recommended)
- 6GB disk space for Docker extraction

## Installation Steps

### Method 1: Docker (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/KoalaqVision.git
cd KoalaqVision

# 2. Start services
docker compose -f deploy/docker-compose.yml up -d

# 3. Check status
docker compose -f deploy/docker-compose.yml ps
```

### Method 2: Local Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download models (see models.md)

# 3. Start service
./start.sh
```

## First Test

Open your browser and visit:

- **Gradio UI**: http://localhost:10770/ui
- **API Documentation**: http://localhost:10770/docs

Try uploading an image in the Gradio interface!