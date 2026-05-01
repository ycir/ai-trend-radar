from __future__ import annotations

from datetime import datetime, timedelta, timezone

from trend_radar.http import HttpClient
from trend_radar.models import TrendItem


def collect_github(
    client: HttpClient,
    days: int,
    limit: int,
    keywords: list[str],
    token: str | None = None,
) -> list[TrendItem]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    since = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    queries = [
        f"topic:artificial-intelligence created:>={since} stars:>=10 archived:false mirror:false",
        f"topic:llm created:>={since} stars:>=10 archived:false mirror:false",
        f"topic:ai-agent created:>={since} stars:>=5 archived:false mirror:false",
        f"topic:rag created:>={since} stars:>=5 archived:false mirror:false",
        f"topic:mcp created:>={since} stars:>=5 archived:false mirror:false",
    ]
    queries.extend(
        f"{keyword} in:name,description,readme pushed:>={since} stars:>=20 archived:false mirror:false"
        for keyword in keywords[:8]
    )

    items: dict[str, TrendItem] = {}
    per_query = max(5, min(50, limit))
    for query in queries:
        payload = client.get_json(
            "https://api.github.com/search/repositories",
            headers=headers,
            params={
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": per_query,
            },
        )
        for repo in payload.get("items", []):
            item = _repo_to_item(repo)
            items[item.key] = item
            if len(items) >= limit:
                break
        if len(items) >= limit:
            break

    return list(items.values())


def _repo_to_item(repo: dict) -> TrendItem:
    created_at = _parse_dt(repo.get("created_at"))
    pushed_at = _parse_dt(repo.get("pushed_at"))
    topics = repo.get("topics") or []
    return TrendItem(
        source="github",
        item_type="github_repo",
        title=repo.get("full_name") or repo.get("name") or "Untitled repository",
        url=repo.get("html_url") or "",
        description=repo.get("description") or "",
        created_at=created_at,
        tags=topics,
        metrics={
            "stars": repo.get("stargazers_count") or 0,
            "forks": repo.get("forks_count") or 0,
            "watchers": repo.get("watchers_count") or 0,
            "open_issues": repo.get("open_issues_count") or 0,
        },
        metadata={
            "language": repo.get("language"),
            "owner": (repo.get("owner") or {}).get("login"),
            "pushed_at": pushed_at.isoformat() if pushed_at else None,
            "license": (repo.get("license") or {}).get("spdx_id"),
        },
    )


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
