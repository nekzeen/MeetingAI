"""Fenêtre principale de MeetingAI."""

from PySide6.QtCore import QPoint
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMainWindow, QWidget


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application MeetingAI.

    Affiche une fenêtre vide centrée avec une barre de statut.
    Aucun widget métier n'est présent.
    """

    DEFAULT_WIDTH: int = 1200
    DEFAULT_HEIGHT: int = 800

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise la fenêtre principale.

        Args:
            parent: Widget parent éventuel.
        """
        super().__init__(parent)
        self.setWindowTitle("MeetingAI")
        self._center_on_screen()
        self.statusBar()

    def _center_on_screen(self) -> None:
        """Centre la fenêtre sur l'écran principal."""
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
            return

        available_geometry = screen.availableGeometry()
        x = available_geometry.center().x() - self.DEFAULT_WIDTH // 2
        y = available_geometry.center().y() - self.DEFAULT_HEIGHT // 2
        self.setGeometry(x, y, self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
