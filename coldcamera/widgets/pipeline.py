
from typing import Optional
import numpy as np

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
                              QFrame, QListWidgetItem, QSizePolicy, QListWidget
from PySide6.QtGui import QImage
from PySide6.QtCore import Qt, QPoint, QSize, Signal

from application.classes.register import EFFECT_REGISTRY
from application.classes.pipeline import ProcessingPipeline
from application.widgets.effect import EffectWidget
from application.widgets.effects_list import EffectsList
from application.widgets.effect_popup import EffectsPopup


class PipelineWidget(QWidget):
    """
    Widget that manages a list of image processing effects in a pipeline.
    Supports adding, removing, reordering effects, and applying them to images.

    :param parent: Optional parent QWidget.
    :signal pipeline_changed: Emitted when pipeline changes (add/remove/reorder effects).
    """

    pipeline_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pipeline = ProcessingPipeline()
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background: transparent;")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # --- Effects list ---
        self.effects_list = EffectsList()
        self.effects_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.effects_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.effects_list.setSpacing(10)
        self.effects_list.setFrameShape(QFrame.Shape.NoFrame)
        self.effects_list.model().rowsMoved.connect(self._update_positions)
        self.effects_list.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.effects_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)

        self.main_layout.addWidget(self.effects_list, 1)

        # Placeholder item for adding effects
        self._add_placeholder_item()
        self.effects_list.set_placeholder_item(self.placeholder_item)

        # --- Bottom control buttons ---
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("+")
        self.add_button.setFlat(True)
        self.remove_button = QPushButton("-")
        self.remove_button.setFlat(True)
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.remove_button)
        buttons_layout.addStretch()
        self.main_layout.addLayout(buttons_layout)

        self.add_button.clicked.connect(self._show_effect_menu_from_add)
        self.remove_button.clicked.connect(self.remove_effect)

        self._check_placeholder()

        self.effects_list.setStyleSheet("""
            QListWidget::item {
                border-radius: 5px; 
            }
            QListWidget::item:hover {
                background: #242626;
                color: #ffffff;
            }
            QListWidget::item:selected{
                background: #282929;
            }
        """)

    # ---------------- Placeholder item ----------------
    def _add_placeholder_item(self):
        """Add a placeholder QListWidgetItem with a button to add effects."""
        self.placeholder_item = QListWidgetItem()
        self.placeholder_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # no drag/drop
        btn = self._create_placeholder_button()
        self.effects_list.addItem(self.placeholder_item)
        self.effects_list.setItemWidget(self.placeholder_item, btn)
        self.placeholder_item.setSizeHint(QSize(0, 40))

    def _create_placeholder_button(self):
        """Create the add-effect button for the placeholder item."""
        btn = QPushButton("Add first effect")
        btn.setFlat(True)
        btn.setStyleSheet("""
            QPushButton {
                color: #2a2b2b;
                border: 1px dashed #2a2b2b;
                padding: 12px;
            }
        """)
        btn.clicked.connect(
            lambda *args: self._show_effect_menu(btn.mapToGlobal(QPoint(0, 0)))
        )
        return btn

    # ---------------- Context menu / effect selection ----------------
    def _show_effect_menu(self, global_pos):
        """
        Show popup menu for selecting effects at a given global position.

        :param global_pos: Global screen position for popup.
        """
        popup = EffectsPopup(EFFECT_REGISTRY, self)
        popup.effect_selected.connect(self.add_effect)
        popup.show_at(global_pos)

    def _show_effect_menu_from_add(self):
        """Show effect selection popup when clicking the add button."""
        btn_pos = self.add_button.mapToGlobal(QPoint(0, 0))
        self._show_effect_menu(btn_pos)

    # ---------------- Effect handling ----------------
    def add_effect(self, effect_name=None):
        """
        Add an effect to the pipeline by name.

        :param effect_name: Name of the effect to add.
        """
        effect_class = None
        for cat, effects in EFFECT_REGISTRY.items():
            if effect_name in effects:
                effect_class = effects[effect_name]
                break
        if effect_class is None:
            return

        effect = EffectWidget.build_from_effect_class(effect_class)
        effect.params_changed.connect(self._on_params_changed)

        item = QListWidgetItem()
        item.setSizeHint(effect.sizeHint())

        # Insert before the placeholder
        insert_row = self.effects_list.row(self.placeholder_item)
        self.effects_list.insertItem(insert_row, item)
        self.effects_list.setItemWidget(item, effect)

        effect.delete_requested.connect(lambda *args, w=effect: self._delete_effect(w))

        self.pipeline.add_effect(effect.effect)
        self._update_positions()
        self._check_placeholder()
        self.pipeline_changed.emit()

    def remove_effect(self):
        """Remove currently selected effect from the list and pipeline."""
        current_row = self.effects_list.currentRow()
        if current_row >= 0:
            item = self.effects_list.item(current_row)
            if item is self.placeholder_item:
                return
            self.effects_list.takeItem(current_row)
            widget = self.effects_list.itemWidget(item)
            if widget:
                widget.setParent(None)
                widget.deleteLater()
            self._update_positions()
            self._check_placeholder()
            self.pipeline_changed.emit()

    def _delete_effect(self, widget):
        """Remove a specific EffectWidget from the list and pipeline."""
        for i in range(self.effects_list.count()):
            item = self.effects_list.item(i)
            if item is self.placeholder_item:
                continue
            w = self.effects_list.itemWidget(item)
            if w is widget:
                self.effects_list.takeItem(i)
                w.setParent(None)
                w.deleteLater()
                break
        self._update_positions()
        self._check_placeholder()
        self.pipeline_changed.emit()

    def _update_positions(self):
        """Update the displayed positions of effects and update the pipeline order."""
        new_effects = []
        pos = 1
        for i in range(self.effects_list.count()):
            item = self.effects_list.item(i)
            if item is self.placeholder_item:
                continue
            widget = self.effects_list.itemWidget(item)
            if isinstance(widget, EffectWidget):
                widget.set_position(pos)
                pos += 1
                new_effects.append(widget.effect)
        self.pipeline.effects = new_effects
        self.pipeline_changed.emit()

    def _check_placeholder(self):
        """Update placeholder button text depending on whether effects exist."""
        has_effects = any(
            self.effects_list.item(i) is not self.placeholder_item
            for i in range(self.effects_list.count())
        )
        btn = self.effects_list.itemWidget(self.placeholder_item)
        btn.setText("+ Add effect" if has_effects else "+ Add first effect")

    # ---------------- Parameter changes ----------------
    def _on_params_changed(self):
        """Emit signal when effect parameters are changed."""
        self.pipeline_changed.emit()

    # ---------------- Image/frame processing ----------------
    def process_image(self, qimage: QImage) -> Optional[QImage]:
        """
        Apply pipeline to a QImage and return the processed image.

        :param qimage: Input QImage.
        :return: Processed QImage or None.
        """
        if qimage is None:
            return None
        if not getattr(self, "pipeline", None) or len(self.pipeline.effects) == 0:
            return qimage.copy()

        img = qimage.convertToFormat(QImage.Format.Format_RGBA8888)
        w, h = img.width(), img.height()
        ptr = img.bits()
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, w, 4)).copy()
        result = self.pipeline.apply_once(arr)
        if result.dtype != np.uint8:
            result = np.clip(result, 0, 255).astype(np.uint8)

        h, w, ch = result.shape
        if ch == 4:
            fmt = QImage.Format.Format_RGBA8888
        elif ch == 3:
            fmt = QImage.Format.Format_RGB888
        else:
            raise ValueError(f"Unsupported channel count: {ch}")
        return QImage(result.data, w, h, result.strides[0], fmt).copy()

    def process_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Apply pipeline to a single NumPy frame.

        :param frame: Input image as NumPy array.
        :return: Processed NumPy array.
        """
        if frame is None:
            return None
        if not getattr(self, "pipeline", None) or len(self.pipeline.effects) == 0:
            return frame.copy()
        result = self.pipeline.apply_once(frame)
        if result.dtype != np.uint8:
            result = np.clip(result, 0, 255).astype(np.uint8)
        return result
