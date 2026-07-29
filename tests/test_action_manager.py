"""Tests du gestionnaire centralisé des actions."""

import unittest

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication

from meetingai.gui.action_manager import ActionManager


class TestActionManager(unittest.TestCase):
    """Tests de l'unicité et de la création des QAction."""

    def setUp(self) -> None:
        """Réinitialise le singleton avant chaque test."""
        ActionManager._reset_instance()
        self.app = QApplication.instance() or QApplication([])

    def tearDown(self) -> None:
        """Réinitialise le singleton après chaque test."""
        ActionManager._reset_instance()

    def test_singleton_returns_same_instance(self) -> None:
        """ActionManager garantit une unique instance."""
        first = ActionManager()
        second = ActionManager()
        self.assertIs(first, second)

    def test_new_action_exists(self) -> None:
        """L'action 'Nouveau' est créée."""
        manager = ActionManager()
        self.assertIsInstance(manager.new_action, QAction)
        self.assertEqual(manager.new_action.text(), "Nouveau")

    def test_open_action_exists(self) -> None:
        """L'action 'Ouvrir' est créée."""
        manager = ActionManager()
        self.assertIsInstance(manager.open_action, QAction)
        self.assertEqual(manager.open_action.text(), "Ouvrir")

    def test_save_action_exists(self) -> None:
        """L'action 'Enregistrer' est créée."""
        manager = ActionManager()
        self.assertIsInstance(manager.save_action, QAction)
        self.assertEqual(manager.save_action.text(), "Enregistrer")

    def test_quit_action_exists(self) -> None:
        """L'action 'Quitter' est créée."""
        manager = ActionManager()
        self.assertIsInstance(manager.quit_action, QAction)
        self.assertEqual(manager.quit_action.text(), "Quitter")

    def test_preferences_action_exists(self) -> None:
        """L'action 'Préférences' est créée."""
        manager = ActionManager()
        self.assertIsInstance(manager.preferences_action, QAction)
        self.assertEqual(manager.preferences_action.text(), "Préférences")

    def test_about_action_exists(self) -> None:
        """L'action 'À propos' est créée."""
        manager = ActionManager()
        self.assertIsInstance(manager.about_action, QAction)
        self.assertEqual(manager.about_action.text(), "À propos")

    def test_transcribe_action_exists(self) -> None:
        """L'action 'Transcrire' est créée."""
        manager = ActionManager()
        self.assertIsInstance(manager.transcribe_action, QAction)
        self.assertEqual(manager.transcribe_action.text(), "Transcrire")

    def test_summarize_action_exists(self) -> None:
        """L'action 'Résumer la transcription' est créée."""
        manager = ActionManager()
        self.assertIsInstance(manager.summarize_action, QAction)
        self.assertEqual(
            manager.summarize_action.text(), "Résumer la transcription"
        )

    def test_export_txt_action_exists(self) -> None:
        """L'action 'Exporter en TXT' est créée."""
        manager = ActionManager()
        self.assertIsInstance(manager.export_txt_action, QAction)
        self.assertEqual(manager.export_txt_action.text(), "Exporter en TXT")

    def test_export_markdown_action_exists(self) -> None:
        """L'action 'Exporter en Markdown' est créée."""
        manager = ActionManager()
        self.assertIsInstance(manager.export_markdown_action, QAction)
        self.assertEqual(
            manager.export_markdown_action.text(), "Exporter en Markdown"
        )

    def test_actions_dictionary(self) -> None:
        """Le dictionnaire expose toutes les actions attendues."""
        manager = ActionManager()
        actions = manager.actions
        expected_keys = {
            "new",
            "open",
            "save",
            "export_txt",
            "export_markdown",
            "quit",
            "transcribe",
            "summarize",
            "preferences",
            "about",
        }
        self.assertEqual(set(actions.keys()), expected_keys)
        for action in actions.values():
            self.assertIsInstance(action, QAction)

    def test_actions_have_no_logic(self) -> None:
        """Les actions ne sont connectées à aucun traitement."""
        manager = ActionManager()
        for action in manager.actions.values():
            self.assertFalse(action.signalsBlocked())


if __name__ == "__main__":
    unittest.main()
