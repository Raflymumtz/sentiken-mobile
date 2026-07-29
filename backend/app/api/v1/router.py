from fastapi import APIRouter

from app.api.v1 import (
    app_sources,
    auth,
    collection,
    dashboard,
    datasets,
    dictionaries,
    evaluation,
    export,
    imports,
    labeling,
    predictions,
    preprocessing,
    reviews,
    split,
    training,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(app_sources.router)
api_router.include_router(datasets.router)
api_router.include_router(collection.router)
api_router.include_router(imports.router)
api_router.include_router(dictionaries.router)
api_router.include_router(preprocessing.router)
api_router.include_router(reviews.router)
api_router.include_router(labeling.router)
api_router.include_router(split.router)
api_router.include_router(training.router)
api_router.include_router(evaluation.router)
api_router.include_router(predictions.router)
api_router.include_router(dashboard.router)
api_router.include_router(export.router)
