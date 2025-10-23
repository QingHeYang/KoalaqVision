from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import gradio as gr

from app.config.settings import settings
from app.services.pipeline_factory import get_pipeline
from app.ui import demo, i18n
from app.utils.exceptions import APIException
from app.utils.response import error, ErrorCode
from app.utils.logger_utils import get_logger

logger = get_logger(__name__)

def log_configuration():
    """Display all loaded configuration in a formatted box"""
    # Print configuration box header
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 21 + "Configuration Loaded Successfully" + " " * 24 + "║")
    print("╚" + "═" * 78 + "╝")

    # Common Configuration
    print("\n[Common Configuration]")
    print(f"  App Mode:              {settings.app_mode}")
    print(f"  App Version:           {settings.app_version}")
    print(f"  API Host:              {settings.api_host}")
    print(f"  API Port:              {settings.api_port}")
    print(f"  Weaviate URL:          {settings.weaviate_url}")
    print(f"  Upload Path:           {settings.upload_path}")
    print(f"  Temp Path:             {settings.temp_path}")
    print(f"  Debug Mode:            {settings.debug}")
    print(f"  Hot Reload:            {settings.reload}")
    print(f"  Log Style:             {settings.log_style}")
    print(f"  SSL Enabled:           {settings.enable_ssl}")
    if settings.enable_ssl:
        print(f"  SSL Cert Dir:          {settings.ssl_cert_dir}")

    # Mode-specific Configuration
    if settings.app_mode == "object":
        print("\n[Object Mode Configuration]")
        print(f"  Backend:               {settings.object_backend}")
        print(f"  ONNX Thread Mode:      {settings.onnx_thread_mode}")

        # Model selection
        if settings.dinov3_model:
            print(f"  DINOv3 Model Preset:   {settings.dinov3_model}")
        actual_dinov3_path = settings.get_dinov3_model_path()
        print(f"  DINOv3 Model Path:     {actual_dinov3_path}")
        print(f"  BG Removal Model:      {settings.bg_removal_model}")

        # Model paths
        if settings.bg_removal_model == "birefnet":
            print(f"  BG Model Path:         {settings.birefnet_model_path}")
        elif settings.bg_removal_model == "u2net":
            print(f"  BG Model Path:         {settings.u2net_model_path}")
        elif settings.bg_removal_model == "u2netp":
            print(f"  BG Model Path:         {settings.u2netp_model_path}")

        # DINOv3 optimization parameters
        print(f"  Temperature:           {settings.dinov3_temperature}")
        print(f"  Multi-scale:           {settings.dinov3_use_multi_scale}")
        if settings.dinov3_use_multi_scale:
            print(f"  CLS Weight:            {settings.dinov3_cls_weight}")
            print(f"  Patch Weight:          {settings.dinov3_patch_weight}")
        print(f"  Feature Enhancement:   {settings.dinov3_feature_enhancement}")

        # PyTorch backend paths (if applicable)
        if settings.object_backend == "pytorch":
            print(f"  PyTorch BiRefNet:      {settings.pytorch_birefnet_path}")
            print(f"  PyTorch DINOv3:        {settings.pytorch_dinov3_path}")
            print(f"  Use GPU:               {settings.use_gpu}")

    elif settings.app_mode == "face":
        print("\n[Face Mode Configuration]")
        print(f"  Face Model Name:       {settings.face_model_name}")
        print(f"  Face Model Root:       {settings.face_model_root}")
        print(f"  Detection Threshold:   {settings.face_det_thresh}")
        print(f"  Detection Size:        {settings.face_det_size}")
        print(f"  Multi-scale Detection: {settings.face_enable_multi_scale}")
        if settings.face_enable_multi_scale:
            print(f"  Fallback Size:         {settings.face_det_size_fallback}")

        # Liveness detection
        print(f"  Liveness Detection:    {settings.enable_liveness}")
        if settings.enable_liveness:
            print(f"  Liveness Threshold:    {settings.liveness_threshold}")
            print(f"  Paper Reject Thresh:   {settings.liveness_paper_reject_threshold}")
            print(f"  Screen Reject Thresh:  {settings.liveness_screen_reject_threshold}")
            print(f"  MiniFASNet Model Dir:  {settings.minifasnet_model_dir}")

    # Configuration box footer
    print("\n" + "╚" + "═" * 78 + "╝\n")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting KoalaqVision API...")

    # Display all loaded configuration
    log_configuration()

    logger.indent()
    logger.info(f"App Mode: {settings.app_mode}")
    logger.info(f"Loading models...")
    try:
        logger.start_timer("model_loading")
        pipeline = get_pipeline()
        pipeline.load_models()
        logger.success(f"Models loaded successfully")
        logger.info(f"Collection: {pipeline.get_collection_name()}")
        logger.info(f"Vector Dimension: {pipeline.get_vector_dim()}D")
        logger.dedent()
        logger.end_timer("model_loading", "Model loading time")
    except Exception as e:
        logger.dedent()
        logger.error(f"Failed to load models: {e}")
    yield
    # Shutdown
    logger.info("Shutting down KoalaqVision API...")

