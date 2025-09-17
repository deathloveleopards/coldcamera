
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QFrame, QMenu,
    QSpinBox, QCheckBox, QComboBox, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from application.widgets.editable_label import EditableLabel


class EffectWidget(QFrame):
    """
    Widget representing a single effect with interactive controls.

    Supports sliders, spin boxes, checkboxes, dropdowns, buttons, and separators.
    Provides signals for parameter changes and effect removal.
    """

    delete_requested = Signal(QWidget)
    params_changed = Signal()

    # ------------------------
    # Initialization
    # ------------------------
    def __init__(self, effect, parent=None):
        super().__init__(parent)
        self.effect = effect
        self.effect.widget = self  # Keep reference for dynamic rebuilds

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setContentsMargins(8, 8, 8, 8)

        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Left panel: position and drag handle
        left_panel = QVBoxLayout()
        left_panel.setSpacing(5)
        left_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.position_label = QLabel("#1")
        font_num = QFont("Montserrat", 9, -1, True)
        self.position_label.setFont(font_num)
        self.position_label.setStyleSheet("color: gray;")
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.drag_label = QLabel("⋮")
        font_drag = QFont("Montserrat", 14)
        self.drag_label.setFont(font_drag)
        self.drag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drag_label.setStyleSheet("color: gray;")

        left_panel.addWidget(self.position_label)
        left_panel.addStretch()
        left_panel.addWidget(self.drag_label)
        left_panel.addStretch()

        # Right panel: effect controls
        self.right_panel = QVBoxLayout()
        self.right_panel.setSpacing(6)
        self.right_panel.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Header with effect name and enable checkbox
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(effect.layout.name)
        font = QFont("Montserrat", 10, QFont.Weight.Bold)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.enable_checkbox = QCheckBox()
        self.enable_checkbox.setChecked(True)
        self.enable_checkbox.setToolTip("Enable/disable effect")
        self.enable_checkbox.toggled.connect(self._toggle_enabled)

        header_layout.addWidget(self.label)
        header_layout.addStretch()
        header_layout.addWidget(self.enable_checkbox)

        self.right_panel.addLayout(header_layout)

        main_layout.addLayout(left_panel)
        main_layout.addLayout(self.right_panel)

        # Build initial controls
        self._build_controls()

    # ------------------------
    # Internal methods
    # ------------------------
    def _toggle_enabled(self, state):
        """Toggle effect enabled state."""
        self.effect.enabled = bool(state)
        self.params_changed.emit()

    def _build_controls(self):
        """Build controls dynamically based on effect layout."""
        layout_data = self.effect.layout.build()
        for el in layout_data["layout"]:
            el_type = el["type"]

            if el_type == "param_slider":
                self._build_slider(el)
            elif el_type == "param_spinbox":
                self._build_spinbox(el)
            elif el_type == "param_checkbox":
                self._build_checkbox(el)
            elif el_type == "param_dropdown":
                self._build_dropdown(el)
            elif el_type == "separator":
                self._build_separator()
            elif el_type == "button":
                self._build_button(el)

    # ------------------------
    # Control builders
    # ------------------------
    def _build_slider(self, el):
        row = QHBoxLayout()
        row.setSpacing(8)

        lbl = QLabel(el["label"])
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        param_type = self.effect.params[el["name"]].param_type
        scale = 100 if param_type is float else 1

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(int(el["min"] * scale), int(el["max"] * scale))
        slider.setSingleStep(int(el["step"] * scale))
        slider.setValue(int(self.effect.get_param(el["name"]) * scale))
        slider.setMinimumWidth(120)

        value_lbl = EditableLabel(self.effect.get_param(el["name"]))
        slider.valueChanged.connect(
            lambda val, n=el["name"], lbl=value_lbl, pt=param_type, sc=scale: self._update_slider(val, n, lbl, pt, sc)
        )
        value_lbl.value_edited.connect(
            lambda val, s=slider, n=el["name"], pt=param_type, sc=scale: self._manual_slider_edit(val, s, n, pt, sc))
        slider.mouseDoubleClickEvent = lambda ev, s=slider, e=el, lbl=value_lbl, sc=scale, \
                                              pt=param_type: self._slider_double_click(ev, s, e, lbl, sc, pt)

        row.addWidget(lbl)
        row.addWidget(slider, 1)
        row.addWidget(value_lbl)
        self.right_panel.addLayout(row)

    def _update_slider(self, val, name, label, param_type, scale):
        real_val = val / scale if param_type is float else int(val / scale)
        self.effect.set_param(name, real_val)
        label.setText(f"{real_val:.2f}" if param_type is float else str(real_val))
        self.params_changed.emit()

    def _manual_slider_edit(self, val, slider, name, param_type, scale):
        slider.setValue(int(val * scale))
        self.effect.set_param(name, param_type(val))
        self.params_changed.emit()

    def _slider_double_click(self, event, slider, el, label, scale, param_type):
        if event.type() == event.MouseButtonDblClick:
            default_val = el.get("default", 0)
            slider.setValue(int(default_val * scale))
            real_val = param_type(default_val)
            self.effect.set_param(el["name"], real_val)
            label.setText(f"{real_val:.2f}" if param_type is float else str(real_val))
            self.params_changed.emit()

    def _build_spinbox(self, el):
        row = QHBoxLayout()
        row.setSpacing(8)
        lbl = QLabel(el["label"])
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        spin = QSpinBox()
        spin.setRange(el["min"], el["max"])
        spin.setSingleStep(el["step"])
        spin.setValue(self.effect.get_param(el["name"]))
        spin.setMinimumWidth(80)
        spin.valueChanged.connect(lambda val, n=el["name"]: self._update_spinbox(val, n))

        row.addWidget(lbl)
        row.addWidget(spin, 1)
        self.right_panel.addLayout(row)

    def _update_spinbox(self, val, name):
        self.effect.set_param(name, val)
        self.params_changed.emit()

    def _build_checkbox(self, el):
        row = QHBoxLayout()
        row.setSpacing(8)
        checkbox = QCheckBox(el["label"])
        checkbox.setChecked(bool(self.effect.get_param(el["name"])))
        checkbox.toggled.connect(self._make_checkbox_callback(el["name"], el.get("callback"), checkbox))
        row.addWidget(checkbox)
        self.right_panel.addLayout(row)

    def _make_checkbox_callback(self, param_name, cb_name, checkbox):
        def callback(value: bool):
            checkbox.blockSignals(True)
            self.effect.set_param(param_name, value)
            if cb_name:
                try:
                    self.effect.layout.trigger(cb_name, value)
                except KeyError:
                    print(f"[WARN] Callback {cb_name} not found")
            self.params_changed.emit()
            checkbox.blockSignals(False)

        return callback

    def _build_dropdown(self, el):
        row = QHBoxLayout()
        row.setSpacing(8)
        lbl = QLabel(el["label"])
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        combo = QComboBox()
        combo.addItems(el["options"])
        current_value = el.get("value")
        if current_value in el["values"]:
            combo.setCurrentIndex(el["values"].index(current_value))
        combo.currentIndexChanged.connect(lambda idx, n=el["name"], v=el["values"]: self._update_dropdown(idx, n, v))

        row.addWidget(lbl)
        row.addWidget(combo, 1)
        self.right_panel.addLayout(row)

    def _update_dropdown(self, index, name, values):
        if 0 <= index < len(values):
            self.effect.set_param(name, values[index])
            self.params_changed.emit()

    def _build_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setLineWidth(1)
        sep.setStyleSheet("""
            QFrame {
                color: #2a2b2b;
                background-color: #2a2b2b;
                max-height: 1px;
                margin-top: 8px;
                margin-bottom: 8px;
            }
        """)
        self.right_panel.addWidget(sep)

    def _build_button(self, el):
        btn = QPushButton(el["label"])
        btn.clicked.connect(lambda checked=False, name=el.get("callback"): self._button_clicked(name))
        self.right_panel.addWidget(btn)

    def _button_clicked(self, callback_name):
        if callback_name:
            try:
                self.effect.layout.trigger(callback_name)
            except KeyError:
                print(f"[WARN] Callback {callback_name} not found")
        self.params_changed.emit()

    # ------------------------
    # Public methods
    # ------------------------
    def contextMenuEvent(self, event):
        """Context menu to delete effect."""
        menu = QMenu(self)
        delete_action = menu.addAction("Remove effect")
        action = menu.exec(event.globalPos())
        if action == delete_action:
            self.delete_requested.emit(self)

    def set_position(self, position: int):
        """Update display position label."""
        self.position_label.setText(f"#{position}")

    def rebuild_controls(self):
        """Clear existing controls (except header) and rebuild from layout."""
        for i in reversed(range(self.right_panel.count())):
            item = self.right_panel.itemAt(i)
            if item.widget() is self.label:
                continue
            widget = item.widget()
            if widget:
                self.right_panel.removeWidget(widget)
                widget.deleteLater()
            else:
                layout = item.layout()
                if layout:
                    while layout.count():
                        sub = layout.takeAt(0)
                        if sub.widget():
                            sub.widget().deleteLater()
                self.right_panel.removeItem(layout)
            self._build_controls()
            self.update()

    @classmethod
    def build_from_effect_class(cls, effect_class, *, existing_effect=None):
        """
        Construct an EffectWidget either from a class or an existing effect instance.

        :param effect_class: The effect class to instantiate if no existing instance is given.
        :param existing_effect: Optional pre-built EffectBase instance (e.g. loaded from preset).
        :return: An EffectWidget wrapping the effect.
        """
        if existing_effect is not None:
            effect = existing_effect
        else:
            effect = effect_class()
        return cls(effect)

