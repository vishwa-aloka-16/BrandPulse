from __future__ import annotations

import os
from typing import Any


class MySQLLoader:
    def __init__(self, table_name: str | None = None) -> None:
        self._table_name = table_name or os.getenv("MYSQL_TABLE", "brand_mentions")
        self._connection_config = {
            "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "user": _required_env("MYSQL_USER"),
            "password": _required_env("MYSQL_PASSWORD"),
        }
        self._database = _required_env("MYSQL_DATABASE")

    def upsert_mentions(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0

        columns = [
            "brand",
            "keyword",
            "source",
            "source_post_id",
            "subreddit",
            "author",
            "title",
            "body",
            "text",
            "url",
            "permalink",
            "score",
            "comment_count",
            "created_at",
            "sentiment_negative",
            "sentiment_neutral",
            "sentiment_positive",
            "sentiment_compound",
            "sentiment_label",
        ]
        placeholders = ", ".join(["%s"] * len(columns))
        column_list = ", ".join(f"`{column}`" for column in columns)
        update_list = ", ".join(
            f"`{column}` = VALUES(`{column}`)"
            for column in columns
            if column not in {"source", "source_post_id"}
        )
        values = [tuple(row.get(column) for column in columns) for row in rows]

        query = (
            f"INSERT INTO `{self._table_name}` ({column_list}) "
            f"VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE {update_list}"
        )

        self._ensure_database()
        connection = _connect_mysql(database=self._database, **self._connection_config)
        try:
            cursor = connection.cursor()
            try:
                self._ensure_table(cursor)
                cursor.executemany(query, values)
                connection.commit()
                return cursor.rowcount
            finally:
                cursor.close()
        finally:
            connection.close()

    def _ensure_database(self) -> None:
        connection = _connect_mysql(**self._connection_config)
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self._database}`")
                connection.commit()
            finally:
                cursor.close()
        finally:
            connection.close()

    def _ensure_table(self, cursor: Any) -> None:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS `{self._table_name}` (
              id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
              brand VARCHAR(255) NOT NULL,
              keyword VARCHAR(255) NOT NULL,
              source VARCHAR(50) NOT NULL,
              source_post_id VARCHAR(100) NOT NULL,
              subreddit VARCHAR(255),
              author VARCHAR(255),
              title TEXT,
              body MEDIUMTEXT,
              text MEDIUMTEXT NOT NULL,
              url TEXT,
              permalink TEXT,
              score INT,
              comment_count INT,
              created_at DATETIME,
              sentiment_negative DOUBLE,
              sentiment_neutral DOUBLE,
              sentiment_positive DOUBLE,
              sentiment_compound DOUBLE,
              sentiment_label VARCHAR(50),
              inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              UNIQUE KEY uq_brand_mentions_source_post (source, source_post_id)
            )
            """
        )


def _connect_mysql(**connection_config: Any) -> Any:
    try:
        import mysql.connector
    except ImportError as exc:
        raise RuntimeError(
            "Missing MySQL dependency. Install it with: "
            ".\\.venv\\Scripts\\pip.exe install -r requirements.txt"
        ) from exc

    return mysql.connector.connect(**connection_config)


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
