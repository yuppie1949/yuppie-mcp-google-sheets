"""电子表格快捷业务操作 MCP 工具"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from yuppie_google_sheets import GoogleSheetsClient
from yuppie_google_sheets.config import GoogleConfig

_client: GoogleSheetsClient | None = None


def _get_client() -> GoogleSheetsClient:
    global _client
    if _client is None:
        GoogleConfig.from_env()
        _client = GoogleSheetsClient()
    return _client


class FilterSheetColumnsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID（名称）")
    keep_columns: list[str] = Field(..., min_length=1, description="要保留的列名列表")
    data_start: int = Field(2, ge=1, description="数据起始行（1-based），默认 2")


class SetBatchIndexInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID（名称）")
    batch_column: str = Field("f_batch_index", description="批次列名")
    batch_size: int = Field(10, ge=1, le=1000, description="每批行数")
    data_start: int = Field(2, ge=1, description="数据起始行（1-based）")


class SetHeaderListInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID（名称）")
    header_list: list[str] = Field(..., min_length=1, description="新表头列表")
    keep_columns: int | None = Field(None, ge=0, description="保留的原始列数")
    data_start: int = Field(2, ge=1, description="表头所在行=data_start-1")


class GetColumnLastValueInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID（名称）")
    column_name: str = Field(..., min_length=1, description="列名")
    data_start: int = Field(2, ge=1, description="数据起始行（1-based）")


class GetRowsByBatchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID（名称）")
    batch_id: int = Field(..., ge=1, description="批次号，从 1 开始")
    batch_size: int = Field(..., ge=1, le=5000, description="每批行数")
    data_start: int = Field(2, ge=1, description="数据起始行（1-based）")


class BatchUpdateInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID（名称）")
    update_data: list[dict[str, Any]] = Field(
        ..., description="更新数据，每行一个 dict，含 row_number"
    )
    columns: list[str] | None = Field(None, description="要写入的列名列表")
    data_start: int = Field(2, ge=1, description="数据起始行（1-based）")


class BatchAppendInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID（名称）")
    data: list[dict[str, Any]] = Field(..., description="要追加的数据，每行一个 dict")
    batch_size: int = Field(500, ge=1, le=5000, description="每批追加行数")
    batch_interval: int = Field(2, ge=0, le=30, description="每批间隔秒数")
    data_start: int = Field(2, ge=1, description="数据起始行（1-based）")
    overwrite_start: int | bool | None = Field(
        None, description="True 从 data_start 覆写，int 从指定行覆写，None 使用 append 寻址"
    )


class SyncFromFileInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID（名称）")
    file_path: str = Field(..., min_length=1, description="本地 CSV 文件路径")
    batch_size: int = Field(5000, ge=1, le=5000, description="每批写入行数")
    data_start: int = Field(2, ge=1, description="数据起始行（1-based）")


class ClearSheetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID（名称）")
    keep_header: bool = Field(True, description="是否保留首行表头")
    data_start: int = Field(2, ge=1, description="数据起始行号")


class ClearSheetContentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_id: str = Field(..., min_length=1, description="电子表格 ID")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID（名称）")
    keep_header: bool = Field(True, description="是否保留首行表头")
    data_start: int = Field(2, ge=1, description="数据起始行号")
    before_column: str | None = Field(None, description="指定列字母，只清空该列之前的所有列")


# ── 工具实现 ──


async def quick_sheets_filter_columns(args: FilterSheetColumnsInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        sheet_id = client.quick_sheets_filter_columns(
            args.spreadsheet_id,
            args.sheet_id,
            args.keep_columns,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
        return (
            "✅ 列过滤完成\n\n"
            f"- **保留列数**: `{len(args.keep_columns)}`\n"
            f"- **sheetId**: `{sheet_id}`\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 列过滤失败：{e}"


async def quick_sheets_set_batch_index(args: SetBatchIndexInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        client.quick_sheets_set_batch_index(
            args.spreadsheet_id,
            args.sheet_id,
            batch_column=args.batch_column,
            batch_size=args.batch_size,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
        return (
            "✅ 批次索引已设置\n\n"
            f"- **batch_column**: `{args.batch_column}`\n"
            f"- **batch_size**: `{args.batch_size}`\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 设置批次索引失败：{e}"


async def quick_sheets_set_header_list(args: SetHeaderListInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        client.quick_sheets_set_header_list(
            args.spreadsheet_id,
            args.sheet_id,
            args.header_list,
            keep_columns=args.keep_columns,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
        return (
            f"✅ 表头已写入\n\n- **列数**: `{len(args.header_list)}`\n- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 写入表头失败：{e}"


async def quick_sheets_get_column_last_value(args: GetColumnLastValueInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = client.quick_sheets_get_last_value(
            args.spreadsheet_id,
            args.sheet_id,
            args.column_name,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
        return (
            f"查询完成\n\n"
            f"- **列**: `{args.column_name}`\n"
            f"- **最后一个非空值**: `{result['value']}`\n"
            f"- **行号**: `{result['row_number']}`\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 查询失败：{e}"


async def quick_sheets_get_rows_by_batch(args: GetRowsByBatchInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        rows = client.quick_sheets_get_rows_by_batch(
            args.spreadsheet_id,
            args.sheet_id,
            args.batch_id,
            args.batch_size,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 读取失败：{e}"
    if not rows:
        return f"查询完成\n\n- **行数**: `0`\n- **耗时**: `{_elapsed:.1f}s`"

    keys = ["row_number"] + [k for k in rows[0] if k != "row_number"]
    header = "| " + " | ".join(keys) + " |"
    sep = "| " + " | ".join("---" for _ in keys) + " |"
    body = "\n".join("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |" for r in rows)
    return (
        f"查询完成\n\n"
        f"- **行数**: `{len(rows)}`\n"
        f"- **耗时**: `{_elapsed:.1f}s`\n\n"
        f"{header}\n{sep}\n{body}"
    )


async def quick_sheets_batch_update(args: BatchUpdateInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        if not args.update_data:
            return "✅ 批量更新完成\n\n- **更新行数**: `0`"
        client.quick_sheets_batch_update(
            args.spreadsheet_id,
            args.sheet_id,
            args.update_data,
            columns=args.columns,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
        return (
            f"✅ 批量更新完成\n\n"
            f"- **更新行数**: `{len(args.update_data)}`\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 批量更新失败：{e}"


async def quick_sheets_batch_append(args: BatchAppendInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        client.quick_sheets_batch_append(
            args.spreadsheet_id,
            args.sheet_id,
            args.data,
            batch_size=args.batch_size,
            batch_interval=args.batch_interval,
            data_start=args.data_start,
            overwrite_start=args.overwrite_start,
        )
        _elapsed = time.time() - _t0
        return (
            f"✅ 批量追加完成\n\n- **追加行数**: `{len(args.data)}`\n- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 批量追加失败：{e}"


async def quick_sheets_sync_from_file(args: SyncFromFileInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        client.quick_sheets_sync_from_file(
            args.spreadsheet_id,
            args.sheet_id,
            args.file_path,
            batch_size=args.batch_size,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
        return f"✅ 从文件同步完成\n\n- **文件**: `{args.file_path}`\n- **耗时**: `{_elapsed:.1f}s`"
    except Exception as e:
        return f"❌ 从文件同步失败：{e}"


async def quick_sheets_clear_sheet_content(args: ClearSheetContentInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        info = client.quick_sheets_clear_sheet_content(
            args.spreadsheet_id,
            args.sheet_id,
            keep_header=args.keep_header,
            data_start=args.data_start,
            before_column=args.before_column,
        )
        _elapsed = time.time() - _t0
        col_label = f"**清空列数**: `{info['col_count']}`\n" if info["col_count"] else ""
        return (
            f"✅ 工作表内容已清空\n\n"
            f"{col_label}"
            f"**清空行数**: `{info['row_count']}`\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 清空工作表内容失败：{e}"


async def quick_sheets_clear_sheet(args: ClearSheetInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        client.quick_sheets_clear_sheet(
            args.spreadsheet_id,
            args.sheet_id,
            keep_header=args.keep_header,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
        return f"✅ 工作表已清空\n\n- **耗时**: `{_elapsed:.1f}s`"
    except Exception as e:
        return f"❌ 清空工作表失败：{e}"
