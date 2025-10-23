"""
训练模块 - 对齐 /api/train 端点
"""
import gradio as gr
from app.services.object_service import object_service
from app.ui.i18n_official import i18n, format_message


def _url_to_path(url: str) -> str:
    """将URL转换为文件路径（Gradio需要文件路径）"""
    if not url:
        return None
    # /images/upload/... → data/upload/...
    if url.startswith("/images/"):
        return url.replace("/images/", "data/", 1)
    return url


def train_single_file(image, object_id: str, save_files: bool):
    """单文件训练 - 对齐 POST /api/train/file"""
    # 验证输入
    if not image:
        gr.Warning(format_message('upload_image_and_id'))
        return None, None, ""
    if not object_id or not object_id.strip():
        gr.Warning(format_message('upload_image_and_id'))
        return None, None, ""

    try:
        result = object_service.add_image(
            image_source=image,
            object_id=object_id,
            save_files=save_files,
            custom_data={}
        )

        # 返回：原图、object图、结果文本
        result_text = f"✅ {format_message('train_success')}\nImage ID: {result.image_id}\n{format_message('object_id')}: {result.object_id}"

        # 将URL转换为文件路径（Gradio需要文件路径，不是URL）
        img_path = _url_to_path(result.img_url) if result.img_url else None
        img_object_path = _url_to_path(result.img_object_url) if result.img_object_url else None

        gr.Info(format_message('train_success'))
        return img_path, img_object_path, result_text
    except Exception as e:
        gr.Error(f"{format_message('error')}: {str(e)}")
        return None, None, f"❌ {format_message('error')}: {str(e)}"


def train_single_url(url: str, object_id: str, save_files: bool):
    """单URL训练 - 对齐 POST /api/train/url"""
    # 验证输入
    if not url or not url.strip():
        gr.Warning(format_message('input_url_and_id'))
        return None, None, ""
    if not object_id or not object_id.strip():
        gr.Warning(format_message('input_url_and_id'))
        return None, None, ""

    try:
        result = object_service.add_image(
            image_source=url,
            object_id=object_id,
            save_files=save_files,
            custom_data={}
        )

        # 返回：原图、object图、结果文本
        result_text = f"✅ {format_message('train_success')}\nImage ID: {result.image_id}\n{format_message('object_id')}: {result.object_id}"

        # 将URL转换为文件路径（Gradio需要文件路径，不是URL）
        img_path = _url_to_path(result.img_url) if result.img_url else None
        img_object_path = _url_to_path(result.img_object_url) if result.img_object_url else None

        gr.Info(format_message('train_success'))
        return img_path, img_object_path, result_text
    except Exception as e:
        gr.Error(f"{format_message('error')}: {str(e)}")
        return None, None, f"❌ {format_message('error')}: {str(e)}"


def create_train_tab():
    """创建训练Tab"""
    with gr.Tab(i18n("tab_train")):
        # 主布局：左侧训练操作栏 + 右侧结果栏 (1:1)
        with gr.Row():
            # 左侧：训练操作栏
            with gr.Column(scale=1):
                # 上传图片框（文件 + URL 上下排布）
                with gr.Accordion(i18n("upload_image"), open=True):
                    train_image = gr.Image(
                        type="pil",
                        sources=["upload", "webcam", "clipboard"],
                        label=i18n("upload_image"),
                        height=250
                    )
                    train_url = gr.Textbox(
                        label=i18n("or_input_url"),
                        placeholder="https://example.com/image.jpg",
                        lines=2
                    )

                # 训练参数框
                with gr.Accordion(i18n("train_params"), open=True):
                    train_object_id = gr.Textbox(
                        label=i18n("object_id"),
                        placeholder=i18n("object_id_placeholder")
                    )
                    train_save = gr.Checkbox(
                        label=i18n("save_files"),
                        value=True
                    )

                    # 训练按钮
                    with gr.Row():
                        train_file_btn = gr.Button(i18n("file_train"), variant="primary")
                        train_url_btn = gr.Button(i18n("url_train"), variant="primary")

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
                    train_img_object = gr.Image(
                        label=i18n("object_image"),
                        height=300
                    )

        # 绑定事件
        train_file_btn.click(
            train_single_file,
            inputs=[train_image, train_object_id, train_save],
            outputs=[train_img_orig, train_img_object, train_output]
        )

        train_url_btn.click(
            train_single_url,
            inputs=[train_url, train_object_id, train_save],
            outputs=[train_img_orig, train_img_object, train_output]
        )
