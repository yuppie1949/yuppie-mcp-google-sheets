#!/bin/bash
set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 双包结构：库包 yuppie-google-sheets（PyPI）+ 壳包 yuppie-mcp-google-sheets（PyPI，依赖库包）
LIB_PKG_DIR="packages/yuppie-google-sheets"
SHELL_PKG_DIR="packages/yuppie-mcp-google-sheets"
SHELL_PYPROJECT="${SHELL_PKG_DIR}/pyproject.toml"
SHELL_INIT="${SHELL_PKG_DIR}/src/yuppie_mcp_google_sheets/__init__.py"

echo -e "${GREEN}=== PyPI 发布脚本（库包 + 壳包）===${NC}"

# 检查 token
if [ -z "$UV_PUBLISH_TOKEN" ]; then
    echo -e "${RED}错误: 未设置 UV_PUBLISH_TOKEN 环境变量${NC}"
    echo "请设置 PyPI API Token:"
    echo "  export UV_PUBLISH_TOKEN='pypi-你的token'"
    exit 1
fi

# ── 壳包版本 ──
CURRENT_VERSION=$(grep '^version = ' "${SHELL_PYPROJECT}" | sed 's/version = "\(.*\)"/\1/')
echo -e "${YELLOW}壳包当前版本: ${CURRENT_VERSION}${NC}"
read -p "壳包新版本号 (当前: ${CURRENT_VERSION}): " NEW_VERSION
if [ -z "$NEW_VERSION" ]; then
    NEW_VERSION=$CURRENT_VERSION
    echo -e "${YELLOW}壳包使用当前版本: ${NEW_VERSION}${NC}"
fi

# ── 库包版本 ──
LIB_VERSION=$(grep '^version = ' "${LIB_PKG_DIR}/pyproject.toml" | sed 's/version = "\(.*\)"/\1/')
read -p "库包是否也要发版？(当前: ${LIB_VERSION}) 输入新版本号直接发布，回车跳过: " NEW_LIB_VERSION
PUBLISH_LIB=0
if [ -n "$NEW_LIB_VERSION" ] && [ "$NEW_LIB_VERSION" != "$LIB_VERSION" ]; then
    PUBLISH_LIB=1
    sed -i '' "s/^version = .*/version = \"${NEW_LIB_VERSION}\"/" "${LIB_PKG_DIR}/pyproject.toml"
    sed -i '' "s/__version__ = .*/__version__ = \"${NEW_LIB_VERSION}\"/" "${LIB_PKG_DIR}/src/yuppie_google_sheets/__init__.py"
    LIB_VERSION="${NEW_LIB_VERSION}"
elif [ -n "$NEW_LIB_VERSION" ] && [ "$NEW_LIB_VERSION" = "$LIB_VERSION" ]; then
    PUBLISH_LIB=1  # 版本未变但要求重发（一般会 403，PyPI 不允许覆盖）
fi

# ── 壳包版本号更新 + 提交 ──
sed -i '' "s/^version = .*/version = \"${NEW_VERSION}\"/" "${SHELL_PYPROJECT}"
sed -i '' "s/__version__ = .*/__version__ = \"${NEW_VERSION}\"/" "${SHELL_INIT}"

# 提交版本 bump（tag 必须指向包含该版本号的提交）
git add "${SHELL_PYPROJECT}" "${SHELL_INIT}" "${LIB_PKG_DIR}/pyproject.toml" "${LIB_PKG_DIR}/src/yuppie_google_sheets/__init__.py"
if ! git diff --cached --quiet; then
    git commit -q -m "chore: bump 版本（壳包 ${NEW_VERSION} + 库包 ${LIB_VERSION}）"
    echo -e "${GREEN}✓ 版本 bump 已提交${NC}"
fi

# ── 确认发布 ──
echo -e "${YELLOW}即将发布到 PyPI:${NC}"
[ "$PUBLISH_LIB" = "1" ] && echo "  库包: yuppie-google-sheets ${LIB_VERSION}"
echo "  壳包: yuppie-mcp-google-sheets ${NEW_VERSION}"
read -p "确认发布? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "${RED}发布已取消${NC}"
    exit 1
fi

# ── 构建：库包先发（壳包依赖它）──
rm -rf dist/
if [ "$PUBLISH_LIB" = "1" ]; then
    echo -e "${GREEN}构建库包...${NC}"
    uv build "${LIB_PKG_DIR}"
    echo -e "${GREEN}发布库包...${NC}"
    UV_PUBLISH_TOKEN="$UV_PUBLISH_TOKEN" uv publish dist/yuppie_google_sheets-*
fi

echo -e "${GREEN}构建壳包...${NC}"
uv build "${SHELL_PKG_DIR}"
echo -e "${GREEN}发布壳包...${NC}"
UV_PUBLISH_TOKEN="$UV_PUBLISH_TOKEN" uv publish dist/yuppie_mcp_google_sheets-*

# ── tag：单一序列，与壳包版本对齐 ──
TAG="v${NEW_VERSION}"
echo -e "${GREEN}正在处理 tag ${TAG} ...${NC}"
if git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null; then
    echo -e "${YELLOW}tag ${TAG} 已存在，跳过${NC}"
else
    read -p "创建并推送 tag ${TAG}？(Y/n): " TAG_CONFIRM
    if [[ ! "$TAG_CONFIRM" =~ ^[Nn]$ ]]; then
        git tag -a "${TAG}" -m "yuppie-mcp-google-sheets ${NEW_VERSION} + yuppie-google-sheets ${LIB_VERSION}"
        git push origin "${TAG}"
        echo -e "${GREEN}✓ tag ${TAG} 已推送${NC}"
    else
        echo -e "${YELLOW}已跳过 tag${NC}"
    fi
fi

echo -e "${GREEN}=== 发布完成 ===${NC}"
echo -e "${GREEN}  https://pypi.org/project/yuppie-mcp-google-sheets/${NC}"
echo -e "${GREEN}  https://pypi.org/project/yuppie-google-sheets/${NC}"
