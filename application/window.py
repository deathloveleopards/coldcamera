
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QFrame,
    QSplitter, QStatusBar, QFileDialog, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QImage

from application.classes.video_provider import VideoFrameProvider
from application.classes.pipeline import ProcessingPipeline
from application.widgets.effect import EffectWidget
from application.widgets.viewport import ViewportWidget
from application.widgets.pipeline import PipelineWidget

from PIL import Image, ImageSequence
import numpy as np
import cv2


class MainWindow(QMainWindow):
    """
    Main application window for ColdCamera (alpha version).

    Handles opening images, GIFs, and videos, applying the processing pipeline,
    and exporting results.
    """
    def __init__(self):
        super().__init__()

        # --- Window setup ---
        self.setWindowTitle("coldcamera (version alpha)")
        self.resize(1200, 800)

        self._setup_menu()
        self._setup_statusbar()
        self._setup_central_widget()

        # Connect pipeline and viewport signals
        self.pipeline_widget.pipeline_changed.connect(self.process_and_update)
        self.viewport.frame_changed.connect(self.process_and_update)
        self.viewport.frame_request.connect(self.process_and_update)

        # --- Storage for frames and video provider ---
        self.original_frames: list[np.ndarray] | None = None
        self.frames_fps = 10
        self.original_qimg: QImage | None = None
        self.video_provider: VideoFrameProvider | None = None

    # -------------------
    # UI Setup
    # -------------------
    def _setup_menu(self):
        """Setup the File menu with actions for opening and exporting media."""
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        # --- Open actions ---
        open_image_action = QAction("Open image...", self)
        open_image_action.triggered.connect(self.open_image)
        file_menu.addAction(open_image_action)

        open_gif_action = QAction("Open GIF... (experimental)", self)
        open_gif_action.triggered.connect(self.open_gif)
        file_menu.addAction(open_gif_action)

        open_video_action = QAction("Open video... (experimental)", self)
        open_video_action.triggered.connect(self.open_video)
        file_menu.addAction(open_video_action)

        file_menu.addSeparator()

        # --- Export actions ---
        export_image_action = QAction("Export image...", self)
        export_image_action.triggered.connect(self.export_image)
        file_menu.addAction(export_image_action)

        export_gif_action = QAction("Export GIF... (experimental)", self)
        export_gif_action.triggered.connect(self.export_gif)
        file_menu.addAction(export_gif_action)

        export_video_action = QAction("Export video... (experimental)", self)
        export_video_action.triggered.connect(self.export_video)
        file_menu.addAction(export_video_action)

        file_menu.addSeparator()

        # --- Preset actions ---
        save_preset_action = QAction("Save preset...", self)
        save_preset_action.triggered.connect(self.save_preset)
        file_menu.addAction(save_preset_action)

        load_preset_action = QAction("Load preset...", self)
        load_preset_action.triggered.connect(self.load_preset)
        file_menu.addAction(load_preset_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _setup_statusbar(self):
        """Setup the status bar at the bottom of the window."""
        statusbar = QStatusBar()
        statusbar.setStyleSheet("background-color: #191a1c;")
        self.setStatusBar(statusbar)
        self.statusBar().showMessage("Application is ready to work!")

    def _setup_central_widget(self):
        """Setup the main viewport and pipeline panel."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(6, 6, 6, 6)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(0)

        self.pipeline_widget = PipelineWidget(self)
        pipeline_frame = QFrame()
        pipeline_frame.setFrameShape(QFrame.Shape.StyledPanel)
        pipeline_layout = QVBoxLayout(pipeline_frame)
        pipeline_layout.setContentsMargins(0, 0, 0, 0)
        pipeline_layout.addWidget(self.pipeline_widget)

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

    # -------------------
    # Frame Processing
    # -------------------
    def process_and_update(self, frame_index: int | None = None):
        """
        Process the current frame or image through the pipeline and update the viewport.

        :param frame_index: Optional frame index to update
        """
        if frame_index is not None:
            self.viewport.current_frame = frame_index

        # --- Single image case ---
        if self.original_qimg is not None:
            self.viewport.original_frame_qimg = self.original_qimg
            processed = self.pipeline_widget.process_image(self.original_qimg)
            self.viewport.processed_qimage = processed

            if self.viewport.showing_original:
                self.viewport.set_qimage(self.viewport.original_frame_qimg)
            else:
                self.viewport.set_qimage(processed)
            return

        # --- Video case ---
        if self.video_provider is not None and 0 <= self.viewport.current_frame < self.video_provider.frame_count:
            arr = self.video_provider.get_frame(self.viewport.current_frame)
            if arr is None:
                return

            orig_qimg = QImage(arr.data, arr.shape[1], arr.shape[0],
                               arr.strides[0], QImage.Format.Format_RGBA8888).copy()
            self.viewport.original_frame_qimg = orig_qimg

            processed = self.pipeline_widget.process_frame(arr)
            if processed.ndim == 3 and processed.shape[2] == 3:
                processed = cv2.cvtColor(processed, cv2.COLOR_RGB2RGBA)
            qimg = QImage(processed.data, processed.shape[1], processed.shape[0],
                          processed.strides[0], QImage.Format.Format_RGBA8888).copy()
            self.viewport.processed_qimage = qimg

            if self.viewport.showing_original:
                self.viewport.update_current_frame(self.viewport.original_frame_qimg)
            else:
                self.viewport.update_current_frame(qimg)
            return

        # --- GIF case ---
        if self.original_frames is not None and 0 <= self.viewport.current_frame < len(self.original_frames):
            arr = self.original_frames[self.viewport.current_frame]

            orig_qimg = QImage(arr.data, arr.shape[1], arr.shape[0],
                               arr.strides[0], QImage.Format.Format_RGBA8888).copy()
            self.viewport.original_frame_qimg = orig_qimg

            processed = self.pipeline_widget.process_frame(arr)
            if processed.ndim == 3 and processed.shape[2] == 3:
                processed = cv2.cvtColor(processed, cv2.COLOR_RGB2RGBA)
            qimg = QImage(processed.data, processed.shape[1], processed.shape[0],
                          processed.strides[0], QImage.Format.Format_RGBA8888).copy()
            self.viewport.processed_qimage = qimg

            if self.viewport.showing_original:
                self.viewport.update_current_frame(self.viewport.original_frame_qimg)
            else:
                self.viewport.update_current_frame(qimg)

    # -------------------
    # Open Media Methods
    # -------------------
    def open_image(self):
        """Open a single image file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_name:
            qimg = self.viewport._load_image(file_name)

            self.video_provider = None
            self.original_frames = None

            self.original_qimg = qimg
            self.viewport.original_qimage = qimg

            processed = self.pipeline_widget.process_image(qimg)
            self.viewport.set_qimage(processed)

            self.statusBar().showMessage(f"Image opened: {file_name}")

    def open_gif(self):
        """Open a GIF file and extract frames."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open GIF", "", "GIF (*.gif)"
        )
        if not file_name:
            return

        if self.video_provider:
            self.video_provider.release()
        self.video_provider = None

        pil_img = Image.open(file_name)
        original_frames = []
        for frame in ImageSequence.Iterator(pil_img):
            rgba = frame.convert("RGBA")
            arr = np.array(rgba)
            original_frames.append(arr)

        self.original_qimg = None
        self.original_frames = original_frames
        duration = pil_img.info.get("duration", 100)
        self.frames_fps = max(1, int(1000 / duration))

        self.viewport.set_frames(self.original_frames, self.frames_fps)
        self.statusBar().showMessage(f"GIF opened: {file_name}")

    def open_video(self):
        """Open a video file for playback via VideoFrameProvider."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open video", "", "Videos (*.mp4 *.avi *.mov)"
        )
        if not file_name:
            return

        if self.video_provider:
            self.video_provider.release()

        self.video_provider = VideoFrameProvider(file_name)
        self.frames_fps = int(self.video_provider.fps)

        self.original_qimg = None
        self.original_frames = None

        self.viewport.set_video(self.video_provider.frame_count, self.frames_fps)
        self.statusBar().showMessage(f"Video opened: {file_name}")

    # -------------------
    # Export Methods
    # -------------------
    def export_image(self):
        """Export the currently processed image."""
        if not hasattr(self.viewport, "processed_qimage") or self.viewport.processed_qimage is None:
            self.statusBar().showMessage("No processed image to export.")
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save image", "", "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)"
        )
        if file_name:
            pil_img = Image.fromqimage(self.viewport.processed_qimage)
            pil_img = pil_img.convert("RGB")
            pil_img.save(file_name)
            self.statusBar().showMessage(f"Image exported: {file_name}")

    def export_gif(self):
        """Export the currently opened GIF after processing frames."""
        if not self.original_frames:
            self.statusBar().showMessage("No GIF to export.")
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save GIF", "", "GIF (*.gif)"
        )
        if not file_name:
            return

        processed_frames = []
        for arr in self.original_frames:
            processed = self.pipeline_widget.process_frame(arr)
            if processed.shape[2] == 4:
                pil_img = Image.fromarray(processed, "RGBA")
            elif processed.shape[2] == 3:
                pil_img = Image.fromarray(processed, "RGB")
            else:
                raise ValueError(f"Unsupported channel count: {processed.shape[2]}")
            processed_frames.append(pil_img)

        processed_frames[0].save(
            file_name,
            save_all=True,
            append_images=processed_frames[1:],
            duration=int(1000 / self.frames_fps),
            loop=0,
            optimize=False,
        )
        self.statusBar().showMessage(f"GIF exported: {file_name}")

    def export_video(self):
        """Export the currently opened video after processing frames."""
        if not self.video_provider:
            self.statusBar().showMessage("No video to export.")
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save video", "", "MP4 (*.mp4);;AVI (*.avi)"
        )
        if not file_name:
            return

        cap = self.video_provider.cap
        frame_count = self.video_provider.frame_count
        fps = self.video_provider.fps

        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
        if not ret:
            return
        h, w, _ = frame.shape

        fourcc = cv2.VideoWriter_fourcc(*"XVID") if file_name.lower().endswith(".avi") \
            else cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(file_name, fourcc, fps, (w, h))

        for idx in range(frame_count):
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            processed = self.pipeline_widget.process_frame(frame_rgb)

            if processed.shape[2] == 4:
                processed_rgb = cv2.cvtColor(processed, cv2.COLOR_RGBA2RGB)
            else:
                processed_rgb = processed

            processed_bgr = cv2.cvtColor(processed_rgb, cv2.COLOR_RGB2BGR)
            out.write(processed_bgr)

        out.release()
        self.statusBar().showMessage(f"Video exported: {file_name}")

    # -------------------
    # Presets Methods
    # -------------------
    def save_preset(self):
        """
        Save the current pipeline configuration to a JSON file.

        This method opens a QFileDialog so the user can select a save path,
        then serializes the current ProcessingPipeline (all effects and
        their parameters) into a JSON file.

        :raises IOError: If writing the file fails.
        """
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save preset", "", "JSON (*.json)"
        )
        if not file_name:
            return

        try:
            self.pipeline_widget.pipeline.save_preset(file_name)
            self.statusBar().showMessage(f"Preset saved: {file_name}")
        except Exception as e:
            self.statusBar().showMessage(f"Failed to save preset: {e}")

    def load_preset(self):
        """
        Load a pipeline configuration from a JSON file.

        This method opens a QFileDialog so the user can choose a preset file,
        then deserializes it into a new ProcessingPipeline. The old pipeline
        in PipelineWidget is replaced, and the effects list in the UI is rebuilt.

        :raises ValueError: If the preset file contains unknown or invalid effects.
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load preset", "", "JSON (*.json)"
        )
        if not file_name:
            return

        try:
            pipeline = ProcessingPipeline.load_preset(file_name)
        except Exception as e:
            self.statusBar().showMessage(f"Failed to load preset: {e}")
            return

        # Replace the pipeline object in the widget
        self.pipeline_widget.pipeline = pipeline

        # Rebuild the UI list of effects
        self.pipeline_widget.effects_list.clear()
        self.pipeline_widget._add_placeholder_item()
        for eff in pipeline.effects:
            # Build widget from an existing effect instance
            w = EffectWidget.build_from_effect_class(eff.__class__, existing_effect=eff)
            item = QListWidgetItem()
            item.setSizeHint(w.sizeHint())
            self.pipeline_widget.effects_list.insertItem(
                self.pipeline_widget.effects_list.row(self.pipeline_widget.placeholder_item),
                item
            )
            self.pipeline_widget.effects_list.setItemWidget(item, w)

        self.pipeline_widget._update_positions()
        self.pipeline_widget._check_placeholder()
        self.statusBar().showMessage(f"Preset loaded: {file_name}")


if __name__ == "__main__":
    import qdarktheme

    app = QApplication(sys.argv)

    qdarktheme.setup_theme(custom_colors={
        "background": "#191a1c",
        "primary": "#ffffff",
        "border": "#2a2b2b"
    })

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
