import re

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

from app.data.seed_dictionary import NEGATION_WORDS

# Istilah domain/nama aplikasi yang TIDAK di-stem agar tidak berubah bentuk
# (mis. Sastrawi bisa memotong imbuhan pada kata pendek secara tidak wajar).
# Bisa diperluas sesuai kebutuhan penelitian -- lihat docs/assumptions.md.
STEMMING_EXCEPTIONS: set[str] = {
    "pln",
    "mobile",
    "pertamina",
    "mypertamina",
    "wifi",
    "sms",
    "otp",
    "pin",
}

_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_EMAIL_RE = re.compile(r"\S+@\S+\.\S+")
_HTML_RE = re.compile(r"<[^>]+>")
_MENTION_RE = re.compile(r"@\w+")
_HASHTAG_MARKER_RE = re.compile(r"#(?=\w)")
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF"
    "\U0000FE0F"
    "]+",
    flags=re.UNICODE,
)
_STANDALONE_NUMBER_RE = re.compile(r"\b\d+\b")
_PUNCTUATION_RE = re.compile(r"[^\w\s]")
_REPEATED_CHAR_RE = re.compile(r"(.)\1{2,}")
_WHITESPACE_RE = re.compile(r"\s+")

_stemmer = StemmerFactory().create_stemmer()
_stem_cache: dict[str, str] = {}


def case_folding(text: str) -> str:
    return text.lower()


def cleaning(text: str) -> str:
    text = _URL_RE.sub(" ", text)
    text = _EMAIL_RE.sub(" ", text)
    text = _HTML_RE.sub(" ", text)
    text = _MENTION_RE.sub(" ", text)
    text = _HASHTAG_MARKER_RE.sub("", text)  # buang tanda # tapi pertahankan isi kata
    text = _EMOJI_RE.sub(" ", text)
    text = _STANDALONE_NUMBER_RE.sub(" ", text)
    text = _PUNCTUATION_RE.sub(" ", text)
    text = _REPEATED_CHAR_RE.sub(r"\1\1", text)  # "baguuuus" -> "baguus"
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def normalize_text(text: str, normalization_map: dict[str, str]) -> str:
    if not normalization_map:
        return text
    tokens = text.split()
    normalized = [normalization_map.get(tok, tok) for tok in tokens]
    return " ".join(normalized)


def tokenize(text: str) -> list[str]:
    return [tok for tok in text.split() if tok]


def remove_stopwords(tokens: list[str], stopword_set: set[str]) -> list[str]:
    return [tok for tok in tokens if tok in NEGATION_WORDS or tok not in stopword_set]


def stem_tokens(tokens: list[str]) -> list[str]:
    result = []
    for tok in tokens:
        if tok in STEMMING_EXCEPTIONS:
            result.append(tok)
            continue
        cached = _stem_cache.get(tok)
        if cached is None:
            cached = _stemmer.stem(tok)
            _stem_cache[tok] = cached
        result.append(cached)
    return result


class PreprocessingPipelineResult:
    __slots__ = (
        "case_folded_text",
        "cleaned_text",
        "normalized_text",
        "tokens",
        "tokens_no_stopword",
        "stemmed_text",
        "final_text",
    )

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def run_pipeline(
    raw_text: str, normalization_map: dict[str, str], stopword_set: set[str]
) -> PreprocessingPipelineResult:
    """Menjalankan seluruh tahapan preprocessing secara berurutan sesuai spesifikasi:
    1) case folding, 2) cleaning, 3) normalisasi, 4) tokenizing,
    5) stopword removal, 6) stemming, 7) final text."""
    case_folded = case_folding(raw_text or "")
    cleaned = cleaning(case_folded)
    normalized = normalize_text(cleaned, normalization_map)
    tokens = tokenize(normalized)
    tokens_no_stopword = remove_stopwords(tokens, stopword_set)
    stemmed_tokens = stem_tokens(tokens_no_stopword)
    stemmed_text = " ".join(stemmed_tokens)
    final_text = _WHITESPACE_RE.sub(" ", stemmed_text).strip()

    return PreprocessingPipelineResult(
        case_folded_text=case_folded,
        cleaned_text=cleaned,
        normalized_text=normalized,
        tokens=tokens,
        tokens_no_stopword=tokens_no_stopword,
        stemmed_text=stemmed_text,
        final_text=final_text,
    )
