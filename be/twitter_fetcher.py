import os
from datetime import datetime
from typing import Any

import tweepy

from db import insert_tweets


def fetch_recent_tweets(query: str, max_results: int = 100, bearer_token: str | None = None) -> dict[str, Any]:
    token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
    bearer_token = token
    if not bearer_token:
        raise RuntimeError("TWITTER_BEARER_TOKEN is not set")

    client = tweepy.Client(bearer_token=bearer_token)
    response = client.search_recent_tweets(
        query=query,
        max_results=max_results,
        tweet_fields=["created_at", "author_id"],
    )

    rows = []
    if response.data:
        for tweet in response.data:
            rows.append(
                {
                    "tweet_id": str(tweet.id),
                    "author_id": str(tweet.author_id) if tweet.author_id else None,
                    "created_at": tweet.created_at,
                    "text": tweet.text,
                    "query": query,
                    "source": "twitter",
                }
            )

    inserted = insert_tweets(rows)
    return {
        "total": len(rows),
        "inserted": inserted,
        "query": query,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
    }
