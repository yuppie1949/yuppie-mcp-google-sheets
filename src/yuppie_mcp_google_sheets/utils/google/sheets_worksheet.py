"""工作表操作 mixin — 创建、删除、复制、调整大小、清空"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import _GoogleProtocol

if TYPE_CHECKING:
    pass


class WorksheetMixin:
    """工作表管理方法（混入 _GoogleBase 子类使用）"""

    def get_worksheet(
        self: _GoogleProtocol, spreadsheet_id: str, sheet_name: str
    ) -> dict[str, Any]:
        """获取指定工作表信息"""
        try:
            worksheet = self._get_spreadsheet(spreadsheet_id).worksheet(sheet_name)
            return {
                "success": True,
                "data": {
                    "sheet_name": sheet_name,
                    "row_count": worksheet.row_count,
                    "col_count": worksheet.col_count,
                    "sheet_id": worksheet.id,
                },
            }
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def create_worksheet(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        title: str,
        rows: int = 1000,
        cols: int = 26,
    ) -> dict[str, Any]:
        "创建新工作表"
        try:
            spreadsheet = self._get_spreadsheet(spreadsheet_id)
            worksheet = spreadsheet.add_worksheet(title, rows, cols)
            return {
                "success": True,
                "data": {
                    "sheet_name": title,
                    "row_count": worksheet.row_count,
                    "col_count": worksheet.col_count,
                },
            }
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def delete_worksheet(
        self: _GoogleProtocol, spreadsheet_id: str, sheet_name: str
    ) -> dict[str, Any]:
        """删除工作表"""
        try:
            spreadsheet = self._get_spreadsheet(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            spreadsheet.del_worksheet(worksheet)
            return {"success": True, "data": {"sheet_name": sheet_name}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def duplicate_worksheet(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        source_sheet_name: str,
        new_sheet_name: str,
    ) -> dict[str, Any]:
        """复制工作表"""
        try:
            spreadsheet = self._get_spreadsheet(spreadsheet_id)
            source = spreadsheet.worksheet(source_sheet_name)
            spreadsheet.duplicate_sheet(source.id, new_sheet_name=new_sheet_name)
            new_ws = spreadsheet.worksheet(new_sheet_name)
            return {
                "success": True,
                "data": {
                    "sheet_name": new_sheet_name,
                    "row_count": new_ws.row_count,
                    "col_count": new_ws.col_count,
                },
            }
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def resize_worksheet(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_name: str,
        total_rows: int,
        data_start: int = 2,
    ) -> dict[str, Any]:
        """调整工作表行数并清空旧数据区域"""
        try:
            spreadsheet = self._get_spreadsheet(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            min_rows = total_rows + (data_start - 1)
            current_rows = worksheet.row_count
            current_cols = worksheet.col_count
            if current_rows != min_rows:
                worksheet.resize(rows=min_rows)
            max_col = self._index_to_letter(current_cols - 1)
            clear_range = f"A{data_start}:{max_col}{min_rows}"
            worksheet.batch_clear([clear_range])
            return {"success": True, "data": {"row_count": min_rows, "clear_range": clear_range}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def clear_sheet(self: _GoogleProtocol, spreadsheet_id: str, sheet_name: str) -> dict[str, Any]:
        """彻底清空工作表（内容、格式、合并单元格）"""
        try:
            spreadsheet = self._get_spreadsheet(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            requests = [
                {
                    "updateCells": {
                        "range": {"sheetId": worksheet.id},
                        "fields": "userEnteredValue,userEnteredFormat,pivotTable",
                    }
                },
                {"unmergeCells": {"range": {"sheetId": worksheet.id}}},
            ]
            spreadsheet.batch_update({"requests": requests})
            return {"success": True, "data": {}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}
