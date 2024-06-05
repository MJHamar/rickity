import os
import re
import time
import json
import shutil
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer

# Setup logging
logging.basicConfig(
#    filename='/Users/hamarmiklos/file_sync/file_sync.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Helper function to create hard link
def create_hard_link(src, dst):
    try:
        logging.debug(f"Creating hard link: {src} -> {dst}")
        if not os.path.exists(dst):
            os.link(src, dst)
            logging.info("Hard link created:\n%s\n->\n%s", src, dst)
    except FileExistsError:
        logging.info(f"Hard link already exists: {dst}")
    except Exception as e:
        logging.error(f"Error creating hard link: {e}")

# Ensure all files in source directory have hard links in target directory
def ensure_hard_links(source, target, include_=[], include_patterns_=[], ignore_patterns_=[]):
    for root, dirs, files in os.walk(source):
        for filename in files:
            # include if matches pattern
            src = os.path.join(root, filename)
            rel_path = os.path.relpath(src, source)
            dst = os.path.join(target, rel_path)
            include = any(re.match(pattern, rel_path) for pattern in include_)\
                if len(include_) > 0 else False
            include_patterns = any(re.match(pattern, rel_path) for pattern in include_patterns_)\
                if len(include_patterns_) > 0 else False
            ignore_patterns = any(re.match(pattern, rel_path) for pattern in ignore_patterns_)\
                if len(ignore_patterns_) > 0 else False
            # priority is include > ignore_patterns > include_patterns
            do_include = include or include_patterns or not ignore_patterns
            if do_include:
                logging.debug(
                    f"Source: {src}, Target: {dst}, DoInclude: {do_include}; Include Patterns: {include_patterns}, Ignore Patterns: {ignore_patterns}, Include: {include}")

            if do_include:
                if not os.path.exists(dst):
                    if not os.path.exists(os.path.dirname(dst)):
                        os.makedirs(os.path.dirname(dst))
                    create_hard_link(src, dst)

# Handler for file system events
class FileHandler(FileSystemEventHandler):
    def __init__(self, source, target, include=[], include_patterns=[], ignore_patterns=[]):
        self.source = source
        self.target = target
        self.include = [re.compile(pattern) for pattern in include]
        self.include_patterns = [re.compile(pattern) for pattern in include_patterns]
        self.ignore_patterns = [re.compile(pattern) for pattern in ignore_patterns]
        logging.info("Source: %s, Target: %s, Include: %s, Include Patterns: %s, Ignore Patterns: %s",
                     source, target, include, include_patterns, ignore_patterns)

    def on_created(self, event):
        if not event.is_directory:
            logging.debug(f"File created: {event.src_path}")
            source_path = event.src_path
            rel_path = os.path.relpath(source_path, self.source)
            target_path = os.path.join(self.target, rel_path)

            include = any(re.match(pattern, rel_path) for pattern in self.include)\
                if len(self.include) > 0 else False
            include_patterns = any(re.match(pattern, rel_path) for pattern in self.include_patterns)\
                if len(self.include_patterns) > 0 else False
            ignore_patterns = any(re.match(pattern, rel_path) for pattern in self.ignore_patterns)\
                if len(self.ignore_patterns) > 0 else False
            # priority is include > ignore_patterns > include_patterns
            do_include = include or include_patterns or not ignore_patterns
            logging.debug(f"Source: {source_path}, Target: {target_path}, Include: {do_include}")

            if do_include:
                if source_path.startswith(self.source):
                    if not os.path.exists(os.path.dirname(target_path)):
                        os.makedirs(os.path.dirname(target_path))
                    create_hard_link(source_path, target_path)
                elif source_path.startswith(self.target):
                    if not os.path.exists(os.path.dirname(source_path)):
                        os.makedirs(os.path.dirname(source_path))
                    shutil.move(source_path, self.source)
                    create_hard_link(os.path.join(self.source, rel_path), target_path)

    def on_deleted(self, event):
        # If a file is deleted in the source directory, delete the hard link in the target directory
        if not event.is_directory:
            logging.debug(f"File deleted: {event.src_path}")
            source_path = event.src_path
            rel_path = os.path.relpath(source_path, self.source)
            target_path = os.path.join(self.target, rel_path)

            include = any(re.match(pattern, rel_path) for pattern in self.include)\
                if len(self.include) > 0 else False
            include_patterns = any(re.match(pattern, rel_path) for pattern in self.include_patterns)\
                if len(self.include_patterns) > 0 else False
            ignore_patterns = any(re.match(pattern, rel_path) for pattern in self.ignore_patterns)\
                if len(self.ignore_patterns) > 0 else False
            # priority is include > ignore_patterns > include_patterns
            do_include = include or include_patterns or not ignore_patterns
            logging.debug(f"Source: {source_path}, Target: {target_path}, Include: {do_include}")

            if do_include:
                if source_path.startswith(self.source):
                    if os.path.exists(target_path):
                        os.remove(target_path)
                        logging.info(f"Hard link deleted: {target_path}")
                elif source_path.startswith(self.target):
                    if os.path.exists(os.path.join(self.source, rel_path)):
                        os.remove(os.path.join(self.source, rel_path))
                        logging.info(f"Hard link deleted: {os.path.join(self.source, rel_path)}")

def periodic_check(directories):
    logging.debug("Periodic check...")
    for directory_pair in directories:
        logging.info(f"Periodically checking {directory_pair['source']} and {directory_pair['target']}")
        ensure_hard_links(source=directory_pair['source'],
                          target=directory_pair['target'],
                          include_=directory_pair.get('include', []),
                          include_patterns_=directory_pair.get('include_patterns', []),
                          ignore_patterns_=directory_pair.get('ignore_patterns', []))
        logging.info("Periodic check for % and %s done.")

def main(config_file):
    logging.info("Starting file sync...")
    with open(config_file, 'r') as file:
        config = json.load(file)

    directories = config['directories']
    logging.info(f"Directories: {json.dumps(directories, indent=2)}")
    # Ensure initial hard links
    periodic_check(directories)

    event_handlers = []
    observers = []

    for directory_pair in directories:
        source = directory_pair['source']
        target = directory_pair['target']
        include = directory_pair.get('include', [])
        include_patterns = directory_pair.get('include_patterns', [])
        ignore_patterns = directory_pair.get('ignore_patterns', [])
        event_handler = FileHandler(source, target, include, include_patterns, ignore_patterns)
        observer = Observer()
        observer.schedule(event_handler, source, recursive=True)
        observer.schedule(event_handler, target, recursive=True)
        observer.start()
        event_handlers.append(event_handler)
        observers.append(observer)

    # Start periodic check
    interval = 300  # Check every 5 minutes
    periodic = Timer(interval=interval,
          function=periodic_check,
          args=[directories])
    periodic.start()

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
        periodic.cancel()

if __name__ == "__main__":
    config_file = "config.json"  # Path to your JSON configuration file
    main(config_file)
