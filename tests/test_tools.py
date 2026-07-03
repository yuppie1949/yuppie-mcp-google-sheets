"""tools 层 BaseModel 输入校验测试"""

import pytest
from pydantic import ValidationError

from yuppie_mcp_google_sheets.tools.sheets import (
    GetWorksheetInput,
    CreateWorksheetInput,
    DeleteWorksheetInput,
    DuplicateWorksheetInput,
    UpdateDataInput,
    BatchUpdateDataInput,
    BatchClearInput,
    VisualizationQueryInput,
    SetBasicFilterInput,
    SetDataValidationInput,
    SetRowHeightInput,
)
from yuppie_mcp_google_sheets.tools.sheets_quick import (
    FilterSheetColumnsInput,
    SetBatchIndexInput,
    SetHeaderListInput,
    GetColumnLastValueInput,
    GetRowsByBatchInput,
    BatchUpdateInput,
    BatchAppendInput,
    ClearSheetContentInput,
    ClearSheetInput,
)
from yuppie_mcp_google_sheets.tools.drive import (
    ListFilesInput,
    CopyFileInput,
)


# ── 工作表域 ──


def test_get_worksheet_required() -> None:
    with pytest.raises(ValidationError):
        GetWorksheetInput()


def test_get_worksheet_valid() -> None:
    args = GetWorksheetInput(spreadsheet_id="sid", sheet_name="Sheet1")
    assert args.spreadsheet_id == "sid"
    assert args.sheet_name == "Sheet1"


def test_create_worksheet_defaults() -> None:
    args = CreateWorksheetInput(spreadsheet_id="sid", title="New")
    assert args.rows == 1000
    assert args.cols == 26


def test_delete_worksheet_required() -> None:
    with pytest.raises(ValidationError):
        DeleteWorksheetInput()


def test_duplicate_worksheet_valid() -> None:
    args = DuplicateWorksheetInput(
        spreadsheet_id="sid", source_sheet_name="Src", new_sheet_name="Dst"
    )
    assert args.source_sheet_name == "Src"


# ── 数据域 ──


def test_update_data_valid() -> None:
    args = UpdateDataInput(
        spreadsheet_id="sid", sheet_name="Sheet1", data=[["a", "b"], ["1", "2"]]
    )
    assert len(args.data) == 2


def test_batch_update_data_defaults() -> None:
    args = BatchUpdateDataInput(
        spreadsheet_id="sid", sheet_name="Sheet1", data=[["a"]]
    )
    assert args.start_row == 2
    assert args.chunk_size == 5000


def test_batch_clear_required_ranges() -> None:
    with pytest.raises(ValidationError):
        BatchClearInput(spreadsheet_id="sid", sheet_name="Sheet1")


def test_visualization_query_required() -> None:
    with pytest.raises(ValidationError):
        VisualizationQueryInput()


def test_visualization_query_valid() -> None:
    args = VisualizationQueryInput(
        spreadsheet_id="sid", query="SELECT A, B WHERE C > 100"
    )
    assert args.headers == 1


# ── 格式域 ──


def test_set_basic_filter_valid() -> None:
    args = SetBasicFilterInput(
        spreadsheet_id="sid", sheet_name="Sheet1",
        start_row=0, end_row=100, start_col=0, end_col=10,
    )
    assert args.end_row == 100


def test_set_data_validation_valid() -> None:
    args = SetDataValidationInput(
        spreadsheet_id="sid", sheet_name="Sheet1",
        column_name="Status", dropdown_options=["Open", "Closed"],
    )
    assert len(args.dropdown_options) == 2
    assert args.header_row == 1


def test_set_row_height_valid() -> None:
    args = SetRowHeightInput(
        spreadsheet_id="sid", sheet_name="Sheet1",
        data_start_row=2, height=40,
    )
    assert args.height == 40


# ── 快捷操作域 ──


def test_filter_columns_required() -> None:
    with pytest.raises(ValidationError):
        FilterSheetColumnsInput()


def test_filter_columns_valid() -> None:
    args = FilterSheetColumnsInput(
        spreadsheet_id="sid", sheet_id="Sheet1", keep_columns=["Name", "Age"],
    )
    assert args.data_start == 2


def test_set_batch_index_defaults() -> None:
    args = SetBatchIndexInput(
        spreadsheet_id="sid", sheet_id="Sheet1",
    )
    assert args.batch_column == "f_batch_index"
    assert args.batch_size == 10


def test_set_header_list_valid() -> None:
    args = SetHeaderListInput(
        spreadsheet_id="sid", sheet_id="Sheet1",
        header_list=["H1", "H2", "H3"],
    )
    assert len(args.header_list) == 3


def test_get_column_last_value_valid() -> None:
    args = GetColumnLastValueInput(
        spreadsheet_id="sid", sheet_id="Sheet1", column_name="batch",
    )
    assert args.column_name == "batch"


def test_get_rows_by_batch_required() -> None:
    with pytest.raises(ValidationError):
        GetRowsByBatchInput()


def test_get_rows_by_batch_valid() -> None:
    args = GetRowsByBatchInput(
        spreadsheet_id="sid", sheet_id="Sheet1", batch_id=1, batch_size=10,
    )
    assert args.batch_id == 1


def test_batch_update_valid() -> None:
    args = BatchUpdateInput(
        spreadsheet_id="sid", sheet_id="Sheet1",
        update_data=[{"row_number": 2, "Name": "Alice"}],
    )
    assert len(args.update_data) == 1


def test_batch_append_defaults() -> None:
    args = BatchAppendInput(
        spreadsheet_id="sid", sheet_id="Sheet1",
        data=[{"Name": "Alice"}],
    )
    assert args.batch_size == 500
    assert args.overwrite_start is None


def test_clear_sheet_content_defaults() -> None:
    args = ClearSheetContentInput(spreadsheet_id="sid", sheet_id="Sheet1")
    assert args.keep_header is True
    assert args.before_column is None


def test_clear_sheet_defaults() -> None:
    args = ClearSheetInput(spreadsheet_id="sid", sheet_id="Sheet1")
    assert args.keep_header is True
    assert args.data_start == 2


# ── Drive 域 ──


def test_list_files_required() -> None:
    with pytest.raises(ValidationError):
        ListFilesInput()


def test_list_files_valid() -> None:
    args = ListFilesInput(folder_id="folder123")
    assert args.folder_id == "folder123"
    assert args.file_type is None


def test_copy_file_required() -> None:
    with pytest.raises(ValidationError):
        CopyFileInput()


def test_copy_file_valid() -> None:
    args = CopyFileInput(file_id="fid", target_folder_id="tid", new_name="copy.xlsx")
    assert args.file_id == "fid"
    assert args.new_name == "copy.xlsx"


# ── extra="forbid" 校验 ──


def test_extra_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        GetWorksheetInput(spreadsheet_id="sid", sheet_name="Sheet1", extra_field="bad")
