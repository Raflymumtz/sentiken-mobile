"""Ekspor dataset ulasan (PLN Mobile & MyPertamina) ke satu file Excel,
masing-masing aplikasi jadi sheet terpisah. Berisi data ulasan asli hasil
scraping beserta label sentimen yang sudah dihitung dari kamus (bukan data
buatan/sintetis -- lihat CLAUDE.md).

Jalankan dari direktori backend/:
    python -m scripts.export_dataset_excel [output_path]
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.app_source import AppSource  # noqa: E402
from app.models.dataset import Dataset  # noqa: E402
from app.models.review import Review  # noqa: E402

LABEL_TEXT = {"positive": "Positif", "negative": "Negatif", "neutral": "Netral"}


def export_dataset_to_dataframe(db, dataset: Dataset) -> pd.DataFrame:
    reviews = (
        db.query(Review)
        .filter(Review.dataset_id == dataset.id)
        .order_by(Review.review_date.desc().nullslast())
        .all()
    )

    rows = []
    for review in reviews:
        label = next(
            (sl for sl in review.sentiment_labels if sl.label_mode == dataset.label_mode),
            None,
        )
        rows.append(
            {
                "review_id": review.review_id or str(review.id),
                "username": review.username,
                "rating": review.score,
                "tanggal_ulasan": review.review_date,
                "versi_aplikasi": review.app_version,
                "isi_ulasan": review.content,
                "balasan_pengembang": review.reply_content,
                "label_sentimen": LABEL_TEXT.get(label.label, "") if label else "",
                "skor_positif": label.positive_score if label else None,
                "skor_negatif": label.negative_score if label else None,
                "skor_sentimen": label.sentiment_score if label else None,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dataset_export.xlsx")

    db = SessionLocal()
    try:
        sources = db.query(AppSource).filter(AppSource.deleted_at.is_(None)).all()
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for source in sources:
                dataset = (
                    db.query(Dataset)
                    .filter(Dataset.app_source_id == source.id, Dataset.deleted_at.is_(None))
                    .first()
                )
                if dataset is None:
                    continue
                df = export_dataset_to_dataframe(db, dataset)
                sheet_name = source.app_name[:31]  # batas panjang nama sheet Excel
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"{source.app_name}: {len(df)} ulasan ditulis ke sheet '{sheet_name}'.")
        print(f"Selesai: {output_path.resolve()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
