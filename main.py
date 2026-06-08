import uvicorn
import argparse
import threading
import logging

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(name)s. %(message)s"
)

def main():
    parser = argparse.ArgumentParser(description = "RAG Book Knowledge Base")
    parser.add_argument(
        "--watch",
        action = "store_true",
        help = "Enable file-drop watcher (auto-ingest books dropped into uploads/)"
    )
    parser.add_argument("--host", default = '0.0.0.0')
    parser.add_argument('--port', type = int, default = 8000)
    args = parser.parse_args()

    if args.watch:
        from app.automation.watcher import start_watcher

        # Making sure the watcher thread dies when the main process dies
        watcher_thread = threading.Thread(
            target = start_watcher,
            kwargs = {'blocking': True},
            daemon = True
        )
        
        watcher_thread.start()

        print('File watcher active! Drop books into ./uploads/ to auto-ingest')

    uvicorn.run(
        "app.api.routes:app",
        host = "0.0.0.0",
        port = 8000,
        reload = False
    )

if __name__ == "__main__":
    main()