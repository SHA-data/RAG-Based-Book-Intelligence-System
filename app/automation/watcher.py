import logging
import time

from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS
from app.ingestion.pipeline import ingest_file

logger = logging.getLogger(__name__)

# Called by watchdog whenever something changes in the wacthed folder
class BookDropHandler(FileSystemEventHandler):

    # Ignores folder creation events
    def on_created(self, event):
        if event.is_directory:
            return
        
        path = Path(event.src_path)

        # Ignores unsupported file types
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            logger.debug('Ignore unsupported file: %s', path.name)
            return
        
        logger.info('New book detected %s. Starting ingestion...', path.name)

        book_title = path.stem # filename without extension

        result = ingest_file(path, book_title)

        if result.success:
            logger.info(
                "Auto-ingested '%s' '%d' pages, '%d' chunks ",
                book_title,
                result.pages_parsed,
                result.chunk_stored
            )
        
        else:
            logger.error(
                "Auto-ingestion failed for '%s': '%s'",
                book_title,
                result.error
            )

def start_watcher(watch_dir: Path | None = None, blocking: bool = True):

    directory = watch_dir or UPLOAD_DIR
    directory.mkdir(parents = True, exist_ok = True)

    handler = BookDropHandler()
    observer = Observer()
    observer.schedule(handler, str(directory), recursive = False)
    observer.start()

    logger.info("Wathing '%s' for new book files...", directory)

    if blocking:
        try:
            while True:
                time.sleep(1)
        
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    return observer

if __name__ == "__main__":
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    start_watcher()
