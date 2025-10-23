"""
Object 模式主界面
"""
import os
from pathlib import Path
import gradio as gr

from app.ui.object_ui.train import create_train_tab
from app.ui.object_ui.match import create_match_tab
from app.ui.object_ui.object_mgmt import create_object_tab
from app.ui.object_ui.image_mgmt import create_image_tab
from app.ui.i18n_official import i18n

# 配置Gradio临时文件目录到项目内
GRADIO_TEMP_DIR = Path("data/temp/gradio")
GRADIO_TEMP_DIR.mkdir(parents=True, exist_ok=True)
os.environ["GRADIO_TEMP_DIR"] = str(GRADIO_TEMP_DIR.absolute())


def create_object_ui():
    """创建 Object UI（4个Tab）"""
    with gr.Blocks(title="KoalaqVision") as demo:
        # 标题
        gr.Markdown(f"# {i18n('app_title')}")
        gr.Markdown(i18n('app_subtitle'))

        # 作者信息
        gr.Markdown(
            '<div style="color: #999; font-size: 0.85em; margin-bottom: 15px;">By <a href="https://github.com/QingHeYang" target="_blank" style="color: #4A90E2; text-decoration: none;">@QHY</a></div>'
        )

        # 4个功能Tab
        create_train_tab()
        create_match_tab()
        create_object_tab()
        create_image_tab()

    return demo, i18n
