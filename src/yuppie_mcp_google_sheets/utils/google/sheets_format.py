"""格式操作 mixin — 筛选器、数据验证、行高、批量更新"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import _GoogleProtocol

if TYPE_CHECKING:
    pass


class FormatMixin:
    """格式化管理方法（混入 _GoogleBase 子类使用）"""

    def set_basic_filter(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_name: str,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
    ) -> dict[str, Any]:
        """设置工作表筛选器"""
        try:
            ws = self._get_spreadsheet(spreadsheet_id).worksheet(sheet_name)
            req = {
                "setBasicFilter": {
                    "filter": {
                        "range": {
                            "sheetId": ws.id,
                            "startRowIndex": start_row,
                            "endRowIndex": end_row,
                            "startColumnIndex": start_col,
                            "endColumnIndex": end_col,
                        }
                    }
                }
            }
            self._get_spreadsheet(spreadsheet_id).batch_update({"requests": [req]})
            return {"success": True, "data": {}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def set_data_validation(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_name: str,
        column_name: str,
        dropdown_options: list[str],
        data_start: int = 2,
    ) -> dict[str, Any]:
        """为列设置下拉列表"""
        try:
            spreadsheet = self._get_spreadsheet(spreadsheet_id)
            ws = spreadsheet.worksheet(sheet_name)
            header_row = data_start - 1
            headers = ws.row_values(header_row)
            try:
                col_index = headers.index(column_name)
            except ValueError:
                return {"success": False, "error": {"code": -1, "msg": f"未找到列 '{column_name}'"}}

            req = {
                "setDataValidation": {
                    "range": {
                        "sheetId": ws.id,
                        "startRowIndex": data_start - 1,
                        "endRowIndex": ws.row_count,
                        "startColumnIndex": col_index,
                        "endColumnIndex": col_index + 1,
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [{"userEnteredValue": o} for o in dropdown_options],
                        },
                        "strict": True,
                        "showCustomUi": True,
                    },
                }
            }
            spreadsheet.batch_update({"requests": [req]})
            return {"success": True, "data": {"column": column_name}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def set_row_height(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_name: str,
        data_start: int,
        height: int,
    ) -> dict[str, Any]:
        """设置工作表行高"""
        try:
            spreadsheet = self._get_spreadsheet(spreadsheet_id)
            ws = spreadsheet.worksheet(sheet_name)
            req = {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": ws.id,
                        "dimension": "ROWS",
                        "startIndex": data_start - 1,
                        "endIndex": ws.row_count,
                    },
                    "properties": {"pixelSize": height},
                    "fields": "pixelSize",
                }
            }
            spreadsheet.batch_update({"requests": [req]})
            return {"success": True, "data": {}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def batch_update_requests(
        self: _GoogleProtocol, spreadsheet_id: str, requests_list: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """执行自定义批量更新操作"""
        try:
            self._get_spreadsheet(spreadsheet_id).batch_update({"requests": requests_list})
            return {"success": True, "data": {"requests_count": len(requests_list)}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}
