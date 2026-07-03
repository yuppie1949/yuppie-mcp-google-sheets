"""GoogleSheetsClient 底层测试（仅测纯函数，不测网络调用）"""

import pytest

from yuppie_mcp_google_sheets.utils.google.base import _GoogleBase


@pytest.mark.parametrize(
    "index,expected",
    [
        (0, "A"),
        (1, "B"),
        (25, "Z"),
        (26, "AA"),
        (27, "AB"),
        (51, "AZ"),
        (52, "BA"),
        (701, "ZZ"),
        (702, "AAA"),
    ],
)
def test_index_to_letter(index: int, expected: str) -> None:
    assert _GoogleBase._index_to_letter(index) == expected


def test_format_error_value_error() -> None:
    err = _GoogleBase._format_error(ValueError("test error"))
    assert err == {"code": -1, "msg": "test error"}


def test_format_error_timeout() -> None:
    err = _GoogleBase._format_error(TimeoutError("timeout"))
    assert err == {"code": -1, "msg": "请求超时"}


def test_format_error_generic() -> None:
    err = _GoogleBase._format_error(RuntimeError("something broke"))
    assert err == {"code": -1, "msg": "something broke"}


def test_google_sheets_client_aggregates_all_mixins() -> None:
    """GoogleSheetsClient 实例应具备所有 mixin 方法"""
    from yuppie_mcp_google_sheets.utils.google import GoogleSheetsClient

    client = GoogleSheetsClient()
    # 工作表域
    assert callable(getattr(client, "get_worksheet", None))
    assert callable(getattr(client, "create_worksheet", None))
    assert callable(getattr(client, "delete_worksheet", None))
    assert callable(getattr(client, "duplicate_worksheet", None))
    assert callable(getattr(client, "resize_worksheet", None))
    assert callable(getattr(client, "clear_sheet", None))
    # 数据域
    assert callable(getattr(client, "update_data", None))
    assert callable(getattr(client, "batch_update_data", None))
    assert callable(getattr(client, "batch_clear", None))
    assert callable(getattr(client, "visualization_query", None))
    # 格式域
    assert callable(getattr(client, "set_basic_filter", None))
    assert callable(getattr(client, "set_data_validation", None))
    assert callable(getattr(client, "set_row_height", None))
    # 表格域
    assert callable(getattr(client, "get_tables", None))
    assert callable(getattr(client, "create_table", None))
    assert callable(getattr(client, "delete_table", None))
    # 快捷操作域
    assert callable(getattr(client, "quick_sheets_filter_columns", None))
    assert callable(getattr(client, "quick_sheets_set_batch_index", None))
    assert callable(getattr(client, "quick_sheets_batch_update", None))
    # Drive 域
    assert callable(getattr(client, "list_files", None))
    assert callable(getattr(client, "copy_file", None))
    assert callable(getattr(client, "get_storage_quota", None))
