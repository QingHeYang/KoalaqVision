"""
Face 模式主界面
"""
import os
from pathlib import Path
import gradio as gr

from app.ui.face_ui.train import create_train_tab
from app.ui.face_ui.match import create_match_tab
from app.ui.face_ui.person_mgmt import create_person_tab
from app.ui.face_ui.image_mgmt import create_image_mgmt_tab
from app.ui.i18n_official import i18n

# 配置Gradio临时文件目录到项目内
GRADIO_TEMP_DIR = Path("data/temp/gradio")
GRADIO_TEMP_DIR.mkdir(parents=True, exist_ok=True)
os.environ["GRADIO_TEMP_DIR"] = str(GRADIO_TEMP_DIR.absolute())


def create_face_ui():
    """创建 Face UI（4个Tab: Register + Recognize + Persons + Face Images）"""
    with gr.Blocks(title="KoalaqVision Face Recognition") as demo:
        # 标题
        gr.Markdown(f"# {i18n('app_title_face')}")
        gr.Markdown(i18n('app_subtitle_face'))

        # 作者信息
        gr.Markdown(
            '<div style="color: #999; font-size: 0.85em; margin-bottom: 15px;">By <a href="https://github.com/QingHeYang" target="_blank" style="color: #4A90E2; text-decoration: none;">@QHY</a></div>'
        )

        # 4个功能Tab
        create_train_tab()      # 人脸注册
        create_match_tab()      # 人脸识别
        create_person_tab()     # 人员管理
        create_image_mgmt_tab() # 人脸管理

    return demo, i18n
