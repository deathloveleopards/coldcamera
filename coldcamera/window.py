"""
Main application window — thin UI shell.

All business logic (media loading, pipeline processing, exporting,
preset management) lives in :class:`Application`.  This module is
responsible only for:

* Building the Qt layout (menu, viewport, pipeline panel, status bar).
* Translating between NumPy arrays (the canonical processing format)
  and QImage (the display format required by the viewport).
* Showing file dialogs and forwarding user intent to :class:`Application`.
"""

from __future__ import annotations

from itertools import count
from typing import TYPE_CHECKING, Any

import numpy as np
from PySide6.QtCore import QElapsedTimer, QTimer, Qt
from PySide6.QtGui import QAction, QImage
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from coldcamera.config import APPLICATION_VERSION
from coldcamera.classes.pipeline import ProcessingPipeline
from coldcamera.core.media_sources import MediaKind
from coldcamera.core.pipeline_snapshot import PipelineSnapshot
from coldcamera.logger import logger
from coldcamera.widgets.pipeline import PipelineWidget
from coldcamera.widgets.progress_dialog import ProgressDialog
from coldcamera.widgets.viewport import ViewportWidget
from coldcamera.workers import QtTaskRunner

if TYPE_CHECKING:
    from coldcamera.application import Application


# ======================================================================
# NumPy ↔ QImage helpers  (display-boundary only)
# ======================================================================


def _numpy_to_qimage(arr: np.ndarray) -> QImage:
    """
    Convert an RGBA / RGB NumPy array to a :class:`QImage`.

    :param arr: ``(H, W, 3|4)`` uint8 array.
    :return: A **copied** QImage (safe to use after the array is freed).
    :raises ValueError: If the channel count is unsupported.
    """

    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)

    h, w = arr.shape[:2]
    ch = arr.shape[2] if arr.ndim == 3 else 1

    if ch == 4:
        fmt = QImage.Format.Format_RGBA8888
    elif ch == 3:
        fmt = QImage.Format.Format_RGB888
    else:
        raise ValueError(f"Unsupported channel count: {ch}")

    return QImage(arr.data, w, h, arr.strides[0], fmt).copy()


# ======================================================================
# MainWindow
# ======================================================================


