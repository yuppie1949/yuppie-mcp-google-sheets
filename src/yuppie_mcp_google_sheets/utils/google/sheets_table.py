"""表格操作 mixin — 查询、删除、创建"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import _GoogleProtocol

if TYPE_CHECKING:
    pass


class TableMixin:
    """表格管理方法（混入 _GoogleBase 子类使用）"""

    def get_tables(self: _GoogleProtocol, spreadsheet_id: str, sheet_name: str) -> dict[str, Any]:
        """获取工作表中的所有表格"""
        try:
            ws = self._get_spreadsheet(spreadsheet_id).worksheet(sheet_name)
            meta = self._get_spreadsheet(spreadsheet_id).fetch_sheet_metadata()
            sheet_data = next(
                (s for s in meta.get("sheets", []) if s["properties"]["sheetId"] == ws.id), None
            )
            tables = sheet_data.get("tables", []) if sheet_data else []
            return {"success": True, "data": {"tables": tables}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def delete_table(
        self: _GoogleProtocol, spreadsheet_id: str, sheet_name: str, table_id: int
    ) -> dict[str, Any]:
        """删除指定表格"""
        try:
            req = {"deleteTable": {"tableId": table_id}}
            self._get_spreadsheet(spreadsheet_id).batch_update({"requests": [req]})
            return {"success": True, "data": {"table_id": table_id}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def delete_table_by_name(
        self: _GoogleProtocol, spreadsheet_id: str, sheet_name: str, table_name: str
    ) -> dict[str, Any]:
        """按名称删除表格"""
        try:
            tables_result = self.get_tables(spreadsheet_id, sheet_name)
            if not tables_result["success"]:
                return tables_result
            spreadsheet = self._get_spreadsheet(spreadsheet_id)
            deleted_count = 0
            for t in tables_result["data"]["tables"]:
                if t.get("name") == table_name:
                    spreadsheet.batch_update(
                        {"requests": [{"deleteTable": {"tableId": t["tableId"]}}]}
                    )
                    deleted_count += 1
            if deleted_count == 0:
                return {
                    "success": False,
                    "error": {"code": -1, "msg": f"未找到名为 '{table_name}' 的表格"},
                }
            return {"success": True, "data": {"deleted_count": deleted_count}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def create_table(
        self: _GoogleProtocol, spreadsheet_id: str, sheet_name: str, table: dict[str, Any]
    ) -> dict[str, Any]:
        """创建表格"""
        try:
            req = {"addTable": {"table": table}}
            self._get_spreadsheet(spreadsheet_id).batch_update({"requests": [req]})
            return {"success": True, "data": {"table_name": table.get("name", "unknown")}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}
