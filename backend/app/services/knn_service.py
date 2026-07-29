from sklearn.neighbors import KNeighborsClassifier

DEFAULT_KNN_CONFIG = {
    "n_neighbors": 3,
    "metric": "euclidean",
    "algorithm": "brute",
    "weights": "uniform",
    "leaf_size": 30,
}


def build_classifier(config: dict) -> KNeighborsClassifier:
    merged = {**DEFAULT_KNN_CONFIG, **config}
    return KNeighborsClassifier(
        n_neighbors=int(merged["n_neighbors"]),
        metric=merged["metric"],
        algorithm=merged["algorithm"],
        weights=merged["weights"],
        leaf_size=int(merged["leaf_size"]),
    )
