from __future__ import annotations

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class SentimentAnalyzer:
    def __init__(self) -> None:
        self._analyzer = SentimentIntensityAnalyzer()

    def analyze(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        analyzed: list[dict[str, object]] = []

        for row in rows:
            scores = self._analyzer.polarity_scores(str(row["text"]))
            compound = scores["compound"]
            analyzed.append(
                {
                    **row,
                    "sentiment_negative": scores["neg"],
                    "sentiment_neutral": scores["neu"],
                    "sentiment_positive": scores["pos"],
                    "sentiment_compound": compound,
                    "sentiment_label": _label_for(compound),
                }
            )

        return analyzed


def _label_for(compound: float) -> str:
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"
