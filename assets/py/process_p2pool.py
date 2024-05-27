#!/usr/bin/python3

import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

try:
        logFilename = sys.argv[1]
except:
        print("Usage: " + sys.argv[0] + " <CSV File>")
        exit(1)


class LogFileHandler(FileSystemEventHandler):
        def on_modified(self, event):
                if event.src_path == logFilename:
                        print("Log file modified")

eventHandler = LogFileHandler()
observer = Observer()
observer.schedule(event_handler=eventHandler, path="/opt/prod/p2pool", recursive=False)

try:
        observer.start()

        while True:
                time.sleep(1)

except KeyboardInterrupt:
        observer.stop()

observer.join()