"""Google Sheets 客户端基类：gspread client、凭据管理、通用方法"""

from __future__ import annotations

import base64
import json
import os
from typing import Any, Optional, Protocol, cast

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class _GoogleProtocol(Protocol):
    """Mixin 自引用协议 — 避免 mypy 对 mixin self 的报错"""

    def _get_credentials_info(self) -> dict[str, Any]: ...
    def _get_gspread_client(self) -> gspread.Client: ...
    def _get_spreadsheet(self, spreadsheet_id: str) -> gspread.Spreadsheet: ...
    def _index_to_letter(self, index: int) -> str: ...
    def _format_error(self, exception: Exception) -> dict[str, Any]: ...
    def _read_headers(self, spreadsheet_id: str, sheet_id: int, data_start: int) -> list[str]: ...
    def _resolve_col_letter(
        self, spreadsheet_id: str, sheet_id: int, column_name: str, data_start: int
    ) -> str: ...
    def _ensure_column(
        self, spreadsheet_id: str, sheet_id: int, column_name: str, data_start: int
    ) -> str: ...
    def _get_drive_service(self) -> Any: ...
    def get_tables(self, spreadsheet_id: str, sheet_id: int) -> dict[str, Any]: ...
    def quick_sheets_batch_append(
        self,
        spreadsheet_id: str,
        sheet_id: int,
        data: list[dict[str, Any]],
        *,
        batch_size: int = 500,
        batch_interval: int = 2,
        data_start: int = 2,
        overwrite_start: int | bool | None = None,
    ) -> None: ...


class _GoogleBase:
    """Google 客户端基类 — 管理 gspread http client、凭据、公共工具方法"""

    def __init__(self) -> None:
        self._gspread: Optional[gspread.Client] = None
        self._credentials_b64 = os.environ.get("GOOGLE_CREDENTIALS_B64", "")

    def _get_credentials_info(self) -> dict[str, Any]:
        """从 base64 环境变量解析凭据 JSON"""
        if not self._credentials_b64:
            raise ValueError("GOOGLE_CREDENTIALS_B64 环境变量未设置")
        raw = base64.b64decode(self._credentials_b64).decode("utf-8")
        return cast(dict[str, Any], json.loads(raw))

    def _get_gspread_client(self) -> gspread.Client:
        """懒加载 gspread http client"""
        if self._gspread is None:
            creds = Credentials.from_service_account_info(  # type: ignore[no-untyped-call]
                self._get_credentials_info(), scopes=SCOPES
            )
            self._gspread = gspread.authorize(creds)
        return self._gspread

    def _get_spreadsheet(self, spreadsheet_id: str) -> gspread.Spreadsheet:
        return self._get_gspread_client().open_by_key(spreadsheet_id)

    @staticmethod
    def _index_to_letter(index: int) -> str:
        """0-based 列索引转列字母：0→A, 25→Z, 26→AA, 701→ZZ"""
        result = ""
        while True:
            result = chr(ord("A") + index % 26) + result
            index = index // 26 - 1
            if index < 0:
                break
        return result

    @staticmethod
    def _format_error(exception: Exception) -> dict[str, Any]:
        """格式化错误信息"""
        if isinstance(exception, ValueError):
            return {"code": -1, "msg": str(exception)}
        elif isinstance(exception, json.JSONDecodeError):
            return {"code": -1, "msg": f"凭据 JSON 解析失败: {exception}"}
        elif isinstance(exception, TimeoutError):
            return {"code": -1, "msg": "请求超时"}
        else:
            return {"code": -1, "msg": str(exception)}