class MainWindow(QMainWindow):
    """
    Thin Qt window for ColdCamera.

    Receives an :class:`Application` instance and delegates every
    non-UI action to it.  The **only** format conversion happening here
    is ``numpy → QImage`` when a processed frame is sent to the viewport.

    :param app: The application controller (Qt-agnostic).
    """

    def __init__(self, app: Application) -> None:
        super().__init__()
        self.app = app

        # --- Window chrome ---
        self.setWindowTitle(f"coldcamera v{APPLICATION_VERSION}")
        self.resize(1200, 800)

        self._setup_menu()
        self._setup_statusbar()
        self._setup_central_widget()

        # --- Signal wiring ---
        self.pipeline_widget.pipeline_changed.connect(self._on_pipeline_changed)
        self.viewport.frame_request.connect(self._on_frame_request)
        # frame_changed kept for legacy/compat — routes to the same handler
        self.viewport.frame_changed.connect(self._on_frame_request)

        self._tasks = QtTaskRunner(self)
        self._tasks.started.connect(self._on_task_started)
        self._tasks.result.connect(self._on_task_result)
        self._tasks.error.connect(self._on_task_error)
        self._tasks.progress.connect(self._on_task_progress)
        self._tasks.cancelled.connect(self._on_task_cancelled)
        self._tasks.finished.connect(self._on_task_finished)

        self._task_ids = count(1)
        self._task_kinds: dict[str, tuple[Any, ...]] = {}
        self._active_load_task: str | None = None
        self._active_preset_load_task: str | None = None
        self._active_preview_task: str | None = None
        self._active_preview_generation = 0
        self._rendering_task_id: str | None = None
        self._render_status_visible = False
        self._render_previous_status_message = ""
        self._render_elapsed = QElapsedTimer()
        self._render_status_timer = QTimer(self)
        self._render_status_timer.setInterval(100)
        self._render_status_timer.timeout.connect(self._update_render_status)
        self._export_task: str | None = None
        self._export_dialog: ProgressDialog | None = None
        self._current_frame_index = 0
        self._close_logged = False

    # ==================================================================
    # UI construction
    # ==================================================================

    def _setup_menu(self) -> None:
        """Build the *File* menu."""

        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        # --- Open ---
        open_image_action = QAction("Open image...", self)
        open_image_action.triggered.connect(self._open_image)
        file_menu.addAction(open_image_action)

        open_gif_action = QAction("Open GIF... (experimental)", self)
        open_gif_action.triggered.connect(self._open_gif)
        file_menu.addAction(open_gif_action)

        open_video_action = QAction("Open video... (experimental)", self)
        open_video_action.triggered.connect(self._open_video)
        file_menu.addAction(open_video_action)

        file_menu.addSeparator()

        # --- Export ---
        export_image_action = QAction("Export image...", self)
        export_image_action.triggered.connect(self._export_image)
        file_menu.addAction(export_image_action)

        export_gif_action = QAction("Export GIF... (experimental)", self)
        export_gif_action.triggered.connect(self._export_gif)
        file_menu.addAction(export_gif_action)

        export_video_action = QAction("Export video... (experimental)", self)
        export_video_action.triggered.connect(self._export_video)
        file_menu.addAction(export_video_action)

        file_menu.addSeparator()

        # --- Presets ---
        save_preset_action = QAction("Save preset...", self)
        save_preset_action.triggered.connect(self._save_preset)
        file_menu.addAction(save_preset_action)

        load_preset_action = QAction("Load preset...", self)
        load_preset_action.triggered.connect(self._load_preset)
        file_menu.addAction(load_preset_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _setup_statusbar(self) -> None:
        statusbar = QStatusBar()
        statusbar.setStyleSheet("background-color: #191a1c;")
        self.setStatusBar(statusbar)
        self.statusBar().showMessage("Application is ready to work!")

    def _setup_central_widget(self) -> None:
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(6, 6, 6, 6)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(0)

        # The editor owns a UI-side draft; workers receive only serialized snapshots.
        self.pipeline_widget = PipelineWidget(ProcessingPipeline(), self)
        pipeline_frame = QFrame()
        pipeline_frame.setFrameShape(QFrame.Shape.StyledPanel)
        pipeline_layout = QVBoxLayout(pipeline_frame)
        pipeline_layout.setContentsMargins(0, 0, 0, 0)
        pipeline_layout.addWidget(self.pipeline_widget)

        # Viewport panel
        viewport_frame = QFrame()
        viewport_frame.setFrameShape(QFrame.Shape.StyledPanel)
        viewport_layout = QVBoxLayout(viewport_frame)
        viewport_layout.setContentsMargins(0, 0, 0, 0)
        self.viewport = ViewportWidget(self)
        viewport_layout.addWidget(self.viewport)

        splitter.addWidget(pipeline_frame)
        splitter.addWidget(viewport_frame)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 5)

        container_layout.addWidget(splitter)
        self.setCentralWidget(container)

    # ==================================================================
    # Signal handlers  (pipeline / viewport → process & display)
    # ==================================================================

    def _on_pipeline_changed(self) -> None:
        """Re-process and display when any pipeline parameter changes."""
        self.app.set_pipeline(self.pipeline_widget.pipeline)
        self._process_and_display()

    def _on_frame_request(self, frame_index: int) -> None:
        """Re-process and display for the requested *frame_index*."""
        self._process_and_display(frame_index)

    # ==================================================================
    # Core display loop
    # ==================================================================

    def _process_and_display(self, frame_index: int | None = None) -> None:
        snapshot = self._capture_snapshot()
        if snapshot.media is None:
            return
        if frame_index is not None:
            self._current_frame_index = frame_index

        self._active_preview_generation += 1
        generation = self._active_preview_generation
        previous_task = self._active_preview_task
        if previous_task is not None:
            self._stop_render_status(previous_task)
            self._tasks.cancel(previous_task)

        task_id = self._new_task_id("preview")
        self._active_preview_task = task_id
        self._task_kinds[task_id] = ("preview", generation, self._current_frame_index, snapshot.media_info)
        application = self.app
        self._tasks.submit(
            task_id,
            lambda cancellation, _progress, snap=snapshot, index=self._current_frame_index, app=application: app.process_snapshot(snap, index, cancellation),
        )

    def _capture_snapshot(self):
        """Synchronize the latest editor draft before creating a task snapshot."""

        self.app.set_pipeline(self.pipeline_widget.pipeline)
        return self.app.snapshot()

    def _on_frame_processed(self, original: np.ndarray, processed: np.ndarray, frame_index: int, kind: MediaKind) -> None:
        """Convert worker output to Qt display objects on the GUI thread."""
        original_qimage = _numpy_to_qimage(original)
        processed_qimage = _numpy_to_qimage(processed)
        if kind == "image":
            self.viewport.original_qimage = original_qimage
            self.viewport.processed_qimage = processed_qimage
            self.viewport.image = original_qimage if self.viewport.showing_original else processed_qimage
            self.viewport.size_label.setText(f"{self.viewport.image.width()}x{self.viewport.image.height()}")
            self.viewport.update()
        else:
            self.viewport.original_frame_qimg = original_qimage
            self.viewport.processed_qimage = processed_qimage
            self.viewport.current_frame = frame_index
            self.viewport.update_current_frame(original_qimage if self.viewport.showing_original else processed_qimage)

    def _new_task_id(self, prefix: str) -> str:
        return f"{prefix}-{next(self._task_ids)}"

    def _on_task_started(self, task_id: str) -> None:
        """Start timing the latest preview without reporting quick renders."""
        task_context = self._task_kinds.get(task_id)
        if task_context is None or task_context[0] != "preview" or task_id != self._active_preview_task:
            return
        self._rendering_task_id = task_id
        self._render_status_visible = False
        self._render_previous_status_message = self.statusBar().currentMessage()
        self._render_elapsed.start()
        self._render_status_timer.start()

    def _update_render_status(self) -> None:
        """Show an elapsed-time heartbeat only while a preview is taking time."""
        if self._rendering_task_id != self._active_preview_task:
            self._render_status_timer.stop()
            return

        current_message = self.statusBar().currentMessage()
        if self._render_status_visible:
            if not current_message.startswith("Rendering effects..."):
                # A different user action owns the status bar now.
                self._render_status_visible = False
                self._render_status_timer.stop()
                return
        elif current_message != self._render_previous_status_message:
            # Do not replace a newer load/export/preset message.
            self._render_status_timer.stop()
            return

        elapsed_seconds = self._render_elapsed.elapsed() / 1000
        if elapsed_seconds < 0.5:
            return

        self.statusBar().showMessage(f"Rendering effects... ({elapsed_seconds:.1f}s)")
        self._render_status_visible = True

    def _stop_render_status(self, task_id: str | None = None) -> None:
        """Stop the render heartbeat and restore the prior message if it is still ours."""
        if task_id is not None and task_id != self._rendering_task_id:
            return
        self._render_status_timer.stop()
        current_message = self.statusBar().currentMessage()
        if self._render_status_visible and current_message.startswith("Rendering effects..."):
            if self._render_previous_status_message:
                self.statusBar().showMessage(self._render_previous_status_message)
            else:
                self.statusBar().clearMessage()
        self._rendering_task_id = None
        self._render_status_visible = False
        self._render_previous_status_message = ""

    def _on_task_result(self, task_id: str, result: Any) -> None:
        task_context = self._task_kinds.pop(task_id, None)
        if task_context is None:
            return
        kind = task_context[0]

        if kind == "load":
            if task_id != self._active_load_task:
                return
            media_source = result
            self._active_preview_generation += 1
            if self._active_preview_task is not None:
                self._stop_render_status(self._active_preview_task)
                self._tasks.cancel(self._active_preview_task)
            self.viewport.stop_playback()
            media_info = self.app.set_media(media_source)
            logger.info(
                f"Media opened in GUI: kind={media_info.kind}, path={media_info.path}, "
                f"frames={media_info.frame_count}, fps={media_info.fps}"
            )
            self._active_load_task = None
            self._current_frame_index = 0
            self.viewport.original_qimage = None
            self.viewport.original_frame_qimg = None
            self.viewport.processed_qimage = None
            if media_info.kind == "image":
                self._process_and_display(0)
            else:
                self.viewport.set_playback(media_info.frame_count, media_info.fps)
            self.statusBar().showMessage(f"{media_info.kind.capitalize()} opened: {media_info.path}")
        elif kind == "preview":
            _kind, generation, frame_index, media_info = task_context
            if task_id != self._active_preview_task or generation != self._active_preview_generation or media_info is None:
                return
            self._stop_render_status(task_id)
            self._active_preview_task = None
            if result is not None:
                original, processed = result
                self._on_frame_processed(original, processed, frame_index, media_info.kind)
            elif media_info.kind != "image":
                self.viewport.finish_frame_request()
        elif kind == "export-image":
            _kind, path = task_context
            self.statusBar().showMessage(f"Image exported: {path}")
        elif kind in {"export-gif", "export-video"}:
            _kind, path, media_label = task_context
            if self._export_dialog is not None:
                self._export_dialog.mark_complete()
            self.statusBar().showMessage(f"{media_label} exported: {path}")
        elif kind == "save-preset":
            self.statusBar().showMessage(f"Preset saved: {task_context[1]}")
        elif kind == "load-preset":
            if task_id != self._active_preset_load_task:
                return
            self._active_preset_load_task = None
            snapshot = result
            self.app.set_pipeline(snapshot)
            self.pipeline_widget.load_pipeline(snapshot.build_pipeline())
            logger.info(f"Preset loaded in GUI: {task_context[1]}")
            self._process_and_display()
            self.statusBar().showMessage(f"Preset loaded: {task_context[1]}")

    def _on_task_error(self, task_id: str, error_msg: str) -> None:
        task_context = self._task_kinds.pop(task_id, None)
        if task_context is None:
            return
        kind = task_context[0]
        error = error_msg.split("\n", 1)[0]
        if kind == "load":
            if task_id != self._active_load_task:
                return
            self._active_load_task = None
            _kind, path, media_kind = task_context
            logger.error(f"Media open failed in GUI: kind={media_kind}, path={path}, error={error}")
            self.statusBar().showMessage(f"Open failed: {error}")
        elif kind == "preview":
            if task_id == self._active_preview_task:
                self._stop_render_status(task_id)
                self._active_preview_task = None
                media_info = task_context[3]
                if media_info is not None and media_info.kind != "image":
                    self.viewport.finish_frame_request()
                if media_info is not None:
                    logger.error(
                        f"Preview failed: kind={media_info.kind}, frame={task_context[2] + 1}, "
                        f"path={media_info.path}, error={error}"
                    )
                self.statusBar().showMessage(f"Preview failed: {error}")
        elif kind in {"export-gif", "export-video"}:
            logger.error(f"{task_context[2]} export failed: path={task_context[1]}, error={error}")
            if self._export_dialog is not None:
                self._export_dialog.mark_error(error)
            self.statusBar().showMessage(f"Export failed: {error}")
        elif kind == "export-image":
            logger.error(f"Image export failed: path={task_context[1]}, error={error}")
            self.statusBar().showMessage(f"Export failed: {error}")
        elif kind == "save-preset":
            logger.error(f"Preset save failed: path={task_context[1]}, error={error}")
            self.statusBar().showMessage(f"Preset operation failed: {error}")
        elif kind == "load-preset":
            if task_id == self._active_preset_load_task:
                self._active_preset_load_task = None
                logger.error(f"Preset load failed: path={task_context[1]}, error={error}")
                self.statusBar().showMessage(f"Preset operation failed: {error}")
        else:
            self.statusBar().showMessage(f"Preset operation failed: {error}")

    def _on_task_progress(self, task_id: str, current: int, total: int) -> None:
        if task_id == self._export_task and self._export_dialog is not None:
            self._export_dialog.set_progress(current, total)

    def _on_task_cancelled(self, task_id: str) -> None:
        context = self._task_kinds.pop(task_id, None)
        if context and context[0] == "preview":
            self._stop_render_status(task_id)
        if context and context[0] in {"export-gif", "export-video"} and self._export_dialog is not None:
            logger.info(f"{context[2]} export cancelled: path={context[1]}")
            self._export_dialog.mark_error("Export cancelled")

    def _on_task_finished(self, task_id: str) -> None:
        if task_id == self._active_load_task:
            self._active_load_task = None
        if task_id == self._active_preset_load_task:
            self._active_preset_load_task = None
        if task_id == self._active_preview_task:
            self._active_preview_task = None
        if task_id == self._export_task:
            self._export_task = None

    # ==================================================================
    # Open actions
    # ==================================================================

    def _open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not path:
            return
        self._start_load(path, "image")

    def _open_gif(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open GIF", "", "GIF (*.gif)")
        if not path:
            return
        self._start_load(path, "gif")

    def _open_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open video", "", "Videos (*.mp4 *.avi *.mov)")
        if not path:
            return
        self._start_load(path, "video")

    def _start_load(self, path: str, kind: MediaKind) -> None:
        if self._active_load_task is not None:
            self._tasks.cancel(self._active_load_task)

        task_id = self._new_task_id("load")
        self._active_load_task = task_id
        self._task_kinds[task_id] = ("load", path, kind)
        logger.info(f"Opening media in GUI: kind={kind}, path={path}")
        self.statusBar().showMessage(f"Opening {kind}: {path}")
        application = self.app
        self._tasks.submit(task_id, lambda cancellation, _progress, app=application: app.prepare_media(path, kind))

    # ==================================================================
    # Export actions
    # ==================================================================

    def _export_image(self) -> None:
        snapshot = self._capture_snapshot()
        if snapshot.media_info is None or snapshot.media_info.kind != "image":
            self.statusBar().showMessage("No processed image to export.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save image",
            "",
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)",
        )
        if not path:
            return

        task_id = self._new_task_id("export-image")
        self._task_kinds[task_id] = ("export-image", path)
        logger.info(f"Image export started: path={path}")
        self.statusBar().showMessage("Exporting image...")
        application = self.app
        self._tasks.submit(task_id, lambda cancellation, _progress, app=application: app.export_image_from_snapshot(snapshot, path, cancellation=cancellation))

    def _export_gif(self) -> None:
        snapshot = self._capture_snapshot()
        if snapshot.media_info is None or snapshot.media_info.kind != "gif":
            self.statusBar().showMessage("No GIF to export.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save GIF", "", "GIF (*.gif)")
        if not path:
            return

        progress_dialog = ProgressDialog("Exporting GIF", self)
        task_id = self._new_task_id("export-gif")
        self._export_task = task_id
        self._export_dialog = progress_dialog
        self._task_kinds[task_id] = ("export-gif", path, "GIF")
        logger.info(f"GIF export started: path={path}")
        progress_dialog.cancelled.connect(lambda tid=task_id: self._tasks.cancel(tid))
        application = self.app
        self._tasks.submit(task_id, lambda cancellation, progress, app=application: app.export_gif_from_snapshot(snapshot, path, progress=progress, cancellation=cancellation))
        progress_dialog.exec()
        if self._export_dialog is progress_dialog:
            self._export_dialog = None

    def _export_video(self) -> None:
        snapshot = self._capture_snapshot()
        if snapshot.media_info is None or snapshot.media_info.kind != "video":
            self.statusBar().showMessage("No video to export.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save video", "", "MP4 (*.mp4);;AVI (*.avi)")
        if not path:
            return

        progress_dialog = ProgressDialog("Exporting Video", self)
        task_id = self._new_task_id("export-video")
        self._export_task = task_id
        self._export_dialog = progress_dialog
        self._task_kinds[task_id] = ("export-video", path, "Video")
        logger.info(f"Video export started: path={path}")
        progress_dialog.cancelled.connect(lambda tid=task_id: self._tasks.cancel(tid))
        application = self.app
        self._tasks.submit(task_id, lambda cancellation, progress, app=application: app.export_video_from_snapshot(snapshot, path, progress=progress, cancellation=cancellation))
        progress_dialog.exec()
        if self._export_dialog is progress_dialog:
            self._export_dialog = None

    # ==================================================================
    # Preset actions
    # ==================================================================

    def _save_preset(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save preset", "", "JSON (*.json)")
        if not path:
            return
        snapshot = PipelineSnapshot.from_pipeline(self.pipeline_widget.pipeline)
        task_id = self._new_task_id("save-preset")
        self._task_kinds[task_id] = ("save-preset", path)
        logger.info(f"Preset save started: path={path}")
        self.statusBar().showMessage("Saving preset...")
        application = self.app
        self._tasks.submit(task_id, lambda _cancellation, _progress, app=application: app.save_preset_snapshot(snapshot, path))

    def _load_preset(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load preset", "", "JSON (*.json)")
        if not path:
            return

        if self._active_preset_load_task is not None:
            self._tasks.cancel(self._active_preset_load_task)
        task_id = self._new_task_id("load-preset")
        self._active_preset_load_task = task_id
        self._task_kinds[task_id] = ("load-preset", path)
        logger.info(f"Preset load started: path={path}")
        self.statusBar().showMessage("Loading preset...")
        application = self.app
        self._tasks.submit(task_id, lambda _cancellation, _progress, app=application: app.read_preset(path))

    # ==================================================================
    # Cleanup
    # ==================================================================

    def closeEvent(self, event) -> None:
        """Cancel backend tasks before the GUI is destroyed."""
        self._stop_render_status()
        self._tasks.cancel_all()
        self._tasks.wait_for_done(2000)
        if not self._close_logged:
            logger.info("Application window closed")
            self._close_logged = True
        event.accept()
