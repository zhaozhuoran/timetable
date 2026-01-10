# 配置说明

- 英文 (主文档) ：[CONFIG.md](CONFIG.md)
- 简体中文：当前文件

## 文件总览

所有配置文件位于 `data/` 目录下：

- `periods.json`：节次时间
- `subjects.json`：课程 ID 到显示名称的映射
- `timetable.json`：主课表配置
- `holidays.json`：节假日配置
- `overrides.json`：临时调课配置
- `timetables/*.json`：具体课表文件

## periods.json

用于定义每节课的起止时间。

### 格式示例

```json
{
  "1": { "start": "08:00", "end": "08:45" },
  "2": { "start": "08:55", "end": "09:40" },
  "3": { "start": "10:00", "end": "10:45" }
}
```

### 说明

- key 为课节 ID (字符串形式)
- `start` 和 `end` 为时间，格式 `HH:MM` (24 小时制)

## subjects.json

用于将课程 ID 映射到在日历中显示的课程名称。

### 格式示例

```json
{
  "Math": "Mathematics",
  "English": "English Language",
  "Physics": "Physics"
}
```

### 说明

- key：课表中引用的课程 ID
- 值：在日历事件中展示的名称

## timetable.json

主课表配置文件，支持两种版本。

### 版本 2 (推荐)

支持配置多个课表文件，每个文件有独立的起止日期范围：

```json
{
  "$version": 2,
  "timetables": [
    {
      "file": "data/timetables/spring2025.json",
      "start": "2025-02-20",
      "end": "2025-06-30",
      "visible_weeks": 2,
      "visible_days": 0,
      "ignore_past_days": false
    },
    {
      "file": "data/timetables/summer2025.json",
      "start": "2025-07-01",
      "end": "2025-07-10",
      "visible_weeks": 1,
      "visible_days": 1,
      "ignore_past_days": true
    }
  ]
}
```

### 版本 1 (兼容旧格式)

直接定义一个课表数组：

```json
{
  "$version": 1,
  "timetable": [
    { "weekday": 1, "period": "1", "subject": "Math" },
    { "weekday": 2, "period": "1", "subject": "English" }
  ]
}
```

或者使用最初的“裸数组”格式：

```json
[
  { "weekday": 1, "period": 1, "subject": "Math" },
  { "weekday": 6, "period": 1, "subject": "Physics" }
]
```

### 字段详解

- `$version`：版本号 (1 或 2)
- `timetables`：版本 2 中的课表配置列表
  - `file`：课表文件路径
  - `start`：生效开始日期 (`YYYY-MM-DD`)
  - `end`：生效结束日期 (`YYYY-MM-DD`)
  - `visible_weeks`：以“周”为窗口的可见范围 (默认 2)
    - 0：禁用按周控制，仅依赖 `visible_days`
    - 1：只显示当前周
    - 2：当前周 + 下一周，以此类推
  - `visible_days`：以“天”为窗口的可见范围 (默认 0)
    - 0：禁用按天控制，仅依赖 `visible_weeks`
    - 1：只显示“今天”
    - N：显示今天及之后共 N 天
    - 注意：与 `visible_weeks` 采用 OR 逻辑，只要满足任一条件即可；若两者都为 0，则该课表配置会被跳过。
      例如：`visible_weeks=1` 且 `visible_days=1` 时，即使在周日也会显示整周；如果只希望在周日预览周一，可以设置 `visible_days=2` 且 `visible_weeks=0`。
  - `ignore_past_days`：是否忽略今天之前的日期 (默认 `false`)，启用日历会更简洁 :)
    - `true`：跳过今天之前的整天事件
    - `false`：包含配置范围内的所有事件
- `timetable`：版本 1 中的课表数组

## timetables/\*.json

具体课表文件

### 格式示例

```json
{
  "$version": 1,
  "timetable": [
    { "weekday": 1, "period": "1", "subject": "Math" },
    { "weekday": 1, "period": "2", "subject": "English" },
    { "weekday": 2, "period": "1", "subject": "Physics" },
    { "weekday": 6, "period": "1", "subject": "Music" }
  ]
}
```

### 字段说明

- `weekday`：星期几，1=周一，2=周二，…，7=周日
- `period`：课节 ID (字符串) ，必须在 `periods.json` 中存在
- `subject`：课程 ID，必须在 `subjects.json` 中存在

## holidays.json

定义节假日，在这些日期内不会生成课程事件。

### 新格式 (v1，推荐)

支持日期范围和过滤条件：

```json
{
  "$version": 1,
  "holidays": [
    {
      "start": "2025-01-01",
      "end": "2025-01-03",
      "comment": "New Year"
    },
    {
      "date": "2025-06-14",
      "comment": "Dragon Boat Festival"
    },
    {
      "start": "2025-07-01",
      "end": "2025-08-31",
      "filter": {
        "weekday": [6, 7]
      },
      "comment": "Summer weekends"
    }
  ]
}
```

### 旧格式 (兼容)

按日期映射到布尔值，其中 `false` 表示跳过：

```json
{
  "2025-01-01": false,
  "2025-12-25": false
}
```

### 字段说明

新格式中支持：

- `date`：单个日期 (`YYYY-MM-DD`)
- `start` + `end`：日期范围 (`YYYY-MM-DD`)
- `filter`：可选过滤条件
  - `weekday`：指定哪些星期几为节假日，数组形式 (1–7)
- `comment`：可选备注信息

## overrides.json

临时调课配置，用于替换某天的正常课表。

### 格式示例

```json
{
  "2025-12-01": { "use_weekday": 1 },
  "2025-12-10": [
    { "period": "2", "subject": "Math" },
    { "period": "3", "subject": "Physics" }
  ],
  "2025-12-15": [{ "period": "1", "subject": "English" }]
}
```

### 字段说明

- 键：日期 (`YYYY-MM-DD`)
- 值：两种形式之一
  - `{ "use_weekday": <1-7> }`：整天按另一星期的课表重排
  - 若干 `{ "period", "subject" }` 组成的数组：仅对指定节次进行替换
  - `use_weekday` 使用源星期的完整课表，不受目标日期本身星期几的影响
  - 同一日期不能同时使用 `use_weekday` 和逐节替换，两种形式互斥

### 备注

- 某天一旦配置了 overrides，当天正常课表将被忽略！
- 仅会添加 overrides 中明确定义的事件

## 小贴士

1. 修改配置后，可先本地运行 `python scripts/generate_ics.py` 验证生成结果
2. 建议在大规模修改前先备份 `data/` 目录，但是 Git 也会帮你记录历史版本 :)
3. 所有日期均使用 `YYYY-MM-DD` 格式
4. 所有时间均使用 `HH:MM` (24 小时制)
5. 确保所有 JSON 文件以 UTF-8 编码保存，尤其是使用中文或者其他非 ASCII 字符时

## CI / 部署

仓库中预配置了两个 GitHub Actions 工作流：

- `.github/workflows/generate.yml`：检测日程设置或代码变化并实施刷新
- `.github/workflows/daily_update.yml`：每日自动刷新

你可以针对你的需要来修改这些工作流。

备注：

- 若提交说明中包含 `[SKIP]`，该次提交会跳过工作流执行。
- 生成脚本会将 `static/` 中的文件（例如 `static/CNAME`）复制到 `_site/`，从而一并发布到 Pages，你可以在这里设置 CNAME 文件，避免发布后自定义域名失效的问题。
- 首次成功运行后，请在仓库设置中启用 GitHub Pages，并选择 `gh-pages` 分支作为发布源。
