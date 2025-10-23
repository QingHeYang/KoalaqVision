"""
人员管理模块
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


def search_persons(search_query: str):
    """搜索人员列表"""
    try:
        # 获取所有人员（只调用一次，性能高）
        persons = vector_service.list_objects()

        if not persons:
            print("⚠️ 没有找到任何人员数据")
            return pd.DataFrame(columns=["person_id", "face_count"])

        # 如果有搜索条件，进行筛选
        if search_query and search_query.strip():
            search_query = search_query.strip().lower()
            persons = [p for p in persons if search_query in p["object_id"].lower()]

        # 构建表格数据 - 使用固定的英文列名
        data = {
            "person_id": [p["object_id"] for p in persons],
            "face_count": [p["image_count"] for p in persons]
        }

        df = pd.DataFrame(data)
        print(f"📊 返回 {len(df)} 条人员数据")
        return df

    except Exception as e:
        print(f"❌ {format_message('error')}: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=["person_id", "face_count"])


def get_person_detail(selected_data):
    """查看人员详情

    Args:
        selected_data: Dataframe选中的行数据
    """
    try:
        # Gradio Dataframe的select事件返回的是SelectData对象
        # 需要从中提取选中的行数据
        if not selected_data or len(selected_data) == 0:
            return None, "", ""

        # 获取选中行的第一列（person_id）
        person_id = selected_data[0] if isinstance(selected_data, list) else selected_data

        if not person_id:
            return None, "", f"❌ {format_message('person_id_required')}"

        # 查询该人员的所有人脸图片
        images = vector_service.get_by_object_id(person_id)

        if not images:
            return None, "", format_message("no_faces_for_person", id=person_id)

        # 构建基本信息
        custom_data_set = set()
        created_times = []
        for img in images:
            cd = img.get("custom_data")
            if cd:
                custom_data_set.add(str(cd))
            # 收集创建时间
            created_at = img.get("created_at")
            if created_at:
                created_times.append(str(created_at))

        info_text = f"👤 {format_message('person_id')}: {person_id}\n"
        info_text += f"📊 {format_message('face_count')}: {len(images)}\n"

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
            # 优先显示人脸图
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

        return gallery_images, info_text, detail_text

    except Exception as e:
        return None, "", f"❌ {format_message('error')}: {str(e)}"


def delete_person(person_id: str, confirm_text: str):
    """删除人员

    Args:
        person_id: 从输入框获取的人员ID
        confirm_text: 确认文本，必须输入 "delete" 才能删除
    """
    if not person_id or not person_id.strip():
        return f"❌ {format_message('person_id_required')}"

    # 检查确认文本
    if confirm_text != "delete":
        return f"❌ {format_message('delete_confirm_required')}"

    try:
        count = vector_service.delete_by_object_id(person_id.strip())
        return f"✅ {format_message('deleted_person_faces', id=person_id, count=count)}"
    except Exception as e:
        return f"❌ {format_message('error')}: {str(e)}"


def create_person_tab():
    """创建人员管理Tab"""
    with gr.Tab(i18n("tab_persons")):
        with gr.Row():
            # 左侧：人员列表 (3)
            with gr.Column(scale=3):
                # 搜索框
                with gr.Row():
                    person_search_input = gr.Textbox(
                        placeholder=i18n("search_person_placeholder"),
                        scale=4,
                        show_label=False,
                        container=False
                    )
                    person_search_btn = gr.Button(i18n("search_button"), scale=1)

                # 人员列表
                person_list_table = gr.Dataframe(
                    label=i18n("person_list"),
                    headers=[i18n("person_id_col"), i18n("face_count_col")],
                    interactive=False,
                    row_count=20,
                    value=lambda: search_persons(""),  # 使用 callable 初始化
                    column_widths=["70%", "30%"]  # 设置列宽比例
                )

                # 操作区
                with gr.Row():
                    person_selected_display = gr.Textbox(
                        label=i18n("selected_person"),
                        placeholder=i18n("click_to_select"),
                        scale=3,
                        interactive=True
                    )

                with gr.Row():
                    person_detail_btn = gr.Button(i18n("view_details"), variant="primary", scale=1)

                # 删除区域
                with gr.Row():
                    person_delete_confirm_input = gr.Textbox(
                        placeholder=i18n("delete_confirm_input"),
                        show_label=False,
                        container=False,
                        scale=3
                    )
                    person_delete_btn = gr.Button(i18n("delete_person"), variant="stop", scale=1)

                person_operation_output = gr.Textbox(
                    label=i18n("operation_result"),
                    lines=3
                )

            # 右侧：详情 (1)
            with gr.Column(scale=1):
                # 基本信息
                person_info = gr.Textbox(
                    label=i18n("person_info"),
                    lines=5,
                    max_lines=8
                )

                # 人脸图片
                person_gallery = gr.Gallery(
                    label=i18n("face_images"),
                    columns=2,
                    height=400,
                    object_fit="contain"
                )

                # 详细信息
                person_detail_text = gr.Textbox(
                    label=i18n("face_details"),
                    lines=8,
                    max_lines=15
                )

        # 事件绑定

        # 搜索按钮
        person_search_btn.click(
            search_persons,
            inputs=[person_search_input],
            outputs=[person_list_table]
        )

        # 点击表格行，显示选中的person_id
        def on_select(evt: gr.SelectData):
            """选中表格行时触发"""
            if evt.index[1] == 0:  # 点击第一列（person_id）
                return evt.value
            return ""

        person_list_table.select(
            on_select,
            outputs=[person_selected_display]
        )

        # 查看详情按钮
        person_detail_btn.click(
            lambda pid: get_person_detail([pid]),
            inputs=[person_selected_display],
            outputs=[person_gallery, person_info, person_detail_text]
        )

        # 删除按钮（需要输入 "delete" 确认）
        person_delete_btn.click(
            delete_person,
            inputs=[person_selected_display, person_delete_confirm_input],
            outputs=[person_operation_output]
        )
