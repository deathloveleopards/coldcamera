from PySide6.QtCore import QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from coldcamera.classes.effect import EffectBase
from coldcamera.classes.pipeline import ProcessingPipeline
from coldcamera.effects.descriptors import EFFECT_DESCRIPTORS
from coldcamera.logger import logger
from coldcamera.widgets.effect import EffectWidget
from coldcamera.widgets.effect_popup import EffectsPopup
from coldcamera.widgets.effects_list import EffectsList


class PipelineWidget(QWidget):
    """
    Widget that manages the visual list of effects in a pipeline.

    This widget owns the GUI-side pipeline draft. The window serializes
    that draft into the Qt-free application API when submitting work.

    :param pipeline: Initial GUI-side :class:`ProcessingPipeline` draft.
    :param parent: Optional parent QWidget.
    :signal pipeline_changed: Emitted whenever the pipeline is modified
                              (effect added / removed / reordered / params changed).
    """

    pipeline_changed = Signal()

    def __init__(self, pipeline: ProcessingPipeline, parent: QWidget | None = None):
        super().__init__(parent)

        self.pipeline = pipeline
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background: transparent;")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # --- Debouncing timer for parameter changes ---
        self._params_change_timer = QTimer(self)
        self._params_change_timer.setSingleShot(True)
        self._params_change_timer.setInterval(50)  # 50ms debounce
        self._params_change_timer.timeout.connect(self._emit_pipeline_changed)

        # --- Effects list ---
        self.effects_list = EffectsList()
        self.effects_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.effects_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.effects_list.setSpacing(10)
        self.effects_list.setFrameShape(QFrame.Shape.NoFrame)
        self.effects_list.model().rowsMoved.connect(self._on_rows_moved)
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
        self.remove_button.clicked.connect(self.remove_selected_effect)

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

    # ================================================================
    # Placeholder item
    # ================================================================
    def _add_placeholder_item(self) -> None:
        """Add a placeholder QListWidgetItem with a button to add effects."""

        self.placeholder_item = QListWidgetItem()
        self.placeholder_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # no drag/drop
        btn = self._create_placeholder_button()
        self.effects_list.addItem(self.placeholder_item)
        self.effects_list.setItemWidget(self.placeholder_item, btn)
        self.placeholder_item.setSizeHint(QSize(0, 40))

    def _create_placeholder_button(self) -> QPushButton:
        """Create the "+ Add effect" button for the placeholder item."""

        btn = QPushButton("Add first effect")
        btn.setFlat(True)
        btn.setStyleSheet("""
            QPushButton {
                color: #2a2b2b;
                border: 1px dashed #2a2b2b;
                padding: 12px;
            }
        """)
        btn.clicked.connect(lambda *_args: self._show_effect_menu(btn.mapToGlobal(QPoint(0, 0))))
        return btn

    # ================================================================
    # Effect popup / selection
    # ================================================================
    def _show_effect_menu(self, global_pos: QPoint) -> None:
        """
        Show the categorised effect-selection popup at *global_pos*.

        :param global_pos: Global screen position for popup.
        """

        popup = EffectsPopup(EFFECT_DESCRIPTORS, self)
        popup.effect_selected.connect(self.add_effect)
        popup.show_at(global_pos)

    def _show_effect_menu_from_add(self) -> None:
        """Show the effect popup anchored to the "+" button."""

        btn_pos = self.add_button.mapToGlobal(QPoint(0, 0))
        self._show_effect_menu(btn_pos)

    # ================================================================
    # Effect handling — public API
    # ================================================================
    def add_effect(self, effect_name: str) -> None:
        """
        Add an effect to the pipeline by its display name.

        Looks up the effect class via
        :meth:`ProcessingPipeline.find_effect_class`, instantiates it,
        creates the corresponding :class:`EffectWidget`, and appends it
        to both the visual list and the underlying pipeline.

        :param effect_name: Human-readable effect name (e.g. ``"Exposure"``).
        """

        effect_class = ProcessingPipeline.find_effect_class(effect_name)
        if effect_class is None:
            return

        effect_widget = EffectWidget.build_from_effect_class(effect_class)
        self._insert_effect_widget(effect_widget)

        self.pipeline.add_effect(effect_widget.effect)
        self._sync_pipeline_order()
        self._check_placeholder()
        logger.info(f"Effect added: {effect_name}")
        self.pipeline_changed.emit()

    def add_existing_effect(self, effect: EffectBase) -> EffectWidget:
        """
        Add a pre-built :class:`EffectBase` instance and create its widget.

        Used when restoring effects from a preset.

        :param effect: An existing EffectBase instance (already in pipeline).
        :return: The created :class:`EffectWidget`.
        """

        effect_widget = EffectWidget.build_from_effect_class(
            effect.__class__,
            existing_effect=effect,
        )
        self._insert_effect_widget(effect_widget)
        return effect_widget

    def remove_selected_effect(self) -> None:
        """Remove the currently selected effect from the list and pipeline."""

        current_row = self.effects_list.currentRow()
        if current_row < 0:
            return

        item = self.effects_list.item(current_row)
        if item is self.placeholder_item:
            return

        widget = self.effects_list.itemWidget(item)
        self.effects_list.takeItem(current_row)
        if widget:
            logger.info(f"Effect removed: {widget.effect.name}")
            widget.setParent(None)
            widget.deleteLater()

        self._sync_pipeline_order()
        self._check_placeholder()
        self.pipeline_changed.emit()

    def load_pipeline(self, pipeline: ProcessingPipeline) -> None:
        """
        Replace the current pipeline reference and rebuild the entire UI.

        Called by the window after :meth:`Application.load_preset` creates
        a new :class:`ProcessingPipeline`.

        :param pipeline: The new pipeline to display.
        """

        self.pipeline = pipeline

        # Tear down existing widgets
        self.effects_list.clear()
        self._add_placeholder_item()
        self.effects_list.set_placeholder_item(self.placeholder_item)

        # Rebuild a widget for every effect already in the pipeline
        for effect in pipeline.effects:
            self.add_existing_effect(effect)

        self._sync_pipeline_order()
        self._check_placeholder()

    # ================================================================
    # Internal helpers
    # ================================================================
    def _insert_effect_widget(self, effect_widget: EffectWidget) -> None:
        """
        Insert an :class:`EffectWidget` into the list just before
        the placeholder and wire up its signals.

        :param effect_widget: Widget to insert.
        """

        effect_widget.params_changed.connect(self._on_params_changed)
        effect_widget.delete_requested.connect(
            lambda *_args, w=effect_widget: self._delete_effect(w),
        )

        item = QListWidgetItem()
        item.setSizeHint(effect_widget.sizeHint())

        insert_row = self.effects_list.row(self.placeholder_item)
        self.effects_list.insertItem(insert_row, item)
        self.effects_list.setItemWidget(item, effect_widget)

    def _delete_effect(self, widget: EffectWidget) -> None:
        """Remove a specific :class:`EffectWidget` by reference."""

        for i in range(self.effects_list.count()):
            item = self.effects_list.item(i)
            if item is self.placeholder_item:
                continue
            w = self.effects_list.itemWidget(item)
            if w is widget:
                logger.info(f"Effect removed: {widget.effect.name}")
                self.effects_list.takeItem(i)
                w.setParent(None)
                w.deleteLater()
                break

        self._sync_pipeline_order()
        self._check_placeholder()
        self.pipeline_changed.emit()

    def _on_rows_moved(self) -> None:
        """Handle drag-and-drop reorder."""

        self._sync_pipeline_order()
        logger.info(f"Effect order changed: {[effect.name for effect in self.pipeline.effects]}")
        self.pipeline_changed.emit()

    def _sync_pipeline_order(self) -> None:
        """
        Walk the widget list in visual order, refresh the ``#N``
        position labels, and synchronise :pyattr:`pipeline.effects`
        via :meth:`ProcessingPipeline.reorder_from_effects`.
        """

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

        self.pipeline.reorder_from_effects(new_effects)

    def _check_placeholder(self) -> None:
        """Update the placeholder button text based on whether effects exist."""

        has_effects = any(self.effects_list.item(i) is not self.placeholder_item for i in range(self.effects_list.count()))
        btn = self.effects_list.itemWidget(self.placeholder_item)
        if isinstance(btn, QPushButton):
            btn.setText("+ Add effect" if has_effects else "+ Add first effect")

    def _on_params_changed(self) -> None:
        """Bubble up parameter edits as a pipeline change with debouncing."""
        # Restart the debounce timer
        self._params_change_timer.start()

    def _emit_pipeline_changed(self) -> None:
        """Actually emit the pipeline_changed signal after debounce delay."""
        self.pipeline_changed.emit()
