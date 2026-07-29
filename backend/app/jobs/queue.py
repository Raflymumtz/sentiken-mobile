import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from app.config import get_settings

logger = logging.getLogger("sentiken")

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="sentiken-job")


def _run_safely(func: Callable, *args, **kwargs) -> None:
    try:
        func(*args, **kwargs)
    except Exception:  # noqa: BLE001
        logger.exception("Job background gagal dijalankan: %s", getattr(func, "__name__", func))


def submit_job(func: Callable, *args, **kwargs) -> None:
    """Menjalankan job di background.

    Mode "rq": job dikirim ke antrean Redis dan dieksekusi oleh container
    worker terpisah (lihat app/workers/worker.py & docker-compose.yml).
    Mode "inline" (default dev/test, JOB_EXECUTION_MODE=inline): job
    dijalankan pada thread pool lokal, tanpa dependensi Redis -- sesuai opsi
    "implementasi background worker yang sederhana dan stabil" pada spesifikasi.
    Jika mode "rq" dipilih namun Redis tidak dapat dihubungi, job otomatis
    di-fallback ke eksekusi inline agar fitur tetap berjalan di lingkungan dev.
    """
    settings = get_settings()

    if settings.job_execution_mode == "rq":
        try:
            from redis import Redis
            from rq import Queue

            redis_conn = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
            redis_conn.ping()
            queue = Queue("sentiken-jobs", connection=redis_conn)
            queue.enqueue(func, *args, job_timeout="2h", **kwargs)
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis/RQ tidak tersedia (%s). Job dijalankan inline sebagai fallback.", exc)

    _executor.submit(_run_safely, func, *args, **kwargs)
