"""Qt task adapter for synchronous Qt-independent backend operations."""

from __future__ import annotations

import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from coldcamera.core.operations import CancellationToken, OperationCancelled, ProgressCallback
from coldcamera.logger import logger

BackendTask = Callable[[CancellationToken, ProgressCallback], Any]


class _TaskSignals(QObject):
    started = Signal(str)
    result = Signal(str, object)
    error = Signal(str, str)
    progress = Signal(str, int, int)
    cancelled = Signal(str)
    finished = Signal(str)


class _TaskWorker(QRunnable):
    def __init__(self, task_id: str, task: BackendTask, cancellation: CancellationToken):
        super().__init__()
        self.task_id = task_id
        self.task = task
        self.cancellation = cancellation
        self.signals = _TaskSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        try:
            self.cancellation.raise_if_cancelled()
            self.signals.started.emit(self.task_id)
            result = self.task(self.cancellation, lambda current, total: self.signals.progress.emit(self.task_id, current, total))
            self.cancellation.raise_if_cancelled()
            self.signals.result.emit(self.task_id, result)
        except OperationCancelled:
            self.signals.cancelled.emit(self.task_id)
        except Exception as exc:
            logger.exception(f"Background task failed: {self.task_id}")
            self.signals.error.emit(self.task_id, f"{exc}\n{traceback.format_exc()}")
        finally:
            self.signals.finished.emit(self.task_id)


class QtTaskRunner(QObject):
    """Schedules backend callables on Qt's thread pool and exposes task events."""

    started = Signal(str)
    result = Signal(str, object)
    error = Signal(str, str)
    progress = Signal(str, int, int)
    cancelled = Signal(str)
    finished = Signal(str)

    def __init__(self, parent: QObject | None = None, pool: QThreadPool | None = None):
        super().__init__(parent)
        self._pool = pool or QThreadPool(self)
        self._cancellations: dict[str, CancellationToken] = {}
        self._workers: dict[str, _TaskWorker] = {}

    def submit(self, task_id: str, task: BackendTask) -> CancellationToken:
        if task_id in self._cancellations:
            raise ValueError(f"Task id is already active: {task_id}")
        cancellation = CancellationToken()
        worker = _TaskWorker(task_id, task, cancellation)
        worker.signals.started.connect(self.started)
        worker.signals.result.connect(self.result)
        worker.signals.error.connect(self.error)
        worker.signals.progress.connect(self.progress)
        worker.signals.cancelled.connect(self.cancelled)
        worker.signals.finished.connect(self._task_finished)
        self._cancellations[task_id] = cancellation
        self._workers[task_id] = worker
        self._pool.start(worker)
        return cancellation

    def cancel(self, task_id: str) -> None:
        token = self._cancellations.get(task_id)
        if token is not None:
            token.cancel()

    def cancel_all(self) -> None:
        for cancellation in tuple(self._cancellations.values()):
            cancellation.cancel()

    def wait_for_done(self, timeout_ms: int = 1000) -> bool:
        return self._pool.waitForDone(timeout_ms)

    @Slot(str)
    def _task_finished(self, task_id: str) -> None:
        self._cancellations.pop(task_id, None)
        self._workers.pop(task_id, None)
        self.finished.emit(task_id)
