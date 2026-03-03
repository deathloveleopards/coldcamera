
from PySide6.QtWidgets import (QWidget, QSizePolicy, QLabel,
                               QVBoxLayout, QHBoxLayout, QPushButton)
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer, Signal
from PySide6.QtGui import QPainter, QImage, QWheelEvent, QMouseEvent, QPen, QColor, QPixmap

from application.utils.resource_path import resource_path

from PIL import Image
import io


class ViewportWidget(QWidget):
    """
    Widget for displaying images, GIFs, and videos with zooming and overlays.

    Signals:
        frame_changed (int): Emitted when frame index changes (GIF).
        frame_request (int): Emitted to request a video frame by index.
    """
    frame_changed = Signal(int)
    frame_request = Signal(int)

    def __init__(self, parent=None, image_path: str | None = None):
        super().__init__(parent)

        # --- Display parameters ---
        self.scale = 1.0
        self.offset = QPointF(0, 0)
        self.last_mouse_position = None
        self.min_scale = 0.1
        self.max_scale = 10.0
        self.image: QImage | None = None

        self.processed_qimage: QImage | None = None
        self.original_qimage: QImage | None = None

        # --- Overlay widgets ---
        self.size_label = QLabel(self)
        self.zoom_label = QLabel("100%", self)
        self.zoom_in_btn = QPushButton("+", self)
        self.zoom_out_btn = QPushButton("-", self)
        self.view_original_btn = QPushButton("View original", self)

        # --- Base setup ---
        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._setup_overlays()

        if image_path:
            self.set_image(image_path)

        self.view_original_btn.pressed.connect(self._show_original)
        self.view_original_btn.released.connect(self._show_processed)

        # --- Video/GIF playback ---
        self.frames: list[QImage] | None = None
        self.current_frame = 0
        self.total_frames = 0
        self.original_frame_qimg: QImage | None = None
        self.showing_original = False

        self.play_timer = QTimer(self)
        self.play_timer.timeout.connect(self._next_frame)

    # -------------------
    # Overlay and UI Setup
    # -------------------
    def _setup_overlays(self):
        """Setup zoom and overlay layouts."""
        zoom_layout = QHBoxLayout()
        zoom_layout.setContentsMargins(4, 4, 4, 4)
        zoom_layout.setSpacing(2)

        zoom_icon = QLabel()
        zoom_path = resource_path("/application/static/zoom.png")
        zoom_icon.setPixmap(QPixmap(zoom_path).scaled(13, 13,
                                                      Qt.AspectRatioMode.KeepAspectRatio,
                                                      Qt.TransformationMode.SmoothTransformation)
                            )

        zoom_layout.addWidget(self.zoom_out_btn)
        zoom_layout.addWidget(zoom_icon)
        zoom_layout.addWidget(self.zoom_label)
        self.zoom_in_btn.setFlat(True)
        self.zoom_out_btn.setFlat(True)
        zoom_layout.addWidget(self.zoom_in_btn)

        zoom_container = QWidget()
        zoom_container.setLayout(zoom_layout)

        self.view_original_btn.setStyleSheet("background-color: #191a1c;")
        zoom_container.setStyleSheet("background-color: none;")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(0)

        top_layout = QHBoxLayout()
        top_layout.addWidget(zoom_container,
                             alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        top_layout.addStretch()
        root_layout.addLayout(top_layout)
        root_layout.addStretch()

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.size_label,
                                alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.view_original_btn,
                                alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        root_layout.addLayout(bottom_layout)

        self.zoom_in_btn.clicked.connect(lambda: self._adjust_zoom(1.25))
        self.zoom_out_btn.clicked.connect(lambda: self._adjust_zoom(0.8))

    # -------------------
    # Image Loading
    # -------------------
    @staticmethod
    def _load_image(image_path: str) -> QImage:
        """
        Load image from file and convert to QImage.

        :param image_path: Path to the image file
        :return: QImage object
        """
        pil_image = Image.open(image_path).convert("RGBA")
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)
        return QImage.fromData(buffer.read())

    def set_image(self, image_path: str):
        """
        Load and display image from file.

        :param image_path: Path to the image file
        """
        self.image = self._load_image(image_path)
        self.size_label.setText(f"{self.image.width()}x{self.image.height()}")
        self.update()

    def set_qimage(self, qimage: QImage):
        """
        Set QImage directly.

        :param qimage: QImage object
        """
        self.processed_qimage = qimage
        self.image = qimage
        if qimage:
            self.size_label.setText(f"{qimage.width()}x{qimage.height()}")
        self.update()

    # -------------------
    # Video and GIF Handling
    # -------------------
    def set_frames(self, frames: list[QImage], fps: int = 10):
        """
        Set GIF frames for playback.

        :param frames: List of QImage frames
        :param fps: Frames per second
        """
        self.frames = frames
        self.current_frame = 0
        self.play_timer.start(int(1000 / fps))
        self.frame_changed.emit(self.current_frame)

    def set_video(self, total_frames: int, fps: int = 10):
        """
        Configure video playback without loading frames into memory.

        :param total_frames: Total frames in video
        :param fps: Frames per second
        """
        self.frames = None
        self.current_frame = 0
        self.total_frames = total_frames
        self.play_timer.start(int(1000 / fps))
        self.frame_changed.emit(self.current_frame)

    def update_current_frame(self, qimg: QImage):
        """
        Update the current frame for video or GIF.

        :param qimg: Current QImage frame
        """
        self.image = qimg
        self.size_label.setText(f"{qimg.width()}x{qimg.height()}")
        self.update()

    def _next_frame(self):
        """Advance to next frame for GIF or video playback."""
        if self.total_frames > 0:
            self.current_frame = (self.current_frame + 1) % self.total_frames
            self.frame_request.emit(self.current_frame)
            return

        if self.frames:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.frame_changed.emit(self.current_frame)

    # -------------------
    # Painting
    # -------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(22, 23, 26))
        if self.image:
            target_rect = QRectF(
                self.offset.x(),
                self.offset.y(),
                self.image.width() * self.scale,
                self.image.height() * self.scale
            )
            self._draw_image(painter)
            self._draw_border(painter, target_rect)
            self._draw_grid(painter, target_rect)

    def _draw_image(self, painter: QPainter):
        """Draw the main image."""
        target_rect = QRectF(
            self.offset.x(),
            self.offset.y(),
            self.image.width() * self.scale,
            self.image.height() * self.scale
        )
        source_rect = QRectF(0, 0, self.image.width(), self.image.height())
        painter.drawImage(target_rect, self.image, source_rect)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

    @staticmethod
    def _draw_border(painter: QPainter, target_rect: QRectF):
        """Draw white border around image."""
        pen = QPen(Qt.GlobalColor.white, 1)
        painter.setPen(pen)
        border_rect = QRectF(
            target_rect.left() - 1,
            target_rect.top() - 1,
            target_rect.width() + 2,
            target_rect.height() + 2
        )
        painter.drawRect(border_rect)

    def _draw_grid(self, painter: QPainter, target_rect: QRectF):
        """Draw grid overlay when zoomed in."""
        if self.scale > 7 and self.image:
            grid_color = QColor(200, 200, 200, 50)
            grid_pen = QPen(grid_color, 0.7)
            painter.setPen(grid_pen)
            painter.save()
            painter.setClipRect(target_rect)

            img_w, img_h = self.image.width(), self.image.height()
            for x in range(img_w + 1):
                x_line = self.offset.x() + x * self.scale
                if target_rect.left() <= x_line <= target_rect.right():
                    painter.drawLine(x_line, target_rect.top(), x_line, target_rect.bottom())
            for y in range(img_h + 1):
                y_line = self.offset.y() + y * self.scale
                if target_rect.top() <= y_line <= target_rect.bottom():
                    painter.drawLine(target_rect.left(), y_line, target_rect.right(), y_line)

            painter.restore()

    # -------------------
    # Zoom and Mouse
    # -------------------
    def _adjust_zoom(self, factor: float, center: QPointF | None = None):
        """
        Adjust zoom level and optionally center on a point.

        :param factor: Zoom multiplier
        :param center: Center point for zooming
        """
        new_scale = max(self.min_scale, min(self.max_scale, self.scale * factor))

        if center and self.image:
            old_img_x = (center.x() - self.offset.x()) / self.scale
            old_img_y = (center.y() - self.offset.y()) / self.scale
            self.offset = QPointF(
                center.x() - old_img_x * new_scale,
                center.y() - old_img_y * new_scale
            )

        self.scale = new_scale
        self.zoom_label.setText(f"{int(self.scale * 100)}%")
        self.update()

    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self._adjust_zoom(zoom_factor, event.position())

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_mouse_position = event.position()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton and self.last_mouse_position:
            delta = event.position() - self.last_mouse_position
            self.offset = QPointF(
                self.offset.x() + delta.x() if self.scale < 7 else round(self.offset.x() + delta.x()),
                self.offset.y() + delta.y() if self.scale < 7 else round(self.offset.y() + delta.y())
            )
            self.last_mouse_position = event.position()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_mouse_position = None

    # -------------------
    # Original Image Toggle
    # -------------------
    def _show_original(self):
        """Display the original unprocessed image."""
        if self.original_qimage:
            self.image = self.original_qimage
            self.showing_original = True
            self.update()
        elif self.original_frame_qimg:
            self.image = self.original_frame_qimg
            self.showing_original = True
            self.update()

    def _show_processed(self):
        """Display the processed image."""
        if self.processed_qimage:
            self.image = self.processed_qimage
            self.showing_original = False
            self.update()
