# Timetable

[![banner](img/banner-title.png)](img/banner-title.png)

生成一个可自动更新的课程表 iCalendar (ICS) 订阅源，并通过 GitHub Pages 发布。

- 英文 README（本仓库主文档）：[README.md](README.md)
- 简体中文：当前文件

## 功能特性

- 生成 ICS 可订阅日历文件
- 控制可见范围：`visible_weeks` 和 `visible_days`（OR 逻辑）
- 节假日过滤：支持日期范围、单日和按星期过滤
- 临时调课：整天按指定星期 (`use_weekday`) 或逐课节替换
- GitHub Actions 工作流和 GitHub Pages 自动发布配置

## 快速开始 (GitHub Action + GitHub Pages)

1. 修改 `data/` 下的 JSON 文件以配置你的课表，配置说明参见下文“数据结构”部分

2. 启用 GitHub Actions 工作流

启用后，当你修改代码或 timetable 数据后，会自动生成并发布新的 ICS 文件

每天早上 6 点也会自动更新一次

3. 在仓库设置中启用 GitHub Pages，选择 `gh-pages` 分支作为发布源

4. 在日历中订阅

```
https://<username>.github.io/<repo>/calendar.ics
```

例如：

```
https://zhaozhuoran.github.io/timetable/calendar.ics
```

## 数据结构

完整的 JSON 配置示例和字段说明请参见 [CONFIG.md](CONFIG.md)。关键文件：

- `data/periods.json`：节次时间
- `data/subjects.json`：课程 ID 到显示名称的映射
- `data/timetable.json`：主课表配置
- `data/holidays.json`：节假日配置
- `data/overrides.json`：临时调课配置
- `data/timetables/*.json`：具体课表文件

请在正式使用前将仓库中 `data/` 目录下的示例文件替换为你的实际配置。

## GitHub Actions 与 GitHub Pages

仓库中预配置了两个 GitHub Actions 工作流：

- `.github/workflows/generate.yml`：检测日程设置或代码变化并实施刷新
- `.github/workflows/daily_update.yml`：每日自动刷新

你可以针对你的需要来修改这些工作流。

备注：

- 若提交说明中包含 `[SKIP]`，该次提交会跳过工作流执行。
- 生成脚本会将 `static/` 中的文件（例如 `static/CNAME`）复制到 `_site/`，从而一并发布到 Pages，你可以在这里设置 CNAME 文件，避免发布后自定义域名失效的问题。
- 首次成功运行后，请在仓库设置中启用 GitHub Pages，并选择 `gh-pages` 分支作为发布源。

## LICENSE

本项目使用 GNU 通用公共许可证第 3 版 (GPLv3) 授权，详见 [LICENSE](LICENSE)。
