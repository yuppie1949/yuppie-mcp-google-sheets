# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## 项目概述

`yuppie-mcp-google-sheets` 是一个 MCP (Model Context Protocol) Server，让 AI 助手通过 MCP 协议操作 Google Sheets。基于 Google 服务账号认证（`gspread` 库），覆盖工作表管理、数据读写、格式化、表格管理、Drive 文件操作等业务域。

## 开发命令

```bash
# 安装开发依赖
uv pip install -e ".[dev]"

# 运行测试
uv run pytest -v

# 代码检查
ruff check src/
ruff format --check src/

# 类型检查
mypy src/

# 本地运行 MCP Server（stdio 模式）
GOOGLE_CREDENTIALS_B64=$(base64 -i credentials.json) uv run yuppie-mcp-google-sheets
```

## 架构设计

### 核心模块

- **`server.py`**: MCP Server 入口，FastMCP 注册 28 个工具
- **`utils/config.py`**: `GoogleConfig`，`from_env()` 读取并校验 `GOOGLE_CREDENTIALS_B64`，自动加载 `.env`
- **`utils/google/`**: Google Sheets 客户端（mixin 模式）
  - `base.py` — `_GoogleBase`：gspread client、凭据管理、`_format_error`、`_index_to_letter`
  - `sheets_worksheet.py` — `WorksheetMixin`：工作表 CRUD（创建/删除/复制/调整大小/清空）
  - `sheets_data.py` — `DataMixin`：数据更新、批量写入、清除、Visualization API 查询
  - `sheets_format.py` — `FormatMixin`：筛选器、数据验证、行高
  - `sheets_table.py` — `TableMixin`：表格（Table）创建/删除/查询
  - `sheets_quick.py` — `QuickSheetsMixin`：快捷业务操作（过滤列、批次索引、批量更新等）
  - `drive.py` — `DriveMixin`：Drive 文件列表、过滤排序
  - `__init__.py` — `GoogleSheetsClient(_GoogleBase, WorksheetMixin, DataMixin, ...)` 聚合
- **`tools/`**: MCP 工具层（按域分），每个模块持模块级 client 单例，首次调用时懒加载
  - 每个工具：Pydantic `BaseModel`（`str_strip_whitespace` + `extra="forbid"`）+ `async def` 实现 + markdown 输出 + try/except 友好错误

### 客户端懒加载

`_get_client()` 首次调用时读取环境变量并构造 `GoogleSheetsClient`，后续重用。

### 传输模式

仅支持 stdio（MCP 主流用法）。`server.py` 直接 `mcp.run()`。

## 代码规范

- 使用 `ruff`（line-length = 100）和 `mypy`（strict = true）
- 所有工具参数通过 Pydantic BaseModel 校验
- 工具返回 markdown 字符串；失败时返回 `❌ ...失败：{异常}`
- 方法命名：通用 API 薄包装用原始名，快捷业务操作前缀 `quick_sheets_`

## 添加新工具

1. 在 `utils/google/<域>.py` 的 mixin 上加 Google API 薄包装方法
2. 在 `tools/<域>.py` 加 BaseModel + async 实现 + 模块级 `_get_client`
3. 在 `server.py` 用 `@mcp.tool(name=..., annotations=ToolAnnotations(...))` 注册，参数用 `Annotated[type, Field(...)]`
4. 在 `tests/test_tools.py` 加 BaseModel 校验测试
