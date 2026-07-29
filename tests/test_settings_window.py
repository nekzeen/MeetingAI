"""Tests de la fenêtre de paramètres."""

import unittest

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLineEdit,
    QPushButton,
)

from meetingai.gui.settings_window import SettingsWindow


class TestSettingsWindow(unittest.TestCase):
    """Tests unitaires de la fenêtre de paramètres."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        """Instancie la fenêtre de paramètres avec des valeurs par défaut."""
        self.initial_settings = {
            "theme": "light",
            "language": "fr",
            "provider": "faster-whisper",
            "model_name": "small",
            "device": "auto",
            "compute_type": "int8",
            "output_directory": "output",
        }
        self.window = SettingsWindow(self.initial_settings)

    def tearDown(self) -> None:
        """Ferme et détruit la fenêtre."""
        self.window.close()
        self.window.deleteLater()

    def test_window_is_qdialog(self) -> None:
        """La fenêtre de paramètres hérite de QDialog."""
        self.assertIsInstance(self.window, QDialog)

    def test_window_title(self) -> None:
        """La fenêtre porte le titre attendu."""
        self.assertEqual(self.window.windowTitle(), "Paramètres")

    def test_general_group_exists(self) -> None:
        """La section Général est présente."""
        groups = self.window.findChildren(QGroupBox)
        titles = [group.title() for group in groups]
        self.assertIn("Général", titles)

    def test_speech_to_text_group_exists(self) -> None:
        """La section Speech-To-Text est présente."""
        groups = self.window.findChildren(QGroupBox)
        titles = [group.title() for group in groups]
        self.assertIn("Speech-To-Text", titles)

    def test_export_group_exists(self) -> None:
        """La section Export est présente."""
        groups = self.window.findChildren(QGroupBox)
        titles = [group.title() for group in groups]
        self.assertIn("Export", titles)

    def _combo_items(self, combo: QComboBox) -> list[str]:
        """Retourne la liste des textes d'un QComboBox."""
        return [combo.itemText(i) for i in range(combo.count())]

    def test_theme_combo_is_populated(self) -> None:
        """Le champ Thème propose les valeurs attendues."""
        combos = self.window.findChildren(QComboBox)
        self.assertTrue(len(combos) > 0)
        theme_combo = combos[0]
        items = self._combo_items(theme_combo)
        self.assertIn("light", items)
        self.assertIn("dark", items)

    def test_initial_values_are_loaded(self) -> None:
        """Les valeurs initiales sont chargées dans les champs."""
        settings = self.window.get_settings()

        self.assertEqual(settings["theme"], "light")
        self.assertEqual(settings["language"], "fr")
        self.assertEqual(settings["provider"], "faster-whisper")
        self.assertEqual(settings["model_name"], "small")
        self.assertEqual(settings["device"], "auto")
        self.assertEqual(settings["compute_type"], "int8")
        self.assertEqual(settings["output_directory"], "output")

    def test_get_settings_reflects_changes(self) -> None:
        """get_settings retourne les valeurs modifiées."""
        combos = self.window.findChildren(QComboBox)
        combos[0].setCurrentText("dark")
        combos[1].setCurrentText("en")
        combos[2].setCurrentText("fake")
        combos[3].setCurrentText("cpu")
        combos[4].setCurrentText("float16")

        edits = self.window.findChildren(QLineEdit)
        model_edit = edits[0]
        output_edit = edits[1]
        model_edit.setText("medium")
        output_edit.setText("custom")

        settings = self.window.get_settings()

        self.assertEqual(settings["theme"], "dark")
        self.assertEqual(settings["language"], "en")
        self.assertEqual(settings["provider"], "fake")
        self.assertEqual(settings["model_name"], "medium")
        self.assertEqual(settings["device"], "cpu")
        self.assertEqual(settings["compute_type"], "float16")
        self.assertEqual(settings["output_directory"], "custom")

    def test_has_ok_and_cancel_buttons(self) -> None:
        """La fenêtre dispose des boutons OK et Annuler."""
        button_box = self.window.findChild(QDialogButtonBox)
        self.assertIsNotNone(button_box)
        self.assertTrue(
            button_box.standardButtons()
            & QDialogButtonBox.StandardButton.Ok
        )
        self.assertTrue(
            button_box.standardButtons()
            & QDialogButtonBox.StandardButton.Cancel
        )


if __name__ == "__main__":
    unittest.main()
