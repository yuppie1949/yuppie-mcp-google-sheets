"""GoogleSheetsClient — 通过 mixin 聚合工作表、数据、格式化、表格、快捷操作能力

对外只暴露 GoogleSheetsClient 一个类。gspread http client 由 _GoogleBase 统一管理，
各业务域方法分散在独立模块便于维护。
"""

from __future__ import annotations

from .base import _GoogleBase
from .drive import DriveMixin
from .sheets_data import DataMixin
from .sheets_format import FormatMixin
from .sheets_quick import QuickSheetsMixin
from .sheets_table import TableMixin
from .sheets_worksheet import WorksheetMixin

__all__ = ["GoogleSheetsClient"]


class GoogleSheetsClient(
    _GoogleBase,
    WorksheetMixin,
    DataMixin,
    FormatMixin,
    TableMixin,
    QuickSheetsMixin,
    DriveMixin,
):
    """Google Sheets API 客户端"""

    pass
