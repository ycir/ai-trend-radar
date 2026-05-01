from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import TrendItem


def sample_items() -> list[TrendItem]:
    now = datetime.now(timezone.utc)
    return [
        TrendItem(
            source="github",
            item_type="github_repo",
            title="example-org/agent-runtime",
            url="https://github.com/example-org/agent-runtime",
            description="A lightweight runtime for tool-using AI agents with tracing and sandboxed execution.",
            created_at=now - timedelta(hours=18),
            tags=["ai-agent", "llm", "tools"],
            metrics={"stars": 1430, "forks": 118, "watchers": 1430},
            metadata={"language": "Python", "license": "MIT"},
        ),
        TrendItem(
            source="huggingface",
            item_type="model",
            title="example/model-small-reasoner",
            url="https://huggingface.co/example/model-small-reasoner",
            description="Hugging Face model tagged: text-generation, reasoning, transformers",
            created_at=now - timedelta(days=2),
            tags=["text-generation", "reasoning", "transformers"],
            metrics={"likes": 890, "downloads": 54000},
            metadata={"pipeline_tag": "text-generation"},
        ),
        TrendItem(
            source="hackernews",
            item_type="discussion",
            title="Show HN: Browser-native coding agent for local repos",
            url="https://news.ycombinator.com/item?id=123456",
            description="HN discussion with 184 comments.",
            created_at=now - timedelta(hours=10),
            tags=["hacker-news"],
            metrics={"points": 612, "comments": 184},
        ),
        TrendItem(
            source="arxiv",
            item_type="paper",
            title="Efficient Long-Context Retrieval for Agentic Workflows",
            url="https://arxiv.org/abs/2604.00000",
            description="A paper proposing a retrieval method that reduces context cost while improving tool selection in multi-step agent tasks.",
            created_at=now - timedelta(days=4),
            tags=["cs.AI", "cs.CL"],
            metrics={"authors": 6},
        ),
    ]
