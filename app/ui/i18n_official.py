"""
Gradio官方i18n实现
使用gr.I18n类实现自动语言检测和切换
"""
import gradio as gr

# 定义翻译字典
translations = {
    # 英文翻译
    "en": {
        # 主界面 - Object Mode
        "app_title": "KoalaqVision",
        "app_subtitle": "Image Retrieval System - Built with DINOv3 (Meta AI)",

        # 主界面 - Face Mode
        "app_title_face": "KoalaqVision Face Recognition",
        "app_subtitle_face": "Face Recognition System - Powered by InsightFace",

        # Tab标签 - Object Mode
        "tab_train": "Train",
        "tab_match": "Match",
        "tab_object": "Objects",
        "tab_image": "Images",

        # Tab标签 - Face Mode
        "tab_register": "Register",
        "tab_recognize": "Recognize",
        "tab_persons": "Persons",
        "tab_face_images": "Face Images",

        # 训练模块
        "upload_image": "Upload Image",
        "or_input_url": "Or Input Image URL",
        "train_params": "Training Parameters",
        "object_id": "Object ID",
        "object_id_placeholder": "e.g. product_001",
        "save_files": "Save Files",
        "file_train": "File Train",
        "url_train": "URL Train",
        "original_image": "Original",
        "object_image": "Object (Background Removed)",
        "result": "Result",

        # 匹配模块
        "query_image": "Query Image",
        "upload_query_image": "Upload Query Image",
        "or_input_url": "Or Input Image URL",
        "match_params": "Match Parameters",
        "limit_object_ids": "Limit to Object IDs (Optional)",
        "object_ids_placeholder": "Comma-separated, e.g. 777,888,999. Leave empty to search all",
        "confidence_threshold": "Confidence Threshold",
        "return_count": "Return Count",
        "save_query_image": "Save Query Image",
        "save_query_image_hint": "Save query object image (background removed) to temp/match directory",
        "file_match": "File Match",
        "url_match": "URL Match",
        "query_object_image": "Query Object (Background Removed)",
        "match_results": "Match Results",
        "result_details": "Result Details",

        # 物品管理
        "object_management": "Object Management",
        "object_list": "Object List",
        "get_list": "Get List",
        "refresh_list": "🔄 Refresh List",
        "object_detail": "Object Detail",
        "object_images": "Object Images",
        "query": "Query",
        "delete_object": "Delete Object",
        "delete_button": "Delete",
        "delete_unrecoverable": "Delete (Permanent)",
        "no_objects": "No objects",
        "object_id_col": "Object ID",
        "image_count_col": "Image Count",
        "deleted_object_images": "Deleted {count} images of object {id}",
        "search_object_placeholder": "Enter object ID to search",
        "selected_object": "Selected Object",
        "click_to_select_object": "Click table to select object",
        "object_info": "Object Info",
        "image_details": "Image Details",
        "image_count": "Image Count",

        # 图片管理
        "image_management": "Image Management",
        "statistics": "Statistics",
        "refresh_stats": "🔄 Refresh Stats",
        "database_status": "Database Status",
        "total_images": "Total Images",
        "total_objects": "Total Objects",
        "vector_dimension": "Vector Dimension",
        "image_list": "Image List",
        "page_size": "Page Size",
        "page_number": "Page",
        "page_info_text": "Page Info",
        "single_query": "Single Query",
        "image_id": "Image ID",
        "image_id_placeholder": "e.g. ce0510e2-...",
        "image_preview": "Image Preview",
        "details": "Details",
        "delete_image": "Delete Image",
        "image_not_exist": "Image does not exist",
        "deleted_image": "Deleted image {id}",
        "image_not_found": "Image {id} not found",
        "created_time": "Created At",

        # 结果消息
        "upload_image_and_id": "Please upload image and enter object ID",
        "input_url_and_id": "Please enter image URL and object ID",
        "input_urls_and_id": "Please enter URL list and object ID",
        "no_valid_urls": "No valid URLs",
        "train_success": "Training successful!",
        "batch_train_complete": "Batch training complete!",
        "total": "Total",
        "success": "Success",
        "upload_query_image_msg": "Please upload query image",
        "input_image_url_msg": "Please enter image URL",
        "found_matches": "Found {count} matching objects",
        "object_similarity": "Object {id}: Similarity {sim:.3f}",
        "total_time": "Total time: {time:.2f}s",
        "input_object_id_msg": "Please enter object ID",
        "no_images_for_object": "Object {id} has no images",
        "object_with_images": "Object {id}\n{count} images total",
        "page_info": "Page {page} ({size} per page)\nTotal: {total} images",
        "no_images_on_page": "No images on page {page}",
        "input_image_id_msg": "Please enter image ID",
        "confirm_delete": "Confirm delete object {id}?",
        "deleted": "Deleted",
        "error": "Error",

        # Face Register Tab
        "register_single_file": "Single Face Registration",
        "register_single_url": "Single URL Registration",
        "upload_face": "Upload Face",
        "register_params": "Register Parameters",
        "person_id": "Person ID",
        "person_id_placeholder": "e.g. Alice",
        "upload_face_image": "Upload Face Image",
        "enable_liveness": "Enable Liveness Detection",
        "liveness_hint": "(Anti-spoofing)",
        "register_button": "Register",
        "file_register": "File Register",
        "url_register": "URL Register",
        "face_image_cropped": "Face (Cropped)",
        "register_success": "Registration successful!",
        "upload_face_and_id": "Please upload face image and enter person ID",
        "input_face_url_and_id": "Please enter face image URL and person ID",
        "upload_face_image_required": "Please upload face image",
        "person_id_required": "Please enter person ID",
        "face_url_required": "Please enter face image URL",

        # Face Recognize Tab
        "query_face": "Query Face",
        "upload_query_face": "Upload Face Image",
        "or_input_face_url": "Or Input Image URL",
        "limit_person_ids": "Limit to Person IDs (Optional)",
        "person_ids_placeholder": "Comma-separated, e.g. Alice,Bob,Charlie",
        "confidence_hint": "(Recommended: 0.75 or above)",
        "return_count": "Top K (Max Persons)",
        "save_query_face": "Save Query Face",
        "save_query_face_hint": "Save query image with face bbox to temp/match directory",
        "file_recognize": "File Recognize",
        "url_recognize": "URL Recognize",
        "query_face_cropped": "Query Face (Detected)",
        "match_results": "Match Results",
        "result_details": "Result Details",
        "upload_query_face_msg": "Please upload query face image",
        "input_face_url_msg": "Please enter face image URL",
        "liveness_passed": "Liveness: ✅ Real Face",
        "liveness_failed": "Liveness: ❌ Fake Face",
        "liveness_score": "Score: {score:.4f}",
        "found_persons": "Found {count} matching persons",
        "person_similarity": "Person {id}: {sim:.3f}",

        # Face Person Management Tab
        "search_person": "Search Person",
        "search_person_placeholder": "Enter person ID to search",
        "search_button": "Search",
        "person_id_col": "Person ID",
        "face_count_col": "Face Count",
        "created_time_col": "Registered At",
        "person_list": "Person List",
        "selected_person": "Selected Person",
        "click_to_select": "Click table to select person",
        "view_details": "View Details",
        "delete_person": "Delete Person",
        "operation_result": "Operation Result",
        "person_info": "Person Info",
        "face_images": "Face Images",
        "face_details": "Face Details",
        "face_count": "Face Count",
        "no_faces_for_person": "Person {id} has no faces",
        "deleted_person_faces": "Deleted {count} faces of person {id}",
        "confirm_delete_person": "⚠️ Confirm delete person {id}? This operation cannot be undone!",
        "delete_confirm_input": "Type 'delete' to confirm",
        "delete_confirm_required": "Please type 'delete' in the confirmation box to proceed with deletion.",

        # Face Image Management Tab
        "face_operations": "Face Operations",
        "click_gallery_or_input": "Click gallery image or input manually",
        "found_n_faces": "Found {count} faces",
        "image_id_required": "Please enter image ID",

        # Gradio 内置组件翻译
        "image.upload_file": "Upload file",
        "image.drop_image": "Drop image here",
        "image.click_to_upload": "Click to upload",
        "image.clear": "Clear",
        "image.webcam": "Webcam",
        "image.no_webcam_support": "No webcam support",
    },

    # 中文翻译（注意：gr.I18n使用zh而不是zh_CN）
    "zh": {
        # 主界面 - Object Mode
        "app_title": "KoalaqVision",
        "app_subtitle": "图像检索系统 - Built with DINOv3 (Meta AI)",

        # 主界面 - Face Mode
        "app_title_face": "KoalaqVision 人脸识别",
        "app_subtitle_face": "人脸识别系统 - 基于 InsightFace  模型",

        # Tab标签 - Object Mode
        "tab_train": "训练",
        "tab_match": "匹配",
        "tab_object": "物品管理",
        "tab_image": "图片管理",

        # Tab标签 - Face Mode
        "tab_register": "注册",
        "tab_recognize": "识别",
        "tab_persons": "人员管理",
        "tab_face_images": "人脸管理",

        # 训练模块
        "upload_image": "上传图片",
        "or_input_url": "或输入图片URL",
        "train_params": "训练参数",
        "object_id": "物品ID",
        "object_id_placeholder": "例如: product_001",
        "save_files": "保存文件",
        "file_train": "文件训练",
        "url_train": "URL训练",
        "original_image": "原图",
        "object_image": "Object图（去背景）",
        "result": "结果",

        # 匹配模块
        "query_image": "查询图片",
        "upload_query_image": "上传查询图片",
        "or_input_url": "或输入图片URL",
        "match_params": "匹配参数",
        "limit_object_ids": "限定物品ID（可选）",
        "object_ids_placeholder": "逗号分隔，例如: 777,888,999 留空则搜索全部",
        "confidence_threshold": "置信度阈值",
        "return_count": "返回数量",
        "save_query_image": "保存查询图片",
        "save_query_image_hint": "保存查询物品去背景图片到 temp/match 目录",
        "file_match": "文件匹配",
        "url_match": "URL匹配",
        "query_object_image": "查询图片Object（去背景）",
        "match_results": "匹配结果",
        "result_details": "结果详情",

        # 物品管理
        "object_management": "物品管理",
        "object_list": "物品列表",
        "get_list": "获取列表",
        "refresh_list": "🔄 刷新列表",
        "object_detail": "物品详情",
        "object_images": "物品图片",
        "query": "查询",
        "delete_object": "删除物品",
        "delete_button": "删除",
        "delete_unrecoverable": "删除（不可恢复）",
        "no_objects": "暂无物品",
        "object_id_col": "物品ID",
        "image_count_col": "图片数",
        "deleted_object_images": "已删除物品 {id} 的 {count} 张图片",
        "search_object_placeholder": "输入物品ID搜索",
        "selected_object": "选中物品",
        "click_to_select_object": "点击表格选择物品",
        "object_info": "物品信息",
        "image_details": "图片详情",
        "image_count": "图片数量",

        # 图片管理
        "image_management": "图片管理",
        "statistics": "统计信息",
        "refresh_stats": "🔄 刷新统计",
        "database_status": "数据库状态",
        "total_images": "总图片数",
        "total_objects": "总物品数",
        "vector_dimension": "向量维度",
        "image_list": "图片列表",
        "page_size": "每页显示",
        "page_number": "页码",
        "page_info_text": "分页信息",
        "single_query": "单张查询",
        "image_id": "图片ID",
        "image_id_placeholder": "例如: ce0510e2-...",
        "image_preview": "图片预览",
        "details": "详情",
        "delete_image": "删除图片",
        "image_not_exist": "图片不存在",
        "deleted_image": "已删除图片 {id}",
        "image_not_found": "图片 {id} 不存在",
        "created_time": "创建时间",

        # 结果消息
        "upload_image_and_id": "请上传图片并输入物品ID",
        "input_url_and_id": "请输入图片URL和物品ID",
        "input_urls_and_id": "请输入URL列表和物品ID",
        "no_valid_urls": "没有有效的URL",
        "train_success": "训练成功！",
        "batch_train_complete": "批量训练完成！",
        "total": "总数",
        "success": "成功",
        "upload_query_image_msg": "请上传查询图片",
        "input_image_url_msg": "请输入图片URL",
        "found_matches": "找到 {count} 个匹配物品",
        "object_similarity": "物品 {id}: 相似度 {sim:.3f}",
        "total_time": "总耗时: {time:.2f}s",
        "input_object_id_msg": "请输入物品ID",
        "no_images_for_object": "物品 {id} 没有图片",
        "object_with_images": "物品 {id}\n共 {count} 张图片",
        "page_info": "第 {page} 页 (每页 {size} 张)\n共 {total} 张图片",
        "no_images_on_page": "第 {page} 页没有图片",
        "input_image_id_msg": "请输入图片ID",
        "confirm_delete": "确认删除物品 {id}？",
        "deleted": "已删除",
        "error": "错误",

        # Face Register Tab
        "register_single_file": "单文件人脸注册",
        "register_single_url": "单URL人脸注册",
        "upload_face": "上传人脸",
        "register_params": "注册参数",
        "person_id": "人员ID",
        "person_id_placeholder": "例如: Alice",
        "upload_face_image": "上传人脸图片",
        "enable_liveness": "启用活体检测",
        "liveness_hint": "（防伪检测）",
        "register_button": "注册",
        "file_register": "文件注册",
        "url_register": "URL注册",
        "face_image_cropped": "人脸图（裁剪）",
        "register_success": "注册成功！",
        "upload_face_and_id": "请上传人脸图片并输入人员ID",
        "input_face_url_and_id": "请输入人脸图片URL和人员ID",
        "upload_face_image_required": "请上传人脸图片",
        "person_id_required": "请输入人员ID",
        "face_url_required": "请输入人脸图片URL",

        # Face Recognize Tab
        "query_face": "查询人脸",
        "upload_query_face": "上传人脸图片",
        "or_input_face_url": "或输入图片URL",
        "limit_person_ids": "限定人员ID（可选）",
        "person_ids_placeholder": "逗号分隔，例如: Alice,Bob,Charlie",
        "confidence_hint": "（推荐: 0.75 以上）",
        "return_count": "Top K（最多返回人数）",
        "save_query_face": "保存查询人脸",
        "save_query_face_hint": "保存带人脸框的查询图片到 temp/match 目录",
        "file_recognize": "文件识别",
        "url_recognize": "URL识别",
        "query_face_cropped": "查询人脸（已标注）",
        "match_results": "匹配结果",
        "result_details": "结果详情",
        "upload_query_face_msg": "请上传查询人脸图片",
        "input_face_url_msg": "请输入人脸图片URL",
        "liveness_passed": "活体检测: ✅ 真人",
        "liveness_failed": "活体检测: ❌ 假脸",
        "liveness_score": "分数: {score:.4f}",
        "found_persons": "找到 {count} 个匹配人员",
        "person_similarity": "人员 {id}: {sim:.3f}",

        # Face Person Management Tab
        "search_person": "搜索人员",
        "search_person_placeholder": "输入人员ID搜索",
        "search_button": "搜索",
        "person_id_col": "人员ID",
        "face_count_col": "人脸数量",
        "created_time_col": "入库时间",
        "person_list": "人员列表",
        "selected_person": "选中人员",
        "click_to_select": "点击表格选择人员",
        "view_details": "查看详情",
        "delete_person": "删除人员",
        "operation_result": "操作结果",
        "person_info": "人员信息",
        "face_images": "人脸图片",
        "face_details": "人脸详情",
        "face_count": "人脸数量",
        "no_faces_for_person": "人员 {id} 没有人脸",
        "deleted_person_faces": "已删除人员 {id} 的 {count} 张人脸",
        "confirm_delete_person": "⚠️ 确认删除人员 {id}？此操作无法恢复！",
        "delete_confirm_input": "输入 'delete' 确认删除",
        "delete_confirm_required": "请在确认框中输入 'delete' 以继续删除操作。",

        # Face Image Management Tab
        "face_operations": "人脸操作",
        "click_gallery_or_input": "点击图片或手动输入",
        "found_n_faces": "找到 {count} 张人脸",
        "image_id_required": "请输入图片ID",

        # Gradio 内置组件翻译
        "image.upload_file": "上传文件",
        "image.drop_image": "拖拽图片到此处",
        "image.click_to_upload": "点击上传",
        "image.clear": "清除",
        "image.webcam": "摄像头",
        "image.no_webcam_support": "不支持摄像头",
    }
}

# 创建官方i18n实例
i18n = gr.I18n(**translations)

def get_i18n_dict(lang="en"):
    """
    获取指定语言的翻译字典（用于后端动态文本）

    Args:
        lang: 语言代码 ("en" 或 "zh")

    Returns:
        对应语言的翻译字典
    """
    if lang == "zh":
        return translations.get("zh", {})
    return translations.get("en", {})

def format_message(key, lang="en", **kwargs):
    """
    格式化带参数的消息（用于后端动态文本）

    Args:
        key: 翻译键
        lang: 语言代码
        **kwargs: 格式化参数

    Returns:
        格式化后的消息
    """
    translations = get_i18n_dict(lang)
    text = translations.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text