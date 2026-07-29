import io
from datetime import UTC, datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_training_summary_pdf(context: dict) -> bytes:
    """Membuat PDF ringkasan hasil training/evaluasi sesuai field yang diwajibkan:
    nama dataset, aplikasi, periode, jumlah data, konfigurasi preprocessing, mode
    label, konfigurasi split, konfigurasi TF-IDF, konfigurasi K-NN, metrik evaluasi,
    confusion matrix, dan tanggal pembuatan."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("SENTIKEN Mobile - Ringkasan Analisis Sentimen", styles["Title"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"Tanggal pembuatan: {datetime.now(UTC):%Y-%m-%d %H:%M UTC}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    def kv_table(title: str, rows: list[tuple[str, str]]):
        story.append(Paragraph(title, styles["Heading2"]))
        table = Table([[k, str(v)] for k, v in rows], colWidths=[6 * cm, 10 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 0.4 * cm))

    kv_table(
        "Informasi Dataset",
        [
            ("Nama dataset", context["dataset_name"]),
            ("Aplikasi", context["app_name"]),
            ("Periode", context["period"]),
            ("Jumlah ulasan", context["total_reviews"]),
            ("Mode label", context["label_mode"]),
        ],
    )

    kv_table(
        "Konfigurasi Preprocessing",
        [
            (
                "Tahapan",
                "Case folding, Cleaning, Normalisasi, Tokenizing, Stopword removal, Stemming (Sastrawi)",
            ),
        ],
    )

    kv_table(
        "Konfigurasi Split Data",
        [
            ("Train size", context["split"]["train_size"]),
            ("Test size", context["split"]["test_size"]),
            ("Random state", context["split"]["random_state"]),
            ("Stratify", context["split"]["stratify"]),
            ("Jumlah data training", context["split"]["train_count"]),
            ("Jumlah data testing", context["split"]["test_count"]),
        ],
    )

    kv_table("Konfigurasi TF-IDF", [(k, v) for k, v in context["tfidf_config"].items()])
    kv_table("Konfigurasi K-Nearest Neighbor", [(k, v) for k, v in context["knn_config"].items()])

    kv_table(
        "Metrik Evaluasi",
        [
            ("Accuracy", f"{context['metrics']['accuracy']:.4f}"),
            ("Precision (weighted)", f"{context['metrics']['precision_weighted']:.4f}"),
            ("Recall (weighted)", f"{context['metrics']['recall_weighted']:.4f}"),
            ("F1-score (weighted)", f"{context['metrics']['f1_weighted']:.4f}"),
            ("Precision (macro)", f"{context['metrics']['precision_macro']:.4f}"),
            ("Recall (macro)", f"{context['metrics']['recall_macro']:.4f}"),
            ("F1-score (macro)", f"{context['metrics']['f1_macro']:.4f}"),
        ],
    )

    story.append(Paragraph("Confusion Matrix", styles["Heading2"]))
    labels = context["metrics"]["confusion_matrix"]["labels"]
    matrix = context["metrics"]["confusion_matrix"]["matrix"]
    header = ["Aktual \\ Prediksi"] + labels
    data = [header] + [[labels[i]] + [str(v) for v in row] for i, row in enumerate(matrix)]
    cm_table = Table(data)
    cm_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(cm_table)

    if context["metrics"].get("warnings"):
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("Catatan", styles["Heading2"]))
        for warning in context["metrics"]["warnings"]:
            story.append(Paragraph(f"- {warning}", styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()
