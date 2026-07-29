from sklearn.feature_extraction.text import TfidfVectorizer

DEFAULT_TFIDF_CONFIG = {
    "max_features": 5000,
    "min_df": 2,
    "max_df": 0.9,
    "ngram_min": 1,
    "ngram_max": 1,
    "sublinear_tf": False,
    "norm": "l2",
}


def build_vectorizer(config: dict) -> TfidfVectorizer:
    merged = {**DEFAULT_TFIDF_CONFIG, **config}
    norm = merged["norm"]
    norm = None if norm in (None, "none") else norm
    return TfidfVectorizer(
        max_features=merged["max_features"],
        min_df=merged["min_df"],
        max_df=merged["max_df"],
        ngram_range=(int(merged["ngram_min"]), int(merged["ngram_max"])),
        sublinear_tf=bool(merged["sublinear_tf"]),
        norm=norm,
    )
