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
            "speech_to_text_providers": ["fake", "faster-whisper"],
            "model_name": "small",
            "device": "auto",
            "compute_type": "int8",
            "output_directory": "output",
            "summarization_provider": "fake",
            "summarization_providers": ["fake", "ollama"],
            "summarization_model": "llama3.2",
            "summarization_available_models": [],
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

    def test_summarization_group_exists(self) -> None:
        """La section Résumé IA est présente."""
        groups = self.window.findChildren(QGroupBox)
        titles = [group.title() for group in groups]
        self.assertIn("Résumé IA", titles)

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
        self.assertEqual(settings["summarization_provider"], "fake")
        self.assertEqual(settings["summarization_model"], "llama3.2")

    def _find_combo_by_items(self, expected_items: set[str]) -> QComboBox:
        """Retourne le QComboBox dont tous les items attendus sont présents."""
        for combo in self.window.findChildren(QComboBox):
            items = set(self._combo_items(combo))
            if expected_items <= items:
                return combo
        raise AssertionError("QComboBox non trouvé")

    def _find_summarization_model_combo(self) -> QComboBox:
        """Retourne le QComboBox de sélection du modèle de résumé IA."""
        combo = self.window.findChild(QComboBox, "summarization_model_combo")
        assert combo is not None
        return combo

    def test_summarization_model_combo_is_populated(self) -> None:
        """Le modèle de résumé se remplit avec les modèles disponibles."""
        self.window.close()
        self.window.deleteLater()
        settings = self.initial_settings.copy()
        settings["summarization_available_models"] = [
            "llama3.2",
            "mistral",
        ]
        self.window = SettingsWindow(settings)

        combo = self._find_summarization_model_combo()

        self.assertIn("llama3.2", self._combo_items(combo))
        self.assertIn("mistral", self._combo_items(combo))

    def test_get_settings_reflects_changes(self) -> None:
        """get_settings retourne les valeurs modifiées."""
        theme_combo = self._find_combo_by_items({"light", "dark"})
        language_combo = self._find_combo_by_items({"fr", "en"})
        provider_combo = self._find_combo_by_items({"fake", "faster-whisper"})
        device_combo = self._find_combo_by_items({"auto", "cpu", "cuda"})
        compute_combo = self._find_combo_by_items(
            {"int8", "float16", "int16", "float32"}
        )

        theme_combo.setCurrentText("dark")
        language_combo.setCurrentText("en")
        provider_combo.setCurrentText("fake")
        device_combo.setCurrentText("cpu")
        compute_combo.setCurrentText("float16")

        model_combo = self._find_summarization_model_combo()
        model_combo.setCurrentText("mistral")

        edits = self.window.findChildren(QLineEdit)
        model_edit = edits[0]
        output_edit = next(
            edit for edit in edits if edit.text() == "output"
        )
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
        self.assertEqual(settings["summarization_provider"], "fake")
        self.assertEqual(settings["summarization_model"], "mistral")

    def test_get_settings_reflects_summarization_provider_change(self) -> None:
        """get_settings reflète le changement de provider de résumé."""
        self.window.close()
        self.window.deleteLater()
        settings = self.initial_settings.copy()
        settings["summarization_providers"] = ["fake", "custom"]
        settings["summarization_provider"] = "fake"
        self.window = SettingsWindow(settings)

        summary_combo = self._find_combo_by_items({"fake", "custom"})
        summary_combo.setCurrentText("custom")

        result = self.window.get_settings()

        self.assertEqual(result["summarization_provider"], "custom")

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
