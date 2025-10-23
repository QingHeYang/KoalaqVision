# API 接口文档

## API 概览

启动服务后，可以访问：

- **Gradio UI**: http://localhost:10770/ui - 简单的测试界面
- **Swagger 文档**: http://localhost:10770/docs - 交互式 API 文档

所有 API 返回统一的 JSON 格式：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "processing_time": 1.23
}
```

---

## Object Mode APIs（物品模式）

### 训练 / 录入

**POST** `/api/object/train/file`
- 通过上传图片文件注册物品
- 应用场景：添加商品图片到数据库

**POST** `/api/object/train/url`
- 通过图片 URL 注册物品
- 应用场景：从远程 URL 批量导入

**DELETE** `/api/object/train/clear`
- 清空数据库中的所有物品
- 警告：此操作不可撤销

### 匹配 / 搜索

**POST** `/api/object/match/file`
- 上传图片搜索相似物品
- 应用场景：拍照搜索同款商品

**POST** `/api/object/match/url`
- 通过图片 URL 搜索相似物品
- 应用场景：从网络图片搜索

### 物品管理

**GET** `/api/object/list`
- 列出所有已注册的物品
- 返回物品 ID 和基本信息

**GET** `/api/object/{object_id}`
- 获取指定物品的详细信息
- 返回该物品关联的所有图片

**DELETE** `/api/object/{object_id}`
- 删除指定物品及其所有图片
- 应用场景：删除已下架的商品

### 图片管理

**GET** `/api/object/image/list`
- 列出所有已注册的图片
- 支持分页

**GET** `/api/object/image/stats`
- 获取数据库统计信息
- 返回总数、物品数等

**GET** `/api/object/image/{image_id}`
- 获取指定图片的详细信息
- 返回图片 URL 和特征元数据

**DELETE** `/api/object/image/{image_id}`
- 删除指定图片
- 应用场景：删除质量不佳的图片

---

## Face Mode APIs（人脸模式）

### 训练 / 录入

**POST** `/api/face/train/file`
- 通过上传图片文件注册人脸
- 支持活体检测（防翻拍）

**POST** `/api/face/train/url`
- 通过图片 URL 注册人脸
- 应用场景：批量导入员工照片

**DELETE** `/api/face/train/clear`
- 清空数据库中的所有人脸数据
- 警告：此操作不可撤销

### 匹配 / 识别

**POST** `/api/face/match/file`
- 上传图片进行人脸识别（1:N 搜索）
- 返回最相似的 Top-K 个人员

**POST** `/api/face/match/url`
- 通过图片 URL 进行人脸识别
- 应用场景：从监控摄像头识别

### 人员管理

**GET** `/api/face/person/list`
- 列出所有已注册的人员
- 支持分页和筛选

**GET** `/api/face/person/{person_id}`
- 获取指定人员的详细信息
- 返回该人员的所有人脸图片

**DELETE** `/api/face/person/{person_id}`
- 删除指定人员及其所有人脸图片
- 应用场景：删除离职员工

**GET** `/api/face/person/stats/summary`
- 获取数据库统计摘要
- 返回总人数、图片数、分布情况

### 图片管理

**GET** `/api/face/image/`
- 列出所有已注册的人脸图片
- 支持分页

**GET** `/api/face/image/{image_id}`
- 获取指定人脸图片的详细信息
- 返回人脸框、关键点、置信度等

**DELETE** `/api/face/image/{image_id}`
- 删除指定人脸图片
- 应用场景：删除低质量照片

---

## 频率限制

当前没有频率限制。生产环境部署时，建议在反向代理层（如 Nginx）实现频率限制。

---

## 身份验证

当前 API 不需要身份验证。生产环境部署时，建议实现：
- API Key 认证
- JWT Token
- OAuth2

如需添加身份验证，可在 `app/main.py` 中添加中间件。
