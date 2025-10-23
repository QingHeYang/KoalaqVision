# KoalaqVision Performance Test Report

## 1. Face Recognition Test

### Test Dataset

- **Registered Faces**: 1,294 (Asian faces)
- **Verification Faces**: 5,485
- **Accuracy**: 100%

### Hardware Performance Test

| Hardware Platform | CPU Model | Cores | Face Model | Avg Time | Throughput |
|-------------------|-----------|-------|------------|----------|------------|
| **Intel N100** | Intel N100 @ 3.4GHz | 4 cores | buffalo_s | **268 ms** | **3.73 faces/sec** |
| **AMD Ryzen7** | Ryzen7 8845HS @ 3.8GHz | 8 cores | antelopev2 | **409 ms** | **2.44 faces/sec** |
| **RK3399** | RK3399 @ 1.4GHz | 6 cores (ARM) | buffalo_s | **1,393 ms** | **0.67 faces/sec** |

---

## 2. Object Recognition Test

> **Status**: To be added

### Test Dataset

- **Registered Objects**: To be tested
- **Verification Objects**: To be tested
- **Accuracy**: To be tested

### Hardware Performance Test

| Hardware Platform | CPU Model | Cores | Feature Model | Background Removal | Avg Time | Throughput |
|-------------------|-----------|-------|---------------|--------------------|----------|------------|
| **Intel N100** | Intel N100 @ 3.4GHz | 4 cores | DINOv3-ViTL16 | U2Net | To be tested | To be tested |
| **AMD Ryzen7** | Ryzen7 8845HS @ 3.8GHz | 8 cores | DINOv3-ViTL16 | U2Net | To be tested | To be tested |
| **RK3399** | RK3399 @ 1.4GHz | 6 cores (ARM) | DINOv3-ViTS16 | U2Net-P | To be tested | To be tested |

### Hardware Selection Recommendations

| Use Case | Recommended Hardware | Recommended Model | Performance |
|----------|---------------------|-------------------|-------------|
| **Entry-level/Edge Device** | Intel N100 | ViTS16 + U2Net-P | To be tested |
| **High-Performance Server** | Ryzen7/Xeon | ViTL16 + U2Net | To be tested |
| **ARM Device** | RK3399 | ViTS16 + U2Net-P | To be tested |

---

## Test Notes

- Test environment: LAN, negligible network latency
- Face recognition: Error samples excluded, InsightFace accuracy 100%
- Object recognition: Test data to be added

---

**Test Date**: October 2025
**Document Version**: 1.0