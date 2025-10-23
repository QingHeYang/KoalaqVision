# API Documentation

## API Overview

After starting the service, you can access:

- **Gradio UI**: http://localhost:10770/ui - Simple test interface
- **Swagger Documentation**: http://localhost:10770/docs - Interactive API documentation

All APIs return a unified JSON format:

```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "processing_time": 1.23
}
```

---

## Object Mode APIs

### Training / Registration

**POST** `/api/object/train/file`
- Register objects by uploading image files
- Use case: Add product images to database

**POST** `/api/object/train/url`
- Register objects via image URL
- Use case: Batch import from remote URLs

**DELETE** `/api/object/train/clear`
- Clear all objects from database
- Warning: This operation is irreversible

### Matching / Search

**POST** `/api/object/match/file`
- Upload image to search for similar objects
- Use case: Photo search for similar products

**POST** `/api/object/match/url`
- Search for similar objects via image URL
- Use case: Search from web images

### Object Management

**GET** `/api/object/list`
- List all registered objects
- Returns object IDs and basic information

**GET** `/api/object/{object_id}`
- Get detailed information for specified object
- Returns all images associated with this object

**DELETE** `/api/object/{object_id}`
- Delete specified object and all its images
- Use case: Remove discontinued products

### Image Management

**GET** `/api/object/image/list`
- List all registered images
- Supports pagination

**GET** `/api/object/image/stats`
- Get database statistics
- Returns totals, object counts, etc.

**GET** `/api/object/image/{image_id}`
- Get detailed information for specified image
- Returns image URL and feature metadata

**DELETE** `/api/object/image/{image_id}`
- Delete specified image
- Use case: Remove poor quality images

---

## Face Mode APIs

### Training / Registration

**POST** `/api/face/train/file`
- Register face by uploading image file
- Supports liveness detection (anti-spoofing)

**POST** `/api/face/train/url`
- Register face via image URL
- Use case: Batch import employee photos

**DELETE** `/api/face/train/clear`
- Clear all face data from database
- Warning: This operation is irreversible

### Matching / Recognition

**POST** `/api/face/match/file`
- Upload image for face recognition (1:N search)
- Returns Top-K most similar persons

**POST** `/api/face/match/url`
- Face recognition via image URL
- Use case: Recognition from surveillance cameras

### Person Management

**GET** `/api/face/person/list`
- List all registered persons
- Supports pagination and filtering

**GET** `/api/face/person/{person_id}`
- Get detailed information for specified person
- Returns all face images for this person

**DELETE** `/api/face/person/{person_id}`
- Delete specified person and all face images
- Use case: Remove departed employees

**GET** `/api/face/person/stats/summary`
- Get database statistics summary
- Returns total persons, images, distribution

### Image Management

**GET** `/api/face/image/`
- List all registered face images
- Supports pagination

**GET** `/api/face/image/{image_id}`
- Get detailed information for specified face image
- Returns face box, landmarks, confidence, etc.

**DELETE** `/api/face/image/{image_id}`
- Delete specified face image
- Use case: Remove low quality photos

---

## Rate Limiting

Currently no rate limiting. For production deployment, it's recommended to implement rate limiting at the reverse proxy layer (e.g., Nginx).

---

## Authentication

Current APIs don't require authentication. For production deployment, consider implementing:
- API Key authentication
- JWT Token
- OAuth2

To add authentication, add middleware in `app/main.py`.