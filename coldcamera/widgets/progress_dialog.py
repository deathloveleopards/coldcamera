"""
Progress dialog for long-running export operations.

Displays a modal progress bar with cancel functionality for
GIF and video export operations.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)


class ProgressDialog(QDialog):
    """
    Modal dialog for showing export progress.

    Displays a progress bar, status message, and cancel button.
    Can be connected to worker signals for automatic updates.

    Signals:
        cancelled: Emitted when user clicks the cancel button.
    """

    cancelled = Signal()

    def __init__(self, title: str = "Exporting", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._setup_ui()
        self._is_cancelled = False

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Status label
        self.status_label = QLabel("Preparing export...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def set_progress(self, current: int, total: int) -> None:
        """
        Update the progress bar.

        :param current: Current frame/item number.
        :param total: Total number of frames/items.
        """
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.status_label.setText(f"Processing frame {current} of {total}...")

    def set_status(self, message: str) -> None:
        """
        Set the status message.

        :param message: Status message to display.
        """
        self.status_label.setText(message)

    def set_indeterminate(self) -> None:
        """Set the progress bar to indeterminate mode."""
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        if not self._is_cancelled:
            self._is_cancelled = True
            self.cancel_button.setEnabled(False)
            self.set_status("Cancelling...")
            self.cancelled.emit()

    def mark_complete(self) -> None:
        """Mark the operation as complete."""
        self.progress_bar.setValue(100)
        self.set_status("Export complete!")
        self.cancel_button.setText("Close")
        self.cancel_button.setEnabled(True)
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.accept)

    def mark_error(self, error_message: str) -> None:
        """
        Mark the operation as failed.

        :param error_message: Error message to display.
        """
        self.set_status(f"Error: {error_message}")
        self.cancel_button.setText("Close")
        self.cancel_button.setEnabled(True)
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.reject)

    def is_cancelled(self) -> bool:
        """
        Check if the operation was cancelled.

        :return: True if cancelled, False otherwise.
        """
        return self._is_cancelled
