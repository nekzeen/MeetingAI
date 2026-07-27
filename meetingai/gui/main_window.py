"""Fenêtre principale de MeetingAI."""

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QMainWindow,
    QMenu,
    QMenuBar,
    QStatusBar,
    QToolBar,
)

from meetingai.gui.workspace import Workspace


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application MeetingAI.

    Cette fenêtre constitue le squelette de l'interface graphique. Elle
    contient une barre de menus, une barre d'outils vide, une barre de statut
    et une zone centrale vide, prêtes à accueillir les futures fonctionnalités.

    Aucun widget métier, aucune action et aucun raccourci clavier ne sont
    définis ici.
    """

    DEFAULT_WIDTH: int = 1200
    DEFAULT_HEIGHT: int = 800

    _MENU_TITLES: tuple[str, ...] = (
        "Fichier",
        "Édition",
        "Outils",
        "Affichage",
        "Aide",
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise la fenêtre principale.

        Args:
            parent: Widget parent éventuel.
        """
        super().__init__(parent)
        self.setWindowTitle("MeetingAI")
        self._setup_ui()
        self._center_on_screen()

    def _setup_ui(self) -> None:
        """Construit le squelette de l'interface graphique."""
        self.setCentralWidget(Workspace(self))
        self._setup_menu_bar()
        self._setup_tool_bar()
        self.setStatusBar(QStatusBar(self))

    def _setup_menu_bar(self) -> None:
        """Ajoute une barre de menus vide."""
        menu_bar: QMenuBar = self.menuBar()
        for title in self._MENU_TITLES:
            menu_bar.addMenu(QMenu(title, self))

    def _setup_tool_bar(self) -> None:
        """Ajoute une barre d'outils vide."""
        self.addToolBar("Principal")

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
