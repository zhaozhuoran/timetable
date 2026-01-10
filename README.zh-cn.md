# 课程表 ICS

生成一个可自动更新的课程表 iCalendar (ICS) 订阅源，并通过 GitHub Pages 对外发布。

- 英文 README（本仓库主文档）：[README.md](README.md)
- 简体中文：当前文件

## 功能特性

- 生成 ICS，使用可重复计算的确定性 UID。
- 控制可见范围：`visible_weeks` 和 `visible_days`（OR 逻辑）。
- 节假日过滤：支持日期范围、单日和按星期过滤。
- 临时调课：整天按指定星期 (`use_weekday`) 或逐节替换。
- 支持课表 v1/v2 以及 `$version` 元数据字段。
- 自带 GitHub Actions 工作流和 GitHub Pages 自动发布配置。

## 快速开始

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 生成 ICS

```bash
python scripts/generate_ics.py
```

生成的文件会写入 `_site/calendar.ics`（目录会自动创建）。

3. 在日历中订阅（示例）

```
https://<username>.github.io/<repo>/calendar.ics
```

## 数据结构

完整的 JSON 配置示例和字段说明请参见 [CONFIG.md](CONFIG.md)。关键文件：

- `data/periods.json`：节次时间，包含 `start` / `end`（格式 `HH:MM`）
- `data/subjects.json`：课程 ID 到显示名称的映射
- `data/timetable.json`：主课表配置；支持 v1（单一数组）和 v2（多课表 + 日期范围）
- `data/holidays.json`：节假日配置，兼容旧/新两种格式
- `data/overrides.json`：临时调课（`{use_weekday}` 或若干 `{period, subject}` 条目）

仓库中 `data/` 下的数据正式使用前请替换为你自己的课表。

## GitHub Actions 与 GitHub Pages

仓库内的 `.github/workflows/generate.yml` 定义了自动生成并发布 ICS 的工作流：

- 当推送到 `main` 分支，且修改了 `data/**`、`scripts/**`、`requirements.txt` 或工作流本身时会触发。
- 工作流会安装依赖并执行 `python scripts/generate_ics.py`，将 ICS 写入 `_site/calendar.ics`。
- 使用 `peaceiris/actions-gh-pages` 将 `_site/` 目录发布到 GitHub Pages（默认推送到 `gh-pages` 分支）。

说明：

- 若提交说明中包含 `[SKIP]`，该次提交会跳过工作流执行。
- 生成脚本会将 `static/` 中的文件（例如 `static/CNAME`）复制到 `_site/`，从而一并发布到 Pages。
- 首次成功运行后，请在仓库设置中启用 GitHub Pages，并选择工作流使用的分支（通常是 `gh-pages`）。

## 测试

项目使用 Python 自带的 `unittest` 测试框架：

```bash
python -m unittest discover
```

测试会临时修改 `data/timetable.json` 并在结束后恢复，同时在需要时清理 `_site/` 目录。

## 许可协议

本项目使用 GNU 通用公共许可证第 3 版 (GPLv3) 授权，详见 [LICENSE](LICENSE)。
