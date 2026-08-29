# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## 项目概述

本仓库是 **uv workspace 双包**结构：

| 包 | 分发 | 职责 |
|----|------|------|
| `packages/yuppie-google-sheets` | 仅 GitHub（`git+...#subdirectory=`） | 纯 Google Sheets/Drive 客户端库，**无 MCP、无 pydantic 依赖**（deps 仅 gspread 系），版本独立演进 |
| `packages/yuppie-mcp-google-sheets` | PyPI（`uvx yuppie-mcp-google-sheets`） | MCP 壳：server.py 把库 tools 注册为 MCP 工具，构建时 hatch `force-include` vendor 库源码进 wheel |

拆分动机：依赖本仓库只想用 Google 客户端代码的用户，不被强制安装 `mcp>=2.0.0,<3.0.0`（与用户自己项目的 MCP 版本冲突）。

## 开发命令

```bash
# 安装开发依赖（workspace 双包 + dev extras）
uv sync --all-packages --all-extras

# 运行测试
uv run pytest -v

# 代码检查
uv run ruff check packages/ tests/
uv run mypy packages/*/src

# 本地运行 MCP Server（stdio 模式）
GOOGLE_CREDENTIALS_B64=$(base64 -i credentials.json) uv run yuppie-mcp-google-sheets

# 构建壳包（必须 hatch 原地构建，uv build 会复制到临时目录导致 ../ force-include 路径失效）
cd packages/yuppie-mcp-google-sheets && uvx hatch build
```

## 架构设计

### 库包 `packages/yuppie-google-sheets/src/yuppie_google_sheets/`

- **`__init__.py`**: `__version__` + `GoogleSheetsClient`（mixin 聚合类，从原 `google/__init__.py` 迁来）+ re-export `GoogleConfig`
- **`config.py`**: `GoogleConfig`，`from_env()` 读取并校验 `GOOGLE_CREDENTIALS_B64`，自动加载 `.env`
- **mixin 模块（平铺在包根）**：Google Sheets 客户端（mixin 模式）
  - `base.py` — `_GoogleBase`：gspread client、凭据管理、`_format_error`、`_index_to_letter`
  - `sheets_worksheet.py` — `WorksheetMixin`：工作表 CRUD（创建/删除/复制/调整大小/清空）
  - `sheets_data.py` — `DataMixin`：数据更新、批量写入、清除、Visualization API 查询
  - `sheets_format.py` — `FormatMixin`：筛选器、数据验证、行高
  - `sheets_table.py` — `TableMixin`：表格（Table）创建/删除/查询
  - `sheets_quick.py` — `QuickSheetsMixin`：快捷业务操作（过滤列、批次索引、批量更新等）
  - `drive.py` — `DriveMixin`：Drive 文件列表、过滤排序


### 壳包 `packages/yuppie-mcp-google-sheets/src/yuppie_mcp_google_sheets/`

- **`tools/`**: MCP 工具层（Pydantic BaseModel + async 实现 + markdown 输出），跨包引用库包 `yuppie_google_sheets.config / .google`，模块级 client 单例懒加载
- **`server.py`**: 唯一 import mcp 的文件。FastMCP 注册 28 个工具

### 客户端懒加载

`tools/` 各模块 `_get_client()` 首次调用时读取环境变量并构造 `GoogleSheetsClient`，后续重用。

### 传输模式

仅支持 stdio（MCP 主流用法）。`server.py` 直接 `mcp.run()`。

## 代码规范

- 使用 `ruff`（line-length = 100）和 `mypy`（strict = true），配置在根 `pyproject.toml`
- 所有工具参数通过 Pydantic BaseModel 校验
- 工具返回 markdown 字符串；失败时返回 `❌ ...失败：{异常}`
- 方法命名：通用 API 薄包装用原始名，快捷业务操作前缀 `quick_sheets_`

## 添加新工具

1. 在库包 `google/<域>.py` 的 mixin 上加 Google API 薄包装方法
2. 在壳包 `tools/<域>.py` 加 BaseModel + async 实现 + 模块级 `_get_client`（引用库包 client）
3. 在壳包 `server.py` 用 `@mcp.tool(name=..., annotations=ToolAnnotations(...))` 注册，参数用 `Annotated[type, Field(...)]`
4. 在 `tests/test_tools.py` 加 BaseModel 校验测试
