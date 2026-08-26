"""表格操作 mixin — 查询、删除、创建"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import _GoogleProtocol

if TYPE_CHECKING:
    pass


class TableMixin:
    """表格管理方法（混入 _GoogleBase 子类使用）"""

    def get_tables(self: _GoogleProtocol, spreadsheet_id: str, sheet_id: str) -> dict[str, Any]:
        """获取工作表中的所有表格"""
        try:
            ws = self._get_spreadsheet(spreadsheet_id).get_worksheet_by_id(sheet_id)
            meta = self._get_spreadsheet(spreadsheet_id).fetch_sheet_metadata()
            sheet_data = next(
                (s for s in meta.get("sheets", []) if s["properties"]["sheetId"] == ws.id), None
            )
            tables = sheet_data.get("tables", []) if sheet_data else []
            return {"success": True, "data": {"tables": tables}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def delete_table(
        self: _GoogleProtocol, spreadsheet_id: str, table_id: int
    ) -> dict[str, Any]:
        """删除指定表格"""
        try:
            req = {"deleteTable": {"tableId": table_id}}
            self._get_spreadsheet(spreadsheet_id).batch_update({"requests": [req]})
            return {"success": True, "data": {"table_id": table_id}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def delete_table_by_name(
        self: _GoogleProtocol, spreadsheet_id: str, sheet_id: str, table_name: str
    ) -> dict[str, Any]:
        """按名称删除表格"""
        try:
            tables_result = self.get_tables(spreadsheet_id, sheet_id)
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
        self: _GoogleProtocol, spreadsheet_id: str, table: dict[str, Any]
    ) -> dict[str, Any]:
        """创建表格（透传 Google Sheets API addTable 的 Table 对象）

        Args:
            spreadsheet_id: 电子表格 ID
            table: Table 对象。columnProperties 项数必须等于列范围宽度，
                且每项必须显式指定 columnIndex（相对表格的 0-based 索引，省略会报
                "Duplicate column indexes"）。columnType 可选值：TEXT / DOUBLE /
                CURRENCY / PERCENT / DATE / TIME / DATE_TIME / BOOLEAN / DROPDOWN 等。
                不要填 tableId（由 API 自动分配）。已验证示例：

                {
                    "range": {
                        "sheetId": 843703152,
                        "startRowIndex": 0,      # 0-based，首行为表头
                        "endRowIndex": 11,       # 半开区间：表头 + 10 行数据
                        "startColumnIndex": 0,
                        "endColumnIndex": 3      # 3 列 = A/B/C
                    },
                    "columnProperties": [
                        {"columnIndex": 0, "columnName": "姓名", "columnType": "TEXT"},
                        {"columnIndex": 1, "columnName": "分数", "columnType": "DOUBLE"},
                        {"columnIndex": 2, "columnName": "日期", "columnType": "DATE"}
                    ]
                }
        """
        try:
            req = {"addTable": {"table": table}}
            self._get_spreadsheet(spreadsheet_id).batch_update({"requests": [req]})
            return {"success": True, "data": {"table_name": table.get("name", "unknown")}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}
