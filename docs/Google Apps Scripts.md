https://developers.google.com/apps-script/overview?hl=zh-cn

## main.gs
```gs
SCRIPT_VERSION = 'V0.0.14';

/**
 * Web App 入口函数，处理 POST 请求。
 * @param {object} e 接收来自 n8n 的请求体数据。
 */
function doPost(e) {
    try {
        // 1. 解析请求体 (通用工具)
        const requestData = Utils.parseRequest(e); 
        
        // 2. 调用独立抽离的路由和执行函数
        return routeAndExecute(requestData); 
        
    } catch (error) {
        // 捕获 routeAndExecute 或 Utils.parseRequest 中抛出的所有未处理异常
        return Utils.errorResponse(1000, "处理请求失败", error.message);
    }
}

/**
 * 核心路由和执行函数。
 * 根据 requestData 中的 project 和 action 路由到具体的处理对象和方法。
 * @param {object} requestData 从 doPost(e) 中解析出的请求体数据。
 * @returns {object} 成功响应对象（使用 Utils.successResponse 格式）。
 * @throws {Error} 如果路由参数缺失或无效，或者业务逻辑执行失败。
 */
function routeAndExecute(requestData) {
    
    // 1. 提取路由关键参数
    const project = requestData.project;
    const action = requestData.action;

    if (!project || !action) {
        throw new Error("请求中缺少必要的参数: project 或 action");
    }

    let handler; // 将被赋值为 SpreadsheetUtils, ProjectDmzdsj 或 ProjectJsfhl

    // 2. 根据 project 字段进行顶层路由
    switch (project) {
        case 'Utils':
            handler = Utils;
            break;
        case 'Jsfhl':
            handler = ProjectJsfhl;
            break;
        case 'Ppzggzsx':
            handler = ProjectPpzggzsx;
            break;
        case 'google_drive':
            handler = ApiGoogleDrive;
            break;
        case 'google_sheet':
            handler = ApiGoogleSheet;
            break;
        default:
            throw new Error(`无效的 project 类型: ${project}`);
    }

    // 3. 校验 handler 是否存在对应的 action 方法
    const handlerFunction = handler[action];
    if (typeof handlerFunction !== 'function') {
        throw new Error(`Project ${project} 中未找到对应的 Action: ${action}`);
    }

    // 4. 调用对应 handler 中的 action 方法 (业务执行)
    // 业务处理函数如果内部出错，也应该抛出异常
    // Use .call() to set 'this' to the 'handler' object
    const resultPayload = handlerFunction.call(handler, requestData);
    
    // 5. 最终返回成功响应
    return Utils.successResponse(200, `${project}:${action} 执行成功`, resultPayload);
}

function testRoute() {
  // Utils.createFileAndMove(
  //   {
  //       "project": "Utils", 
  //       "action": "createFileAndMove", 
  //       "name": "测试哇唧唧1111", 
  //       "sheetName": "数据",
  //       "targetFolderId": "1BKY3v7VK0SFFC3xwo5AOZEHRdkf4Q3zN",
  //       "headerValues": ["www","rttre","564645"]
  //   }
  // );
  // const resultPayload = Utils.fetch_worksheet_last_data_row(
  //   {
  //     "spreadsheetId": "1W9nM7flUCczk3Q3w5_O209woGUnXVnpwAGtIU3Ej3aw",
  //     "sheetName": "outsunny",
  //   }
  // );

  // const resultPayload = Utils.fetch_multi_worksheet_last_data_row(
  //   {
  //     "spreadsheetId": "1W9nM7flUCczk3Q3w5_O209woGUnXVnpwAGtIU3Ej3aw",
  //     "sheets": [
  //       {"sheetName": "homcom", "headerRowIndex": 1},
  //       {"sheetName": "outsunny", "headerRowIndex": 1},
  //     ],
  //   }
  // );


  // const resultPayload = Utils.delete_worksheet_rows(
  //   {
  //     "project": "Utils",
  //     "action": "delete_worksheet_rows",
  //     "spreadsheetId": "1IOiBkjaqIU4Dndn67zt8s6ckhNQ5fC9BHJJ-PdKeWEc",
  //     "sheetName": "记录",
  //     "conditionColumnName": "id", 
  //     "conditionValue": "2"
  //   }
  // );

  // const resultPayload = Utils.reset_and_rewrite_batch_id(
  //   {
  //     "project": "Utils",
  //     "action": "reset_and_rewrite_batch_id",
  //     "spreadsheetId": "1W9nM7flUCczk3Q3w5_O209woGUnXVnpwAGtIU3Ej3aw",
  //     "sheetName": "outsunny",
  //     "columnName": "batch_id", 
  //     "keyColumnName": "partner id"
  //   }
  // );
  
  const resultPayload = Utils.batch_insert_columns(
    {
      "project": "Utils",
      "action": "batch_insert_columns",
      "spreadsheetId": "1W9nM7flUCczk3Q3w5_O209woGUnXVnpwAGtIU3Ej3aw",
      "sheetName": "outsunny",
      "columns": ["AAAA", "BBB"],
      "clearIfExists": true
    }
  );

  

//   const resultPayload = Utils.fetch_worksheet_data(
// {
//       "project": "Utils",
//       "action": "fetch_worksheet_data",
//       "spreadsheetId": "1IOiBkjaqIU4Dndn67zt8s6ckhNQ5fC9BHJJ-PdKeWEc",
//       "sheetName": "记录",
//       "firstDataRowIndex": 2, 
//       "limit": 100,
//       "filters": [
//           {
//               "columnHeader": "步骤名称",
//               "condition": "EQUALS",
//               "value": "AI分析"
//           }
//       ]
//     } 
//   );
  Logger.log(`resultPayload: ${JSON.stringify(resultPayload)}`);

}

```

