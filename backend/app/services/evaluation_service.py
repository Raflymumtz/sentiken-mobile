from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)


def compute_metrics(y_true: list[str], y_pred: list[str], labels: list[str]) -> dict:
    """Menghitung seluruh metrik evaluasi dengan zero_division=0 (tidak crash bila
    suatu kelas tidak pernah diprediksi), plus daftar warning bila hal itu terjadi."""
    correct = sum(1 for a, b in zip(y_true, y_pred, strict=True) if a == b)
    accuracy = correct / len(y_true) if y_true else 0.0

    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="macro", zero_division=0
    )
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="weighted", zero_division=0
    )
    _, _, _, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average=None, zero_division=0
    )
    support_dict = {label: int(s) for label, s in zip(labels, support, strict=True)}

    matrix = confusion_matrix(y_true, y_pred, labels=labels).tolist()
    report = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)

    warnings: list[str] = []
    predicted_set = set(y_pred)
    actual_set = set(y_true)
    for label in labels:
        if label in actual_set and label not in predicted_set:
            warnings.append(f"Model tidak pernah memprediksi kelas '{label}' pada data testing ini.")

    return {
        "accuracy": float(accuracy),
        "precision_macro": float(precision_macro),
        "recall_macro": float(recall_macro),
        "f1_macro": float(f1_macro),
        "precision_weighted": float(precision_weighted),
        "recall_weighted": float(recall_weighted),
        "f1_weighted": float(f1_weighted),
        "support": support_dict,
        "confusion_matrix": {"labels": labels, "matrix": matrix},
        "classification_report": report,
        "warnings": warnings,
    }
