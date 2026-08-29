#!/bin/bash
set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 双包结构：只发布壳包 yuppie-mcp-google-sheets 到 PyPI
# 库包 yuppie-google-sheets 仅 GitHub 分发，不发布
SHELL_PKG_DIR="packages/yuppie-mcp-google-sheets"
SHELL_PYPROJECT="${SHELL_PKG_DIR}/pyproject.toml"
SHELL_INIT="${SHELL_PKG_DIR}/src/yuppie_mcp_google_sheets/__init__.py"

echo -e "${GREEN}=== PyPI 发布脚本（壳包 yuppie-mcp-google-sheets）===${NC}"

# 检查 token
if [ -z "$UV_PUBLISH_TOKEN" ]; then
    echo -e "${RED}错误: 未设置 UV_PUBLISH_TOKEN 环境变量${NC}"
    echo "请设置 PyPI API Token:"
    echo "  export UV_PUBLISH_TOKEN='pypi-你的token'"
    exit 1
fi

# 检查版本号
CURRENT_VERSION=$(grep '^version = ' "${SHELL_PYPROJECT}" | sed 's/version = "\(.*\)"/\1/')
echo -e "${YELLOW}当前版本: ${CURRENT_VERSION}${NC}"

# 提示输入新版本
read -p "请输入新版本号 (当前: ${CURRENT_VERSION}): " NEW_VERSION

if [ -z "$NEW_VERSION" ]; then
    NEW_VERSION=$CURRENT_VERSION
    echo -e "${YELLOW}使用当前版本: ${NEW_VERSION}${NC}"
fi

# 更新版本号（同步两处）
sed -i '' "s/^version = .*/version = \"${NEW_VERSION}\"/" "${SHELL_PYPROJECT}"
sed -i '' "s/__version__ = .*/__version__ = \"${NEW_VERSION}\"/" "${SHELL_INIT}"
echo -e "${GREEN}✓ 版本号已更新为 ${NEW_VERSION}${NC}"

# 确认发布
echo -e "${YELLOW}即将发布到 PyPI:${NC}"
echo "  包名: yuppie-mcp-google-sheets"
echo "  版本: ${NEW_VERSION}"
read -p "确认发布? (y/N): " CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "${RED}发布已取消${NC}"
    exit 1
fi

# 清理旧构建产物
rm -rf "${SHELL_PKG_DIR}/dist/"
echo -e "${GREEN}正在构建（hatch 原地构建，保证 force-include 的 ../ 相对路径有效）...${NC}"
(cd "${SHELL_PKG_DIR}" && uvx hatch build)

# 校验 wheel 已 vendor 库代码
WHEEL=$(ls "${SHELL_PKG_DIR}"/dist/yuppie_mcp_google_sheets-*.whl)
VENDOR_COUNT=$(unzip -l "$WHEEL" | grep -c yuppie_google_sheets || true)
if [ "$VENDOR_COUNT" -eq 0 ]; then
    echo -e "${RED}错误: wheel 未包含 vendor 的 yuppie_google_sheets，中止发布${NC}"
    exit 1
fi
echo -e "${GREEN}✓ wheel 已 vendor ${VENDOR_COUNT} 个库文件${NC}"

# 发布（只发壳包 dist 目录）
echo -e "${GREEN}正在发布到 PyPI...${NC}"
UV_PUBLISH_TOKEN="$UV_PUBLISH_TOKEN" uv publish "${SHELL_PKG_DIR}/dist/"*

# tag 流程：库包 yuppie-google-sheets 仅 GitHub 分发，用户通过 @tag 锁定版本
TAG="v${NEW_VERSION}"
echo -e "${GREEN}正在处理 tag ${TAG} ...${NC}"
if git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null; then
    echo -e "${YELLOW}tag ${TAG} 已存在，跳过${NC}"
else
    read -p "创建并推送 tag ${TAG}？(Y/n): " TAG_CONFIRM
    if [[ ! "$TAG_CONFIRM" =~ ^[Nn]$ ]]; then
        LIB_VERSION=$(grep '^version = ' "packages/yuppie-google-sheets/pyproject.toml" | sed 's/version = "\(.*\)"/\1/')
        git tag -a "${TAG}" -m "yuppie-mcp-google-sheets ${NEW_VERSION} + yuppie-google-sheets ${LIB_VERSION}"
        git push origin "${TAG}"
        echo -e "${GREEN}✓ tag ${TAG} 已推送${NC}"
    else
        echo -e "${YELLOW}已跳过 tag（注意：库包用户将无法通过 @${TAG} 锁定本版本）${NC}"
    fi
fi

echo -e "${GREEN}=== 发布完成 ===${NC}"
echo -e "${GREEN}查看: https://pypi.org/project/yuppie-mcp-google-sheets/${NC}"
