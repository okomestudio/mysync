import re
import sys
import time
from collections import namedtuple
from importlib.metadata import version
from pathlib import Path
from subprocess import DEVNULL, run
from typing import List, Optional

from watchdog.events import (
    DirCreatedEvent,
    DirModifiedEvent,
    DirMovedEvent,
    FileCreatedEvent,
    FileModifiedEvent,
    FileMovedEvent,
)

try:
    from watchdog.events import RegexMatchingEventHandler
    from watchdog.observers import Observer
except ImportError:
    raise ImportError("The watchdog Python package is not available")

Link = namedtuple("Link", ("source", "target"))
"""Two files to be synced."""


def err(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


class MyHandler(RegexMatchingEventHandler):
    """Handler for the file to watch."""

    def __init__(self, path, *args, **kwargs) -> None:
        regexes = [r"^" + re.escape(str(path.absolute())) + r"$"]
        kwargs["regexes"] = regexes
        super().__init__(*args, **kwargs)
        self.path = path

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        self.synchronize(self)

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        self.synchronize(self)

    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        if event.dest_path == str(self.path.absolute()):
            self.synchronize(self)


class Synchronizer:
    def __init__(self, observer: Observer, eh1: MyHandler, eh2: MyHandler) -> None:
        self.observer = observer
        eh1.synchronize = self.synchronize
        eh2.synchronize = self.synchronize
        self.eh1 = eh1
        self.eh2 = eh2
        self.watches = {}
        self.other = {eh1: eh2, eh2: eh1}

    def schedule_all(self) -> None:
        self.schedule(self.eh1)
        self.schedule(self.eh2)

    def schedule(self, event_handler: MyHandler) -> None:
        watch = self.observer.schedule(
            event_handler,
            path=str(event_handler.path.parent.absolute()),
            recursive=False,
        )
        self.watches[event_handler] = watch

    def unschedule(self, event_handler: MyHandler) -> None:
        self.observer.unschedule(self.watches[event_handler])
        del self.watches[event_handler]

    def synchronize(self, event_handler: Optional[MyHandler] = None) -> None:
        if event_handler:
            other = self.other[event_handler]
            self.unschedule(other)
            self._synchronize()
            self.schedule(other)
        else:
            self._synchronize()

    def _synchronize(self) -> None:
        result = run(
            [
                "unison",
                "-batch",
                "-prefer",
                "newer",
                "-copyonconflict",
                self.eh1.path.absolute(),
                self.eh2.path.absolute(),
            ]
        )
        if result.returncode == 0:
            result = run(["which", "notify-send"], stdout=DEVNULL, stderr=DEVNULL)
            if result.returncode == 0:
                run(
                    [
                        "notify-send",
                        "Synched the following files:\n"
                        f"{self.eh1.path.absolute()}\n"
                        f"{self.eh2.path.absolute()}",
                    ]
                )


<<<<<<< HEAD
def validate_file(path: Path) -> None:
    "Check if watched files are valid for sync."
=======
def _validate_file(path: Path) -> None:
>>>>>>> 4ec9d2e9a1424fb41c4b566f97a1fb3f4539f480
    if not path.exists():
        raise OSError(f"File does not exist: {path}")
    if not (path.is_file() and not path.is_symlink()):
        raise IOError(f"Not valid files to watch: {path.absolute()}")


def _prepare_link(observer: Observer, path1: Path, path2: Path) -> None:
    try:
        _validate_file(path1)
        _validate_file(path2)
    except Exception as exc:
        err("Sync will not be established for the link: " + repr(exc))
        return

    event_handler1 = MyHandler(path1)
    event_handler2 = MyHandler(path2)

    synchronizer = Synchronizer(observer, event_handler1, event_handler2)
    synchronizer.synchronize()
    synchronizer.schedule_all()


def check_requirements() -> None:
    "Check required programs are available."
    result = run(["which", "unison"], stdout=DEVNULL, stderr=DEVNULL)
    if result.returncode != 0:
        raise RuntimeError("Install the unison command")


def serve_forever(links: List[Link]) -> None:
    "Start the service."
    err(f"Starting mysync v{version('mysync')}...")

    observer = Observer()

    for link in links:
        _prepare_link(observer, link.source, link.target)

    observer.start()
    try:
        while 1:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
