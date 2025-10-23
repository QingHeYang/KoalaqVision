"""
人脸识别模块 - 对齐 face_service
"""
import gradio as gr
from app.services.face_service import face_service
from app.ui.i18n_official import i18n, format_message


def _url_to_path(url: str) -> str:
    """将URL转换为文件路径（Gradio需要文件路径）"""
    if not url:
        return None
    # /images/upload/... → data/upload/...
    # /images/temp/... → data/temp/...
    if url.startswith("/images/"):
        return url.replace("/images/", "data/", 1)
    return url


def match_image_file(image, person_ids: str, confidence: float, top_k: int, enable_liveness: bool, save_temp: bool):
    """文件识别 - 调用 face_service"""
    if not image:
        return None, None, f"❌ {format_message('upload_query_face_msg')}"

    try:
        # 解析 person_ids
        person_id_list = None
        if person_ids and person_ids.strip():
            person_id_list = [id.strip() for id in person_ids.split(",") if id.strip()]

        # 调用 service
        result = face_service.match_face(
            image_source=image,
            save_temp=save_temp,
            person_ids=person_id_list,
            confidence=confidence,
            top_k=top_k,
            enable_liveness=enable_liveness
        )

        # 处理结果
        gallery, text = _process_match_result(result)

        # 返回查询人脸图路径（文件路径，不是URL）
        query_face_path = result.get("temp_path")  # 这已经是文件路径

        return query_face_path, gallery, text

    except Exception as e:
        return None, None, f"❌ {format_message('error')}: {str(e)}"


def match_image_url(url: str, person_ids: str, confidence: float, top_k: int, enable_liveness: bool, save_temp: bool):
    """URL识别 - 调用 face_service"""
    if not url:
        return None, None, f"❌ {format_message('input_face_url_msg')}"

    try:
        # 解析 person_ids
        person_id_list = None
        if person_ids and person_ids.strip():
            person_id_list = [id.strip() for id in person_ids.split(",") if id.strip()]

        # 调用 service
        result = face_service.match_face(
            image_source=url,
            save_temp=save_temp,
            person_ids=person_id_list,
            confidence=confidence,
            top_k=top_k,
            enable_liveness=enable_liveness
        )

        # 处理结果
        gallery, text = _process_match_result(result)

        # 返回查询人脸图路径（文件路径，不是URL）
        query_face_path = result.get("temp_path")  # 这已经是文件路径

        return query_face_path, gallery, text

    except Exception as e:
        return None, None, f"❌ {format_message('error')}: {str(e)}"


def _process_match_result(result):
    """处理匹配结果，转换为Gallery格式"""
    matches = result.get("grouped_matches", [])
    liveness_info = result.get("liveness")  # 可能为 None

    gallery_images = []
    result_text = ""

    # 活体检测信息（如果有）
    if liveness_info:
        if liveness_info["passed"]:
            result_text += f"✅ {format_message('liveness_passed')}\n"
            result_text += f"{format_message('liveness_score', score=liveness_info['score'])}\n\n"
        else:
            result_text += f"❌ {format_message('liveness_failed')}\n"
            result_text += f"{format_message('liveness_score', score=liveness_info['score'])}\n\n"

    # 匹配结果
    result_text += f"🔍 {format_message('found_persons', count=len(matches))}\n\n"

    for match in matches:
        person_id = match["person_id"]
        max_sim = match["max_similarity"]
        result_text += f"👤 {format_message('person_similarity', id=person_id, sim=max_sim)}\n"

        for face in match["faces"]:
            # 显示原图，不是剪裁的人脸
            img_url = face.get("img_url")
            if img_url:
                # 将URL转换为文件路径（Gradio需要文件路径）
                img_path = _url_to_path(img_url)

                # Caption只包含：person_id + 相似度
                caption = f"{person_id} - {face['similarity']:.3f}"
                gallery_images.append((img_path, caption))

                # custom_data 显示在结果详情中
                custom_data = face.get("custom_data")
                if custom_data:
                    result_text += f"   📝 Custom Data: {custom_data}\n"

                # 显示 image_id
                image_id = face.get("image_id")
                if image_id:
                    result_text += f"   🆔 Image ID: {image_id}\n"

        result_text += "\n"

    processing_time = result.get("processing_time", {})
    result_text += f"⏱️ {format_message('total_time', time=processing_time.get('total', 0))}"

    return gallery_images, result_text


def create_match_tab():
    """创建人脸识别Tab"""
    with gr.Tab(i18n("tab_recognize")):
        # 主要布局：左侧输入区+右侧结果区 (1:1)
        with gr.Row():
            # 左侧：查询人脸输入 + 匹配参数（上下排布）
            with gr.Column(scale=1):
                # 查询人脸输入
                with gr.Accordion(i18n("query_face"), open=True):
                    match_file_image = gr.Image(
                        type="pil",
                        sources=["upload", "webcam", "clipboard"],
                        label=i18n("upload_query_face"),
                        height=250
                    )
                    match_url_input = gr.Textbox(
                        label=i18n("or_input_face_url"),
                        placeholder="https://example.com/query.jpg",
                        lines=2
                    )

                # 匹配参数
                with gr.Accordion(i18n("match_params"), open=True):
                    match_person_ids = gr.Textbox(
                        label=i18n("limit_person_ids"),
                        placeholder=i18n("person_ids_placeholder"),
                        lines=2
                    )
                    match_confidence = gr.Slider(
                        0, 1, value=0.75,
                        label=i18n("confidence_threshold"),
                        info=i18n("confidence_hint")
                    )
                    match_top_k = gr.Slider(
                        1, 20, value=10, step=1,
                        label=i18n("return_count")
                    )
                    match_enable_liveness = gr.Checkbox(
                        label=i18n("enable_liveness"),
                        value=True,
                        info=i18n("liveness_hint")
                    )
                    match_save_temp = gr.Checkbox(
                        label=i18n("save_query_face"),
                        value=False,
                        info=i18n("save_query_face_hint")
                    )

                    # 识别按钮
                    with gr.Row():
                        match_file_btn = gr.Button(i18n("file_recognize"), variant="primary")
                        match_url_btn = gr.Button(i18n("url_recognize"), variant="primary")

            # 右侧：结果详情 + 查询人脸/匹配结果（上下排布）
            with gr.Column(scale=1):
                # 结果详情（最顶部）
                match_output = gr.Textbox(
                    label=i18n("result_details"),
                    lines=6,
                    max_lines=10
                )

                # 查询人脸（已标注）+ 匹配结果（左右排布 1:1）
                with gr.Row():
                    # 查询人脸
                    match_query_face = gr.Image(
                        label=i18n("query_face_cropped"),
                        height=400,
                        show_label=True
                    )

                    # 匹配结果Gallery
                    match_gallery = gr.Gallery(
                        label=i18n("match_results"),
                        columns=2,
                        height=400,
                        object_fit="contain",
                        show_label=True
                    )

        # 绑定事件
        match_file_btn.click(
            match_image_file,
            inputs=[match_file_image, match_person_ids, match_confidence, match_top_k, match_enable_liveness, match_save_temp],
            outputs=[match_query_face, match_gallery, match_output]
        )

        match_url_btn.click(
            match_image_url,
            inputs=[match_url_input, match_person_ids, match_confidence, match_top_k, match_enable_liveness, match_save_temp],
            outputs=[match_query_face, match_gallery, match_output]
        )
