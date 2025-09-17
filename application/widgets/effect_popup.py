
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt, Signal, QRect


class EffectsPopup(QFrame):
    """
    Popup window to select effects from categorized lists.

    :param categories: Dictionary mapping category names to effect name → effect class/type.
    :param parent: Optional parent widget.
    """

    effect_selected = Signal(str)

    def __init__(self, categories: dict[str, dict[str, type]], parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 4px 8px;
                border: none;
                background: transparent;
                color: #ddd;
            }
            QPushButton:hover {
                background: #404040;
                color: white;
                border-radius: 3px;
            }
            QLabel {
                font-weight: bold;
                color: #aaa;
                margin-bottom: 4px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(12)

        first_col = True
        for category, effects in categories.items():
            # Vertical layout for each category
            vbox = QVBoxLayout()
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.setSpacing(4)

            # Category header
            label = QLabel(category)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            vbox.addWidget(label)

            # Buttons for effects
            for eff_name in effects.keys():
                btn = QPushButton(eff_name)
                btn.clicked.connect(lambda checked=False, e=eff_name: self._on_select(e))
                vbox.addWidget(btn)

            vbox.addStretch()

            # Wrap in QFrame for visual separation
            column_frame = QFrame()
            column_frame.setLayout(vbox)

            # Vertical separator between columns
            if not first_col:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.VLine)
                sep.setFrameShadow(QFrame.Shadow.Sunken)
                layout.addWidget(sep)

            layout.addWidget(column_frame)
            first_col = False

    def _on_select(self, eff: str):
        """
        Handle effect selection and close the popup.

        :param eff: Selected effect name.
        """
        self.effect_selected.emit(eff)
        self.close()

    def show_at(self, global_pos):
        """
        Show the popup at a given global position, adjusting to stay on screen.

        :param global_pos: QPoint specifying the desired popup location.
        """
        self.adjustSize()
        screen_geo: QRect = QGuiApplication.primaryScreen().availableGeometry()
        popup_geo = self.frameGeometry()

        x = global_pos.x()
        y = global_pos.y()

        # Adjust vertically if exceeding bottom
        if y + popup_geo.height() > screen_geo.bottom():
            y -= popup_geo.height()  # show above

        # Adjust horizontally if exceeding right edge
        if x + popup_geo.width() > screen_geo.right():
            x = screen_geo.right() - popup_geo.width() - 5

        self.move(x, y)
        self.show()
