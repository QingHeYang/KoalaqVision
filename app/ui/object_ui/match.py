"""
匹配模块 - 对齐 /api/match 端点
"""
import gradio as gr
from app.services.object_service import object_service
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


def match_image_file(image, object_ids: str, confidence: float, top_k: int, save_temp: bool):
    """文件匹配 - 对齐 POST /api/match/file"""
    if not image:
        gr.Warning(format_message('upload_query_image_msg'))
        return None, None, ""

    try:
        object_id_list = None
        if object_ids and object_ids.strip():
            object_id_list = [id.strip() for id in object_ids.split(",") if id.strip()]

        result = object_service.match_image(
            image_source=image,
            save_temp=save_temp,
            object_ids=object_id_list,
            confidence=confidence,
            top_k=top_k
        )

        gallery, text = _process_match_result(result)
        # 返回查询图片的object图（文件路径，不是URL）
        query_object_path = result.get("temp_path")  # 这已经是文件路径

        gr.Info(format_message('found_matches', count=len(result.get("grouped_matches", []))))
        return query_object_path, gallery, text

    except Exception as e:
        gr.Error(f"{format_message('error')}: {str(e)}")
        return None, None, f"❌ {format_message('error')}: {str(e)}"


def match_image_url(url: str, object_ids: str, confidence: float, top_k: int, save_temp: bool):
    """URL匹配 - 对齐 POST /api/match/url"""
    if not url or not url.strip():
        gr.Warning(format_message('input_image_url_msg'))
        return None, None, ""

    try:
        object_id_list = None
        if object_ids and object_ids.strip():
            object_id_list = [id.strip() for id in object_ids.split(",") if id.strip()]

        result = object_service.match_image(
            image_source=url,
            save_temp=save_temp,
            object_ids=object_id_list,
            confidence=confidence,
            top_k=top_k
        )

        gallery, text = _process_match_result(result)
        # 返回查询图片的object图（文件路径，不是URL）
        query_object_path = result.get("temp_path")  # 这已经是文件路径

        gr.Info(format_message('found_matches', count=len(result.get("grouped_matches", []))))
        return query_object_path, gallery, text

    except Exception as e:
        gr.Error(f"{format_message('error')}: {str(e)}")
        return None, None, f"❌ {format_message('error')}: {str(e)}"


def _process_match_result(result):
    """处理匹配结果，转换为Gallery格式"""
    matches = result.get("grouped_matches", [])

    gallery_images = []
    result_text = f"✅ {format_message('found_matches', count=len(matches))}\n\n"

    for match in matches:
        obj_id = match["object_id"]
        max_sim = match["max_similarity"]
        result_text += f"{format_message('object_similarity', id=obj_id, sim=max_sim)}\n"

        for img in match["images"]:
            img_url = img.get("img_object_url") or img.get("img_url")
            if img_url:
                # 将URL转换为文件路径（Gradio需要文件路径）
                img_path = _url_to_path(img_url)
                caption = f"{obj_id} - {img['similarity']:.3f}"
                gallery_images.append((img_path, caption))

    processing_time = result.get("processing_time", {})
    result_text += f"\n⏱️ {format_message('total_time', time=processing_time.get('total', 0))}"

    return gallery_images, result_text


def create_match_tab():
    """创建匹配Tab"""
    with gr.Tab(i18n("tab_match")):
        # 主布局：左侧查询输入 + 右侧结果 (1:1)
        with gr.Row():
            # 左侧：查询图片 + 匹配参数
            with gr.Column(scale=1):
                # 查询图片输入
                with gr.Accordion(i18n("query_image"), open=True):
                    match_file_image = gr.Image(
                        type="pil",
                        sources=["upload", "webcam", "clipboard"],
                        label=i18n("upload_query_image"),
                        height=250
                    )
                    match_url_input = gr.Textbox(
                        label=i18n("or_input_url"),
                        placeholder="https://example.com/query.jpg",
                        lines=2
                    )

                # 匹配参数
                with gr.Accordion(i18n("match_params"), open=True):
                    match_obj_ids = gr.Textbox(
                        label=i18n("limit_object_ids"),
                        placeholder=i18n("object_ids_placeholder"),
                        lines=2
                    )
                    match_confidence = gr.Slider(0, 1, value=0.7, label=i18n("confidence_threshold"))
                    match_top_k = gr.Slider(1, 20, value=5, step=1, label=i18n("return_count"))
                    match_save_temp = gr.Checkbox(
                        label=i18n("save_query_image"),
                        value=False,
                        info=i18n("save_query_image_hint")
                    )

                    # 匹配按钮
                    with gr.Row():
                        match_file_btn = gr.Button(i18n("file_match"), variant="primary")
                        match_url_btn = gr.Button(i18n("url_match"), variant="primary")

            # 右侧：结果栏
            with gr.Column(scale=1):
                # 查询结果文本（上方）
                match_output = gr.Textbox(
                    label=i18n("result_details"),
                    lines=8,
                    max_lines=15
                )

                # 两张图片并列（下方）
                with gr.Row():
                    # 查询图片Object
                    match_query_object = gr.Image(
                        label=i18n("query_object_image"),
                        height=400
                    )
                    # 匹配结果Gallery
                    match_gallery = gr.Gallery(
                        label=i18n("match_results"),
                        columns=2,
                        height=400,
                        object_fit="contain"
                    )

        match_file_btn.click(
            match_image_file,
            inputs=[match_file_image, match_obj_ids, match_confidence, match_top_k, match_save_temp],
            outputs=[match_query_object, match_gallery, match_output]
        )

        match_url_btn.click(
            match_image_url,
            inputs=[match_url_input, match_obj_ids, match_confidence, match_top_k, match_save_temp],
            outputs=[match_query_object, match_gallery, match_output]
        )
