"""TEST FIXTURE: pengujian unit fungsi evaluasi dengan data prediksi uji sintetis."""

from app.services.evaluation_service import compute_metrics


def test_compute_metrics_perfect_prediction():
    y_true = ["positive", "positive", "negative", "negative"]
    y_pred = ["positive", "positive", "negative", "negative"]
    metrics = compute_metrics(y_true, y_pred, ["positive", "negative"])
    assert metrics["accuracy"] == 1.0
    assert metrics["f1_weighted"] == 1.0
    assert metrics["warnings"] == []


def test_compute_metrics_no_crash_when_class_never_predicted():
    y_true = ["positive", "negative", "negative"]
    y_pred = ["negative", "negative", "negative"]  # 'positive' tidak pernah diprediksi
    metrics = compute_metrics(y_true, y_pred, ["positive", "negative"])
    assert metrics["accuracy"] == 2 / 3
    assert metrics["precision_macro"] >= 0.0  # tidak crash walau precision positive = 0/0
    assert any("positive" in w for w in metrics["warnings"])


def test_compute_metrics_single_class_dataset():
    y_true = ["positive", "positive", "positive"]
    y_pred = ["positive", "positive", "positive"]
    metrics = compute_metrics(y_true, y_pred, ["positive"])
    assert metrics["accuracy"] == 1.0
    assert metrics["confusion_matrix"]["matrix"] == [[3]]
    assert metrics["warnings"] == []
