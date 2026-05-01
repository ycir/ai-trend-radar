from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

from .models import TrendItem


def write_reports(items: list[TrendItem], output_dir: str, days: int) -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    label = _window_label(days)
    md_path = out / f"{stamp}-{label}.md"
    html_path = out / f"{stamp}-{label}.html"
    md_path.write_text(render_markdown(items, days), encoding="utf-8")
    html_path.write_text(render_html(items, days), encoding="utf-8")
    return md_path, html_path


def render_markdown(items: list[TrendItem], days: int) -> str:
    lines = [
        f"# AI Trend Radar - {_window_title(days)}",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    for index, item in enumerate(items, start=1):
        lines.extend(
            [
                f"## {index}. {item.title}",
                "",
                f"- Source: `{item.source}` / `{item.item_type}`",
                f"- Score: `{item.score}`",
                f"- Link: {item.url}",
                f"- Tags: {', '.join(item.tags[:8]) if item.tags else 'n/a'}",
                f"- Metrics: {_format_metrics(item)}",
                f"- Why now: {', '.join(item.score_reasons) if item.score_reasons else 'fresh signal'}",
                "",
                _one_line(item.description),
                "",
            ]
        )
    return "\n".join(lines)


def render_html(items: list[TrendItem], days: int) -> str:
    cards = "\n".join(_card(item, index) for index, item in enumerate(items, start=1))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Trend Radar - {_window_title(days)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f7f2;
      --text: #1f2933;
      --muted: #667085;
      --line: #d9ddd0;
      --accent: #0f766e;
      --accent-2: #b42318;
      --card: #ffffff;
    }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    header {{
      padding: 32px max(20px, 6vw) 20px;
      border-bottom: 1px solid var(--line);
      background: #ffffff;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(28px, 4vw, 48px);
      letter-spacing: 0;
    }}
    .sub {{
      margin: 0;
      color: var(--muted);
      font-size: 15px;
    }}
    main {{
      width: min(1120px, calc(100% - 32px));
      margin: 24px auto 48px;
      display: grid;
      gap: 12px;
    }}
    article {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    .topline {{
      display: flex;
      gap: 12px;
      justify-content: space-between;
      align-items: flex-start;
    }}
    h2 {{
      margin: 0;
      font-size: 18px;
      line-height: 1.35;
      letter-spacing: 0;
    }}
    a {{
      color: var(--accent);
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    .score {{
      flex: 0 0 auto;
      color: #ffffff;
      background: var(--accent);
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 13px;
      font-weight: 700;
    }}
    .meta, .reasons, .desc {{
      color: var(--muted);
      font-size: 14px;
      line-height: 1.5;
    }}
    .chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin: 12px 0;
    }}
    .chip {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 8px;
      font-size: 12px;
      color: #344054;
      background: #fafafa;
    }}
    @media (max-width: 640px) {{
      .topline {{
        flex-direction: column;
      }}
      .score {{
        border-radius: 6px;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>AI Trend Radar</h1>
    <p class="sub">{_window_title(days)} · Generated at {html.escape(datetime.now().isoformat(timespec='seconds'))}</p>
  </header>
  <main>
    {cards}
  </main>
</body>
</html>
"""


def _card(item: TrendItem, index: int) -> str:
    tags = "".join(f'<span class="chip">{html.escape(tag)}</span>' for tag in item.tags[:10])
    reasons = ", ".join(item.score_reasons) if item.score_reasons else "fresh signal"
    return f"""<article>
  <div class="topline">
    <h2>{index}. <a href="{html.escape(item.url)}">{html.escape(item.title)}</a></h2>
    <span class="score">{item.score:.2f}</span>
  </div>
  <p class="meta">{html.escape(item.source)} / {html.escape(item.item_type)} · {html.escape(_format_metrics(item))}</p>
  <div class="chips">{tags}</div>
  <p class="desc">{html.escape(_one_line(item.description))}</p>
  <p class="reasons">Why now: {html.escape(reasons)}</p>
</article>"""


def _format_metrics(item: TrendItem) -> str:
    if not item.metrics:
        return "n/a"
    return ", ".join(f"{key}: {value}" for key, value in item.metrics.items())


def _one_line(text: str) -> str:
    normalized = " ".join((text or "").split())
    return normalized[:360] + ("..." if len(normalized) > 360 else "")


def _window_label(days: int) -> str:
    if days <= 1:
        return "daily"
    if days <= 7:
        return "weekly"
    return "monthly"


def _window_title(days: int) -> str:
    if days <= 1:
        return "Today"
    if days <= 7:
        return "This Week"
    return "This Month"
