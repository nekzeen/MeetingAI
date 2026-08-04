"""Tests du squelette de la fenêtre principale."""

import unittest

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
)

from meetingai.gui.workspace import Workspace

from meetingai.gui.action_manager import ActionManager
from meetingai.gui.main_window import MainWindow
from meetingai.gui.workspace import Workspace


class TestMainWindow(unittest.TestCase):
    """Tests de la fenêtre principale MeetingAI."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        """Instancie la fenêtre principale."""
        self.window = MainWindow()

    def tearDown(self) -> None:
        """Ferme et détruit la fenêtre."""
        self.window.close()
        self.window.deleteLater()
        ActionManager._reset_instance()

    def _menu_by_title(self, title: str) -> QMenu | None:
        """Retourne le menu dont le titre correspond."""
        for action in self.window.menuBar().actions():
            menu = action.menu()
            if menu is not None and menu.title() == title:
                return menu
        return None

    def test_is_qmainwindow(self) -> None:
        """La fenêtre hérite de QMainWindow."""
        self.assertIsInstance(self.window, QMainWindow)

    def test_window_title(self) -> None:
        """La fenêtre porte le titre attendu."""
        self.assertEqual(self.window.windowTitle(), "MeetingAI")

    def test_initial_size(self) -> None:
        """La taille initiale correspond aux dimensions définies."""
        self.assertEqual(self.window.width(), 1200)
        self.assertEqual(self.window.height(), 800)

    def test_central_widget_is_workspace(self) -> None:
        """La fenêtre utilise le composant Workspace comme widget central."""
        self.assertIsInstance(self.window.centralWidget(), Workspace)

    def test_workspace_has_vertical_layout(self) -> None:
        """Le workspace dispose d'un layout vertical."""
        workspace = self.window.centralWidget()
        self.assertIsInstance(workspace.layout(), QVBoxLayout)

    def test_welcome_widget_is_initial_page(self) -> None:
        """La page d'accueil est affichée au démarrage."""
        workspace = self.window.centralWidget()
        stack = workspace.findChild(QStackedWidget)
        self.assertIsNotNone(stack)
        current = stack.widget(0)
        self.assertIsNotNone(current.findChild(QPushButton, "welcome_open_button"))

    def test_has_menu_bar(self) -> None:
        """La fenêtre possède une barre de menus."""
        self.assertIsInstance(self.window.menuBar(), QMenuBar)

    def test_menu_titles(self) -> None:
        """La barre de menus contient les menus attendus."""
        actions = self.window.menuBar().actions()
        titles = [action.menu().title() for action in actions if action.menu()]
        expected = ["Fichier", "Édition", "Outils", "Affichage", "Aide"]
        self.assertEqual(titles, expected)

    def test_file_menu_contains_expected_actions(self) -> None:
        """Le menu Fichier contient les actions attendues."""
        file_menu = self._menu_by_title("Fichier")
        self.assertIsNotNone(file_menu)
        texts = [action.text() for action in file_menu.actions()]
        self.assertIn("Nouveau", texts)
        self.assertIn("Ouvrir", texts)
        self.assertIn("Enregistrer", texts)
        self.assertIn("Exporter en TXT", texts)
        self.assertIn("Exporter en Markdown", texts)
        self.assertIn("Quitter", texts)

    def test_tools_menu_contains_expected_actions(self) -> None:
        """Le menu Outils contient les actions attendues."""
        tools_menu = self._menu_by_title("Outils")
        self.assertIsNotNone(tools_menu)
        texts = [action.text() for action in tools_menu.actions()]
        self.assertIn("Transcrire", texts)
        self.assertIn("Résumer la transcription", texts)
        self.assertIn("État du système", texts)
        self.assertIn("Préférences", texts)

    def test_help_menu_contains_about(self) -> None:
        """Le menu Aide contient l'action À propos."""
        help_menu = self._menu_by_title("Aide")
        self.assertIsNotNone(help_menu)
        texts = [action.text() for action in help_menu.actions()]
        self.assertIn("À propos", texts)

    def test_has_tool_bar(self) -> None:
        """La fenêtre possède une barre d'outils avec les actions du workflow."""
        toolbars = self.window.findChildren(QToolBar)
        self.assertEqual(len(toolbars), 1)
        texts = [action.text() for action in toolbars[0].actions()]
        self.assertIn("Ouvrir", texts)
        self.assertIn("Transcrire", texts)

    def test_status_bar_has_provider_labels(self) -> None:
        """La barre d'état affiche les fournisseurs et la progression."""
        self.assertIsInstance(self.window.statusBar(), QStatusBar)
        self.assertIsNotNone(self.window.findChild(QLabel, "runtime_status_label"))
        self.assertIsNotNone(self.window.findChild(QLabel, "stt_provider_label"))
        self.assertIsNotNone(self.window.findChild(QLabel, "ia_provider_label"))
        self.assertIsNotNone(self.window.findChild(QProgressBar, "progress_bar"))

    def test_has_status_bar(self) -> None:
        """La fenêtre possède une barre de statut."""
        self.assertIsInstance(self.window.statusBar(), QStatusBar)


if __name__ == "__main__":
    unittest.main()
