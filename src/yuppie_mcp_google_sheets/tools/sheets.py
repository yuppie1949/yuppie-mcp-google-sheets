"""电子表格域 MCP 工具"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..utils.config import GoogleConfig
from ..utils.google import GoogleSheetsClient
from ..utils.google.visualization import VisualizationClient

_client: GoogleSheetsClient | None = None
_viz_client: VisualizationClient | None = None


def _get_viz_client() -> VisualizationClient:
    global _viz_client
    if _viz_client is None:
        GoogleConfig.from_env()
        _viz_client = VisualizationClient()
    return _viz_client


def _get_client() -> GoogleSheetsClient:
    global _client
    if _client is None:
        GoogleConfig.from_env()
        _client = GoogleSheetsClient()
    return _client


class GetWorksheetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_id: str = Field(..., min_length=1, description="工作表id")


class CreateWorksheetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    title: str = Field(..., min_length=1, description="新工作表标题")
    rows: int = Field(1000, ge=1, description="行数")
    cols: int = Field(26, ge=1, le=18278, description="列数")


class DeleteWorksheetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_id: str = Field(..., min_length=1, description="工作表id")


class DuplicateWorksheetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    source_sheet_id: str = Field(..., min_length=1, description="源工作表id")
    insert_sheet_index: int | None = Field(None, description="插入位置")
    new_sheet_id: str | None = Field(None, description="新工作表id")
    new_sheet_name: str | None = Field(None, description="新工作表标题")


class UpdateDataInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_name: str = Field(..., min_length=1, description="工作表名称")
    data: list[list[Any]] = Field(..., description="二维数据列表")
    range_name: str | None = Field(None, description="更新范围，如 'A1:B10'（可选）")


class BatchUpdateDataInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_name: str = Field(..., min_length=1, description="工作表名称")
    data: list[list[Any]] = Field(..., description="二维数据列表")
    data_start: int = Field(2, ge=1, description="数据起始行号（1-based），默认 2")
    chunk_size: int = Field(5000, ge=1, le=5000, description="每块写入行数")
    sleep_interval: float = Field(1.0, ge=0, description="每块写入间隔秒数")


class BatchClearInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_name: str = Field(..., min_length=1, description="工作表名称")
    ranges: list[str] = Field(..., min_length=1, description="范围列表，如 ['A1:B10', 'D1:E20']")


class VisualizationQueryInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    query: str = Field(..., min_length=1, description='SQL 查询，如 "SELECT A, B WHERE C > 100"')
    sheet_name: str | None = Field(None, description="工作表名称（与 gid 二选一）")
    gid: int | None = Field(None, description="工作表 ID（与 sheet_name 二选一）")
    headers: int = Field(1, ge=0, description="表头行数")


class SetBasicFilterInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_name: str = Field(..., min_length=1, description="工作表名称")
    start_row: int = Field(..., ge=0, description="起始行索引（0-based）")
    end_row: int = Field(..., ge=0, description="结束行索引")
    start_col: int = Field(..., ge=0, description="起始列索引（0-based）")
    end_col: int = Field(..., ge=0, description="结束列索引")


class SetDataValidationInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_name: str = Field(..., min_length=1, description="工作表名称")
    column_name: str = Field(..., min_length=1, description="列名称")
    dropdown_options: list[str] = Field(..., min_length=1, description="下拉选项列表")
    data_start: int = Field(2, ge=1, description="数据起始行号，表头=data_start-1，默认 2")


class SetRowHeightInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_name: str = Field(..., min_length=1, description="工作表名称")
    data_start: int = Field(..., ge=1, description="数据起始行号（1-based）")
    height: int = Field(..., ge=1, description="行高（像素）")


class BatchUpdateRequestsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    requests: list[dict[str, Any]] = Field(..., description="批量更新请求列表")


class GetTablesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_name: str = Field(..., min_length=1, description="工作表名称")


class CreateTableInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_name: str = Field(..., min_length=1, description="工作表名称")
    table: dict[str, Any] = Field(..., description="表格配置")


class DeleteTableInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_name: str = Field(..., min_length=1, description="工作表名称")
    table_id: int = Field(..., description="表格 ID")


class DeleteTableByNameInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_name: str = Field(..., min_length=1, description="工作表名称")
    table_name: str = Field(..., min_length=1, description="表格名称")


# ── 工具实现 ──


async def get_worksheet(args: GetWorksheetInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = client.get_worksheet(args.spreadsheet_id, args.sheet_id)
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 获取工作表信息失败：{e}"
    if not result.get("success"):
        return f"❌ 失败：{result.get('error', {}).get('msg', '未知错误')}"
    d = result["data"]
    return (
        f"查询完成\n\n"
        f"- **工作表**: `{d['sheet_name']}`\n"
        f"- **工作表id**: `{d['sheet_id']}`\n"
        f"- **行数**: `{d['row_count']}`\n"
        f"- **列数**: `{d['col_count']}`\n"
        f"- **耗时**: `{_elapsed:.1f}s`"
    )


async def create_worksheet(args: CreateWorksheetInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = client.create_worksheet(args.spreadsheet_id, args.title, args.rows, args.cols)
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 创建工作表失败：{e}"
    if not result.get("success"):
        return f"❌ 失败：{result.get('error', {}).get('msg', '未知错误')}"

    d = result["data"]
    return (
        f"创建成功\n\n"
        f"- **工作表**: `{d['sheet_name']}`\n"
        f"- **工作表id**: `{d['sheet_id']}`\n"
        f"- **行数**: `{d['row_count']}`\n"
        f"- **列数**: `{d['col_count']}`\n"
        f"- **耗时**: `{_elapsed:.1f}s`"
    )


async def delete_worksheet(args: DeleteWorksheetInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = client.delete_worksheet(args.spreadsheet_id, args.sheet_id)
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 删除工作表失败：{e}"
    if not result.get("success"):
        return f"❌ 失败：{result.get('error', {}).get('msg', '未知错误')}"
    d = result["data"]
    return (
        f"删除完成\n\n"
        f"- **工作表**: `{d['sheet_name']}`\n"
        f"- **工作表id**: `{d['sheet_id']}`\n"
        f"- **耗时**: `{_elapsed:.1f}s`"
    )


async def duplicate_worksheet(args: DuplicateWorksheetInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = client.duplicate_worksheet(
            args.spreadsheet_id, args.source_sheet_id, args.insert_sheet_index, args.new_sheet_id, args.new_sheet_name
        )
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 复制工作表失败：{e}"
    if not result.get("success"):
        return f"❌ 失败：{result.get('error', {}).get('msg', '未知错误')}"
    d = result["data"]
    return (
        f"复制成功\n\n"
        f"- **工作表**: `{d['sheet_name']}`\n"
        f"- **工作表id**: `{d['sheet_id']}`\n"
        f"- **工作表index**: `{d['sheet_index']}`\n"
        f"- **行数**: `{d['row_count']}`\n"
        f"- **列数**: `{d['col_count']}`\n"
        f"- **耗时**: `{_elapsed:.1f}s`"
    )    


async def update_data(args: UpdateDataInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = client.update_data(
            args.spreadsheet_id,
            args.sheet_name,
            args.data,
            range_name=args.range_name,
        )
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 写入数据失败：{e}"
    if not result.get("success"):
        return f"❌ 失败：{result.get('error', {}).get('msg', '未知错误')}"
    return f"✅ 写入完成\n\n- **行数**: `{result['data']['rows']}`\n- **耗时**: `{_elapsed:.1f}s`"


async def batch_update_data(args: BatchUpdateDataInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = client.batch_update_data(
            args.spreadsheet_id,
            args.sheet_name,
            args.data,
            data_start=args.data_start,
            chunk_size=args.chunk_size,
            sleep_interval=args.sleep_interval,
        )
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 批量写入失败：{e}"
    if not result.get("success"):
        return f"❌ 失败：{result.get('error', {}).get('msg', '未知错误')}"
    d = result["data"]
    return (
        f"✅ 批量写入完成\n\n"
        f"- **总行数**: `{d['total_rows']}`\n"
        f"- **总块数**: `{d['total_chunks']}`\n"
        f"- **耗时**: `{d['elapsed']}s`"
    )


async def batch_clear(args: BatchClearInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = client.batch_clear(args.spreadsheet_id, args.sheet_name, args.ranges)
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 批量清除失败：{e}"
    if not result.get("success"):
        return f"❌ 失败：{result.get('error', {}).get('msg', '未知错误')}"
    return f"✅ 已清除 {result['data']['ranges_cleared']} 个区域\n- **耗时**: `{_elapsed:.1f}s`"


async def visualization_query(args: VisualizationQueryInput) -> str:
    try:
        _t0 = time.time()
        client = _get_viz_client()
        result = client.query(
            args.spreadsheet_id,
            args.query,
            sheet_name=args.sheet_name,
            gid=args.gid,
            headers=args.headers,
        )
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 查询失败：{e}"
    if not result.get("success"):
        return f"❌ 查询失败：{result.get('error', {}).get('msg', '未知错误')}"

    cols = result["data"]["cols"]
    rows = result["data"]["rows"]
    if not rows:
        return f"查询完成\n\n- **行数**: `0`\n- **耗时**: `{_elapsed:.1f}s`"

    keys = [c["label"] for c in cols]
    header = "| " + " | ".join(keys) + " |"
    sep = "| " + " | ".join("---" for _ in keys) + " |"
    body = "\n".join("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |" for r in rows)
    return f"查询完成，共 {len(rows)} 行\n\n{header}\n{sep}\n{body}"


async def set_basic_filter(args: SetBasicFilterInput) -> str:
    try:
        client = _get_client()
        result = client.set_basic_filter(
            args.spreadsheet_id,
            args.sheet_name,
            args.start_row,
            args.end_row,
            args.start_col,
            args.end_col,
        )
    except Exception as e:
        return f"❌ 设置筛选器失败：{e}"
    return (
        "✅ 筛选器已设置"
        if result.get("success")
        else f"❌ 失败：{result.get('error', {}).get('msg', '')}"
    )


async def set_data_validation(args: SetDataValidationInput) -> str:
    try:
        client = _get_client()
        result = client.set_data_validation(
            args.spreadsheet_id,
            args.sheet_name,
            args.column_name,
            args.dropdown_options,
            data_start=args.data_start,
        )
    except Exception as e:
        return f"❌ 设置数据验证失败：{e}"
    if not result.get("success"):
        return f"❌ 失败：{result.get('error', {}).get('msg', '未知错误')}"
    return (
        f"✅ 下拉列表已设置\n\n"
        f"- **列**: `{args.column_name}`\n"
        f"- **选项数**: `{len(args.dropdown_options)}`"
    )


async def set_row_height(args: SetRowHeightInput) -> str:
    try:
        client = _get_client()
        result = client.set_row_height(
            args.spreadsheet_id, args.sheet_name, args.data_start, args.height
        )
    except Exception as e:
        return f"❌ 设置行高失败：{e}"
    return (
        "✅ 行高已设置"
        if result.get("success")
        else f"❌ 失败：{result.get('error', {}).get('msg', '')}"
    )


async def batch_update_requests(args: BatchUpdateRequestsInput) -> str:
    try:
        client = _get_client()
        result = client.batch_update_requests(args.spreadsheet_id, args.requests)
    except Exception as e:
        return f"❌ 批量更新失败：{e}"
    return (
        f"✅ 批量更新完成\n\n- **请求数**: `{result['data']['requests_count']}`"
        if result.get("success")
        else f"❌ 失败：{result.get('error', {}).get('msg', '')}"
    )


async def get_tables(args: GetTablesInput) -> str:
    try:
        client = _get_client()
        result = client.get_tables(args.spreadsheet_id, args.sheet_name)
    except Exception as e:
        return f"❌ 查询表格失败：{e}"
    if not result.get("success"):
        return f"❌ 失败：{result.get('error', {}).get('msg', '未知错误')}"
    tables = result["data"]["tables"]
    if not tables:
        return "查询完成，无表格"
    lines = ["| 名称 | 表头行数 | 数据行数 | 列数 | ID |", "| --- | --- | --- | --- | --- |"]
    for t in tables:
        props = t.get("tableProperties", {}) if isinstance(t, dict) else {}
        n_cols = len(props.get("columns", []))
        lines.append(
            f"| {t.get('name', '')} | {props.get('headerRowCount', 0)} | "
            f"{props.get('dataRowCount', 0)} | {n_cols} | {t.get('tableId', '')} |"
        )
    return "\n".join(lines)


async def create_table(args: CreateTableInput) -> str:
    try:
        client = _get_client()
        result = client.create_table(args.spreadsheet_id, args.sheet_name, args.table)
    except Exception as e:
        return f"❌ 创建表格失败：{e}"
    return (
        f"✅ 表格已创建\n\n- **table_name**: `{args.table.get('name', '')}`"
        if result.get("success")
        else f"❌ 失败：{result.get('error', {}).get('msg', '')}"
    )


async def delete_table(args: DeleteTableInput) -> str:
    try:
        client = _get_client()
        result = client.delete_table(args.spreadsheet_id, args.sheet_name, args.table_id)
    except Exception as e:
        return f"❌ 删除表格失败：{e}"
    return (
        f"✅ 表格已删除\n\n- **table_id**: `{args.table_id}`"
        if result.get("success")
        else f"❌ 失败：{result.get('error', {}).get('msg', '')}"
    )


async def delete_table_by_name(args: DeleteTableByNameInput) -> str:
    try:
        client = _get_client()
        result = client.delete_table_by_name(args.spreadsheet_id, args.sheet_name, args.table_name)
    except Exception as e:
        return f"❌ 删除表格失败：{e}"
    if not result.get("success"):
        return f"❌ 失败：{result.get('error', {}).get('msg', '未知错误')}"
    return f"✅ 已删除 {result['data']['deleted_count']} 个表格"
