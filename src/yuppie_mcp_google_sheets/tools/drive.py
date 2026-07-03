"""Drive 域 MCP 工具"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..utils.config import GoogleConfig
from ..utils.google import GoogleSheetsClient

_client: GoogleSheetsClient | None = None


def _get_client() -> GoogleSheetsClient:
    global _client
    if _client is None:
        GoogleConfig.from_env()  # 校验环境变量
        _client = GoogleSheetsClient()
    return _client


class ListFilesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    folder_id: str = Field(..., min_length=1, description="Drive 文件夹 ID")
    file_type: str | None = Field(
        None, description="文件 MIME 类型，如 'application/vnd.google-apps.spreadsheet'"
    )


class FilterAndSortFilesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    file_list: list[dict[str, Any]] = Field(..., description="文件列表，每项含 id 和 name")
    prefix: str | None = Field(None, description="文件名前缀过滤")
    suffix: str | None = Field(None, description="文件名后缀过滤")
    datetime_format: str | None = Field(None, description="时间戳格式，如 '%%Y%%m%%d'")
    reverse: bool = Field(True, description="是否降序排序")


class GetStorageQuotaInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class CopyFileInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    file_id: str = Field(..., min_length=1, description="源文件 ID")
    target_folder_id: str = Field(..., min_length=1, description="目标文件夹 ID")
    new_name: str | None = Field(None, description="新文件名（可选，默认保持原名）")


async def list_files(args: ListFilesInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = client.list_files(args.folder_id, file_type=args.file_type)
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 查询文件列表失败：{e}"
    if not result.get("success"):
        return f"❌ 查询失败：{result.get('error', {}).get('msg', '未知错误')}"

    files = result["data"]["files"]
    if not files:
        return f"查询完成\n\n- **文件数**: `0`\n- **耗时**: `{_elapsed:.1f}s`"

    lines = [
        f"查询完成\n\n- **文件数**: `{len(files)}`\n- **耗时**: `{_elapsed:.1f}s`\n",
        "| 文件名 | ID |",
        "| --- | --- |",
    ]
    for f in files:
        lines.append(f"| {f.get('name', '')} | {f.get('id', '')} |")
    return "\n".join(lines)


async def filter_and_sort_files(args: FilterAndSortFilesInput) -> str:
    try:
        client = _get_client()
        result = client.filter_and_sort_files(
            args.file_list,
            prefix=args.prefix,
            suffix=args.suffix,
            datetime_format=args.datetime_format,
            reverse=args.reverse,
        )
    except Exception as e:
        return f"❌ 过滤排序失败：{e}"
    if not result.get("success"):
        return f"❌ 失败：{result.get('error', {}).get('msg', '未知错误')}"

    files = result["data"]["files"]
    if not files:
        return "查询完成，无匹配文件"

    lines = ["| 文件名 | ID |", "| --- | --- |"]
    for f in files:
        name = f.get("name", "")
        dt = f.get("datetime", "")
        label = f"{name} ({dt})" if dt else name
        lines.append(f"| {label} | {f.get('id', '')} |")
    return "\n".join(lines)


async def get_storage_quota(args: GetStorageQuotaInput) -> str:
    try:
        client = _get_client()
        result = client.get_storage_quota()
    except Exception as e:
        return f"❌ 查询存储配额失败：{e}"
    if not result.get("success"):
        return f"❌ 失败：{result.get('error', {}).get('msg', '未知错误')}"

    q = result["data"]
    limit_mb = q.get("limit", 0) / (1024 * 1024)
    usage_mb = q.get("usage", 0) / (1024 * 1024)
    return (
        "查询完成\n\n"
        f"- **总配额**: `{limit_mb:.1f} MB`\n"
        f"- **已用**: `{usage_mb:.1f} MB`\n"
        f"- **Drive 用量**: `{q.get('usage_in_drive', 0) / (1024 * 1024):.1f} MB`"
    )


async def copy_file(args: CopyFileInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = client.copy_file(
            args.file_id, args.target_folder_id, new_name=args.new_name
        )
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 复制文件失败：{e}"
    if not result.get("success"):
        return f"❌ 失败：{result.get('error', {}).get('msg', '未知错误')}"
    d = result["data"]
    name_link = f"[{d['name']}]({d['url']})" if d.get("url") else f"`{d['name']}`"
    return (
        f"✅ 文件已复制\n\n"
        f"- **新文件**: {name_link}\n"
        f"- **ID**: `{d['id']}`\n"
        f"- **耗时**: `{_elapsed:.1f}s`"
    )