## project_utils.gs
```gs
/**
 * * Utils: 通用工具类，封装了数据导入、格式化和响应处理方法。
 */
const Utils = {
  /**
   * 解析 doPost 请求中的参数，并执行基础校验。
   * @param {object} e - doPost 事件对象。
   * @param {Array<string>} requiredKeys - 必须包含在请求体中的键名列表（在 doPost 中动态确定）。
   * @returns {object} 解析后的请求数据对象。
   */
  parseRequest: function(e) {
      if (!e.postData || !e.postData.contents) {
          throw new Error("请求体为空。");
      }
      return JSON.parse(e.postData.contents);
  },
  /**
   * 通用的成功响应格式。
   * * @param {number} status - 状态码 (应为 200)。
   * @param {string} message - 描述信息。
   * @param {object} [resultPayload] - 包含特定工具结果的额外对象 (例如 {url: '...', rows: 10})。
   * @returns {GoogleAppsScript.Content.TextOutput} JSON 格式的响应。
   */
  successResponse: function(status, message, resultPayload) {
      // 基础响应结构
      let baseResponse = { 
          status: status, // 建议工具调用成功时总是返回 200
          message: message,
          version: typeof SCRIPT_VERSION !== 'undefined' ? SCRIPT_VERSION : 'Unknown'
      };

      // 如果提供了自定义结果，则合并到基础响应中
      if (resultPayload && typeof resultPayload === 'object') {
          baseResponse = { ...baseResponse, ...resultPayload };
      }

      return ContentService.createTextOutput(JSON.stringify(baseResponse))
                          .setMimeType(ContentService.MimeType.JSON);
  },

  /**
   * 通用的错误响应格式。
   */
  errorResponse: function(status, message, details) {
      // 确保 SCRIPT_VERSION 变量在全局可用
      return ContentService.createTextOutput(JSON.stringify({ 
        status: status, 
        message: message,
        details: details || '',
        version: typeof SCRIPT_VERSION !== 'undefined' ? SCRIPT_VERSION : 'Unknown'
      })).setMimeType(ContentService.MimeType.JSON);
  },

  /**
   * 创建一个新的Spreadsheet文件并移动到指定文件夹。
   * @param {string} name 文件名。
   * @param {string} sheetName 第一个worksheet名。
   * @param {string} headerValues 表头。
   * @param {string} targetFolderId 目标文件夹ID。
   */
  createFileAndMove: function(requestData) {
    const { name, sheetName, headerValues, targetFolderId} = requestData;
    if (!name) {
        throw new Error("请求中缺少必要的参数: name");
    }
    // 1.在根目录创建文件
    const result = this._createNewSpreadsheet(name, sheetName); 
    const spreadsheetId = result.spreadsheetId;

    // 2. 写入表头 (新增逻辑)
    if (Array.isArray(headerValues) && headerValues.length > 0) {
        this._writeHeaderToSheet(spreadsheetId, headerValues);
        result.header_status = "Header written successfully.";
    } else {
        result.header_status = "No header provided or header is empty.";
    }

    // 3.将文件移动到指定文件夹
    if (targetFolderId) {
      this._moveFileToFolder(result.spreadsheetId, targetFolderId);
    }  
    return result;
  },

  /**
   * 获取worksheet数据，并根据复杂的 filters 数组进行筛选。
   * @param {object} requestData 包含以下参数：
   * - headerRowIndex (可选, 默认 1): 表头所在的行数（基于 1）。
   * - firstDataRowIndex (可选, 默认 2): 实际数据开始读取的行数（基于 1）。
   * - filters: 复杂的筛选规则数组。
   * - limit: 最大返回行数。
   */
  fetch_worksheet_data: function(requestData) {
    const { 
        spreadsheetId, 
        sheetName, 
        limit = 100,
        filters = [],
        matchMode = 'AND',
        headerRowIndex = 1,      // 默认表头在第 1 行
        firstDataRowIndex = 2    // 默认数据从第 2 行开始
    } = requestData; 
          
    // --- 校验 ---
    if (!spreadsheetId || !sheetName) {
      throw new Error("请求中缺少必要的参数: spreadsheetId sheetName");
    }
    if (headerRowIndex >= firstDataRowIndex) {
      throw new Error("headerRowIndex 必须小于 firstDataRowIndex，请检查参数。");
    }
    
    const spreadsheet = SpreadsheetApp.openById(spreadsheetId);
    const sheet = spreadsheet.getSheetByName(sheetName);
    if (!sheet) throw new Error(`在 Spreadsheet ID ${spreadsheetId} 中未找到名称为 ${sheetName} 的工作表。`);

    // 获取整个表格的边界
    const fullRange = sheet.getDataRange();
    const numColumns = fullRange.getLastColumn();
    const lastRow = fullRange.getLastRow();
    Logger.log(`fullRange="${fullRange}" numColumns="${numColumns}" lastRow="${lastRow}"`);

    // 1. 获取表头行数据
    if (headerRowIndex > lastRow) {
        throw new Error(`指定的表头行 ${headerRowIndex} 超过了表格总行数 ${lastRow}。`);
    }
    const headerRange = sheet.getRange(headerRowIndex, 1, 1, numColumns);
    const headerRow = headerRange.getValues()[0];
    
    // 2. 确定实际数据读取范围
    const startRow = Math.max(1, firstDataRowIndex); // 确保不小于 1
    const readRows = Math.max(0, lastRow - startRow + 1); // 需要读取的行数

    Logger.log(`startRow="${startRow}" readRows="${readRows}"`);

    // 如果没有数据行可读，统一返回空结构
    if (readRows <= 0) {
        return { 
            data: headerRow.length > 0 ? [headerRow] : [], // 如果有表头，只返回表头
            rowCount: headerRow.length > 0 ? 1 : 0         // 包含表头行计数
        };
    }
          
    // 获取所有数据行
    const dataRange = sheet.getRange(startRow, 1, readRows, numColumns);
    let dataRows = dataRange.getValues(); // dataRows 是二维数组
    
    // --- 3. 执行筛选逻辑 (与之前相同) ---
    if (filters.length > 0) {
        // ... [筛选逻辑：使用 headerRow 和 dataRows 进行 _findColumnIndexByHeader 等操作] ...
        dataRows = dataRows.filter(row => {
            // ... (筛选规则执行逻辑，使用 headerRow 来解析列名) ...
            // 确保筛选逻辑能够访问到 headerRow 和 dataRows
            const results = filters.map(filter => {
                // 1. 确定要检查的列索引
                let colIndex = filter.columnIndex;
                if (filter.columnHeader && colIndex === undefined) {
                    colIndex = this._findColumnIndexByHeader(headerRow, filter.columnHeader);
                }
                                  
                if (colIndex === null || colIndex >= row.length) return false;
                const cellValue = row[colIndex];
                const targetValue = filter.value;
                
                // 2. 根据 condition 执行检查
                switch (filter.condition) {
                    case 'EQUALS':
                        return String(cellValue) === String(targetValue);
                    case 'NOT_EQUALS':
                        return String(cellValue) !== String(targetValue); // 您的核心需求
                    case 'IS_EMPTY':
                        return cellValue === "" || cellValue === null;
                    case 'NOT_EMPTY':
                        return cellValue !== "" && cellValue !== null;
                    case 'GREATER_THAN':
                        // 简单的数值或日期比较
                        return cellValue > targetValue; 
                    // ... 可以添加更多的条件：CONTAINS, LESS_THAN, etc.
                    default:
                        Logger.log(`未知条件: ${filter.condition}`);
                        return false; 
                }
            });
            return matchMode === 'OR' ? results.some(r => r) : results.every(r => r);
        });
    }
    
    // 4. 实现数量限制
    const limitedDataRows = dataRows.slice(0, limit);
    
    // 5. 重新组合：表头 + 限制后的数据行
    // const finalValues = [headerRow, ...limitedDataRows];
    const finalValues = this._convertDataToObjects(headerRow, limitedDataRows);
    Logger.log(`查询结果数量: ${finalValues.length}`);

    return {
      data: finalValues,
      rowCount: finalValues.length
    };
  },

  /**
   * 获取指定工作表中，有内容的最后一行数据，并返回 JSON 对象格式。
   * @param {object} requestData 包含 spreadsheetId, sheetName, headerRowIndex (可选, 默认 1)。
   * @returns {object} 包含最后一行数据的 JSON 对象，格式与 fetch_and_filter_data 统一。
   */
  fetch_worksheet_last_data_row: function(requestData) {
    const { 
        spreadsheetId, 
        sheetName,
        headerRowIndex = 1 // 默认表头在第 1 行
    } = requestData; 
    
    if (!spreadsheetId || !sheetName) {
       throw new Error("Action 'fetch_worksheet_last_data_row' 缺少必要的参数: spreadsheetId 或 sheetName"); 
    }
    
    const spreadsheet = SpreadsheetApp.openById(spreadsheetId);
    const sheet = spreadsheet.getSheetByName(sheetName);

    if (!sheet) {
      throw new Error(`在 Spreadsheet ID ${spreadsheetId} 中未找到名称为 ${sheetName} 的工作表。`);
    }

    // 1. 获取工作表的边界
    const lastRowIndex = sheet.getLastRow(); 
    const lastColumnIndex = sheet.getLastColumn();

    // 2. 获取表头行数据 (即使没有数据行，也应尝试获取表头)
    let headerRow = [];
    if (headerRowIndex > 0 && lastColumnIndex > 0 && headerRowIndex <= lastRowIndex) {
        const headerRange = sheet.getRange(headerRowIndex, 1, 1, lastColumnIndex);
        headerRow = headerRange.getValues()[0];
    } else if (headerRowIndex > lastRowIndex) {
         // 如果指定的表头行大于实际最后一行，说明数据是空的或表头索引错误
         Logger.log(`警告: 指定的表头行 ${headerRowIndex} 超过了实际数据范围，可能数据为空。`);
    }
    
    // 3. 检查是否有数据行（排除表头行）
    if (lastRowIndex <= headerRowIndex) {
        Logger.log(`工作表 ${sheetName} 中没有数据行（或只有表头行）。`);
        // 返回统一的空结构
        return {
            data: [], // 返回空数组
            rowCount: 0
        };
    }
    
    // 4. 获取最后一行数据的范围
    const dataRange = sheet.getRange(lastRowIndex, 1, 1, lastColumnIndex);
    const lastRowData = dataRange.getValues()[0]; // 一维数组

    // 5. 将数据映射为 JSON 对象 (复用 _convertDataToObjects 逻辑)
    let finalDataPayload = [];
    if (headerRow.length > 0) {
        finalDataPayload = this._convertDataToObjects(headerRow, [lastRowData]);
    } else {
        // 如果没有表头，则直接返回原始数组，但最好是抛出警告或错误
        Logger.log("警告: 未能获取表头，返回原始数组格式。");
        finalDataPayload = [lastRowData];
    }
    
    Logger.log(`已成功获取第 ${lastRowIndex} 行数据。`);

    // 6. 返回统一的结构
    return {
      data: finalDataPayload, // 包含列名映射的 JSON 对象数组（只包含一个元素）
      rowCount: 1, // 只返回了 1 行数据
    };
  },

  /**
   * 获取多个工作表中，各自的「最后一行有效数据」
   * 【方式 1 专用】每个 Sheet 明确指定 headerRowIndex
   *
   * requestData 示例：
   * {
   *   spreadsheetId: "...",
   *   sheets: [
   *     { sheetName: "A", headerRowIndex: 1 },
   *     { sheetName: "B", headerRowIndex: 3 }
   *   ]
   * }
   */
  fetch_multi_worksheet_last_data_row: function (requestData) {
    const { spreadsheetId, sheets } = requestData;

    if (!spreadsheetId || !Array.isArray(sheets) || sheets.length === 0) {
      throw new Error(
        "fetch_multi_worksheet_last_data_row 缺少参数: spreadsheetId 或 sheets"
      );
    }

    const spreadsheet = SpreadsheetApp.openById(spreadsheetId);
    const results = [];

    sheets.forEach(cfg => {
      const { sheetName, headerRowIndex } = cfg;

      if (!sheetName || !headerRowIndex) {
        results.push({
          sheetName,
          error: "缺少 sheetName 或 headerRowIndex"
        });
        return;
      }

      try {
        const sheet = spreadsheet.getSheetByName(sheetName);
        if (!sheet) {
          throw new Error(`未找到 Sheet: ${sheetName}`);
        }

        const lastRowIndex = sheet.getLastRow();
        const lastColumnIndex = sheet.getLastColumn();

        // 没有正式数据行
        if (lastRowIndex <= headerRowIndex || lastColumnIndex === 0) {
          results.push({
            sheetName,
            headerRowIndex,
            rowCount: 0,
            data: null
          });
          return;
        }

        // 表头
        const headerRow = sheet
          .getRange(headerRowIndex, 1, 1, lastColumnIndex)
          .getValues()[0];

        // 最后一行数据
        const lastRowData = sheet
          .getRange(lastRowIndex, 1, 1, lastColumnIndex)
          .getValues()[0];

        const dataObject =
          headerRow.length > 0
            ? this._convertDataToObjects(headerRow, [lastRowData])[0]
            : lastRowData;

        results.push({
          sheetName,
          headerRowIndex,
          lastRowIndex,
          rowCount: 1,
          data: dataObject
        });

      } catch (err) {
        Logger.log(`Sheet "${sheetName}" 处理失败: ${err.message}`);
        results.push({
          sheetName,
          headerRowIndex,
          error: err.message
        });
      }
    });

    return {
      data: results,
      totalSheets: results.length
    };
  },

  /**
   * 根据指定列的值和条件删除工作表中的行。
   * @param {object} requestData 包含以下参数：
   * - spreadsheetId: Spreadsheet ID
   * - sheetName: Sheet 名称
   * - headerRowIndex: 表头所在的行号 (基于 1)
   * - conditionColumnName: 用于判断的列名
   * - conditionValue: 条件值 (匹配该值的行将被删除)
   */
  delete_worksheet_rows: function(requestData) {
      const { 
          spreadsheetId, 
          sheetName, 
          conditionColumnName, 
          conditionValue,
          headerRowIndex = 1
      } = requestData; 
      
      // 1. 参数校验
      if (!spreadsheetId || !sheetName || !conditionColumnName || conditionValue === undefined) {
          throw new Error("Action 'delete_rows_by_condition' 缺少必要的参数。"); 
      }
      
      const spreadsheet = SpreadsheetApp.openById(spreadsheetId);
      const sheet = spreadsheet.getSheetByName(sheetName);

      if (!sheet) {
          throw new Error(`未找到工作表: ${sheetName}`);
      }
      
      const lastRow = sheet.getLastRow();
      const lastCol = sheet.getLastColumn();
      const firstDataRow = headerRowIndex + 1;

      if (lastRow < firstDataRow) {
          Logger.log("工作表中没有数据行需要检查。");
          return {
              numRowsDeleted: 0
          };
      }

      // 2. 获取表头和确定条件列的索引
      const headerRange = sheet.getRange(headerRowIndex, 1, 1, lastCol);
      const headerRow = headerRange.getValues()[0];
      
      const columnIndex = headerRow.findIndex(h => String(h).trim() === conditionColumnName);

      if (columnIndex === -1) {
          throw new Error(`在表头中找不到列名: ${conditionColumnName}。`);
      }
      
      // 3. 读取所有数据行
      // 注意：只读取从 firstDataRow 到 lastRow 的数据
      const numDataRows = lastRow - firstDataRow + 1;
      const dataRange = sheet.getRange(firstDataRow, 1, numDataRows, lastCol);
      const allDataValues = dataRange.getValues();
      
      const rowsToDelete = []; // 存储需要删除的实际行号（基于 1）

      // 4. 遍历数据并标记需要删除的行
      for (let i = 0; i < allDataValues.length; i++) {
          const row = allDataValues[i];
          const cellValue = row[columnIndex];
          
          // 默认进行严格相等比较
          if (String(cellValue) === String(conditionValue)) {
              // 计算实际行号：数据起始行 + 遍历索引 i
              const actualRowIndex = firstDataRow + i;
              rowsToDelete.push(actualRowIndex);
          }
      }

      let deleteCount = 0;
      
      // 5. 从后往前删除行 (关键步骤，避免行号错位)
      for (let i = rowsToDelete.length - 1; i >= 0; i--) {
          const rowIndex = rowsToDelete[i];
          sheet.deleteRow(rowIndex);
          deleteCount++;
      }
      
      Logger.log(`已成功删除 ${deleteCount} 行，条件列为 ${conditionColumnName}，值为 ${conditionValue}。`);
      
      // 6. 返回统一的成功结构
      return {
          numRowsDeleted: deleteCount
      };
  },

  /**
   * 重置并重新写入指定 Sheet 的 batch_id 列（非公式，值写入）
   * 
   * @param {object} requestData
   * @param {string} spreadsheetId       Spreadsheet ID
   * @param {string} sheetName            Sheet 名称
   * @param {string} columnName           batch_id 列名
   * @param {number} batchSize            每批大小
   * @param {number} headerRowIndex       最后一行表头所在行（1-based，默认 1）
   * @param {number} firstDataRowIndex    第一条正式数据行（1-based，默认 headerRowIndex + 1）
   * @param {string} keyColumnName        （可选）用于判断“是否有效行”的主列名
   */
  reset_and_rewrite_batch_id: function(requestData) {
    const {
      spreadsheetId,
      sheetName,
      columnName = 'batch_id',
      batchSize = 50,
      headerRowIndex = 1,
      firstDataRowIndex = headerRowIndex + 1,
      keyColumnName
    } = requestData;

    if (!spreadsheetId || !sheetName) {
      throw new Error('缺少必要参数 spreadsheetId / sheetName');
    }

    const ss = SpreadsheetApp.openById(spreadsheetId);
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      throw new Error(`未找到 Sheet: ${sheetName}`);
    }

    const lastRow = sheet.getLastRow();
    const lastCol = sheet.getLastColumn();

    if (lastRow < firstDataRowIndex) {
      return {
        message: '无数据行，未生成 batch_id',
        rowsUpdated: 0
      };
    }

    // 1. 读取表头
    const headerRange = sheet.getRange(headerRowIndex, 1, 1, lastCol);
    const headerRow = headerRange.getValues()[0];

    // 2. 找 batch_id 列
    let batchColIndex = headerRow.findIndex(h => String(h).trim() === columnName);

    // 不存在则新增一列
    if (batchColIndex === -1) {
      batchColIndex = headerRow.length;
      sheet.getRange(headerRowIndex, batchColIndex + 1).setValue(columnName);
    }

    // 3. 找 key 列（用于判断是否是有效数据行）
    let keyColIndex = null;
    if (keyColumnName) {
      keyColIndex = headerRow.findIndex(h => String(h).trim() === keyColumnName);
      if (keyColIndex === -1) {
        throw new Error(`未找到 keyColumnName: ${keyColumnName}`);
      }
    }

    const writeCol = batchColIndex + 1;
    const numRows = lastRow - firstDataRowIndex + 1;

    // 4. 先清空 batch_id 列（只清数据区）
    sheet
      .getRange(firstDataRowIndex, writeCol, numRows, 1)
      .clearContent();

    // 5. 读取数据行（用于判断有效行）
    const dataRange = sheet.getRange(firstDataRowIndex, 1, numRows, lastCol);
    const rows = dataRange.getValues();

    const effectiveRowIndexes = []; // 存 sheet 中真实的行号（1-based）
    const output = [];
    let effectiveRowCounter = 0;

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];

      // 如果指定了 keyColumnName，用它判断是否有效行
      if (keyColIndex !== null) {
        if (row[keyColIndex] === '' || row[keyColIndex] === null) {
          output.push(['']);
          continue;
        }
      }

      const batchId = Math.floor(effectiveRowCounter / batchSize) + 1;
      output.push([batchId]);

      // ✅ 记录真实 sheet 行号
      effectiveRowIndexes.push(firstDataRowIndex + i);
      
      effectiveRowCounter++;
    }

    // 6. 写入 batch_id
    sheet
      .getRange(firstDataRowIndex, writeCol, output.length, 1)
      .setValues(output);


    // 7. 取最后 2 条有效数据
    const lastTwoRowIndexes = effectiveRowIndexes.slice(-2);

    let tailRecords = [];

    if (lastTwoRowIndexes.length > 0) {
      const header = headerRow;

      lastTwoRowIndexes.forEach(rowIndex => {
        const rowValues = sheet
          .getRange(rowIndex, 1, 1, lastCol)
          .getValues()[0];

        const obj = {};
        header.forEach((key, idx) => {
          if (key !== '') {
            obj[key] = rowValues[idx];
          }
        });

        tailRecords.push({
          rowIndex,
          data: obj
        });
      });
    }

    return {
      message: 'batch_id 已成功重置并重新写入',
      rowsUpdated: effectiveRowCounter,
      batchSize,
      columnName,
      tailRecords: tailRecords
    };
  },

  /**
   * 在指定 Sheet 中批量插入多列（可选清空已存在列）
   *
   * @param {object} requestData
   * @param {string} requestData.spreadsheetId
   * @param {string} requestData.sheetName
   * @param {number} requestData.headerRowIndex
   * @param {string[]} requestData.columns
   * @param {string} [requestData.insertAfter]
   * @param {boolean} [requestData.clearIfExists=false]
   */
  batch_insert_columns: function(requestData) {
    const {
      spreadsheetId,
      sheetName,
      headerRowIndex = 1,
      columns = [],
      insertAfter,
      clearIfExists = false
    } = requestData;

    if (!spreadsheetId || !sheetName) {
      throw new Error('缺少必要参数 spreadsheetId / sheetName');
    }

    if (!Array.isArray(columns) || columns.length === 0) {
      throw new Error('columns 必须是非空数组');
    }

    const ss = SpreadsheetApp.openById(spreadsheetId);
    const sheet = ss.getSheetByName(sheetName);

    if (!sheet) {
      throw new Error(`未找到 Sheet: ${sheetName}`);
    }

    const lastRow = sheet.getLastRow();
    const lastCol = sheet.getLastColumn();

    // 1. 读取表头
    const headerRange = sheet.getRange(headerRowIndex, 1, 1, lastCol);
    const headerRow = headerRange.getValues()[0].map(h => String(h).trim());

    const existingHeaders = new Map();
    headerRow.forEach((h, idx) => {
      if (h) existingHeaders.set(h, idx + 1); // 1-based
    });

    const columnsToInsert = [];
    const columnsToClear = [];

    for (const col of columns) {
      if (existingHeaders.has(col)) {
        if (clearIfExists) {
          columnsToClear.push({
            name: col,
            colIndex: existingHeaders.get(col)
          });
        }
      } else {
        columnsToInsert.push(col);
      }
    }

    // 2. 计算插入位置
    let insertIndex;
    if (insertAfter) {
      const afterIdx = headerRow.indexOf(insertAfter);
      if (afterIdx === -1) {
        throw new Error(`insertAfter 列不存在: ${insertAfter}`);
      }
      insertIndex = afterIdx + 1;
    } else {
      insertIndex = headerRow.length;
    }

    // 3. 插入新列（一次性）
    if (columnsToInsert.length > 0) {
      sheet.insertColumnsAfter(insertIndex, columnsToInsert.length);
      sheet
        .getRange(headerRowIndex, insertIndex + 1, 1, columnsToInsert.length)
        .setValues([columnsToInsert]);
    }

    // 4. 清空已存在列的数据（只清数据区）
    if (clearIfExists && columnsToClear.length > 0 && lastRow > headerRowIndex) {
      const numRows = lastRow - headerRowIndex;
      columnsToClear.forEach(col => {
        sheet
          .getRange(headerRowIndex + 1, col.colIndex, numRows, 1)
          .clearContent();
      });
    }

    return {
      message: '批量列处理完成',
      insertedColumns: columnsToInsert,
      clearedColumns: columnsToClear.map(c => c.name),
      skippedColumns: columns.filter(c => !columnsToInsert.includes(c)),
      headerRowIndex
    };
  },

  // ------------------------------------------------------------------
  // Spreadsheet：创建文件
  // ------------------------------------------------------------------
  /**
   * 创建一个新的 Google Spreadsheet 文件(在根目录创建)。
   * @param {string} name 文件名。
   * @param {string} sheetName 第一个工作表的名称（可选）。
   */
  _createNewSpreadsheet: function(name, sheetName) {
    const newSpreadsheet = SpreadsheetApp.create(name);
    const sheet = newSpreadsheet.getSheets()[0];

    // 如果提供了 sheetName name
    const finalSheetName = sheetName || name;
    sheet.setName(finalSheetName);

    const spreadsheetId = newSpreadsheet.getId();
    Logger.log('已创建文件： name:%s id=%s, sheetName:%s', name, spreadsheetId, finalSheetName);
    
    return {
      name: name,
      spreadsheetId: spreadsheetId,
      url: newSpreadsheet.getUrl()
    };
  },
  /**
   * 写入表头到新建文件的第一个工作表。
   * @param {string} spreadsheetId 目标文件ID。
   * @param {Array<string>} headerValues 要写入的表头数据数组。
   */
  _writeHeaderToSheet: function(spreadsheetId, headerValues) {
    if (!spreadsheetId || !Array.isArray(headerValues) || headerValues.length === 0) {
        Logger.log("无法写入表头：参数不完整。");
        return;
    }
      
    const spreadsheet = SpreadsheetApp.openById(spreadsheetId);
    // 获取第一个 Sheet
    const sheet = spreadsheet.getSheets()[0];
    
    // 获取第一行、第一列开始的区域，行数1，列数为表头长度
    const range = sheet.getRange(1, 1, 1, headerValues.length);
    
    // setValues 接收一个二维数组，所以将 headerValues 包装起来
    range.setValues([headerValues]);
    
    Logger.log('已成功写入表头：%s', headerValues.join(', '));
  },
  /**
   * 移动文件到指定的文件夹。
   * @param {string} fileId 要移动的文件ID。
   * @param {string} targetFolderId 目标文件夹ID。
   */
  _moveFileToFolder: function(fileId, targetFolderId) {
    const file = DriveApp.getFileById(fileId);
    const targetFolder = DriveApp.getFolderById(targetFolderId);
    
    targetFolder.addFile(file);
    DriveApp.getRootFolder().removeFile(file);
    
    Logger.log('文件 %s 已成功移动到文件夹 %s。', fileId, targetFolderId);
  },

  // ------------------------------------------------------------------
  // Spreadsheet 读取数据
  // ------------------------------------------------------------------
  /**
   * 私有辅助函数：根据表头名称在表头行中查找对应的列索引。
   * @param {Array<string>} headerRow 表头行的数组。
   * @param {string} columnName 要查找的列名称。
   * @returns {number | null} 列索引（从 0 开始），未找到返回 null。
   */
  _findColumnIndexByHeader: function(headerRow, columnName) {
    const index = headerRow.findIndex(header => String(header).trim() === columnName.trim());
    return index !== -1 ? index : null;
  },
  /**
   * 私有辅助函数：将二维数组（包含表头）转换为 JSON 对象数组。
   * @param {Array<string>} headerRow 表头行数组。
   * @param {Array<Array<any>>} dataRows 数据行二维数组。
   * @returns {Array<object>} 转换后的 JSON 对象数组。
   */
  _convertDataToObjects: function(headerRow, dataRows) {
    if (!headerRow || headerRow.length === 0 || !dataRows || dataRows.length === 0) {
        return [];
    }

    // 确保所有表头都是字符串，并去除首尾空格
    const cleanHeaders = headerRow.map(h => String(h).trim());

    return dataRows.map(row => {
        const rowObject = {};
        cleanHeaders.forEach((header, index) => {
            // 使用表头作为键 (key)，行数据作为值 (value)
            // 确保不越界
            if (index < row.length) {
                rowObject[header] = row[index];
            }
        });
        return rowObject;
    });
  },


  // ------------------------------------------------------------------
  // 1. 数据写入工具
  // ------------------------------------------------------------------

  /**
   * 辅助函数：将数据写入指定的 Sheet。
   * @param {GoogleAppsScript.Spreadsheet.Spreadsheet} ss - 目标表格对象。
   * @param {string} sheetName - 目标 Sheet 的名称。
   * @param {Array<Array<any>>} data - 要写入的数据（二维数组）。
   * @param {Array<string>} headers - 列头数组。
   */
  outputDataToSheet: function(ss, sheetName, data, headers) {
      let outputSheet = ss.getSheetByName(sheetName);
      
      // 覆盖模式：如果 Sheet 存在，则删除它
      if (outputSheet) {
          ss.deleteSheet(outputSheet);
      }
      
      outputSheet = ss.insertSheet(sheetName);
      
      // 写入列头
      outputSheet.appendRow(headers);
      
      // 写入数据（从第 2 行开始）
      if (data.length > 0) {
          outputSheet.getRange(2, 1, data.length, data[0].length).setValues(data);
      }
  },

  /**
   * 设置目标表格中指定 Sheet 的一整列为纯文本格式。
   * @param {GoogleAppsScript.Spreadsheet.Spreadsheet} ss - 目标表格对象。
   * @param {string} sheetName - 目标 Sheet 的名称。
   * @param {number} columnIndex - 目标列的索引（1-based，例如 D 列是 4）。
   */
  forceColumnToPlainText: function(ss, sheetName, columnIndex) {
      const sheet = ss.getSheetByName(sheetName);
      
      if (!sheet) {
          Logger.log(`警告：未能找到 Sheet: ${sheetName}。跳过格式化。`);
          return;
      }
      
      // 使用 this 调用内部的列转换方法
      const columnLetter = this.columnToLetters(columnIndex); 
      
      // 使用 A1 表示法获取整列
      const range = sheet.getRange(`${columnLetter}1:${columnLetter}${sheet.getMaxRows()}`); 
      
      // '@' 是 Google Sheets 中纯文本格式的代号
      range.setNumberFormat('@'); 
      
      Logger.log(`已将 Sheet "${sheetName}" 的 ${columnLetter} 列格式化为纯文本。`);
  },
  
  // ------------------------------------------------------------------
  // 2. 辅助工具 (被内部方法调用)
  // ------------------------------------------------------------------

  /**
   * Helper function: Converts a column index (1-based) to its letter representation (A, B, C...).
   * @param {number} column - The column index (1-based).
   * @returns {string} The column letter.
   */
  columnToLetters: function(column) {
      let temp, letter = '';
      while (column > 0) {
          temp = (column - 1) % 26;
          letter = String.fromCharCode(temp + 65) + letter;
          column = (column - temp - 1) / 26;
      }
      return letter;
  },
};
```

