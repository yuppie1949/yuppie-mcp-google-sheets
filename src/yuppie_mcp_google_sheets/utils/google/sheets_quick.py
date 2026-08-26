"""电子表格快捷业务操作 mixin — 跨项目复用，基于 gspread 实现"""

from __future__ import annotations

import csv
import os
import time
from itertools import groupby
from typing import TYPE_CHECKING, Any

from .base import _GoogleProtocol

if TYPE_CHECKING:
    pass


class QuickSheetsMixin:
    """电子表格批量快捷操作（混入 _GoogleBase 子类使用）"""

    _RETRY_MAX_ATTEMPTS = 5
    _RETRY_BASE_DELAY = 30.0

    def _find_last_data_row(self: _GoogleProtocol, ws: Any) -> int:
        """找到工作表首列最后一个非空行号（1-based）"""
        return len(ws.col_values(1))

    def _update_with_retry(self: _GoogleProtocol, ws: Any, **kwargs: Any) -> None:
        """执行 ws.update，429 配额超限时指数退避重试"""
        for attempt in range(1, self._RETRY_MAX_ATTEMPTS + 1):
            try:
                ws.update(**kwargs)
                return
            except Exception as e:
                if "429" not in str(e) or attempt == self._RETRY_MAX_ATTEMPTS:
                    raise
                delay = self._RETRY_BASE_DELAY * attempt
                time.sleep(delay)

    def _values_batch_update_with_retry(
        self: _GoogleProtocol, spreadsheet: Any, body: dict[str, Any]
    ) -> None:
        """执行 values.batchUpdate，429 配额超限时指数退避重试"""
        for attempt in range(1, self._RETRY_MAX_ATTEMPTS + 1):
            try:
                spreadsheet.values_batch_update(body)
                return
            except Exception as e:
                if "429" not in str(e) or attempt == self._RETRY_MAX_ATTEMPTS:
                    raise
                delay = self._RETRY_BASE_DELAY * attempt
                time.sleep(delay)

    def _read_headers(
        self: _GoogleProtocol, spreadsheet_id: str, sheet_id: str, data_start: int
    ) -> list[str]:
        """读取表头行"""
        ws = self._get_spreadsheet(spreadsheet_id).get_worksheet_by_id(sheet_id)
        return ws.row_values(data_start - 1)

    def _get_col_count(self: _GoogleProtocol, spreadsheet_id: str, sheet_id: str) -> int:
        """获取工作表列数"""
        ws = self._get_spreadsheet(spreadsheet_id).get_worksheet_by_id(sheet_id)
        return ws.col_count

    def _resolve_col_letter(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_id: str,
        column_name: str,
        data_start: int,
    ) -> str:
        """根据列名解析列字母"""
        headers = self._read_headers(spreadsheet_id, sheet_id, data_start)
        for i, h in enumerate(headers):
            if h == column_name:
                return self._index_to_letter(i)
        raise ValueError(f"未找到列 '{column_name}'")

    def _ensure_column(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_id: str,
        column_name: str,
        data_start: int,
    ) -> str:
        """确保列存在，不存在则创建"""
        try:
            return self._resolve_col_letter(spreadsheet_id, sheet_id, column_name, data_start)
        except ValueError:
            headers = self._read_headers(spreadsheet_id, sheet_id, data_start)
            col_letter = self._index_to_letter(len(headers))
            ws = self._get_spreadsheet(spreadsheet_id).get_worksheet_by_id(sheet_id)
            ws.update(values=[[column_name]], range_name=f"{col_letter}{data_start - 1}")
            return col_letter

    def quick_sheets_filter_columns(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_id: str,
        keep_columns: list[str],
        *,
        data_start: int = 2,
    ) -> str:
        """只保留指定列，删除其余列（包括空白列），返回 sheetId"""
        headers = self._read_headers(spreadsheet_id, sheet_id, data_start)
        col_count = len(headers)
        if col_count <= 0:
            return sheet_id

        keep = set()
        for col in keep_columns:
            if col in headers:
                keep.add(headers.index(col))
        if not keep:
            return sheet_id

        drop = sorted(i for i in range(col_count) if i not in keep)
        if not drop:
            return sheet_id

        # 合并连续区间，逆序删除
        groups: list[tuple[int, int]] = []
        for _, g in groupby(enumerate(drop), key=lambda x: x[1] - x[0]):
            gl = list(g)
            groups.append((gl[0][1] + 1, gl[-1][1] + 1))

        for s, e in reversed(groups):
            spreadsheet = self._get_spreadsheet(spreadsheet_id)
            ws = spreadsheet.get_worksheet_by_id(sheet_id)
            req = {
                "deleteDimension": {
                    "range": {
                        "sheetId": ws.id,
                        "dimension": "COLUMNS",
                        "startIndex": s,
                        "endIndex": e + 1,
                    }
                }
            }
            spreadsheet.batch_update({"requests": [req]})

        return sheet_id

    def quick_sheets_set_batch_index(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_id: str,
        *,
        batch_column: str = "f_batch_index",
        batch_size: int = 10,
        data_start: int = 2,
    ) -> None:
        """按列设置批次索引"""
        col_letter = self._ensure_column(spreadsheet_id, sheet_id, batch_column, data_start)
        ws = self._get_spreadsheet(spreadsheet_id).get_worksheet_by_id(sheet_id)
        data = ws.col_values(1)

        rows_to_write: list[tuple[int, int]] = []
        batch_num = 1
        row_count = 0
        for i in range(data_start - 1, len(data)):
            val = str(data[i]).strip() if i < len(data) and data[i] else ""
            if val:
                rows_to_write.append((i + 1, batch_num))
                row_count += 1
                if row_count >= batch_size:
                    batch_num += 1
                    row_count = 0

        if not rows_to_write:
            return

        # 合并连续行，按块写入（5000 行/块），避免每批次一个请求导致 429
        first = rows_to_write[0][0]
        last = rows_to_write[-1][0]
        values: list[list[str]] = [[""] for _ in range(first, last + 1)]
        for row_num, batch_val in rows_to_write:
            values[row_num - first] = [str(batch_val)]

        ws = self._get_spreadsheet(spreadsheet_id).get_worksheet_by_id(sheet_id)
        chunk_size = 50000
        for i in range(0, len(values), chunk_size):
            chunk = values[i : i + chunk_size]
            start_row = first + i
            rng = f"{col_letter}{start_row}:{col_letter}{start_row + len(chunk) - 1}"
            self._update_with_retry(ws, values=chunk, range_name=rng)

    def quick_sheets_set_header_list(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_id: str,
        header_list: list[str],
        *,
        keep_columns: int | None = None,
        data_start: int = 2,
    ) -> None:
        """从指定位置写入新表头，超出网格时自动扩列"""
        header_row = data_start - 1
        start_col = keep_columns if keep_columns is not None else 0
        start_letter = self._index_to_letter(start_col)
        end_letter = self._index_to_letter(start_col + len(header_list) - 1)
        ws = self._get_spreadsheet(spreadsheet_id).get_worksheet_by_id(sheet_id)
        end_col_index = start_col + len(header_list)
        if end_col_index > ws.col_count:
            ws.add_cols(end_col_index - ws.col_count)
        ws.update(
            values=[header_list],
            range_name=f"{start_letter}{header_row}:{end_letter}{header_row}",
        )

    def quick_sheets_get_last_value(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_id: str,
        column_name: str,
        *,
        data_start: int = 2,
    ) -> dict[str, Any]:
        """获取指定列中最后一个非空值和行号"""
        col_letter = self._resolve_col_letter(spreadsheet_id, sheet_id, column_name, data_start)
        ws = self._get_spreadsheet(spreadsheet_id).get_worksheet_by_id(sheet_id)
        vals = ws.get(f"{col_letter}:{col_letter}")
        for i in range(len(vals) - 1, data_start - 2, -1):
            row = vals[i]
            if row and row[0] is not None and str(row[0]).strip():
                return {"value": row[0], "row_number": i + 1}
        return {"value": None, "row_number": 0}

    def quick_sheets_get_rows_by_batch(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_id: str,
        batch_id: int,
        batch_size: int,
        *,
        data_start: int = 2,
    ) -> list[dict[str, Any]]:
        """按批次获取行数据"""
        headers = self._read_headers(spreadsheet_id, sheet_id, data_start)
        if not headers:
            return []

        ws = self._get_spreadsheet(spreadsheet_id).get_worksheet_by_id(sheet_id)
        col_count = ws.col_count
        end_col = self._index_to_letter(col_count - 1)
        start_row = data_start + (batch_id - 1) * batch_size
        end_row = start_row + batch_size - 1
        all_data = ws.get(f"A{start_row}:{end_col}{end_row}")

        result: list[dict[str, Any]] = []
        for row_offset, row in enumerate(all_data):
            row_dict: dict[str, Any] = {}
            for col_idx, header in enumerate(headers):
                row_dict[header] = row[col_idx] if col_idx < len(row) else ""
            row_dict["row_number"] = start_row + row_offset
            result.append(row_dict)
        return result

    def quick_sheets_batch_update(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_id: str,
        update_data: list[dict[str, Any]],
        columns: list[str] | None = None,
        *,
        data_start: int = 2,
    ) -> None:
        """批量更新多行（不连续列拆成区间，values.batchUpdate 单请求写入）

        Args:
            spreadsheet_id: 电子表格 ID
            sheet_id: 工作表 ID（数字 gid）
            update_data: 每行一个 dict，必须含 row_number（1-based），其余键为列名。
                列名须与表头一致；不存在的列或缺失的键会被跳过。
            columns: 要写入的列名列表；不传则从第一条数据的键自动推导（除 row_number 外）。
            data_start: 表头行 = data_start - 1，默认 2。

        示例（表头为 ['partner id', 'name', 'status']）：

            更新多行，columns 自动推导（只更新每行出现的列）:
            {
                "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBk...",
                "sheet_id": "843703152",
                "update_data": [
                    {"row_number": 2, "name": "alice", "status": "done"},
                    {"row_number": 5, "name": "bob"}
                ]
            }
            → 第 2 行写 B2=alice、C2=done；第 5 行写 B5=bob。

            只更新指定列，忽略数据里的其他键:
            {
                "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBk...",
                "sheet_id": "843703152",
                "update_data": [
                    {"row_number": 3, "name": "carol", "status": "ignored"}
                ],
                "columns": ["name"]
            }
            → 仅 B3=carol，status 不写入。

            同一行更新不连续列（A、C），B 列不受影响:
            {
                "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBk...",
                "sheet_id": "843703152",
                "update_data": [
                    {"row_number": 4, "partner id": "p99", "status": "done"}
                ]
            }
            → 拆成 A4 与 C4 两个区间写入。
        """
        if not update_data:
            return
        if columns is None:
            columns = [k for k in update_data[0] if k != "row_number"]

        headers = self._read_headers(spreadsheet_id, sheet_id, data_start)
        col_indices = {h: i for i, h in enumerate(headers) if h is not None}
        spreadsheet = self._get_spreadsheet(spreadsheet_id)
        ws = spreadsheet.get_worksheet_by_id(sheet_id)

        def letter(i: int) -> str:
            return self._index_to_letter(i)

        data_values: list[dict[str, Any]] = []
        for row in update_data:
            row_number = row.get("row_number")
            if not row_number:
                continue
            try:
                row_number = int(row_number)
            except (ValueError, TypeError):
                continue

            # 本行要写的列索引，排序后切连续区间（A、C 不连续 → A、C 两段）
            col_idx = sorted(
                col_indices[c] for c in columns if c in col_indices and c in row
            )
            if not col_idx:
                continue

            spans: list[list[int]] = []
            for i in col_idx:
                if spans and i == spans[-1][-1] + 1:
                    spans[-1].append(i)
                else:
                    spans.append([i])

            for span in spans:
                idx_to_col = {col_indices[c]: c for c in columns if c in col_indices and c in row}
                span_range = (
                    f"{ws.title}!{letter(span[0])}{row_number}:{letter(span[-1])}{row_number}"
                )
                data_values.append(
                    {"range": span_range, "values": [[row[idx_to_col[i]]] for i in span]}
                )

        if not data_values:
            return

        # values.batchUpdate 一次请求写全部区间；区间数过多时分批（每批 500）
        batch_size = 500
        for i in range(0, len(data_values), batch_size):
            chunk = data_values[i : i + batch_size]
            self._values_batch_update_with_retry(
                spreadsheet,
                {"valueInputOption": "USER_ENTERED", "data": chunk},
            )

    def quick_sheets_clear_sheet(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_id: str,
        *,
        keep_header: bool = True,
        data_start: int = 2,
    ) -> None:
        """清空工作表（删除行），默认保留首行表头"""
        ws = self._get_spreadsheet(spreadsheet_id).get_worksheet_by_id(sheet_id)
        row_count = ws.row_count
        start = data_start if keep_header else 1
        if start > row_count:
            return

        for end in range(row_count, start - 1, -5000):
            chunk_start = max(start, end - 5000 + 1)
            req = {
                "deleteDimension": {
                    "range": {
                        "sheetId": ws.id,
                        "dimension": "ROWS",
                        "startIndex": chunk_start - 1,
                        "endIndex": end,
                    }
                }
            }
            self._get_spreadsheet(spreadsheet_id).batch_update({"requests": [req]})

    def quick_sheets_clear_sheet_content(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_id: str,
        *,
        keep_header: bool = True,
        data_start: int = 2,
        before_column: str | None = None,
    ) -> dict[str, Any]:
        """清空工作表数据内容（不移除行），默认保留首行表头"""
        ws = self._get_spreadsheet(spreadsheet_id).get_worksheet_by_id(sheet_id)
        row_count = ws.row_count
        start = data_start if keep_header else 1
        if start > row_count:
            return {"col_count": 0, "row_count": 0, "start_row": start}

        if before_column:
            upper = before_column.upper().strip()
            before_idx = 0
            for ch in upper:
                before_idx = before_idx * 26 + (ord(ch) - ord("A") + 1)
            if before_idx <= 1:
                return {"col_count": 0, "row_count": 0, "start_row": start}
            clear_count = before_idx - 1
            end_col = self._index_to_letter(clear_count - 1)
            empty_row = [""] * clear_count
        else:
            col_count = ws.col_count
            if col_count <= 0:
                return {"col_count": 0, "row_count": 0, "start_row": start}
            end_col = self._index_to_letter(col_count - 1)
            empty_row = [""] * col_count

        for batch_start in range(start, row_count + 1, 5000):
            batch_end = min(batch_start + 5000 - 1, row_count)
            vals = [empty_row] * (batch_end - batch_start + 1)
            ws.update(values=vals, range_name=f"A{batch_start}:{end_col}{batch_end}")

        return {"col_count": len(empty_row), "row_count": row_count - start + 1, "start_row": start}

    def quick_sheets_batch_append(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_id: str,
        data: list[dict[str, Any]],
        *,
        batch_size: int = 500,
        batch_interval: int = 2,
        data_start: int = 2,
        overwrite_start: int | bool | None = None,
    ) -> None:
        """批量追加行数据，自动分片并带间隔

        overwrite_start:
            None — 追加：从现有数据末尾之后逐批写入，不覆盖已有数据
            True — 覆盖：从 data_start 行开始逐批覆盖写
            int  — 覆盖：从指定行开始逐批覆盖写
        """
        if not data:
            return
        headers = list(data[0].keys()) if isinstance(data[0], dict) else []
        values: list[list[str]] = [[str(row.get(h, "")) for h in headers] for row in data]

        ws = self._get_spreadsheet(spreadsheet_id).get_worksheet_by_id(sheet_id)
        end_col = self._index_to_letter(len(headers) - 1)
        if overwrite_start is None:
            # 追加：找现有数据最后一行（首列最后一个非空），从下一行开始写
            start_row = self._find_last_data_row(ws) + 1
        else:
            start_row = data_start if overwrite_start is True else int(overwrite_start)

        for i in range(0, len(values), batch_size):
            chunk = values[i : i + batch_size]
            row_start = start_row + i
            row_end = row_start + len(chunk) - 1
            ws.update(values=chunk, range_name=f"A{row_start}:{end_col}{row_end}")
            if i + batch_size < len(values) and batch_interval > 0:
                time.sleep(batch_interval)

    def quick_sheets_sync_from_file(
        self: _GoogleProtocol,
        spreadsheet_id: str,
        sheet_id: str,
        file_path: str,
        *,
        batch_size: int = 5000,
        data_start: int = 2,
    ) -> None:
        """从本地 CSV 文件同步数据到工作表"""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            if not fieldnames:
                raise ValueError("CSV 文件缺少表头")
            rows = list(reader)

        if not rows:
            raise ValueError("CSV 文件没有数据行")

        self.quick_sheets_batch_append(
            spreadsheet_id,
            sheet_id,
            rows,
            batch_size=batch_size,
            batch_interval=2,
            data_start=data_start,
            overwrite_start=True,
        )
