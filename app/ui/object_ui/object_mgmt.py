"""
物品管理模块 - 对齐 /api/object 端点
"""
import gradio as gr
import pandas as pd
from app.services.vector_service import vector_service
from app.ui.i18n_official import i18n, format_message


def _url_to_path(url: str) -> str:
    """将URL转换为文件路径（Gradio需要文件路径）"""
    if not url:
        return None
    if url.startswith("/images/"):
        return url.replace("/images/", "data/", 1)
    return url


def search_objects(search_query: str):
    """搜索物品列表"""
    try:
        # 获取所有物品
        objects = vector_service.list_objects()

        if not objects:
            return pd.DataFrame(columns=["object_id", "image_count"])

        # 如果有搜索条件，进行筛选
        if search_query and search_query.strip():
            search_query = search_query.strip().lower()
            objects = [o for o in objects if search_query in o["object_id"].lower()]

        # 构建表格数据
        data = {
            "object_id": [o["object_id"] for o in objects],
            "image_count": [o["image_count"] for o in objects]
        }

        df = pd.DataFrame(data)
        return df

    except Exception as e:
        gr.Error(f"{format_message('error')}: {str(e)}")
        return pd.DataFrame(columns=["object_id", "image_count"])


def get_object_detail(selected_data):
    """查看物品详情

    Args:
        selected_data: Dataframe选中的行数据
    """
    try:
        if not selected_data or len(selected_data) == 0:
            return None, "", ""

        # 获取选中行的第一列（object_id）
        object_id = selected_data[0] if isinstance(selected_data, list) else selected_data

        if not object_id:
            gr.Warning(format_message('input_object_id_msg'))
            return None, "", ""

        # 查询该物品的所有图片
        images = vector_service.get_by_object_id(object_id)

        if not images:
            gr.Info(format_message("no_images_for_object", id=object_id))
            return None, "", ""

        # 构建基本信息
        custom_data_set = set()
        created_times = []
        for img in images:
            cd = img.get("custom_data")
            if cd:
                custom_data_set.add(str(cd))
            created_at = img.get("created_at")
            if created_at:
                created_times.append(str(created_at))

        info_text = f"📦 {format_message('object_id')}: {object_id}\n"
        info_text += f"📊 {format_message('image_count')}: {len(images)}\n"

        # 显示最早入库时间
        if created_times:
            earliest_time = min(created_times)
            info_text += f"📅 {format_message('created_time')}: {earliest_time[:19]}\n"

        if custom_data_set:
            info_text += f"📝 Custom Data: {', '.join(custom_data_set)}\n"

        # 构建Gallery图片列表
        gallery_images = []
        detail_text = ""
        for img in images:
            # 优先显示物品图（去背景）
            img_url = img.get("img_object_url") or img.get("img_url")
            if img_url:
                img_path = _url_to_path(img_url)
                image_id = img.get("image_id", "")

                # Caption显示前8位image_id
                caption = f"ID: {image_id[:8]}..."
                gallery_images.append((img_path, caption))

                # 详情文本中显示完整信息
                detail_text += f"\n🆔 Image ID: {image_id}\n"
                cd = img.get("custom_data")
                if cd:
                    detail_text += f"   📝 Custom Data: {cd}\n"
                created = img.get("created_at")
                if created:
                    detail_text += f"   📅 Created: {created}\n"

        gr.Info(format_message('object_with_images', id=object_id, count=len(images)))
        return gallery_images, info_text, detail_text

    except Exception as e:
        gr.Error(f"{format_message('error')}: {str(e)}")
        return None, "", ""


def delete_object(object_id: str, confirm_text: str):
    """删除物品

    Args:
        object_id: 从输入框获取的物品ID
        confirm_text: 确认文本，必须输入 "delete" 才能删除
    """
    if not object_id or not object_id.strip():
        gr.Warning(format_message('input_object_id_msg'))
        return

    # 检查确认文本
    if confirm_text != "delete":
        gr.Warning(format_message('delete_confirm_required'))
        return

    try:
        count = vector_service.delete_by_object_id(object_id.strip())
        gr.Info(format_message('deleted_object_images', id=object_id, count=count))
    except Exception as e:
        gr.Error(f"{format_message('error')}: {str(e)}")


def create_object_tab():
    """创建物品管理Tab"""
    with gr.Tab(i18n("tab_object")):
        with gr.Row():
            # 左侧：物品列表 (3)
            with gr.Column(scale=3):
                # 搜索框
                with gr.Row():
                    object_search_input = gr.Textbox(
                        placeholder=i18n("search_object_placeholder"),
                        scale=4,
                        show_label=False,
                        container=False
                    )
                    object_search_btn = gr.Button(i18n("search_button"), scale=1)

                # 物品列表
                object_list_table = gr.Dataframe(
                    label=i18n("object_list"),
                    headers=[i18n("object_id_col"), i18n("image_count_col")],
                    interactive=False,
                    row_count=20,
                    value=lambda: search_objects(""),  # 使用 callable 初始化
                    column_widths=["70%", "30%"]
                )

                # 操作区
                with gr.Row():
                    object_selected_display = gr.Textbox(
                        label=i18n("selected_object"),
                        placeholder=i18n("click_to_select_object"),
                        scale=3,
                        interactive=True
                    )

                with gr.Row():
                    object_detail_btn = gr.Button(i18n("view_details"), variant="primary", scale=1)

                # 删除区域
                with gr.Row():
                    object_delete_confirm_input = gr.Textbox(
                        placeholder=i18n("delete_confirm_input"),
                        show_label=False,
                        container=False,
                        scale=3
                    )
                    object_delete_btn = gr.Button(i18n("delete_object"), variant="stop", scale=1)

            # 右侧：详情 (1)
            with gr.Column(scale=1):
                # 基本信息
                object_info = gr.Textbox(
                    label=i18n("object_info"),
                    lines=5,
                    max_lines=8
                )

                # 物品图片
                object_gallery = gr.Gallery(
                    label=i18n("object_images"),
                    columns=2,
                    height=400,
                    object_fit="contain"
                )

                # 详细信息
                object_detail_text = gr.Textbox(
                    label=i18n("image_details"),
                    lines=8,
                    max_lines=15
                )

        # 事件绑定

        # 搜索按钮
        object_search_btn.click(
            search_objects,
            inputs=[object_search_input],
            outputs=[object_list_table]
        )

        # 点击表格行，显示选中的object_id
        def on_select(evt: gr.SelectData):
            """选中表格行时触发"""
            if evt.index[1] == 0:  # 点击第一列（object_id）
                return evt.value
            return ""

        object_list_table.select(
            on_select,
            outputs=[object_selected_display]
        )

        # 查看详情按钮
        object_detail_btn.click(
            lambda oid: get_object_detail([oid]),
            inputs=[object_selected_display],
            outputs=[object_gallery, object_info, object_detail_text]
        )

        # 删除按钮（需要输入 "delete" 确认）
        object_delete_btn.click(
            delete_object,
            inputs=[object_selected_display, object_delete_confirm_input]
        )