app = FastAPI(
    title=settings.app_name,
    description="""
# Content-Based Image Retrieval System

An advanced image retrieval system powered by DINOv3 and InsightFace.

**Built with DINOv3** (Meta AI)

---

**Powered by [QHY](https://github.com/QingHeYang)**
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理器
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """处理自定义API异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理未预期的异常"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=error(ErrorCode.INTERNAL_ERROR, "Internal server error")
    )

# Register API routers based on app_mode
if settings.app_mode == "object":
    logger.info("Loading Object Recognition APIs...")
    from app.api.object import train, match, image, object
    app.include_router(train.router)
    app.include_router(match.router)
    app.include_router(image.router)
    app.include_router(object.router)
elif settings.app_mode == "face":
    logger.info("Loading Face Recognition APIs...")
    from app.api.face import train, match, person, image
    app.include_router(train.router)
    app.include_router(match.router)
    app.include_router(person.router)
    app.include_router(image.router)
else:
    logger.error(f"Unknown app_mode: {settings.app_mode}")

# Mount static files (serve uploaded images)
app.mount("/images", StaticFiles(directory="data"), name="images")

# Redirect /ui to /ui/ for Gradio
@app.get("/ui")
async def redirect_ui():
    """Redirect /ui to /ui/ to ensure Gradio works properly"""
    return RedirectResponse(url="/ui/")

# Mount Gradio UI to /ui with i18n support
app = gr.mount_gradio_app(app, demo, path="/ui", i18n=i18n)

@app.get("/")
async def root():
    pipeline = get_pipeline()

    base_info = {
        "message": "KoalaqVision API",
        "version": settings.app_version,
        "mode": settings.app_mode,
        "collection": pipeline.get_collection_name(),
        "vector_dimension": f"{pipeline.get_vector_dim()}D"
    }

    # 根据模式返回不同的模型信息
    if settings.app_mode == "object":
        base_info["models"] = {
            "pipeline": "ObjectPipeline",
            "feature_extraction": "DINOv3",
            "background_removal": "U2Net/BiRefNet"
        }
    elif settings.app_mode == "face":
        base_info["models"] = {
            "pipeline": "FacePipeline",
            "face_detection": "SCRFD-10GF",
            "face_recognition": "ResNet50@WebFace600K"
        }

    return base_info

@app.get("/health")
async def health_check():
    pipeline = get_pipeline()

    health_info = {
        "status": "healthy",
        "mode": settings.app_mode,
        "collection": pipeline.get_collection_name(),
        "vector_dimension": pipeline.get_vector_dim()
    }

    # 根据模式返回不同的健康检查信息
    if settings.app_mode == "object":
        from app.services.pipelines.object_pipeline import object_pipeline
        health_info["models"] = {
            "dinov3_loaded": object_pipeline.dinov3_session is not None,
            "background_removal_loaded": object_pipeline.bg_removal_session is not None,
            "background_removal_type": object_pipeline.bg_model_type
        }
    elif settings.app_mode == "face":
        from app.services.pipelines.face_pipeline import face_pipeline
        health_info["models"] = {
            "insightface_loaded": face_pipeline.app is not None,
            "model_pack": "buffalo_l"
        }

    return health_info

if __name__ == "__main__":
    import uvicorn
    from app.utils.ssl_utils import SSLCertFinder

    # 构建 uvicorn 配置
    uvicorn_config = {
        "app": "app.main:app",
        "host": settings.api_host,
        "port": settings.api_port,
        "reload": settings.reload
    }

    # 如果启用 SSL，自动查找证书文件
    if settings.enable_ssl:
        ssl_files = SSLCertFinder.find_cert_files(settings.ssl_cert_dir)

        if ssl_files:
            cert_file, key_file = ssl_files

            # 验证证书文件
            if SSLCertFinder.validate_cert_files(cert_file, key_file):
                uvicorn_config["ssl_certfile"] = cert_file
                uvicorn_config["ssl_keyfile"] = key_file
                logger.success(f"HTTPS enabled on port {settings.api_port}")
                logger.info(f"Certificate: {cert_file}")
                logger.info(f"Private Key: {key_file}")
            else:
                logger.error("SSL certificate validation failed, starting with HTTP")
                settings.enable_ssl = False
        else:
            logger.error(f"No SSL certificates found in: {settings.ssl_cert_dir}")
            logger.warning("Starting with HTTP mode")
            settings.enable_ssl = False

    if not settings.enable_ssl:
        logger.info(f"HTTP mode on port {settings.api_port}")

    uvicorn.run(**uvicorn_config)