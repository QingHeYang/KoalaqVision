"""
人脸注册模块 - 对齐 face_service
"""
import gradio as gr
from app.services.face_service import face_service
from app.ui.i18n_official import i18n, format_message


def _url_to_path(url: str) -> str:
    """将URL转换为文件路径（Gradio需要文件路径）"""
    if not url:
        return None
    # /images/upload/... → data/upload/...
    if url.startswith("/images/"):
        return url.replace("/images/", "data/", 1)
    return url


def train_single_file(image, person_id: str, save_files: bool, enable_liveness: bool):
    """单文件人脸注册 - 调用 face_service"""
    # 判空检查
    if not image:
        return None, None, f"❌ {format_message('upload_face_image_required')}"
    if not person_id or not person_id.strip():
        return None, None, f"❌ {format_message('person_id_required')}"

    try:
        result = face_service.add_face(
            image_source=image,
            person_id=person_id,
            save_files=save_files,
            enable_liveness=enable_liveness
        )

        # 返回：原图、人脸图、结果文本
        result_text = f"✅ {format_message('register_success')}\nImage ID: {result.image_id}\n{format_message('person_id')}: {result.person_id}"
        if result.face_bbox:
            result_text += f"\nFace bbox: {result.face_bbox}"
        if result.face_score is not None:
            result_text += f"\nFace score: {result.face_score}"

        # 将URL转换为文件路径（Gradio需要文件路径，不是URL）
        img_path = _url_to_path(result.img_url) if result.img_url else None
        img_face_path = _url_to_path(result.img_face_url) if result.img_face_url else None

        return img_path, img_face_path, result_text
    except Exception as e:
        return None, None, f"❌ {format_message('error')}: {str(e)}"


def train_single_url(url: str, person_id: str, save_files: bool, enable_liveness: bool):
    """单URL人脸注册 - 调用 face_service"""
    # 判空检查
    if not url or not url.strip():
        return None, None, f"❌ {format_message('face_url_required')}"
    if not person_id or not person_id.strip():
        return None, None, f"❌ {format_message('person_id_required')}"

    try:
        result = face_service.add_face(
            image_source=url,
            person_id=person_id,
            save_files=save_files,
            enable_liveness=enable_liveness
        )

        # 返回：原图、人脸图、结果文本
        result_text = f"✅ {format_message('register_success')}\nImage ID: {result.image_id}\n{format_message('person_id')}: {result.person_id}"
        if result.face_bbox:
            result_text += f"\nFace bbox: {result.face_bbox}"
        if result.face_score is not None:
            result_text += f"\nFace score: {result.face_score}"

        # 将URL转换为文件路径（Gradio需要文件路径，不是URL）
        img_path = _url_to_path(result.img_url) if result.img_url else None
        img_face_path = _url_to_path(result.img_face_url) if result.img_face_url else None

        return img_path, img_face_path, result_text
    except Exception as e:
        return None, None, f"❌ {format_message('error')}: {str(e)}"


def create_train_tab():
    """创建人脸注册Tab"""
    with gr.Tab(i18n("tab_register")):
        # 主布局：左侧注册操作栏 + 右侧结果栏 (1:1)
        with gr.Row():
            # 左侧：注册操作栏
            with gr.Column(scale=1):
                # 上传人脸框（文件 + URL 上下排布）
                with gr.Accordion(i18n("upload_face"), open=True):
                    train_image = gr.Image(
                        type="pil",
                        sources=["upload", "webcam", "clipboard"],
                        label=i18n("upload_face_image"),
                        height=250
                    )
                    train_url = gr.Textbox(
                        label=i18n("or_input_face_url"),
                        placeholder="https://example.com/face.jpg",
                        lines=2
                    )

                # 注册参数框
                with gr.Accordion(i18n("register_params"), open=True):
                    train_person_id = gr.Textbox(
                        label=i18n("person_id"),
                        placeholder=i18n("person_id_placeholder")
                    )
                    train_save = gr.Checkbox(
                        label=i18n("save_files"),
                        value=True
                    )
                    train_liveness = gr.Checkbox(
                        label=i18n("enable_liveness"),
                        value=False,
                        info=i18n("liveness_hint")
                    )

                    # 注册按钮
                    with gr.Row():
                        train_file_btn = gr.Button(i18n("file_register"), variant="primary")
                        train_url_btn = gr.Button(i18n("url_register"), variant="primary")

            # 右侧：结果栏
            with gr.Column(scale=1):
                # 结果文本（上方）
                train_output = gr.Textbox(
                    label=i18n("result"),
                    lines=8,
                    max_lines=15
                )

                # 两个并列的图片框（下方）
                with gr.Row():
                    train_img_orig = gr.Image(
                        label=i18n("original_image"),
                        height=300
                    )
                    train_img_face = gr.Image(
                        label=i18n("face_image_cropped"),
                        height=300
                    )

        # 绑定事件
        train_file_btn.click(
            train_single_file,
            inputs=[train_image, train_person_id, train_save, train_liveness],
            outputs=[train_img_orig, train_img_face, train_output]
        )

        train_url_btn.click(
            train_single_url,
            inputs=[train_url, train_person_id, train_save, train_liveness],
            outputs=[train_img_orig, train_img_face, train_output]
        )
