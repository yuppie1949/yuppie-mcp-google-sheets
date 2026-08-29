# yuppie-mcp-google-sheets

Google Sheets MCP Server — 让 AI 助手通过 MCP 协议操作 Google Sheets 电子表格和 Drive 文件。

## 特性

- **Drive 文件操作**：列出文件夹文件、按文件名过滤排序、存储用量查询
- **工作表管理**：创建、删除、复制、调整大小、清空
- **数据操作**：范围读写、批量写入、区域清除、Visualization API SQL 查询
- **格式设置**：筛选器、数据验证（下拉列表）、行高
- **表格管理**：创建、删除、查询表格（Table）
- **快捷操作**：列过滤、批次索引、批量更新、批量追加、CSV 同步、按批次读取
- **鉴权**：基于 Google 服务账号，base64 编码凭据

## 架构说明

本包是 MCP 壳：核心 Google Sheets 客户端代码在库包 `yuppie-google-sheets`（同仓库 `packages/yuppie-google-sheets`，仅 GitHub 分发、无 MCP 依赖）。构建时库源码被 vendor 进本包 wheel，因此 PyPI 安装自包含。

如只需在 Python 项目中操作 Google Sheets（不要 MCP），安装库包（支持 `@tag` 锁定版本，如 `@v0.3.1`）：

```bash
uv pip install "yuppie-google-sheets @ git+https://github.com/yuppie1949/yuppie-mcp-google-sheets.git@v0.3.1#subdirectory=packages/yuppie-google-sheets"
```

## 快速开始

### 准备凭据

1. 在 [Google Cloud Console](https://console.cloud.google.com/) 创建服务账号
2. 为该服务账号生成 JSON 密钥
3. 下载 JSON 文件并 base64 编码：

```bash
base64 -i your-credentials.json
```

### Claude Code

在 `.mcp.json` 中添加：

```json
{
  "mcpServers": {
    "google-sheets": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--refresh", "yuppie-mcp-google-sheets"],
      "env": {
        "GOOGLE_CREDENTIALS_B64": "<your-base64-credentials>",
        "GOOGLE_APPS_SCRIPT_URL": "<your_google_apps_script_url_here>"
      }
    }
  }
}
```

### Cursor

在 `~/.cursor/mcp.json` 中添加同上配置。

### Cherry Studio / Claude Desktop / OpenCode

参照上方 env 字段，按各自 MCP 配置格式填入即可。

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `GOOGLE_CREDENTIALS_B64` | 是 | - | Google 服务账号 JSON 密钥的 base64 编码 |
| `GOOGLE_APPS_SCRIPT_URL` | 否 | - | Google Apps Script URL，`gsheets_copy_file` 需要 |

## 可用工具（共 28 个）

### Drive 文件

| 工具 | 说明 |
|------|------|
| `gsheets_list_files` | 列出 Drive 文件夹中的文件 |
| `gsheets_filter_and_sort_files` | 按文件名过滤和排序 |
| `gsheets_get_storage_quota` | 查询 Drive 存储配额 |

### 工作表管理

| 工具 | 说明 |
|------|------|
| `gsheets_get_worksheet` | 获取工作表信息 |
| `gsheets_create_worksheet` | 创建工作表 |
| `gsheets_delete_worksheet` | 删除工作表 |
| `gsheets_duplicate_worksheet` | 复制工作表 |

### 数据操作

| 工具 | 说明 |
|------|------|
| `gsheets_update_data` | 更新工作表数据 |
| `gsheets_batch_update_data` | 批量分块写入数据 |
| `gsheets_batch_clear` | 批量清除区域 |
| `gsheets_visualization_query` | SQL 风格查询数据 |

### 格式设置

| 工具 | 说明 |
|------|------|
| `gsheets_set_basic_filter` | 设置筛选器 |
| `gsheets_set_data_validation` | 设置下拉列表 |
| `gsheets_set_row_height` | 设置行高 |

### 表格管理

| 工具 | 说明 |
|------|------|
| `gsheets_get_tables` | 获取表格列表 |
| `gsheets_create_table` | 创建表格 |
| `gsheets_delete_table` | 删除表格 |
| `gsheets_delete_table_by_name` | 按名称删除表格 |

### 快捷操作

| 工具 | 说明 |
|------|------|
| `gsheets_filter_columns` | 只保留指定列，删除其余列 |
| `gsheets_set_batch_index` | 按列设置批次索引 |
| `gsheets_set_header_list` | 写入新表头 |
| `gsheets_get_column_last_value` | 获取列最后一个非空值 |
| `gsheets_get_rows_by_batch` | 按批次读取行 |
| `gsheets_batch_update` | 批量更新行 |
| `gsheets_batch_append` | 批量追加行 |
| `gsheets_clear_sheet_content` | 清空工作表内容（不移除行） |
| `gsheets_clear_sheet` | 清空工作表数据（删除行） |
| `gsheets_sync_from_file` | 从 CSV 文件同步数据 |

## 测试与调试

```bash
uv pip install -e ".[dev]"
uv run pytest -v
```

使用 MCP Inspector 调试（需先在 `.env` 配置 `GOOGLE_CREDENTIALS_B64`）：

```bash
npx @modelcontextprotocol/inspector uv run yuppie-mcp-google-sheets
```

## License

MIT
