import re
from dataclasses import dataclass


@dataclass
class LexiconScoreResult:
    positive_score: float
    negative_score: float
    sentiment_score: float
    label: str


def _count_weighted_occurrences(text: str, lexicon: dict[str, float]) -> float:
    total = 0.0
    for word, weight in lexicon.items():
        pattern = r"(?<!\w)" + re.escape(word) + r"(?!\w)"
        occurrences = len(re.findall(pattern, text))
        if occurrences:
            total += weight * occurrences
    return total


def score_text(
    final_text: str, positive_lexicon: dict[str, float], negative_lexicon: dict[str, float]
) -> LexiconScoreResult:
    """Menghitung skor sentimen berbasis kamus sesuai rumus penelitian:

    positive_score = total bobot kata positif
    negative_score = total bobot kata negatif
    sentiment_score = positive_score - abs(negative_score)

    Aturan label: skor > 0 -> positive, skor < 0 -> negative, skor = 0 -> neutral.
    """
    positive_score = _count_weighted_occurrences(final_text, positive_lexicon)
    negative_score = _count_weighted_occurrences(final_text, negative_lexicon)
    sentiment_score = positive_score - abs(negative_score)

    if sentiment_score > 0:
        label = "positive"
    elif sentiment_score < 0:
        label = "negative"
    else:
        label = "neutral"

    return LexiconScoreResult(
        positive_score=positive_score,
        negative_score=negative_score,
        sentiment_score=sentiment_score,
        label=label,
    )
