"""Tests du squelette de la fenêtre principale."""

import unittest

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QMenuBar,
    QStatusBar,
    QToolBar,
    QWidget,
)

from meetingai.gui.main_window import MainWindow


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

    def test_has_central_widget(self) -> None:
        """La fenêtre possède un widget central vide."""
        self.assertIsInstance(self.window.centralWidget(), QWidget)

    def test_has_menu_bar(self) -> None:
        """La fenêtre possède une barre de menus."""
        self.assertIsInstance(self.window.menuBar(), QMenuBar)

    def test_menu_titles(self) -> None:
        """La barre de menus contient les menus attendus."""
        actions = self.window.menuBar().actions()
        titles = [action.menu().title() for action in actions if action.menu()]
        expected = ["Fichier", "Édition", "Outils", "Affichage", "Aide"]
        self.assertEqual(titles, expected)

    def test_menus_have_no_actions(self) -> None:
        """Les menus ne contiennent aucune action."""
        for action in self.window.menuBar().actions():
            menu = action.menu()
            if menu:
                self.assertFalse(menu.actions())

    def test_has_tool_bar(self) -> None:
        """La fenêtre possède une barre d'outils vide."""
        toolbars = self.window.findChildren(QToolBar)
        self.assertEqual(len(toolbars), 1)
        self.assertFalse(toolbars[0].actions())

    def test_has_status_bar(self) -> None:
        """La fenêtre possède une barre de statut."""
        self.assertIsInstance(self.window.statusBar(), QStatusBar)


if __name__ == "__main__":
    unittest.main()
