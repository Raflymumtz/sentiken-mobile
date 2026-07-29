"""TEST FIXTURE: pengujian pipeline preprocessing memakai kalimat uji sintetis."""

from app.services.preprocessing import (
    case_folding,
    cleaning,
    normalize_text,
    remove_stopwords,
    run_pipeline,
    stem_tokens,
    tokenize,
)


def test_case_folding_lowercases_text():
    assert case_folding("APLIKASI Bagus SEKALI") == "aplikasi bagus sekali"


def test_cleaning_removes_url_email_mention_hashtag():
    text = "cek https://contoh.com dan email saya@contoh.com @admin #plnmobile keren"
    result = cleaning(text)
    assert "http" not in result
    assert "@" not in result
    assert "#" not in result
    assert "plnmobile" in result
    assert "keren" in result


def test_cleaning_removes_html_and_numbers_and_punctuation():
    text = "<b>bagus banget</b>!!! rating 5 bintang, top!!"
    result = cleaning(text)
    assert "<" not in result and ">" not in result
    assert "!" not in result and "," not in result
    assert " 5 " not in f" {result} "


def test_cleaning_collapses_repeated_characters_and_whitespace():
    text = "bagusssss    banget   yaaaa"
    result = cleaning(text)
    assert "ssssss" not in result
    assert "  " not in result


def test_normalize_text_uses_mapping():
    mapping = {"gak": "tidak", "bgt": "banget"}
    result = normalize_text("aplikasi gak bagus bgt", mapping)
    assert result == "aplikasi tidak bagus banget"


def test_tokenize_splits_on_whitespace():
    assert tokenize("aplikasi ini bagus") == ["aplikasi", "ini", "bagus"]


def test_stopword_removal_preserves_negation_words():
    stopword_set = {"yang", "ini", "tidak", "belum", "adalah"}
    tokens = ["aplikasi", "ini", "tidak", "bagus", "belum", "sempurna"]
    result = remove_stopwords(tokens, stopword_set)
    assert "tidak" in result
    assert "belum" in result
    assert "ini" not in result


def test_stemming_reduces_affixed_words_to_base_form():
    tokens = ["mempermudah", "pembayaran", "berjalan"]
    result = stem_tokens(tokens)
    assert result == ["mudah", "bayar", "jalan"]


def test_stemming_exception_words_are_not_stemmed():
    result = stem_tokens(["pln", "mypertamina"])
    assert result == ["pln", "mypertamina"]


def test_run_pipeline_full_flow_preserves_negation_and_normalizes():
    normalization_map = {"gak": "tidak", "bgt": "banget"}
    stopword_set = {"yang", "di", "ini"}
    result = run_pipeline(
        "Aplikasi ini gak bisa dibuka, parah bgt!! https://contoh.com",
        normalization_map,
        stopword_set,
    )
    assert result.case_folded_text.startswith("aplikasi ini gak bisa dibuka")
    assert "http" not in result.cleaned_text
    assert "tidak" in result.normalized_text
    assert "tidak" in result.tokens_no_stopword
    assert "ini" not in result.tokens_no_stopword
    assert result.final_text == result.stemmed_text.strip()
    assert result.final_text != ""
