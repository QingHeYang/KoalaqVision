"""
人脸图片管理模块
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


def query_person_faces(person_id: str):
    """查询人员的所有人脸"""
    print(f"🔍 查询人员ID: {person_id}")

    if not person_id or not person_id.strip():
        print(f"⚠️ 人员ID为空")
        gr.Warning(format_message('person_id_required'))
        return "", [], []

    try:
        # 查询该人员的所有人脸
        images = vector_service.get_by_object_id(person_id.strip())
        print(f"📊 查询到 {len(images) if images else 0} 张人脸")

        if not images:
            gr.Info(format_message("no_faces_for_person", id=person_id))
            return "", [], []

        # 构建基础信息
        info_text = f"👤 {format_message('person_id')}: {person_id}\n"
        info_text += f"📊 {format_message('face_count')}: {len(images)}\n"

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
                print(f"  ✓ 添加图片: {img_path}, caption: {caption}")

        print(f"✅ 构建完成，info_text长度: {len(info_text)}, gallery长度: {len(gallery_images)}")
        gr.Info(format_message('found_n_faces', count=len(images)))
        return info_text, gallery_images, images

    except Exception as e:
        print(f"❌ 查询出错: {str(e)}")
        import traceback
        traceback.print_exc()
        gr.Error(f"{format_message('error')}: {str(e)}")
        return "", [], []


def delete_face_image(image_id: str, confirm_text: str):
    """删除单张人脸图片"""
    # 验证 image_id
    if not image_id or not image_id.strip():
        gr.Warning(format_message('image_id_required'))
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


def create_image_mgmt_tab():
    """创建人脸图片管理 Tab"""
    with gr.Tab(i18n("tab_face_images")):
        # 使用 State 存储当前查询的 images 数据
        images_state = gr.State([])

        # 顶部：左侧查询 + 右侧人员信息
        with gr.Row():
            # 左侧：人员ID + 查询按钮（1）
            with gr.Column(scale=1):
                face_query_person_id = gr.Textbox(
                    label=i18n("person_id"),
                    placeholder=i18n("person_id_placeholder")
                )
                face_query_btn = gr.Button(i18n("query"), variant="primary")

            # 右侧：人员信息（1）
            with gr.Column(scale=1):
                face_person_info = gr.Textbox(
                    label=i18n("person_info"),
                    lines=4,
                    max_lines=6
                )

        # 下方：左侧人脸图片 + 右侧人脸操作
        with gr.Row():
            # 左侧：人脸图片 Gallery（1）
            with gr.Column(scale=1):
                face_gallery = gr.Gallery(
                    label=i18n("face_images"),
                    columns=2,
                    rows=3,
                    height=800,
                    object_fit="contain"
                )

            # 右侧：人脸操作（1）
            with gr.Column(scale=1):
                gr.Markdown(f"### {i18n('face_operations')}")

                # Image ID 输入框
                face_image_id_input = gr.Textbox(
                    label=i18n("image_id"),
                    placeholder=i18n("click_gallery_or_input")
                )

                # 删除区域
                with gr.Row():
                    face_delete_confirm_input = gr.Textbox(
                        placeholder=i18n("delete_confirm_input"),
                        show_label=False,
                        container=False,
                        scale=3
                    )
                    face_delete_btn = gr.Button(i18n("delete_image"), variant="stop", scale=1)

        # 事件绑定

        # 查询按钮
        face_query_btn.click(
            query_person_faces,
            inputs=[face_query_person_id],
            outputs=[face_person_info, face_gallery, images_state]
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

        face_gallery.select(
            on_gallery_select,
            inputs=[images_state],
            outputs=[face_image_id_input]
        )

        # 删除按钮
        face_delete_btn.click(
            delete_face_image,
            inputs=[face_image_id_input, face_delete_confirm_input]
        )
