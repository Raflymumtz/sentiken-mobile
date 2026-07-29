from collections import Counter
from dataclasses import dataclass

from sklearn.model_selection import train_test_split


class SplitValidationError(Exception):
    """Dilempar bila konfigurasi split tidak dapat dipenuhi (mis. kelas terlalu sedikit)."""


@dataclass
class EligibleItem:
    review_id: str
    label: str
    text: str


@dataclass
class SplitResult:
    train_ids: list[str]
    test_ids: list[str]
    class_distribution: dict[str, int]


def validate_and_split(
    items: list[EligibleItem],
    *,
    train_size: float,
    test_size: float,
    random_state: int,
    stratify: bool,
) -> SplitResult:
    if len(items) < 2:
        raise SplitValidationError(
            f"Data terlalu sedikit untuk displit (hanya {len(items)} data tersedia, minimal 2)."
        )

    class_distribution = dict(Counter(item.label for item in items))

    if stratify:
        n_classes = len(class_distribution)
        min_class_count = min(class_distribution.values()) if class_distribution else 0
        if min_class_count < 2:
            worst_class = min(class_distribution, key=class_distribution.get)
            raise SplitValidationError(
                "Stratified split tidak dapat dijalankan: kelas "
                f"'{worst_class}' hanya memiliki {min_class_count} data (minimal 2 diperlukan "
                "agar tiap kelas terwakili di data training maupun testing)."
            )
        expected_test_count = round(len(items) * test_size)
        if expected_test_count < n_classes:
            raise SplitValidationError(
                "Stratified split tidak dapat dijalankan: ukuran data testing "
                f"({expected_test_count}) lebih kecil dari jumlah kelas ({n_classes})."
            )

    labels = [item.label for item in items]
    ids = [item.review_id for item in items]

    train_ids, test_ids = train_test_split(
        ids,
        train_size=train_size,
        test_size=test_size,
        random_state=random_state,
        stratify=labels if stratify else None,
    )

    return SplitResult(train_ids=train_ids, test_ids=test_ids, class_distribution=class_distribution)
