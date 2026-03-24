"""
PostForge — Inbox Watcher
Monitors the input/inbox directory for new files and auto-triggers processing.
Uses Watchdog for filesystem events.
"""
import threading
import time
from pathlib import Path

from loguru import logger
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from watchdog.observers import Observer

from app.config import get_settings
from app.database import SessionLocal

settings = get_settings()

# Extensions that trigger auto-processing
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".txt", ".md"}


class InboxEventHandler(FileSystemEventHandler):

    def __init__(self, brand_id: str = "confluex"):
        super().__init__()
        self.brand_id = brand_id
        self._processing: set[str] = set()

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            logger.debug(f"Watcher: ignoring unsupported file {path.name}")
            return

        if str(path) in self._processing:
            return

        self._processing.add(str(path))
        logger.info(f"Watcher: new file detected → {path.name}")

        # Small delay to ensure file is fully written
        time.sleep(1.5)
        self._trigger_processing(str(path))

    def _trigger_processing(self, file_path: str) -> None:
        """Run job processing in a background thread with its own DB session."""
        def run():
            from app.services.job_manager import job_manager
            db = SessionLocal()
            try:
                job = job_manager.process_inbox_file(
                    db=db,
                    file_path=file_path,
                    brand_id=self.brand_id,
                )
                logger.info(f"Watcher: job completed id={job.id} status={job.status}")
            except Exception as e:
                logger.error(f"Watcher: job failed for {file_path}: {e}", exc_info=True)
            finally:
                db.close()
                self._processing.discard(file_path)

        thread = threading.Thread(target=run, daemon=True, name=f"watcher-job-{Path(file_path).stem}")
        thread.start()


class InboxWatcher:

    def __init__(self):
        self._observer: Observer | None = None
        self._running = False

    def start(self, brand_id: str = "confluex") -> None:
        if not settings.watcher_enabled:
            logger.info("Watcher is disabled (WATCHER_ENABLED=false)")
            return

        inbox_path = settings.abs_path(settings.input_inbox_dir)
        inbox_path.mkdir(parents=True, exist_ok=True)

        handler = InboxEventHandler(brand_id=brand_id)
        self._observer = Observer()
        self._observer.schedule(handler, str(inbox_path), recursive=False)
        self._observer.start()
        self._running = True
        logger.info(f"Watcher started: monitoring {inbox_path}")

    def stop(self) -> None:
        if self._observer and self._running:
            self._observer.stop()
            self._observer.join()
            self._running = False
            logger.info("Watcher stopped.")

    @property
    def is_running(self) -> bool:
        return self._running


inbox_watcher = InboxWatcher()
