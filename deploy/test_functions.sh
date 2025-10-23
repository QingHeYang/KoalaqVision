#!/bin/bash
source package.sh 2>/dev/null

# 测试版本解析
echo "=== 测试 get_base_version ==="
get_base_version "0.4.5-amd64"
get_base_version "0.4.5-arm64"
get_base_version "0.4.5"

echo ""
echo "=== 测试 parse_version_arch ==="
parse_version_arch "0.4.5-amd64"
parse_version_arch "0.4.5"

echo ""
echo "=== 测试 group_versions_by_base ==="
# 创建测试镜像tag
docker tag 775495797/koalaqvision:0.4.3 775495797/koalaqvision:0.4.5-amd64 2>/dev/null || true
docker tag 775495797/koalaqvision:0.4.3 775495797/koalaqvision:0.4.5-arm64 2>/dev/null || true
docker tag 775495797/koalaqvision:0.4.3 775495797/koalaqvision:0.4.6-amd64 2>/dev/null || true

group_versions_by_base
