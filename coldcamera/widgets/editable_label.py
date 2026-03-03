
from typing import Optional

from PySide6.QtWidgets import QLabel, QLineEdit, QWidget
from PySide6.QtCore import Qt, Signal, QPoint


class EditableLabel(QLabel):
    """
    Label that allows manual editing of its value on double click.

    Automatically reverts to label mode when focus is lost or Enter/Esc is pressed.

    :param value: Initial float value to display.
    :param min_val: Optional minimum allowed value.
    :param max_val: Optional maximum allowed value.
    :param precision: Number of decimal places to display.
    :param parent: Optional parent QWidget.
    """

    value_edited = Signal(float)

    def __init__(
        self,
        value: float,
        *,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        precision: int = 2,
        parent: QWidget = None,
    ):
        super().__init__(f"{value:.{precision}f}", parent)
        self._value = float(value)
        self._min = min_val
        self._max = max_val
        self._precision = precision
        self._edit: Optional[QLineEdit] = None

        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.setFixedWidth(60)

    # ------------------------
    # Event handlers
    # ------------------------
    def mouseDoubleClickEvent(self, event):
        """
        Open a QLineEdit over the label for manual editing.

        :param event: QMouseEvent instance.
        """
        if self._edit is not None:
            return  # Already editing

        parent_widget = self.parentWidget() or self.window()

        # Read current value from label text
        current_text = self.text()
        self._edit = QLineEdit(current_text, parent_widget)
        self._edit.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._edit.setFixedWidth(self.width())

        # Position QLineEdit over the label
        global_pos = self.mapToGlobal(QPoint(0, 0))
        local_pos = parent_widget.mapFromGlobal(global_pos)
        self._edit.setGeometry(local_pos.x(), local_pos.y(), self.width(), self.height())

        self.hide()
        self._edit.show()
        self._edit.setFocus()
        self._edit.selectAll()

        # Connect handlers
        self._edit.editingFinished.connect(self._finish_edit)
        self._edit.keyPressEvent = self._key_press_override
        old_focus_out = self._edit.focusOutEvent
        self._edit.focusOutEvent = lambda ev: self._finish_edit_wrapper(ev, old_focus_out)

    def _key_press_override(self, event):
        """Handle Esc to cancel editing, otherwise default key behavior."""
        if event.key() == Qt.Key.Key_Escape:
            self._cancel_edit()
        else:
            QLineEdit.keyPressEvent(self._edit, event)

    def _finish_edit_wrapper(self, event, old_focus_out):
        """Finish editing on focus out."""
        self._finish_edit()
        if old_focus_out:
            old_focus_out(event)

    # ------------------------
    # Editing methods
    # ------------------------
    def _cancel_edit(self):
        """Cancel editing and revert to label display."""
        if not self._edit:
            return
        self._edit.deleteLater()
        self._edit = None
        self.show()

    def _finish_edit(self):
        """
        Complete editing, clamp value, update label,
        and emit value_edited signal.
        """
        if not self._edit:
            return

        text = self._edit.text()
        try:
            val = float(text)
        except ValueError:
            val = self._value

        # Clamp value
        if self._min is not None and val < self._min:
            val = self._min
        if self._max is not None and val > self._max:
            val = self._max

        self._value = val
        self.setText(f"{val:.{self._precision}f}")
        self.value_edited.emit(val)

        self._edit.deleteLater()
        self._edit = None
        self.show()

    # ------------------------
    # Public methods
    # ------------------------
    def set_value(self, v: float):
        """
        Update the label with a new value.

        :param v: New float value to display.
        """
        self._value = float(v)
        self.setText(f"{self._value:.{self._precision}f}")
