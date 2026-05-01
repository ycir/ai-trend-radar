# AI Trend Radar MVP

一个用于追踪 AI 行业新热点的最小可行工具。它会从 GitHub、Hugging Face、Hacker News 和 arXiv 抓取信号，做一个简单趋势评分，然后生成 Markdown 和 HTML 报告。

第一版目标不是完美预测趋势，而是每天稳定地产生一份可以快速扫读的“新项目 / 新模型 / 新论文 / 社区讨论”清单。

## 功能

- 支持今日、本周、本月窗口：`--days 1`、`--days 7`、`--days 30`
- 采集 GitHub 新仓库和热门 AI 相关仓库
- 采集 Hugging Face 热门模型
- 采集 Hacker News 相关讨论
- 采集 arXiv 最新 AI 相关论文
- 本地 SQLite 保存历史快照，为后续计算增长率做准备
- 基于历史快照计算 Star、下载、点赞、评论等增长指标
- 可选 OpenAI 摘要：解释项目是什么、为什么值得看、有什么风险
- 输出 Markdown 和 HTML 报告
- GitHub Actions 可自动发布到 GitHub Pages
- 支持离线样例模式，方便先验证环境

## 快速开始

如果你不想安装包，直接在项目根目录运行：

```powershell
$env:PYTHONPATH="src"
python -m trend_radar --offline
```

生成结果会在：

```text
reports/
data/trends.sqlite3
```

如果要跑真实数据：

```powershell
$env:PYTHONPATH="src"
$env:GITHUB_TOKEN="你的 GitHub token"
python -m trend_radar --days 1 --limit 25
```

如果要给榜单前几项加 LLM 摘要：

```powershell
$env:PYTHONPATH="src"
$env:OPENAI_API_KEY="sk_xxx"
python -m trend_radar --days 1 --limit 25 --summarize
```

如果你已经安装了 Python，也可以先安装成命令行工具：

```powershell
python -m pip install -e .
trend-radar --offline
```

本周和本月：

```powershell
$env:PYTHONPATH="src"
python -m trend_radar --days 7 --limit 40
python -m trend_radar --days 30 --limit 60
```

## GitHub Token

不配置 token 也能跑，但 GitHub API 很容易触发限制。建议创建一个只读 token，然后设置：

```powershell
$env:GITHUB_TOKEN="ghp_xxx"
```

## GitHub Pages

仓库里包含 `.github/workflows/daily-report.yml`。它会每天生成 daily、weekly、monthly 三份报告，并把 daily 报告发布成 GitHub Pages 首页。

启用方式：

1. 到 GitHub 仓库的 `Settings -> Pages`
2. `Build and deployment` 选择 `GitHub Actions`
3. 如需 LLM 摘要，在 `Settings -> Secrets and variables -> Actions` 添加 `OPENAI_API_KEY`
4. 手动运行一次 `Daily AI Trend Radar` workflow 验证

## 自定义关键词

```powershell
$env:PYTHONPATH="src"
python -m trend_radar --days 7 --keywords "agent,llm,rag,mcp,inference,eval,coding agent,voice,video"
```

## 目录结构

```text
src/trend_radar/
  collectors/      数据源采集器
  cli.py           命令行入口
  scoring.py       趋势评分
  storage.py       SQLite 快照
  summarizer.py    可选 LLM 摘要
  report.py        Markdown / HTML 报告
```

## 下一步建议

1. 加 GitHub Stargazers 时间序列，让 Star 增长统计更精确。
2. 加 GH Archive，捕捉突然增多的 Star/Fork/Watch 事件。
3. 加 Product Hunt、Reddit、GDELT、公司博客 RSS。
4. 做 Telegram、Email 或 Slack 推送。
5. 加项目详情页，展示指标曲线、README 摘要、Release 和许可证。
