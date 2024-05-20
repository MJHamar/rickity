import os
import time
import json
import shutil
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer

# Setup logging
logging.basicConfig(
    filename='file_sync.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Helper function to create hard link
def create_hard_link(src, dst):
    try:
        if not os.path.exists(dst):
            os.link(src, dst)
            logging.info(f"Hard link created: {src} -> {dst}")
    except FileExistsError:
        logging.info(f"Hard link already exists: {dst}")
    except Exception as e:
        logging.error(f"Error creating hard link: {e}")

# Ensure all files in source directory have hard links in target directory
def ensure_hard_links(source, target, ignore):
    for root, dirs, files in os.walk(source):
        for filename in files:
            rel_path = os.path.relpath(os.path.join(root, filename), source)
            if rel_path not in ignore:
                source_path = os.path.join(root, filename)
                target_path = os.path.join(target, rel_path)
                if not os.path.exists(os.path.dirname(target_path)):
                    os.makedirs(os.path.dirname(target_path))
                create_hard_link(source_path, target_path)

# Handler for file system events
class FileHandler(FileSystemEventHandler):
    def __init__(self, source, target, ignore):
        self.source = source
        self.target = target
        self.ignore = ignore

    def on_created(self, event):
        if not event.is_directory:
            source_path = event.src_path
            rel_path = os.path.relpath(source_path, self.source)
            target_path = os.path.join(self.target, rel_path)
            if rel_path not in self.ignore:
                if source_path.startswith(self.source):
                    if not os.path.exists(os.path.dirname(target_path)):
                        os.makedirs(os.path.dirname(target_path))
                    create_hard_link(source_path, target_path)
                elif source_path.startswith(self.target):
                    if not os.path.exists(os.path.dirname(source_path)):
                        os.makedirs(os.path.dirname(source_path))
                    shutil.move(source_path, self.source)
                    create_hard_link(os.path.join(self.source, rel_path), target_path)

def periodic_check(directories):
    for directory_pair in directories:
        logging.info(f"Periodically checking {directory_pair['source']} and {directory_pair['target']}")
        ensure_hard_links(directory_pair['source'], directory_pair['target'], directory_pair.get('ignore', []))

def main(config_file):
    logging.info("Starting file sync...")
    with open(config_file, 'r') as file:
        config = json.load(file)

    directories = config['directories']
    
    # Ensure initial hard links
    for directory_pair in directories:
        ensure_hard_links(directory_pair['source'], directory_pair['target'], directory_pair.get('ignore', []))

    event_handlers = []
    observers = []

    for directory_pair in directories:
        source = directory_pair['source']
        target = directory_pair['target']
        ignore = directory_pair.get('ignore', [])
        event_handler = FileHandler(source, target, ignore)
        observer = Observer()
        observer.schedule(event_handler, source, recursive=True)
        observer.schedule(event_handler, target, recursive=True)
        observer.start()
        event_handlers.append(event_handler)
        observers.append(observer)

    # Start periodic check
    interval = 300  # Check every 5 minutes
    Timer(interval=interval,
          function=periodic_check,
          args=[directories]).start()

    try:
        while True:
            time.sleep(1)
    # sigint or sigterm
    except (KeyboardInterrupt, SystemExit):
        logging.info("Stopping observers...")
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()

if __name__ == "__main__":
    config_file = "directories.json"  # Path to your JSON configuration file
    main(config_file)
