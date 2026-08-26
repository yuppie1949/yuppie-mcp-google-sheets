"""数据操作 mixin — 更新、批量写入、清除"""

from __future__ import annotations

import time
from typing import Any

from gspread.utils import ValueInputOption

from .base import _GoogleProtocol


class DataMixin:
    """数据操作方法（混入 _GoogleBase 子类使用）"""

    def update_data(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_id: str,
        data: list[list[Any]],
        range_name: str | None = None,
        value_input_option: ValueInputOption = ValueInputOption.user_entered,
    ) -> dict[str, Any]:
        """更新工作表数据"""
        try:
            ws = self._get_spreadsheet(spreadsheet_id).get_worksheet_by_id(sheet_id)
            ws.update(values=data, range_name=range_name, value_input_option=value_input_option)
            return {"success": True, "data": {"rows": len(data)}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def batch_update_data(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_id: str,
        data: list[list[Any]],
        data_start: int = 2,
        chunk_size: int = 5000,
        value_input_option: ValueInputOption = ValueInputOption.user_entered,
        sleep_interval: float = 1.0,
    ) -> dict[str, Any]:
        """批量分块写入数据"""
        total = len(data)
        chunks = (total + chunk_size - 1) // chunk_size
        try:
            ws = self._get_spreadsheet(spreadsheet_id).get_worksheet_by_id(sheet_id)
            t0 = time.time()
            for i in range(0, total, chunk_size):
                chunk = data[i : i + chunk_size]
                ws.update(
                    values=chunk,
                    range_name=f"A{data_start + i}",
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
        self: _GoogleProtocol, spreadsheet_id: str, sheet_id: str, ranges: list[str]
    ) -> dict[str, Any]:
        """批量清除工作表区域"""
        try:
            ws = self._get_spreadsheet(spreadsheet_id).get_worksheet_by_id(sheet_id)
            ws.batch_clear(ranges)
            return {"success": True, "data": {"ranges_cleared": len(ranges)}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}
