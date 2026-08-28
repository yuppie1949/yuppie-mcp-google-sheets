"""Google Visualization API 客户端 — SQL 风格查询 Google Sheets 数据"""

from __future__ import annotations

import json
import os
import re
from typing import Any, cast
from urllib.parse import urlencode

import google.auth.transport.requests
import requests
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class VisualizationClient:
    """Google Visualization API 客户端

    不走 gspread，直接调用 /gviz/tq 端点获取 JSONP 响应，
    支持 SELECT, WHERE, ORDER BY, LIMIT, OFFSET, LABEL, FORMAT, PIVOT 等子句。
    """

    def __init__(self) -> None:
        credentials_b64 = os.environ.get("GOOGLE_CREDENTIALS_B64", "")
        if not credentials_b64:
            raise ValueError("GOOGLE_CREDENTIALS_B64 环境变量未设置")
        raw = _b64decode(credentials_b64)
        self._creds_info = json.loads(raw)

    def _get_access_token(self) -> str:
        creds = Credentials.from_service_account_info(  # type: ignore[no-untyped-call]
            self._creds_info, scopes=SCOPES
        )
        creds.refresh(google.auth.transport.requests.Request())
        return creds.token  # type: ignore[no-any-return]

    def query(
        self,
        spreadsheet_id: str,
        sheet_id: int,
        query: str,
    ) -> dict[str, Any]:
        """通过 Google Visualization API 执行 SQL 风格查询

        Args:
            spreadsheet_id: 电子表格 ID
            sheet_id: 工作表 ID
            query: SQL 查询语句，如 "SELECT A, B WHERE C > 100 ORDER BY A DESC LIMIT 10"

        Returns:
            { success: bool, data: { cols: [...], rows: [...] } }
        """
        try:
            access_token = self._get_access_token()

            params: dict[str, Any] = {"tq": query, "gid": sheet_id }

            url = (
                f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq"
                f"?{urlencode(params)}"
            )
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
            return {"success": False, "error": {"code": -1, "msg": str(e)}}


def _b64decode(b64: str) -> str:
    import base64

    return base64.b64decode(b64).decode("utf-8")


def _parse_gviz_response(raw: str) -> dict[str, Any]:
    """解析 Google Visualization API 的 JSONP 响应"""
    cleaned = re.sub(r"^/\*.*?\*/", "", raw).strip()
    match = re.match(r"google\.visualization\.Query\.setResponse\((.*)\);?$", cleaned, re.DOTALL)
    if not match:
        raise ValueError(f"无法解析 gviz 响应格式: {cleaned[:200]}")
    return cast(dict[str, Any], json.loads(match.group(1)))


def _transform_table(table: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """将 gviz table 转换为标准格式"""
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
