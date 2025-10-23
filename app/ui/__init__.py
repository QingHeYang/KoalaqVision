"""
KoalaqVision WebUI Package - 根据 app_mode 加载对应 UI
"""
from app.config.settings import settings

if settings.app_mode == "object":
    from app.ui.object_ui import create_object_ui
    demo, i18n = create_object_ui()

elif settings.app_mode == "face":
    from app.ui.face_ui import create_face_ui
    demo, i18n = create_face_ui()

else:
    raise ValueError(f"Unknown app_mode: {settings.app_mode}")

__all__ = ["demo", "i18n"]
