from __future__ import annotations

import html
import re

from extract.extractor import RedditMention


_WHITESPACE_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)


def clean_text(value: str) -> str:
    text = html.unescape(value or "")
    text = _URL_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def clean_mentions(mentions: list[RedditMention]) -> list[dict[str, object]]:
    cleaned: list[dict[str, object]] = []

    for mention in mentions:
        title = clean_text(mention.title)
        body = clean_text(mention.body)
        combined_text = clean_text(f"{title} {body}")

        if not combined_text:
            continue

        cleaned.append(
            {
                "brand": mention.brand,
                "keyword": mention.keyword,
                "source": mention.source,
                "source_post_id": mention.source_post_id,
                "subreddit": mention.subreddit,
                "author": mention.author,
                "title": title,
                "body": body,
                "text": combined_text,
                "url": mention.url,
                "permalink": mention.permalink,
                "score": mention.score,
                "comment_count": mention.comment_count,
                "created_at": mention.created_at,
            }
        )

    return cleaned
