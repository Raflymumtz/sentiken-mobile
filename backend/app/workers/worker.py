"""Entry point worker RQ. Dijalankan oleh container `worker` pada docker-compose.

    python -m app.workers.worker

Worker ini mengonsumsi antrean "sentiken-jobs" yang sama dipakai oleh
app/jobs/queue.py ketika JOB_EXECUTION_MODE=rq.
"""

import logging

from redis import Redis
from rq import Queue, Worker

from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("sentiken.worker")


def main() -> None:
    settings = get_settings()
    connection = Redis.from_url(settings.redis_url)
    queue = Queue("sentiken-jobs", connection=connection)
    logger.info("Worker SENTIKEN dimulai, mendengarkan antrean: %s", queue.name)
    worker = Worker([queue], connection=connection)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
