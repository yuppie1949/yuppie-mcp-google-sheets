"""数据操作 mixin — 更新、批量写入、清除、Visualization API"""

from __future__ import annotations

import json
import re
import time
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

import google.auth.transport.requests
import requests
from google.oauth2.service_account import Credentials

from .base import SCOPES, _GoogleProtocol

if TYPE_CHECKING:
    pass


class DataMixin:
    """数据操作方法（混入 _GoogleBase 子类使用）"""

    def update_data(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_name: str,
        data: list[list[Any]],
        range_name: str | None = None,
        value_input_option: str = "USER_ENTERED",
    ) -> dict[str, Any]:
        """更新工作表数据"""
        try:
            ws = self._get_spreadsheet(spreadsheet_id).worksheet(sheet_name)
            ws.update(values=data, range_name=range_name, value_input_option=value_input_option)
            return {"success": True, "data": {"rows": len(data)}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def batch_update_data(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_name: str,
        data: list[list[Any]],
        start_row: int = 2,
        chunk_size: int = 5000,
        value_input_option: str = "USER_ENTERED",
        sleep_interval: float = 1.0,
    ) -> dict[str, Any]:
        """批量分块写入数据"""
        total = len(data)
        chunks = (total + chunk_size - 1) // chunk_size
        try:
            ws = self._get_spreadsheet(spreadsheet_id).worksheet(sheet_name)
            t0 = time.time()
            for i in range(0, total, chunk_size):
                chunk = data[i : i + chunk_size]
                ws.update(
                    values=chunk,
                    range_name=f"A{start_row + i}",
                    value_input_option=value_input_option,
                )
                if sleep_interval > 0 and (i // chunk_size + 1) < chunks:
                    time.sleep(sleep_interval)
            elapsed = time.time() - t0
            return {
                "success": True,
                "data": {"total_rows": total, "total_chunks": chunks, "elapsed": round(elapsed, 2)},
            }
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def batch_clear(
        self: _GoogleProtocol, spreadsheet_id: str, sheet_name: str, ranges: list[str]
    ) -> dict[str, Any]:
        """批量清除工作表区域"""
        try:
            ws = self._get_spreadsheet(spreadsheet_id).worksheet(sheet_name)
            ws.batch_clear(ranges)
            return {"success": True, "data": {"ranges_cleared": len(ranges)}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def visualization_query(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        query: str,
        sheet_name: str | None = None,
        gid: int | None = None,
        headers: int = 1,
    ) -> dict[str, Any]:
        """通过 Google Visualization API 执行 SQL 风格查询"""
        try:
            creds = Credentials.from_service_account_info(
                self._get_credentials_info(), scopes=SCOPES
            )
            creds.refresh(google.auth.transport.requests.Request())
            access_token = creds.token

            params: dict[str, Any] = {"tq": query, "headers": str(headers)}
            if sheet_name:
                params["sheet"] = sheet_name
            elif gid is not None:
                params["gid"] = str(gid)

            url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?{urlencode(params)}"
            resp = requests.get(
                url, headers={"Authorization": f"Bearer {access_token}"}, timeout=30
            )
            resp.raise_for_status()

            result = _parse_gviz_response(resp.text)
            if result.get("status") != "ok":
                return {
                    "success": False,
                    "error": {
                        "code": -1,
                        "msg": f"Visualization API 错误: {result.get('errors', [])}",
                    },
                }

            table = result.get("table", {})
            cols, rows = _transform_table(table)
            return {"success": True, "data": {"cols": cols, "rows": rows}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}


def _parse_gviz_response(raw: str) -> dict:
    cleaned = re.sub(r"^/\*.*?\*/", "", raw).strip()
    match = re.match(r"google\.visualization\.Query\.setResponse\((.*)\);?$", cleaned, re.DOTALL)
    if not match:
        raise ValueError(f"无法解析 gviz 响应格式: {cleaned[:200]}")
    return json.loads(match.group(1))


def _transform_table(table: dict) -> tuple[list[dict], list[dict]]:
    col_defs = table.get("cols", [])
    cols = [
        {
            "id": c.get("id", ""),
            "label": c.get("label") or c.get("id", ""),
            "type": c.get("type", ""),
        }
        for c in col_defs
    ]
    rows = []
    for row in table.get("rows", []):
        cells = row.get("c", [])
        row_data = {}
        for idx, col in enumerate(col_defs):
            key = col.get("label") or col.get("id", f"col_{idx}")
            cell = cells[idx] if idx < len(cells) else None
            value = None
            if cell and cell.get("v") is not None:
                value = cell["v"]
                if isinstance(value, float) and value.is_integer():
                    value = int(value)
                if isinstance(value, str) and value.startswith("Date("):
                    m = re.match(r"Date\((\d+),(\d+),(\d+)", value)
                    if m:
                        value = f"{int(m.group(1))}-{int(m.group(2)) + 1:02d}-{int(m.group(3)):02d}"
            row_data[key] = value
        rows.append(row_data)
    return cols, rows
