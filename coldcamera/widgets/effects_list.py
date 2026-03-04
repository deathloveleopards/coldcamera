
from PySide6.QtWidgets import QListWidget
from PySide6.QtCore import Qt


class EffectsList(QListWidget):
    """
    Custom QListWidget that prevents dropping items below a designated placeholder.

    :param parent: Optional parent QWidget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.placeholder_item = None

    def set_placeholder_item(self, item):
        """
        Set an item that acts as a drop limit (cannot drop below it).

        :param item: QListWidgetItem to act as placeholder.
        """
        self.placeholder_item = item
        if self.placeholder_item is not None:
            self.placeholder_item.setFlags(Qt.ItemFlag.NoItemFlags)

    def dropEvent(self, event):
        """
        Override drop behavior to prevent dropping below the placeholder item.

        :param event: QDropEvent instance.
        """
        if self.placeholder_item is not None:
            drop_row = self.indexAt(event.position().toPoint()).row()
            placeholder_row = self.row(self.placeholder_item)

            # Ignore drops below the placeholder
            if drop_row == -1 or drop_row >= placeholder_row:
                event.ignore()
                return

        super().dropEvent(event)
