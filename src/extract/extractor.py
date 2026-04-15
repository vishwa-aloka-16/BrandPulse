from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urlencode

import requests


@dataclass(frozen=True)
class RedditMention:
    brand: str
    keyword: str
    source: str
    source_post_id: str
    subreddit: str
    author: str | None
    title: str
    body: str
    url: str
    permalink: str
    score: int
    comment_count: int
    created_at: datetime


class RedditExtractor:
    def __init__(self, user_agent: str | None = None) -> None:
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": user_agent
                or os.getenv("REDDIT_USER_AGENT")
                or "VlokProduction-Bot-0.1"
            }
        )

    def search_brand(
        self,
        brand: str,
        keywords: Iterable[str],
        *,
        subreddits: Iterable[str] | None = None,
        limit: int = 25,
        time_filter: str = "week",
        sort: str = "new",
    ) -> list[RedditMention]:
        mentions: list[RedditMention] = []
        seen_ids: set[str] = set()
        subreddit_names = list(subreddits or ["all"])

        for keyword in keywords:
            for subreddit_name in subreddit_names:
                for post in self._search_json(
                    subreddit_name=subreddit_name,
                    keyword=keyword,
                    sort=sort,
                    time_filter=time_filter,
                    limit=limit,
                ):
                    post_id = str(post.get("id") or "")
                    if not post_id or post_id in seen_ids:
                        continue

                    seen_ids.add(post_id)
                    created_utc = float(post.get("created_utc") or 0)
                    permalink = str(post.get("permalink") or "")
                    mentions.append(
                        RedditMention(
                            brand=brand,
                            keyword=keyword,
                            source="reddit",
                            source_post_id=post_id,
                            subreddit=str(post.get("subreddit") or subreddit_name),
                            author=post.get("author"),
                            title=str(post.get("title") or ""),
                            body=str(post.get("selftext") or ""),
                            url=str(post.get("url") or ""),
                            permalink=_absolute_reddit_url(permalink),
                            score=int(post.get("score") or 0),
                            comment_count=int(post.get("num_comments") or 0),
                            created_at=datetime.fromtimestamp(
                                created_utc,
                                tz=timezone.utc,
                            ).replace(tzinfo=None),
                        )
                    )

        return mentions

    def _search_json(
        self,
        *,
        subreddit_name: str,
        keyword: str,
        sort: str,
        time_filter: str,
        limit: int,
    ) -> list[dict[str, object]]:
        params = urlencode(
            {
                "q": keyword,
                "sort": sort,
                "t": time_filter,
                "limit": min(limit, 100),
                "restrict_sr": "on" if subreddit_name != "all" else "off",
            }
        )
        url = f"https://www.reddit.com/r/{subreddit_name}/search.json?{params}"
        response = self._session.get(url, timeout=30)
        response.raise_for_status()
        payload = response.json()
        children = payload.get("data", {}).get("children", [])
        return [child.get("data", {}) for child in children]


def _absolute_reddit_url(permalink: str) -> str:
    if permalink.startswith("http"):
        return permalink
    return f"https://www.reddit.com{permalink}"