## project_jsfhl.gs
```gs
/**
 * ProjectJsfhl: 用于处理`及时发货率`相关逻辑。
 */
const ProjectJsfhl = {
  
};


```

## project_ppzggzsx.gs
```gs
/**
 * ProjectPpzggzsx: 跨文件数据补充与同步逻辑
 */
const ProjectPpzggzsx = {
  /**
   * 补充 dt 和 batch_index 列，并返回批次汇总
   */
  fill_dt_and_batch_index: function(requestData) {
    const { spreadsheetId, sheetName, batchSize = 10, headerRowIndex = 1 } = requestData;
    Logger.log(`>>> [开始补充列数据] SpreadsheetId: ${spreadsheetId}, Sheet: ${sheetName}`);

    const spreadsheet = SpreadsheetApp.openById(spreadsheetId);
    const sheet = spreadsheet.getSheetByName(sheetName);
    if (!sheet) throw new Error(`未找到表: ${sheetName}`);

    const lastRow = sheet.getLastRow();

    // 情况 A：没有数据行
    if (lastRow <= headerRowIndex) {
      Logger.log(`--- [补充结束] 表内无有效数据。`);
      return {
        state: "no_data",
        batch_summary: [], // 返回空数组
        message: "表格为空，未进行任何处理。"
      };
    }

    // 查找列索引
    const headers = sheet.getRange(headerRowIndex, 1, 1, sheet.getLastColumn()).getDisplayValues()[0];
    const dtIdx = headers.indexOf("dt") + 1;
    const batchIdx = headers.indexOf("batch_index") + 1;
    const timeIdx = headers.indexOf("create_time") + 1;

    if (!dtIdx || !batchIdx || !timeIdx) throw new Error("缺少必要的列名: dt, batch_index 或 create_time");

    const numRows = lastRow - headerRowIndex;
    const timeValues = sheet.getRange(headerRowIndex + 1, timeIdx, numRows, 1).getDisplayValues();

    const dtCounterMap = {}; // 记录每个 dt 出现的次数
    const dtOut = [];
    const batchOut = [];

    for (let i = 0; i < numRows; i++) {
      const timeStr = timeValues[i][0];
      if (!timeStr) {
        dtOut.push([""]); batchOut.push([""]);
        continue;
      }
      
      // 提取日期 YYYYMMDD
      const rawDt = timeStr.substring(0, 10).replace(/-/g, "");
      const dtWithQuote = "'" + rawDt;
      
      if (!dtCounterMap[rawDt]) dtCounterMap[rawDt] = 0;
      
      // 计算当前行的批次号 (从1开始)
      const currentBatch = Math.floor(dtCounterMap[rawDt] / batchSize) + 1;
      dtCounterMap[rawDt]++;

      dtOut.push([dtWithQuote]);
      batchOut.push([currentBatch]);
    }

    // 批量写入
    sheet.getRange(headerRowIndex + 1, dtIdx, numRows, 1).setValues(dtOut);
    sheet.getRange(headerRowIndex + 1, batchIdx, numRows, 1).setValues(batchOut);
    
    // --- 核心修改：构造返回的汇总数组 ---
    const batchSummary = Object.keys(dtCounterMap).map(dtKey => {
      return {
        "dt": dtKey,
        "max_batch_index": Math.ceil(dtCounterMap[dtKey] / batchSize)
      };
    });

    Logger.log(`<<< [补充完成] 汇总信息: ${JSON.stringify(batchSummary)}`);

    // 返回执行结果对象
    return {
      state: "success",
      processedRows: numRows,
      batch_summary: batchSummary, // 这里就是你需要的数组
      message: `成功补充数据，包含 ${batchSummary.length} 个不同的日期。`
    };
  },
  /**
   * 2. 跨文件同步指定 dt 的数据（幂等更新）
   * 
   * 【同步规则描述】：
   * 1. 筛选逻辑 (Filtering): 
   *    - 脚本仅从 [源表] 中提取 `dt` 列完全匹配 `targetDt` 参数的数据行。
   *    - 匹配时会自动忽略前缀单引号 `'` 和前后空格，确保比对的准确性。
   * 
   * 2. 数据转换 (Transformation):
   *    - id 字段生成：使用 `${dt}_${partner id}` 格式拼接。
   *    - 文本强制格式：为了防止 Google 表格将 ID 或日期误识别为数字/日期格式，
   *      写入 [目标表] 的 `id` 和 `dt` 两列数据都会在前缀加上单引号 `'`。
   * 
   * 3. 幂等更新/去重 (Idempotency):
   *    - 脚本并非简单的“追加”数据，而是执行“局部更新”。
   *    - 过程：读取 [目标表] 现有所有行 -> 在内存中剔除所有 `dt === targetDt` 的旧数据 -> 
   *      合并 [源表] 提取的新数据 -> 重新写回 [目标表]。
   *    - 效果：同一个日期多次同步，目标表永远只保留该日期的最新版本，且不会影响其他日期已存在的数据。
   * 
   * 4. 列动态匹配 (Dynamic Mapping):
   *    - 脚本通过 [源表] 和 [目标表] 的表头名称（dt, batch_index, partner id, id）自动查找列索引。
   *    - 即使两个 Spreadsheet 文件的列顺序不一致，只要列名正确，同步依然能准确完成。
   * 
   * 5. 跨文件操作 (Cross-File):
   *    - 支持通过 spreadsheetId 打开分布在不同文件夹下的两个独立文件。
   */
  sync_to_sheet2: function(requestData) {
    const {
      sourceSpreadsheetId,
      targetSpreadsheetId,
      sourceSheetName,
      targetSheetName,
      targetDt,
      headerRowIndex = 1
    } = requestData;

    Logger.log(`>>> [开始跨同步] 目标日期: ${targetDt}`);
    Logger.log(`    源: ${sourceSpreadsheetId} (${sourceSheetName})`);
    Logger.log(`    目: ${targetSpreadsheetId} (${targetSheetName})`);

    const sourceSS = SpreadsheetApp.openById(sourceSpreadsheetId);
    const targetSS = SpreadsheetApp.openById(targetSpreadsheetId);
    const sSheet = sourceSS.getSheetByName(sourceSheetName);
    const tSheet = targetSS.getSheetByName(targetSheetName);

    if (!sSheet || !tSheet) throw new Error("源表或目标表不存在");

    // 获取表头映射
    const sHeaders = sSheet.getRange(headerRowIndex, 1, 1, sSheet.getLastColumn()).getDisplayValues()[0];
    const tHeaders = tSheet.getRange(headerRowIndex, 1, 1, tSheet.getLastColumn()).getDisplayValues()[0];

    const s_dtIdx = sHeaders.indexOf("dt") + 1;
    const s_batchIdx = sHeaders.indexOf("batch_index") + 1;
    const s_partnerIdx = sHeaders.indexOf("partner id") + 1;
    const t_idIdx = tHeaders.indexOf("id") + 1;
    const t_dtIdx = tHeaders.indexOf("dt") + 1;
    const t_batchIdx = tHeaders.indexOf("batch_index") + 1;
    const t_partnerIdx = tHeaders.indexOf("partner id") + 1;

    Logger.log(`    源表索引: dt(${s_dtIdx}), partner(${s_partnerIdx})`);
    Logger.log(`    目标索引: id(${t_idIdx}), dt(${t_dtIdx})`);

    // --- A. 从源表筛选数据 ---
    const sLastRow = sSheet.getLastRow();
    const sData = sSheet.getRange(headerRowIndex + 1, 1, sLastRow - headerRowIndex, sHeaders.length).getDisplayValues();
    const searchDt = targetDt.toString().replace(/'/g, "").trim();

    const newData = sData.filter(row => row[s_dtIdx - 1].replace(/'/g, "").trim() === searchDt)
      .map(row => {
        const dtVal = row[s_dtIdx - 1].replace(/'/g, "");
        const partnerId = row[s_partnerIdx - 1];
        const newRow = new Array(tHeaders.length).fill("");
        newRow[t_idIdx - 1] = "'" + `${dtVal}_${partnerId}`;
        newRow[t_dtIdx - 1] = "'" + dtVal;
        newRow[t_batchIdx - 1] = row[s_batchIdx - 1];
        newRow[t_partnerIdx - 1] = partnerId;
        return newRow;
      });

    Logger.log(`    从源表筛选出匹配行数: ${newData.length}`);
    if (newData.length === 0) return { state: "warn", message: "源表无该日期数据" };

    // --- B. 排除目标表中的旧数据 (去重) ---
    const tLastRow = tSheet.getLastRow();
    let finalData = [];
    if (tLastRow > headerRowIndex) {
      const existingData = tSheet.getRange(headerRowIndex + 1, 1, tLastRow - headerRowIndex, tHeaders.length).getValues();
      finalData = existingData.filter(row => row[t_dtIdx - 1].toString().replace(/'/g, "").trim() !== searchDt);
      Logger.log(`    目标表原总行数: ${existingData.length}, 排除旧日期后保留行数: ${finalData.length}`);
    }

    // --- C. 合并并写回 ---
    finalData = finalData.concat(newData);
    Logger.log(`    最终待写入总行数: ${finalData.length}`);

    if (tSheet.getLastRow() > headerRowIndex) {
      tSheet.getRange(headerRowIndex + 1, 1, tSheet.getLastRow() - headerRowIndex, tHeaders.length).clearContent();
      Logger.log(`    已清空目标表旧数据区。`);
    }

    tSheet.getRange(headerRowIndex + 1, 1, finalData.length, tHeaders.length).setValues(finalData);
    Logger.log(`<<< [跨表同步完成] 日期: ${targetDt}, 目标表总行数现为: ${finalData.length}`);

    return { state: "success", count: newData.length };
  },
  /**
   * 通用方法：根据某一列的条件值，获取另一列的最大值
   * 
   * @param {object} requestData 参数对象
   * {
   *   spreadsheetId: "...",
   *   sheetName: "...",
   *   conditionColumnName: "dt",       // 条件列名
   *   conditionValue: "20260210",     // 匹配的条件值
   *   targetColumnName: "batch_index", // 要找最大值的目标列名
   *   headerRowIndex: 1
   * }
   * 
   * @return {Map} 包含结果的 Map 对象
   */
  get_max_value_by_condition: function(requestData) {
    const { 
      spreadsheetId, 
      sheetName, 
      conditionColumnName, 
      conditionValue, 
      targetColumnName,
      headerRowIndex = 1 
    } = requestData;

    // 1. 参数基础校验
    if (!spreadsheetId || !sheetName || !conditionColumnName || conditionValue === undefined || !targetColumnName) {
      throw new Error("get_max_value_by_condition 缺少必要参数");
    }

    const ss = SpreadsheetApp.openById(spreadsheetId);
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) throw new Error(`未找到表: ${sheetName}`);

    const lastRow = sheet.getLastRow();
    
    // 初始化返回对象
    const result = {
      conditionValue: conditionValue,
      maxValue: 0,
      matchCount: 0,
      status: "pending"
    };

    if (lastRow <= headerRowIndex) {
      result.status = "empty_sheet";
      return result;
    }

    // 2. 获取表头并查找列索引
    const headers = sheet.getRange(headerRowIndex, 1, 1, sheet.getLastColumn()).getDisplayValues()[0];
    const condColIdx = headers.indexOf(conditionColumnName);
    const targetColIdx = headers.indexOf(targetColumnName);

    if (condColIdx === -1 || targetColIdx === -1) {
      throw new Error(`列名未找到: 请检查表中是否存在 "${conditionColumnName}" 和 "${targetColumnName}"`);
    }

    // 3. 读取数据区 (使用 getValues 提高处理效率)
    const data = sheet.getRange(headerRowIndex + 1, 1, lastRow - headerRowIndex, headers.length).getValues();
    
    // 预处理搜索值：转为字符串并去掉可能存在的单引号 '
    const normalizedCondValue = conditionValue.toString().replace(/'/g, "").trim();
    
    let maxVal = 0;
    let count = 0;

    // 4. 遍历逻辑
    for (let i = 0; i < data.length; i++) {
      const row = data[i];
      // 单元格数据预处理（处理 dt 等可能带单引号的文本）
      const cellValue = row[condColIdx].toString().replace(/'/g, "").trim();
      
      if (cellValue === normalizedCondValue) {
        count++;
        // 尝试转为数字进行比较
        const currentTargetVal = Number(row[targetColIdx]);
        if (!isNaN(currentTargetVal) && currentTargetVal > maxVal) {
          maxVal = currentTargetVal;
        }
      }
    }

    // 5. 完善返回对象
    result.maxValue = maxVal;
    result.matchCount = count;
    result.status = count > 0 ? "success" : "not_found";

    Logger.log(`[查询完成] ${conditionColumnName}=${conditionValue}, 最大 ${targetColumnName}: ${maxVal}`);
    
    return result;
  }
};

/**
 * 外部调用的主入口
 */
function runMainTask() {
  const config = {
    sourceId: "1K6O83_1wklZFh9lNCXWje1TiAYyYyv-xBPLBYOmwPIQ",
    targetId: "1G0apwNOGSPKedvmUm_ynQMTvfO-k62mdOMozEIrbstU",
    sheet1: "url_content3",
    sheet2: "url_content",
    dt: "20260210"
  };

  try {
    // 1. 先完善源表的 dt 和 batch_index
    ProjectPpzggzsx.fill_dt_and_batch_index({
      spreadsheetId: config.sourceId,
      sheetName: config.sheet1,
      batchSize: 50
    });

    // 2. 跨表同步
    const result = ProjectPpzggzsx.sync_to_sheet2({
      sourceSpreadsheetId: config.sourceId,
      targetSpreadsheetId: config.targetId,
      sourceSheetName: config.sheet1,
      targetSheetName: config.sheet2,
      targetDt: config.dt
    });

    if (result.status === "success") {
      Logger.log("任务全部成功完成！");
    }
  } catch (e) {
    Logger.log("!!! 任务执行失败: " + e.toString());
  }
}
/**
 * 如何调用通用方法的示例
 */
function testFillDtAndBatchIndex() {
  // 示例：获取 dt 为 20260210 的最大 batch_index
  const resultPayload = ProjectPpzggzsx.fill_dt_and_batch_index({
    spreadsheetId: "1K6O83_1wklZFh9lNCXWje1TiAYyYyv-xBPLBYOmwPIQ",
    sheetName: "url_content3",
  });
  Logger.log(`resultPayload: ${JSON.stringify(resultPayload)}`);
}
/**
 * 如何调用通用方法的示例
 */
function testGenericMax() {
  // 示例：获取 dt 为 20260210 的最大 batch_index
  const resultPayload = ProjectPpzggzsx.get_max_value_by_condition({
    spreadsheetId: "1G0apwNOGSPKedvmUm_ynQMTvfO-k62mdOMozEIrbstU",
    sheetName: "partners",
    conditionColumnName: "dt",
    conditionValue: "20260210",
    targetColumnName: "batch_index"
  });
  Logger.log(`resultPayload: ${JSON.stringify(resultPayload)}`);
}
```

## api_google_drive.gs
```gs
/**
 * ApiGoogleDrive: Drive 操作
 */
const ApiGoogleDrive = {
  /**
   * 1. 复制 Google Drive 文件到指定文件夹
   * 
   * @param {object} requestData 参数对象
   * {
   *   sourceFileId: "...",        // 必填：源文件 ID
   *   newName: "...",             // 选填：新文件名（不填则默认为 原名 + " 副本"）
   *   destinationFolderId: "..."  // 选填：目标文件夹 ID（不填则默认放在源文件同级目录）
   * }
   */
  copy_file: function(requestData) {
    const { sourceFileId, newName, destinationFolderId } = requestData;
    Logger.log(`>>> [开始复制文件] 源文件 ID: ${sourceFileId}`);

    try {
      // 1. 获取源文件
      const sourceFile = DriveApp.getFileById(sourceFileId);
      
      // 2. 确定目标文件夹
      let targetFolder;
      if (destinationFolderId) {
        targetFolder = DriveApp.getFolderById(destinationFolderId);
      } else {
        // 如果未指定文件夹，获取源文件所在的第一个父文件夹
        const parents = sourceFile.getParents();
        targetFolder = parents.hasNext() ? parents.next() : DriveApp.getRootFolder();
      }

      // 3. 确定新文件名
      const finalName = newName || (sourceFile.getName() + " 副本");

      // 4. 执行复制操作
      const newFile = sourceFile.makeCopy(finalName, targetFolder);

      Logger.log(`<<< [复制完成] 新文件 ID: ${newFile.getId()}, 名称: ${finalName}`);

      return {
        newFileId: newFile.getId(),
        newFileName: finalName,
        url: newFile.getUrl()
      };

    } catch (e) {
      const errorMsg = e.toString();
      Logger.log(`!!! [复制失败] 错误信息: ${errorMsg}`);
      throw new Error(`!!! [复制失败] 错误信息: ${errorMsg}`);
    }
  }
};



/**
 * 测试方法：测试复制文件逻辑
 */
function testCopyFile() {
  const testPayload = {
    // 换成你实际的源文件 ID
    sourceFileId: "1IM7Oarzpy1Prj5j0v_o3iVaagaZpil2cunD2bJDEnEg", 
    // 换成你实际的目标文件夹 ID
    destinationFolderId: "1zy8TzdIshKYziAosfWZBTTLuGdHLOLG5",
    // 新文件名
    newName: "eBay抓取数据模板_20260428"
  };

  const result = ApiGoogleDrive.copy_file(testPayload);
  
  if (result.state === "success") {
    Logger.log("✅ 复制成功！");
    Logger.log("新文件 ID: " + result.newFileId);
    Logger.log("文件预览地址: " + result.url);
  } else {
    Logger.log("❌ 复制失败: " + result.message);
  }
}

```

## api_google_sheet.gs
```gs
/**
 * ApiGoogleSheet: GoogleSheet
 */
const ApiGoogleSheet = {
  /**
   * 补充 dt 和 batch_index 列，并返回批次汇总
   */
  fill_dt_and_batch_index: function(requestData) {
    const { spreadsheetId, sheetName, batchSize = 10, headerRowIndex = 1 } = requestData;
    Logger.log(`>>> [开始补充列数据] SpreadsheetId: ${spreadsheetId}, Sheet: ${sheetName}`);

    const spreadsheet = SpreadsheetApp.openById(spreadsheetId);
    const sheet = spreadsheet.getSheetByName(sheetName);
    if (!sheet) throw new Error(`未找到表: ${sheetName}`);

    const lastRow = sheet.getLastRow();

    // 情况 A：没有数据行
    if (lastRow <= headerRowIndex) {
      Logger.log(`--- [补充结束] 表内无有效数据。`);
      return {
        batch_summary: [], // 返回空数组
        message: "表格为空，未进行任何处理。"
      };
    }

    // 查找列索引
    const headers = sheet.getRange(headerRowIndex, 1, 1, sheet.getLastColumn()).getDisplayValues()[0];
    const dtIdx = headers.indexOf("dt") + 1;
    const batchIdx = headers.indexOf("batch_index") + 1;
    const timeIdx = headers.indexOf("create_time") + 1;

    if (!dtIdx || !batchIdx || !timeIdx) throw new Error("缺少必要的列名: dt, batch_index 或 create_time");

    const numRows = lastRow - headerRowIndex;
    const timeValues = sheet.getRange(headerRowIndex + 1, timeIdx, numRows, 1).getDisplayValues();

    const dtCounterMap = {}; // 记录每个 dt 出现的次数
    const dtOut = [];
    const batchOut = [];

    for (let i = 0; i < numRows; i++) {
      const timeStr = timeValues[i][0];
      if (!timeStr) {
        dtOut.push([""]); batchOut.push([""]);
        continue;
      }
      
      // 提取日期 YYYYMMDD
      const rawDt = timeStr.substring(0, 10).replace(/-/g, "");
      const dtWithQuote = "'" + rawDt;
      
      if (!dtCounterMap[rawDt]) dtCounterMap[rawDt] = 0;
      
      // 计算当前行的批次号 (从1开始)
      const currentBatch = Math.floor(dtCounterMap[rawDt] / batchSize) + 1;
      dtCounterMap[rawDt]++;

      dtOut.push([dtWithQuote]);
      batchOut.push([currentBatch]);
    }

    // 批量写入
    sheet.getRange(headerRowIndex + 1, dtIdx, numRows, 1).setValues(dtOut);
    sheet.getRange(headerRowIndex + 1, batchIdx, numRows, 1).setValues(batchOut);
    
    // --- 核心修改：构造返回的汇总数组 ---
    const batchSummary = Object.keys(dtCounterMap).map(dtKey => {
      return {
        "dt": dtKey,
        "max_batch_index": Math.ceil(dtCounterMap[dtKey] / batchSize)
      };
    });

    Logger.log(`<<< [补充完成] 汇总信息: ${JSON.stringify(batchSummary)}`);

    // 返回执行结果对象
    return {
      processedRows: numRows,
      batch_summary: batchSummary, // 这里就是你需要的数组
      message: `成功补充数据，包含 ${batchSummary.length} 个不同的日期。`
    };
  },
  /**
   * 根据某一列的条件值，获取另一列的最大值
   * 
   * @param {object} requestData 参数对象
   * {
   *   spreadsheetId: "...",
   *   sheetName: "...",
   *   conditionColumnName: "dt",       // 条件列名
   *   conditionValue: "20260210",     // 匹配的条件值
   *   targetColumnName: "batch_index", // 要找最大值的目标列名
   *   headerRowIndex: 1
   * }
   * 
   * @return {Map} 包含结果的 Map 对象
   */
  get_max_value_by_condition: function(requestData) {
    const { 
      spreadsheetId, 
      sheetName, 
      conditionColumnName, 
      conditionValue, 
      targetColumnName,
      headerRowIndex = 1 
    } = requestData;

    // 1. 参数基础校验
    if (!spreadsheetId || !sheetName || !conditionColumnName || conditionValue === undefined || !targetColumnName) {
      throw new Error("get_max_value_by_condition 缺少必要参数");
    }

    const ss = SpreadsheetApp.openById(spreadsheetId);
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) throw new Error(`未找到表: ${sheetName}`);

    const lastRow = sheet.getLastRow();
    
    // 初始化返回对象
    const result = {
      conditionValue: conditionValue,
      maxValue: 0,
      matchCount: 0,
      status: "pending"
    };

    if (lastRow <= headerRowIndex) {
      result.status = "empty_sheet";
      return result;
    }

    // 2. 获取表头并查找列索引
    const headers = sheet.getRange(headerRowIndex, 1, 1, sheet.getLastColumn()).getDisplayValues()[0];
    const condColIdx = headers.indexOf(conditionColumnName);
    const targetColIdx = headers.indexOf(targetColumnName);

    if (condColIdx === -1 || targetColIdx === -1) {
      throw new Error(`列名未找到: 请检查表中是否存在 "${conditionColumnName}" 和 "${targetColumnName}"`);
    }

    // 3. 读取数据区 (使用 getValues 提高处理效率)
    const data = sheet.getRange(headerRowIndex + 1, 1, lastRow - headerRowIndex, headers.length).getValues();
    
    // 预处理搜索值：转为字符串并去掉可能存在的单引号 '
    const normalizedCondValue = conditionValue.toString().replace(/'/g, "").trim();
    
    let maxVal = 0;
    let count = 0;

    // 4. 遍历逻辑
    for (let i = 0; i < data.length; i++) {
      const row = data[i];
      // 单元格数据预处理（处理 dt 等可能带单引号的文本）
      const cellValue = row[condColIdx].toString().replace(/'/g, "").trim();
      
      if (cellValue === normalizedCondValue) {
        count++;
        // 尝试转为数字进行比较
        const currentTargetVal = Number(row[targetColIdx]);
        if (!isNaN(currentTargetVal) && currentTargetVal > maxVal) {
          maxVal = currentTargetVal;
        }
      }
    }

    // 5. 完善返回对象
    result.maxValue = maxVal;
    result.matchCount = count;
    result.status = count > 0 ? "success" : "not_found";

    Logger.log(`[查询完成] ${conditionColumnName}=${conditionValue}, 最大 ${targetColumnName}: ${maxVal}`);
    
    return result;
  }
};

/**
 * 如何调用通用方法的示例
 */
function testFillDtAndBatchIndex() {
  // 示例：获取 dt 为 20260210 的最大 batch_index
  const resultPayload = ApiGoogleSheet.fill_dt_and_batch_index({
    spreadsheetId: "1K6O83_1wklZFh9lNCXWje1TiAYyYyv-xBPLBYOmwPIQ",
    sheetName: "url_content3",
  });
  Logger.log(`resultPayload: ${JSON.stringify(resultPayload)}`);
}
/**
 * 如何调用通用方法的示例
 */
function testGenericMax() {
  // 示例：获取 dt 为 20260210 的最大 batch_index
  const resultPayload = ApiGoogleSheet.get_max_value_by_condition({
    spreadsheetId: "1G0apwNOGSPKedvmUm_ynQMTvfO-k62mdOMozEIrbstU",
    sheetName: "partners",
    conditionColumnName: "dt",
    conditionValue: "20260210",
    targetColumnName: "batch_index"
  });
  Logger.log(`resultPayload: ${JSON.stringify(resultPayload)}`);
}
```