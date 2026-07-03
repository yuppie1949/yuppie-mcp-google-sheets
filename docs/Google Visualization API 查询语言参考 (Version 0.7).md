这是一份根据 Google Visualization API 查询语言官方文档（[Google Charts Query Language Reference](https://developers.google.com/chart/interactive/docs/querylanguage)）整理的 Markdown 格式参考指南。

---

# Google Visualization API 查询语言参考 (Version 0.7)

Google Visualization API 查询语言允许你对图表的数据源进行各种数据操作。它的语法与 SQL 非常相似。开发者可以通过查询语言发送数据处理和格式化请求，确保返回的数据结构和内容完全匹配可视化图表的需求。

## 1. 使用查询语言 (Using the Query Language)

你可以通过两种方式将查询字符串附加到数据源请求中：

### 1.1 在 JavaScript 代码中设置查询
调用 `google.visualization.Query` 类的 `setQuery` 方法：
```javascript
var query = new google.visualization.Query(DATA_SOURCE_URL);
query.setQuery('select dept, sum(salary) group by dept');
query.send(handleQueryResponse);
```

### 1.2 在数据源 URL 中设置查询
可以通过 `tq` 参数将查询字符串附加到数据源 URL 中。查询字符串必须进行 URL 编码（例如使用 JavaScript 的 `encodeURIComponent` 函数）。
```text
原始查询: select A, sum(B) group by A
编码后: select%20A%2C%20sum(B)%20group%20by%20A
完整URL: https://docs.google.com/.../gviz/tq?tq=select%20A%2C%20sum(B)%20group%20by%20A
```

---

## 2. 语言语法 (Language Syntax)

查询语言是一种类似于 SQL 的语法，但它是 SQL 的子集，并包含一些独有功能。**列总是通过标识符（ID，如 A、B、C）而不是标签来引用的。**

### 2.1 语言子句 (Language Clauses)
查询由多个子句组成，各个子句用空格分隔，并且 **必须严格按照以下顺序排列**（所有子句均为可选）：

| 子句 (Clause) | 用途说明 |
| :--- | :--- |
| **`select`** | 选择要返回的列及其顺序。如果省略或使用 `select *`，则按默认顺序返回所有列。 |
| **`where`** | 仅返回符合特定条件的行。 |
| **`group by`** | 对跨行的值进行聚合。 |
| **`pivot`** | 将列中的唯一值（distinct values）转换为新的数据列。 |
| **`order by`** | 根据指定列的值对行进行排序。 |
| **`limit`** | 限制返回的行数。 |
| **`offset`** | 跳过给定数量的首批行。 |
| **`label`** | 为列设置标签。 |
| **`format`** | 使用给定的格式模式（Pattern）对特定列的值进行格式化。 |
| **`options`** | 设置附加选项（例如 `no_format` 或 `no_values`）。 |

*(注：原 SQL 中的 `from` 子句已被该语言移除)*

---

### 2.2 核心子句详解

#### `select`
用于指定要返回的列。
```sql
select dept, salary
select max(salary)
select `email address`, name, `date` 
-- 包含空格或为保留字的列名需用反引号 (`) 括起来
```

#### `where`
支持常规比较运算符 (`<=`, `<`, `>`, `>=`, `=`, `!=`, `<>`)、逻辑运算符 (`and`, `or`, `not`)，且判断空值使用 `is null` 或 `is not null`。
复杂字符串比较支持：
* `contains` (包含子串)
* `starts with` (前缀匹配)
* `ends with` (后缀匹配)
* `matches` (正则表达式匹配)
* `like` (通配符匹配，`%` 代替任意多个字符，`_` 代替一个字符)
```sql
where salary >= 600
where dept != 'Eng' and date '2005-01-21' < hireDate
where name contains 'John'
```

#### `group by` 和 `pivot`
* **`group by`**: 按组聚合数据。`select` 中出现的每个列必须要么在 `group by` 中，要么被包裹在聚合函数中。
* **`pivot`**: 将数据透视为新列（经常在绘制按时间分布的多线图时非常有用）。 `pivot` 同样要求未被透视的列必须进行聚合。
```sql
select dept, max(salary) group by dept
select dept, sum(salary) group by dept pivot lunchTime
```

#### 其他功能子句
* **`order by`**: 排序（加上 `desc` 降序）。如 `order by dept, salary desc`
* **`limit`** / **`offset`**: 如 `limit 10 offset 20` (跳过前20条，取10条)
* **`label`**: 修改显示名称。如 `label dept 'Department'`
* **`format`**: 修改显示格式（ICU标准）。如 `format salary '#,##0.00'`

---

## 3. 数据操作函数 (Data Manipulation Functions)

### 3.1 聚合函数 (Aggregation Functions)
*只能传递**列标识符**，不能作用于其他函数的结果（如不能用 `max(year(startDate))` ）。只能在 `select`, `order by`, `label`, `format` 中使用。*

| 函数 | 说明 |
| :--- | :--- |
| **`avg()`** | 返回分组中列值的平均数（仅数字） |
| **`count()`** | 返回分组中的元素计数（不计算 null 值） |
| **`max()`** / **`min()`** | 返回列中的最大/小值（支持任意类型） |
| **`sum()`** | 返回所有值的总和（仅数字） |

### 3.2 标量函数 (Scalar Functions)
用于单值计算，可在几乎所有子句中使用（`select`, `where`, `group by`, `pivot`, `order by`, `label`, `format`）。

| 类型 | 函数列表 |
| :--- | :--- |
| **日期时间** | `year()`, `month()` (0-11), `day()`, `hour()`, `minute()`, `second()`, `millisecond()`, `quarter()`, `dayOfWeek()` (1代表周日), `now()`, `dateDiff()`, `toDate()` |
| **字符串** | `upper()`, `lower()` |

*(示例: `year(date "2009-02-05")` 返回 2009)*

### 3.3 算术运算符
支持加（`+`）、减（`-`）、乘（`*`）、除（`/`）。
```sql
select empSalary - empTax
```

---

## 4. 语言元素 (Language Elements)

### 4.1 字面量 (Literals)
* **字符串 (string)**: 用单引号或双引号括起 (例: `'hello world'`, `"fourteen"`)
* **数字 (number)**: 十进制小数 (例: `3.14`, `-71`)
* **布尔值 (boolean)**: `true` 或 `false`
* **日期 (date)**: 格式为 `date "yyyy-MM-dd"` (例: `date "2008-03-18"`)
* **时间 (timeofday)**: 格式为 `timeofday "HH:mm:ss[.SSS]"`
* **日期时间 (datetime)**: 格式为 `datetime "yyyy-MM-dd HH:mm:ss[.sss]"`

### 4.2 标识符 (Identifiers) / 列ID
列的 ID 如果满足以下任意条件，**必须使用反引号 (`) 括起来**：
1. 包含空格
2. 是保留字
3. 包含除了字母、数字、下划线 `[a-zA-Z0-9_]` 之外的字符
4. 以数字开头

### 4.3 大小写敏感性 (Case Sensitivity)
* **标识符（列名）** 和 **字符串字面量** 是 **区分大小写** 的。
* 所有的查询语言关键字（如 `select`, `where`, `max` 等）是 **不区分大小写** 的。

### 4.4 保留字 (Reserved Words)
如果在标识符中使用了以下保留字，必须使用反引号 (`) 括起来：
`and`, `asc`, `by`, `date`, `datetime`, `desc`, `false`, `format`, `group`, `label`, `limit`, `not`, `offset`, `options`, `or`, `order`, `pivot`, `select`, `timeofday`, `timestamp`, `true`, `where`。