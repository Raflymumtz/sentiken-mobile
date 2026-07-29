"""Mengisi data referensi awal: app_sources (PLN Mobile, MyPertamina) dan kamus.

Jalankan dari direktori backend/:
    python -m scripts.seed_reference_data

Skrip ini idempoten (aman dijalankan berulang kali, tidak membuat duplikat).
Tidak ada data ULASAN sintetis yang dibuat oleh skrip ini -- hanya metadata
sumber aplikasi dan kamus kata bantu preprocessing/labelisasi.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.data.seed_dictionary import (  # noqa: E402
    NEGATION_WORDS,
    NEGATIVE_WORDS,
    NORMALIZATION_PAIRS,
    POSITIVE_WORDS,
)
from app.database import SessionLocal  # noqa: E402
from app.models.app_source import AppSource  # noqa: E402
from app.models.dictionary import (  # noqa: E402
    DictionaryNegative,
    DictionaryPositive,
    NormalizationDictionary,
    Stopword,
)


def seed_app_sources(db) -> None:
    settings = get_settings()
    seeds = [
        ("PLN Mobile", settings.pln_mobile_package_id),
        ("MyPertamina", settings.mypertamina_package_id),
    ]
    for app_name, package_id in seeds:
        existing = db.query(AppSource).filter(AppSource.app_name == app_name).first()
        if existing:
            continue
        placeholder_id = package_id.strip() or f"belum.diisi.{app_name.lower().replace(' ', '')}"
        db.add(
            AppSource(
                app_name=app_name,
                package_id=placeholder_id,
                play_store_url=(f"https://play.google.com/store/apps/details?id={placeholder_id}"),
                description=f"Sumber ulasan untuk aplikasi {app_name} pada Google Play Store.",
                language="id",
                country="id",
                is_active=bool(package_id.strip()),
            )
        )
        print(f"App source ditambahkan: {app_name} (package_id={placeholder_id})")
    db.commit()


def seed_dictionaries(db) -> None:
    added = 0
    for word, weight in POSITIVE_WORDS.items():
        if not db.query(DictionaryPositive).filter(DictionaryPositive.word == word).first():
            db.add(DictionaryPositive(word=word, weight=weight))
            added += 1
    for word, weight in NEGATIVE_WORDS.items():
        if not db.query(DictionaryNegative).filter(DictionaryNegative.word == word).first():
            db.add(DictionaryNegative(word=word, weight=weight))
            added += 1
    for informal, formal in NORMALIZATION_PAIRS.items():
        if not (
            db.query(NormalizationDictionary)
            .filter(NormalizationDictionary.informal_word == informal)
            .first()
        ):
            db.add(NormalizationDictionary(informal_word=informal, formal_word=formal))
            added += 1

    stopword_factory = StopWordRemoverFactory()
    stopwords = {w for w in stopword_factory.get_stop_words() if w not in NEGATION_WORDS}
    for word in stopwords:
        if not db.query(Stopword).filter(Stopword.word == word).first():
            db.add(Stopword(word=word))
            added += 1

    db.commit()
    print(f"Kamus: {added} entri baru ditambahkan (duplikat dilewati).")


def main() -> None:
    db = SessionLocal()
    try:
        seed_app_sources(db)
        seed_dictionaries(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
