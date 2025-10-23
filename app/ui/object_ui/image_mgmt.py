"""
图片管理模块
"""
import gradio as gr
from app.services.vector_service import vector_service
from app.ui.i18n_official import i18n, format_message


def _url_to_path(url: str) -> str:
    """将URL转换为文件路径（Gradio需要文件路径）"""
    if not url:
        return None
    if url.startswith("/images/"):
        return url.replace("/images/", "data/", 1)
    return url


def query_object_images(object_id: str):
    """查询物品的所有图片"""
    if not object_id or not object_id.strip():
        gr.Warning(format_message('input_object_id_msg'))
        return "", [], []

    try:
        # 查询该物品的所有图片
        images = vector_service.get_by_object_id(object_id.strip())

        if not images:
            gr.Info(format_message("no_images_for_object", id=object_id))
            return "", [], []

        # 构建基础信息
        info_text = f"📦 {format_message('object_id')}: {object_id}\n"
        info_text += f"📊 {format_message('image_count')}: {len(images)}\n"

        # 收集创建时间
        created_times = [img.get("created_at") for img in images if img.get("created_at")]
        if created_times:
            earliest_time = min(created_times)
            # 转换为字符串
            time_str = str(earliest_time)[:19] if earliest_time else ""
            info_text += f"📅 {format_message('created_time')}: {time_str}\n"

        # 构建 Gallery 图片列表（显示原图）
        gallery_images = []
        for img in images:
            # 显示原图
            img_url = img.get("img_url")
            if img_url:
                img_path = _url_to_path(img_url)
                image_id = img.get("image_id", "")

                # Caption 显示前8位 image_id
                caption = f"ID: {image_id[:8]}..."
                gallery_images.append((img_path, caption))

        gr.Info(format_message('object_with_images', id=object_id, count=len(images)))
        return info_text, gallery_images, images

    except Exception as e:
        gr.Error(f"{format_message('error')}: {str(e)}")
        return "", [], []


def delete_image(image_id: str, confirm_text: str):
    """删除单张图片"""
    # 验证 image_id
    if not image_id or not image_id.strip():
        gr.Warning(format_message('input_image_id_msg'))
        return

    # 验证确认文本
    if confirm_text != "delete":
        gr.Warning(format_message('delete_confirm_required'))
        return

    try:
        # 调用 vector_service 删除
        vector_service.delete_by_image_id(image_id.strip())
        gr.Info(format_message('deleted_image', id=image_id[:8]))
    except Exception as e:
        gr.Error(f"{format_message('error')}: {str(e)}")


def create_image_tab():
    """创建图片管理 Tab"""
    with gr.Tab(i18n("tab_image")):
        # 使用 State 存储当前查询的 images 数据
        images_state = gr.State([])

        # 顶部：左侧查询 + 右侧物品信息
        with gr.Row():
            # 左侧：物品ID + 查询按钮（1）
            with gr.Column(scale=1):
                image_query_object_id = gr.Textbox(
                    label=i18n("object_id"),
                    placeholder=i18n("object_id_placeholder")
                )
                image_query_btn = gr.Button(i18n("query"), variant="primary")

            # 右侧：物品信息（1）
            with gr.Column(scale=1):
                image_object_info = gr.Textbox(
                    label=i18n("object_info"),
                    lines=4,
                    max_lines=6
                )

        # 下方：左侧图片 + 右侧操作
        with gr.Row():
            # 左侧：图片 Gallery（1）
            with gr.Column(scale=1):
                image_gallery = gr.Gallery(
                    label=i18n("object_images"),
                    columns=2,
                    rows=3,
                    height=800,
                    object_fit="contain"
                )

            # 右侧：图片操作（1）
            with gr.Column(scale=1):
                gr.Markdown(f"### {format_message('image_management')}")

                # Image ID 输入框
                image_id_input = gr.Textbox(
                    label=i18n("image_id"),
                    placeholder=i18n("click_gallery_or_input")
                )

                # 删除区域
                with gr.Row():
                    image_delete_confirm_input = gr.Textbox(
                        placeholder=i18n("delete_confirm_input"),
                        show_label=False,
                        container=False,
                        scale=3
                    )
                    image_delete_btn = gr.Button(i18n("delete_image"), variant="stop", scale=1)

        # 事件绑定

        # 查询按钮
        image_query_btn.click(
            query_object_images,
            inputs=[image_query_object_id],
            outputs=[image_object_info, image_gallery, images_state]
        )

        # Gallery 点击事件：通过 index 获取完整 image_id
        def on_gallery_select(images_data, evt: gr.SelectData):
            """点击 Gallery 图片时，从 State 中提取完整的 image_id"""
            if not images_data or evt.index >= len(images_data):
                return ""

            # 通过 index 获取对应的 image 数据
            selected_image = images_data[evt.index]
            image_id = selected_image.get("image_id", "")
            return image_id

        image_gallery.select(
            on_gallery_select,
            inputs=[images_state],
            outputs=[image_id_input]
        )

        # 删除按钮
        image_delete_btn.click(
            delete_image,
            inputs=[image_id_input, image_delete_confirm_input]
        )
