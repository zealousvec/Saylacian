# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small, local-only diagnostics that never record translation text."""

from __future__ import annotations

import logging
import sys
import threading
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path


class PrivateDiagnostics:
    """Write safe startup/error metadata to a rotating user-local log."""

    def __init__(self, directory: Path, max_bytes: int = 512_000, backups: int = 2):
        self.directory = Path(directory)
        self.max_bytes = max_bytes
        self.backups = backups
        self.logger = logging.getLogger(f"saylacian.private.{id(self)}")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self.handler = None

    @property
    def path(self) -> Path:
        return self.directory / "diagnostics.log"

    def start(self, version: str = "unknown") -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        self.handler = RotatingFileHandler(
            self.path,
            maxBytes=self.max_bytes,
            backupCount=self.backups,
            encoding="utf-8",
        )
        self.handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        self.logger.addHandler(self.handler)
        self.logger.info("startup version=%s python=%s", version, sys.version_info[:3])
        return self.path

    def record_exception(self, context: str, error: BaseException) -> None:
        """Record exception type and code locations, never exception text/locals."""
        frames = (
            traceback.extract_tb(error.__traceback__) if error.__traceback__ else []
        )
        locations = ";".join(
            f"{Path(frame.filename.replace('\\', '/')).name}:{frame.lineno}:{frame.name}"
            for frame in frames
        )
        self.logger.error(
            "failure context=%s type=%s frames=%s",
            context,
            type(error).__name__,
            locations or "unavailable",
        )

    def close(self) -> None:
        if self.handler is not None:
            self.logger.removeHandler(self.handler)
            self.handler.close()
            self.handler = None


def install_exception_hooks(diagnostics: PrivateDiagnostics) -> None:
    """Capture uncaught errors without writing messages or local variables."""
    old_sys_hook = sys.excepthook

    def sys_hook(error_type, error, tb):
        diagnostics.record_exception("main", error)
        old_sys_hook(error_type, error, tb)

    sys.excepthook = sys_hook
    old_thread_hook = threading.excepthook

    def thread_hook(args):
        diagnostics.record_exception(f"thread:{args.thread.name}", args.exc_value)
        old_thread_hook(args)

    threading.excepthook = thread_hook
