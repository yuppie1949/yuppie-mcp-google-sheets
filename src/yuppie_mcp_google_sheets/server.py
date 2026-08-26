"""Google Sheets MCP Server 主入口"""

import os
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from . import __version__
from .tools import drive, sheets, sheets_quick

mcp = MCPServer(
    name="google_sheets_mcp",
    instructions=(
        "Google Sheets 和 Google Drive 操作工具集：读写电子表格范围、管理工作表"
        "（新增/复制/删除/重命名/清空）、追加数据、批量数据处理（更新/追加/按批次读写）、"
        "Auto-resize 行列、设置单元格格式/边框、保护范围、条件格式、图表创建、"
        "Google Drive 文件浏览和搜索。"
    ),
    version=__version__,
)


# ═══════════════════════════════════════════
# Drive 工具
# ═══════════════════════════════════════════

# ✅
@mcp.tool(
    name="gsheets_list_files",
    annotations=ToolAnnotations(
        title="列出 Drive 文件夹中的文件",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def tool_list_files(
    folder_id: Annotated[str, Field(description="Drive 文件夹 ID", min_length=1)],
    file_type: Annotated[
        str | None,
        Field(description="文件 MIME 类型，如 'application/vnd.google-apps.spreadsheet'"),
    ] = None,
) -> str:
    """列出 Google Drive 文件夹中的文件。"""
    return await drive.list_files(drive.ListFilesInput(folder_id=folder_id, file_type=file_type))

# ✅
@mcp.tool(
    name="gsheets_filter_and_sort_files",
    annotations=ToolAnnotations(
        title="按文件名过滤排序",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def tool_filter_and_sort_files(
    file_list: Annotated[list[dict[str, Any]], Field(description="文件列表，每项含 id 和 name")],
    prefix: Annotated[str | None, Field(description="文件名前缀过滤")] = None,
    suffix: Annotated[str | None, Field(description="文件名后缀过滤")] = None,
    datetime_format: Annotated[str | None, Field(description="时间戳格式，如 %%Y%%m%%d")] = None,
    reverse: Annotated[bool, Field(description="是否降序排序，默认 true")] = True,
) -> str:
    """按文件名前缀、后缀过滤，并按时间戳排序。"""
    return await drive.filter_and_sort_files(
        drive.FilterAndSortFilesInput(
            file_list=file_list,
            prefix=prefix,
            suffix=suffix,
            datetime_format=datetime_format,
            reverse=reverse,
        )
    )

# ✅
@mcp.tool(
    name="gsheets_get_storage_quota",
    annotations=ToolAnnotations(
        title="查询 Drive 存储配额",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def tool_get_storage_quota() -> str:
    """查询 Google Drive 存储用量信息。"""
    return await drive.get_storage_quota(drive.GetStorageQuotaInput())

# ✅
@mcp.tool(
    name="gsheets_copy_file",
    annotations=ToolAnnotations(
        title="复制 Drive 文件",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_copy_file(
    file_id: Annotated[str, Field(description="源文件 ID", min_length=1)],
    target_folder_id: Annotated[str, Field(description="目标文件夹 ID", min_length=1)],
    new_name: Annotated[str | None, Field(description="新文件名（可选）")] = None,
) -> str:
    """通过 Google Apps Script 复制文件到指定文件夹（解决服务账号存储配额限制）。"""
    return await drive.copy_file(
        drive.CopyFileInput(file_id=file_id, target_folder_id=target_folder_id, new_name=new_name)
    )


# ═══════════════════════════════════════════
# 工作表管理工具
# ═══════════════════════════════════════════

# ✅
@mcp.tool(
    name="gsheets_get_worksheet",
    annotations=ToolAnnotations(
        title="获取工作表信息",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def tool_get_worksheet(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表id", min_length=1)],
) -> str:
    """获取指定工作表信息（行数、列数、ID）。"""
    return await sheets.get_worksheet(
        sheets.GetWorksheetInput(spreadsheet_id=spreadsheet_id, sheet_id=sheet_id)
    )

# ✅
@mcp.tool(
    name="gsheets_create_worksheet",
    annotations=ToolAnnotations(
        title="创建工作表",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_create_worksheet(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    title: Annotated[str, Field(description="新工作表标题", min_length=1)],
    rows: Annotated[int, Field(description="行数，默认 1000", ge=1)] = 1000,
    cols: Annotated[int, Field(description="列数，默认 26", ge=1, le=18278)] = 26,
) -> str:
    """创建新工作表。"""
    return await sheets.create_worksheet(
        sheets.CreateWorksheetInput(
            spreadsheet_id=spreadsheet_id, title=title, rows=rows, cols=cols
        )
    )

# ✅
@mcp.tool(
    name="gsheets_delete_worksheet",
    annotations=ToolAnnotations(
        title="删除工作表",
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_delete_worksheet(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: str = Field(..., min_length=1, description="工作表id")
) -> str:
    """删除指定工作表。"""
    return await sheets.delete_worksheet(
        sheets.DeleteWorksheetInput(spreadsheet_id=spreadsheet_id, sheet_id=sheet_id)
    )

# ✅
@mcp.tool(
    name="gsheets_duplicate_worksheet",
    annotations=ToolAnnotations(
        title="复制工作表",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_duplicate_worksheet(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    source_sheet_id: Annotated[str, Field(description="源工作表id", min_length=1)],
    insert_sheet_index: Annotated[int | None, Field(description="插入位置")] = None,
    new_sheet_id: Annotated[str | None, Field(description="新工作表id")] = None,
    new_sheet_name: Annotated[str | None, Field(description="新工作表标题")] = None,
) -> str:
    """复制工作表。"""
    return await sheets.duplicate_worksheet(
        sheets.DuplicateWorksheetInput(
            spreadsheet_id=spreadsheet_id,
            source_sheet_id=source_sheet_id,
            insert_sheet_index=insert_sheet_index,
            new_sheet_id=new_sheet_id,
            new_sheet_name=new_sheet_name,
        )
    )


# ═══════════════════════════════════════════
# 数据操作工具
# ═══════════════════════════════════════════

# ✅
@mcp.tool(
    name="gsheets_update_data",
    annotations=ToolAnnotations(
        title="更新工作表数据",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_update_data(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表id", min_length=1)],
    data: Annotated[list[list[Any]], Field(description="二维数据列表")],
    range_name: Annotated[str | None, Field(description="更新范围，如 'A1:B10'")] = None,
) -> str:
    """更新工作表数据。"""
    return await sheets.update_data(
        sheets.UpdateDataInput(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
            data=data,
            range_name=range_name,
        )
    )

# ✅
@mcp.tool(
    name="gsheets_batch_update_data",
    annotations=ToolAnnotations(
        title="批量写入数据",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_batch_update_data(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表id", min_length=1)],
    data: Annotated[list[list[Any]], Field(description="二维数据列表")],
    data_start: Annotated[int, Field(description="数据起始行号（1-based），默认 2", ge=1)] = 2,
    chunk_size: Annotated[int, Field(description="每块写入行数，默认 5000", ge=1, le=5000)] = 5000,
    sleep_interval: Annotated[float, Field(description="每块写入间隔秒数，默认 1.0", ge=0)] = 1.0,
) -> str:
    """批量分块写入数据到工作表。"""
    return await sheets.batch_update_data(
        sheets.BatchUpdateDataInput(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
            data=data,
            data_start=data_start,
            chunk_size=chunk_size,
            sleep_interval=sleep_interval,
        )
    )

# ✅
@mcp.tool(
    name="gsheets_batch_clear",
    annotations=ToolAnnotations(
        title="批量清除区域",
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_batch_clear(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表id", min_length=1)],
    ranges: Annotated[
        list[str], Field(description="范围列表，如 ['A1:B10', 'D1:E20']", min_length=1)
    ],
) -> str:
    """批量清除工作表区域。"""
    return await sheets.batch_clear(
        sheets.BatchClearInput(spreadsheet_id=spreadsheet_id, sheet_id=sheet_id, ranges=ranges)
    )

# ✅
@mcp.tool(
    name="gsheets_visualization_query",
    annotations=ToolAnnotations(
        title="SQL 查询数据",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def tool_visualization_query(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID")],
    query: Annotated[
        str,
        Field(description='SQL 查询，如 "SELECT A, B WHERE C > 100 ORDER BY A DESC LIMIT 10"'),
    ],
) -> str:
    """通过 Google Visualization API 执行 SQL 风格查询。

    支持 SELECT, WHERE, ORDER BY, LIMIT 等子句。
    列引用必须使用大写字母（A, B, C...），不支持表头名称。"""
    return await sheets.visualization_query(
        sheets.VisualizationQueryInput(
            spreadsheet_id=spreadsheet_id,
            query=query,
            sheet_id=sheet_id,
        )
    )


# ═══════════════════════════════════════════
# 格式工具
# ═══════════════════════════════════════════

# ✅
@mcp.tool(
    name="gsheets_set_basic_filter",
    annotations=ToolAnnotations(
        title="设置筛选器",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_set_basic_filter(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表id", min_length=1)],
    start_row: Annotated[int, Field(description="起始行索引（0-based）", ge=0)],
    end_row: Annotated[int, Field(description="结束行索引", ge=0)],
    start_col: Annotated[int, Field(description="起始列索引（0-based）", ge=0)],
    end_col: Annotated[int, Field(description="结束列索引", ge=0)],
) -> str:
    """设置工作表筛选器。"""
    return await sheets.set_basic_filter(
        sheets.SetBasicFilterInput(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
            start_row=start_row,
            end_row=end_row,
            start_col=start_col,
            end_col=end_col,
        )
    )

# ✅
@mcp.tool(
    name="gsheets_set_data_validation",
    annotations=ToolAnnotations(
        title="设置下拉列表",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_set_data_validation(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表id", min_length=1)],
    column_name: Annotated[str, Field(description="列名称", min_length=1)],
    dropdown_options: Annotated[list[str], Field(description="下拉选项列表", min_length=1)],
    data_start: Annotated[
        int, Field(description="数据起始行号，表头=data_start-1，默认 2", ge=1)
    ] = 2,
) -> str:
    """为列设置下拉列表（数据验证）。"""
    return await sheets.set_data_validation(
        sheets.SetDataValidationInput(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
            column_name=column_name,
            dropdown_options=dropdown_options,
            data_start=data_start,
        )
    )

# ✅
@mcp.tool(
    name="gsheets_set_row_height",
    annotations=ToolAnnotations(
        title="设置行高",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_set_row_height(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表id", min_length=1)],
    data_start: Annotated[int, Field(description="数据起始行号（1-based）", ge=1)],
    height: Annotated[int, Field(description="行高（像素）", ge=1)],
) -> str:
    """设置工作表行高（从指定行到末尾）。"""
    return await sheets.set_row_height(
        sheets.SetRowHeightInput(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
            data_start=data_start,
            height=height,
        )
    )


# ═══════════════════════════════════════════
# 表格 (Table) 工具
# ═══════════════════════════════════════════

# ✅
@mcp.tool(
    name="gsheets_get_tables",
    annotations=ToolAnnotations(
        title="获取表格列表",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def tool_get_tables(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表id", min_length=1)],
) -> str:
    """获取工作表中的所有表格。"""
    return await sheets.get_tables(
        sheets.GetTablesInput(spreadsheet_id=spreadsheet_id, sheet_id=sheet_id)
    )

# ✅
@mcp.tool(
    name="gsheets_create_table",
    annotations=ToolAnnotations(
        title="创建表格",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_create_table(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    table: Annotated[dict[str, Any], Field(description="表格配置")],
) -> str:
    """创建表格。"""
    return await sheets.create_table(
        sheets.CreateTableInput(spreadsheet_id=spreadsheet_id, table=table)
    )

# ✅
@mcp.tool(
    name="gsheets_delete_table",
    annotations=ToolAnnotations(
        title="删除表格",
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_delete_table(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    table_id: Annotated[str, Field(description="表格 ID", min_length=1)],
) -> str:
    """删除指定表格。"""
    return await sheets.delete_table(
        sheets.DeleteTableInput(
            spreadsheet_id=spreadsheet_id, table_id=table_id
        )
    )

# ✅
@mcp.tool(
    name="gsheets_delete_table_by_name",
    annotations=ToolAnnotations(
        title="按名称删除表格",
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_delete_table_by_name(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    table_name: Annotated[str, Field(description="表格名称", min_length=1)],
) -> str:
    """按名称删除表格。"""
    return await sheets.delete_table_by_name(
        sheets.DeleteTableByNameInput(
            spreadsheet_id=spreadsheet_id, sheet_id=sheet_id,table_name=table_name
        )
    )


# ═══════════════════════════════════════════
# 快捷操作工具
# ═══════════════════════════════════════════

# ✅
@mcp.tool(
    name="gsheets_filter_columns",
    annotations=ToolAnnotations(
        title="过滤工作表列",
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_filter_columns(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表名称（ID）", min_length=1)],
    keep_columns: Annotated[list[str], Field(description="要保留的列名列表", min_length=1)],
    data_start: Annotated[int, Field(description="数据起始行（1-based），默认 2", ge=1)] = 2,
) -> str:
    """只保留指定列，删除其余列。"""
    return await sheets_quick.quick_sheets_filter_columns(
        sheets_quick.FilterSheetColumnsInput(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
            keep_columns=keep_columns,
            data_start=data_start,
        )
    )


@mcp.tool(
    name="gsheets_set_batch_index",
    annotations=ToolAnnotations(
        title="设置批次索引",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_set_batch_index(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表名称（ID）", min_length=1)],
    batch_column: Annotated[
        str, Field(description="批次列名，默认 f_batch_index")
    ] = "f_batch_index",
    batch_size: Annotated[int, Field(description="每批行数，默认 10", ge=1, le=1000)] = 10,
    data_start: Annotated[int, Field(description="数据起始行（1-based），默认 2", ge=1)] = 2,
) -> str:
    """按列设置批次索引，将数据按 batch_size 分组并写入批次号。"""
    return await sheets_quick.quick_sheets_set_batch_index(
        sheets_quick.SetBatchIndexInput(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
            batch_column=batch_column,
            batch_size=batch_size,
            data_start=data_start,
        )
    )


@mcp.tool(
    name="gsheets_set_header_list",
    annotations=ToolAnnotations(
        title="写入新表头",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_set_header_list(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表名称（ID）", min_length=1)],
    header_list: Annotated[list[str], Field(description="新表头列表", min_length=1)],
    keep_columns: Annotated[
        int | None,
        Field(description="保留的原始列数，不指定则从 A 列写入", ge=0),
    ] = None,
    data_start: Annotated[int, Field(description="表头所在行=data_start-1，默认 2", ge=1)] = 2,
) -> str:
    """从指定位置写入新表头。"""
    return await sheets_quick.quick_sheets_set_header_list(
        sheets_quick.SetHeaderListInput(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
            header_list=header_list,
            keep_columns=keep_columns,
            data_start=data_start,
        )
    )


@mcp.tool(
    name="gsheets_get_column_last_value",
    annotations=ToolAnnotations(
        title="获取列最后一个值",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def tool_get_column_last_value(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表名称（ID）", min_length=1)],
    column_name: Annotated[str, Field(description="列名，将在表头中查找其位置", min_length=1)],
    data_start: Annotated[int, Field(description="数据起始行（1-based），默认 2", ge=1)] = 2,
) -> str:
    """获取指定列中最后一个非空值（跳过表头），用于确定最大批次等场景。"""
    return await sheets_quick.quick_sheets_get_column_last_value(
        sheets_quick.GetColumnLastValueInput(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
            column_name=column_name,
            data_start=data_start,
        )
    )


@mcp.tool(
    name="gsheets_get_rows_by_batch",
    annotations=ToolAnnotations(
        title="按批次读取行",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def tool_get_rows_by_batch(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表名称（ID）", min_length=1)],
    batch_id: Annotated[int, Field(description="批次号，从 1 开始", ge=1)],
    batch_size: Annotated[int, Field(description="每批行数", ge=1, le=5000)],
    data_start: Annotated[int, Field(description="数据起始行（1-based），默认 2", ge=1)] = 2,
) -> str:
    """按批次范围读取行数据，返回 markdown 表格。"""
    return await sheets_quick.quick_sheets_get_rows_by_batch(
        sheets_quick.GetRowsByBatchInput(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
            batch_id=batch_id,
            batch_size=batch_size,
            data_start=data_start,
        )
    )


@mcp.tool(
    name="gsheets_batch_update",
    annotations=ToolAnnotations(
        title="批量更新行数据",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_batch_update(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表名称（ID）", min_length=1)],
    update_data: Annotated[
        list[dict[str, Any]],
        Field(description="更新数据，每行一个 dict，含 row_number 和要更新的列"),
    ],
    columns: Annotated[
        list[str] | None,
        Field(description="要写入的列名列表，不传则从第一条数据自动推导"),
    ] = None,
    data_start: Annotated[int, Field(description="数据起始行（1-based），默认 2", ge=1)] = 2,
) -> str:
    """批量更新多行，一次请求更新所有指定列。"""
    return await sheets_quick.quick_sheets_batch_update(
        sheets_quick.BatchUpdateInput(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
            update_data=update_data,
            columns=columns,
            data_start=data_start,
        )
    )


@mcp.tool(
    name="gsheets_batch_append",
    annotations=ToolAnnotations(
        title="批量追加行数据",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_batch_append(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表名称（ID）", min_length=1)],
    data: Annotated[list[dict[str, Any]], Field(description="要追加的数据，每行一个 dict")],
    batch_size: Annotated[int, Field(description="每批追加行数，默认 500", ge=1, le=5000)] = 500,
    batch_interval: Annotated[int, Field(description="每批追加间隔秒数，默认 2", ge=0, le=30)] = 2,
    data_start: Annotated[int, Field(description="数据起始行（1-based），默认 2", ge=1)] = 2,
    overwrite_start: Annotated[
        int | bool | None,
        Field(description="True 从 data_start 覆写，int 从指定行覆写，None 使用 append 寻址"),
    ] = None,
) -> str:
    """批量追加行到工作表，自动分片并带间隔。指定 overwrite_start 则从该行覆盖写入。"""
    return await sheets_quick.quick_sheets_batch_append(
        sheets_quick.BatchAppendInput(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
            data=data,
            batch_size=batch_size,
            batch_interval=batch_interval,
            data_start=data_start,
            overwrite_start=overwrite_start,
        )
    )


@mcp.tool(
    name="gsheets_sync_from_file",
    annotations=ToolAnnotations(
        title="从 CSV 文件同步数据",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_sync_from_file(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表名称（ID）", min_length=1)],
    file_path: Annotated[str, Field(description="本地 CSV 文件路径")],
    batch_size: Annotated[int, Field(description="每批写入行数，默认 5000", ge=1, le=5000)] = 5000,
    data_start: Annotated[int, Field(description="数据起始行（1-based），默认 2", ge=1)] = 2,
) -> str:
    """从本地 CSV 文件同步数据到工作表。CSV 第一行为表头，默认从 data_start 行开始覆盖写入。"""
    return await sheets_quick.quick_sheets_sync_from_file(
        sheets_quick.SyncFromFileInput(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
            file_path=file_path,
            batch_size=batch_size,
            data_start=data_start,
        )
    )


@mcp.tool(
    name="gsheets_clear_sheet_content",
    annotations=ToolAnnotations(
        title="清空工作表内容（不移除行）",
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_clear_sheet_content(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表名称（ID）", min_length=1)],
    keep_header: Annotated[bool, Field(description="是否保留首行表头，默认 true")] = True,
    data_start: Annotated[int, Field(description="数据起始行号，默认 2", ge=1)] = 2,
    before_column: Annotated[
        str | None,
        Field(description='指定列字母（如 "F"），只清空该列之前的所有列。不指定则清空全部列'),
    ] = None,
) -> str:
    """清空工作表数据内容（不移除行）。指定 before_column 则只清空该列之前的所有列。"""
    return await sheets_quick.quick_sheets_clear_sheet_content(
        sheets_quick.ClearSheetContentInput(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
            keep_header=keep_header,
            data_start=data_start,
            before_column=before_column,
        )
    )


@mcp.tool(
    name="gsheets_clear_sheet",
    annotations=ToolAnnotations(
        title="清空工作表数据（删除行）",
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def tool_clear_sheet(
    spreadsheet_id: Annotated[str, Field(description="电子表格 ID", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表名称（ID）", min_length=1)],
    keep_header: Annotated[bool, Field(description="是否保留首行表头，默认 true")] = True,
    data_start: Annotated[int, Field(description="数据起始行号，默认 2", ge=1)] = 2,
) -> str:
    """清空工作表数据（删除行），默认保留首行表头。"""
    return await sheets_quick.quick_sheets_clear_sheet(
        sheets_quick.ClearSheetInput(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
            keep_header=keep_header,
            data_start=data_start,
        )
    )


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "8000")),
        )
    else:
        mcp.run()


if __name__ == "__main__":
    main()
