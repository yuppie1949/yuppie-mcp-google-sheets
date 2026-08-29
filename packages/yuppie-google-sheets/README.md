# yuppie-google-sheets

Google Sheets & Drive 客户端库（基于服务账号 + gspread），**无 MCP 依赖**。

从 `yuppie-mcp-google-sheets` 仓库拆出的纯 Python 库：如果你只想在自己的项目里操作 Google Sheets / Drive，不想引入 MCP 及其版本约束，直接用这个包。

## 安装

本包不发布到 PyPI，从 GitHub 安装（monorepo 子目录）：

```bash
# uv（跟踪 main 分支）
uv add "yuppie-google-sheets @ git+https://github.com/yuppie1949/yuppie-mcp-google-sheets.git#subdirectory=packages/yuppie-google-sheets"

# pip / uv pip
uv pip install "yuppie-google-sheets @ git+https://github.com/yuppie1949/yuppie-mcp-google-sheets.git#subdirectory=packages/yuppie-google-sheets"

# 锁定版本（推荐生产环境）— @tag / @分支 / @commit 三种方式
# requirements.txt 锁 tag
yuppie-google-sheets @ git+https://github.com/yuppie1949/yuppie-mcp-google-sheets.git@v0.3.2#subdirectory=packages/yuppie-google-sheets
```

> tag 与 PyPI 壳包版本同步（`v<mcp版本>`），如 `v0.3.2` = 壳包 0.3.2 + 库包 0.1.0 时的仓库快照。tag 列表见 [releases](https://github.com/yuppie1949/yuppie-mcp-google-sheets/tags)。

## 快速开始

```python
from yuppie_google_sheets.config import GoogleConfig
from yuppie_google_sheets import GoogleSheetsClient

config = GoogleConfig.from_env()  # 读 GOOGLE_CREDENTIALS_B64 环境变量（base64 编码的服务账号 JSON）
client = GoogleSheetsClient(config)

spreadsheet = client.open_spreadsheet("<spreadsheet_id>")
client.update_values(spreadsheet, "Sheet1!A1", [["hello", "world"]])
```

## 模块结构

- `yuppie_google_sheets` — 包根直接暴露 `GoogleSheetsClient`（mixin 聚合）与 `GoogleConfig`
- `yuppie_google_sheets.config` — `GoogleConfig` 环境配置（服务账号凭据）
- 各业务域 mixin 平铺在包根：工作表 CRUD、数据读写/批量写入/Visualization API SQL 查询、筛选器/数据验证/行高/表格（Table）、快捷批量操作、Drive 文件列表
- 无 pydantic 依赖（deps 仅 gspread/google-auth/google-api-python-client/requests/python-dotenv）

## 与 MCP Server 的关系

同一仓库的 `packages/yuppie-mcp-google-sheets` 是本库的 MCP 壳（把 `tools` 注册为 MCP 工具），走 PyPI 分发（`uvx yuppie-mcp-google-sheets`）。两者版本独立演进。

## 依赖

Python ≥ 3.10；python-dotenv、gspread、google-auth、google-api-python-client、requests
