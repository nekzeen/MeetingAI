"""Tests de la fenêtre d'état du Runtime."""

import unittest
from unittest.mock import MagicMock

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
)

from meetingai.gui.runtime_window import RuntimeWindow
from meetingai.runtime.runtime_action import RuntimeAction, RuntimeActionType
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus


class TestRuntimeWindow(unittest.TestCase):
    """Tests unitaires de la fenêtre d'état du système."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        """Instancie la fenêtre avec un contrôleur simulé."""
        self.controller = MagicMock()
        self.controller.refresh.return_value = (
            RuntimeStatus.HEALTHY,
            [],
            [],
        )
        self.controller.report_for.return_value = None
        self.window = RuntimeWindow(self.controller)

    def tearDown(self) -> None:
        """Ferme et détruit la fenêtre."""
        self.window.close()
        self.window.deleteLater()

    def test_window_is_qdialog(self) -> None:
        """La fenêtre hérite de QDialog."""
        self.assertIsInstance(self.window, QDialog)

    def test_window_title(self) -> None:
        """La fenêtre porte le titre attendu."""
        self.assertEqual(self.window.windowTitle(), "État du système")

    def test_status_label_exists(self) -> None:
        """Le libellé de l'état global est présent."""
        label = self.window.findChild(QLabel, "status_label")
        self.assertIsNotNone(label)
        self.assertIn("HEALTHY", label.text())

    def test_reports_table_exists(self) -> None:
        """Le tableau des diagnostics est présent."""
        table = self.window.findChild(QTableWidget, "reports_table")
        self.assertIsNotNone(table)
        self.assertEqual(table.columnCount(), 3)

    def test_actions_list_exists(self) -> None:
        """La liste des actions est présente."""
        self.assertIsNotNone(self.window.findChild(QListWidget, "actions_list"))

    def test_refresh_button_exists(self) -> None:
        """Le bouton de rafraîchissement est présent."""
        button = self.window.findChild(QPushButton, "refresh_button")
        self.assertIsNotNone(button)
        self.assertEqual(button.text(), "Rafraîchir")

    def test_reports_are_populated(self) -> None:
        """Le tableau est rempli avec les rapports fournis."""
        report = RuntimeReport(
            provider_name="whisper",
            status=RuntimeStatus.HEALTHY,
            message="Tout va bien.",
            details={},
        )
        self.controller.refresh.return_value = (RuntimeStatus.HEALTHY, [report], [])
        self.window._refresh()

        table = self.window.findChild(QTableWidget, "reports_table")
        self.assertEqual(table.rowCount(), 1)
        self.assertEqual(table.item(0, 0).text(), "whisper")
        self.assertEqual(table.item(0, 1).text(), "HEALTHY")
        self.assertEqual(table.item(0, 2).text(), "Tout va bien.")

    def test_actions_are_populated(self) -> None:
        """La liste est remplie avec les actions fournies."""
        action = RuntimeAction(
            action_type=RuntimeActionType.DOWNLOAD_MODEL,
            provider_name="whisper",
            message="Télécharger le modèle.",
            description="Action requise.",
            available=True,
            requires_user=True,
        )
        self.controller.refresh.return_value = (RuntimeStatus.MISSING, [], [action])
        self.window._refresh()

        list_widget = self.window.findChild(QListWidget, "actions_list")
        self.assertEqual(list_widget.count(), 1)

    def test_available_action_button_is_enabled(self) -> None:
        """Le bouton d'une action disponible est actif."""
        action = RuntimeAction(
            action_type=RuntimeActionType.DOWNLOAD_MODEL,
            provider_name="whisper",
            message="Télécharger le modèle.",
            available=True,
            requires_user=True,
        )
        self.controller.refresh.return_value = (RuntimeStatus.MISSING, [], [action])
        self.window._refresh()

        button = self.window.findChild(QPushButton, "action_button_0")
        self.assertIsNotNone(button)
        self.assertTrue(button.isEnabled())

    def test_unavailable_action_button_is_disabled(self) -> None:
        """Le bouton d'une action indisponible est inactif."""
        action = RuntimeAction(
            action_type=RuntimeActionType.INSTALL_PACKAGE,
            provider_name="ollama",
            message="Installer Ollama.",
            available=False,
            requires_user=True,
        )
        self.controller.refresh.return_value = (RuntimeStatus.MISSING, [], [action])
        self.window._refresh()

        button = self.window.findChild(QPushButton, "action_button_0")
        self.assertIsNotNone(button)
        self.assertFalse(button.isEnabled())

    def test_diagnostic_group_exists(self) -> None:
        """La section Diagnostics est présente."""
        groups = self.window.findChildren(QGroupBox)
        titles = [group.title() for group in groups]
        self.assertIn("Diagnostics", titles)
        self.assertIn("Actions recommandées", titles)

    def test_whisper_group_exists(self) -> None:
        """La section Whisper est présente."""
        group = self.window.findChild(QGroupBox, "whisper_group")
        self.assertIsNotNone(group)

    def test_whisper_install_button_exists(self) -> None:
        """Le bouton d'installation Whisper est présent."""
        button = self.window.findChild(QPushButton, "whisper_install_button")
        self.assertIsNotNone(button)
        self.assertEqual(button.text(), "Installer")

    def test_whisper_section_is_populated(self) -> None:
        """La section Whisper affiche les informations du rapport."""
        report = RuntimeReport(
            provider_name="whisper",
            status=RuntimeStatus.MISSING,
            message="Modèle absent.",
            details={
                "model_size": "small",
                "model_path": "models/small",
                "version": "1.2.1",
            },
        )
        self.controller.report_for.return_value = report
        self.window._refresh()

        self.assertIn("small", self.window.findChild(QLabel, "whisper_model_label").text())
        self.assertIn("models/small", self.window.findChild(QLabel, "whisper_path_label").text())
        self.assertIn("1.2.1", self.window.findChild(QLabel, "whisper_info_label").text())

    def test_whisper_install_button_enabled_when_missing(self) -> None:
        """Le bouton Installer est actif lorsque le modèle est manquant."""
        report = RuntimeReport(
            provider_name="whisper",
            status=RuntimeStatus.MISSING,
            message="",
            details={},
        )
        self.controller.report_for.return_value = report
        self.window._refresh()

        button = self.window.findChild(QPushButton, "whisper_install_button")
        self.assertTrue(button.isEnabled())

    def test_whisper_install_button_disabled_when_healthy(self) -> None:
        """Le bouton Installer est inactif lorsque le modèle est sain."""
        report = RuntimeReport(
            provider_name="whisper",
            status=RuntimeStatus.HEALTHY,
            message="",
            details={},
        )
        self.controller.report_for.return_value = report
        self.window._refresh()

        button = self.window.findChild(QPushButton, "whisper_install_button")
        self.assertFalse(button.isEnabled())

    def test_run_install_uses_controller(self) -> None:
        """L'installation délègue au contrôleur dans un thread."""
        self.controller.install.return_value = RuntimeReport(
            provider_name="whisper",
            status=RuntimeStatus.HEALTHY,
            message="ok",
            details={},
        )

        self.window._run_install("whisper")

        thread = self.window._install_thread
        self.assertIsNotNone(thread)
        self.assertTrue(thread.wait(2000))
        self.controller.install.assert_called_once_with("whisper")

    def test_ollama_group_exists(self) -> None:
        """La section Ollama est présente."""
        group = self.window.findChild(QGroupBox, "ollama_group")
        self.assertIsNotNone(group)

    def test_ollama_section_is_populated(self) -> None:
        """La section Ollama affiche les informations du rapport."""
        report = RuntimeReport(
            provider_name="ollama",
            status=RuntimeStatus.DEGRADED,
            message="Modèle manquant.",
            details={
                "host": "http://localhost:11434",
                "version": "0.5.0",
                "model": "llama3.2",
                "installed_models": ["llama3"],
            },
        )
        self.controller.report_for = MagicMock(
            side_effect=lambda name: report if name == "ollama" else None
        )
        self.window._refresh()

        self.assertIn(
            "0.5.0",
            self.window.findChild(QLabel, "ollama_version_label").text(),
        )
        self.assertIn(
            "llama3.2",
            self.window.findChild(QLabel, "ollama_model_label").text(),
        )
        self.assertIn(
            "llama3",
            self.window.findChild(QLabel, "ollama_models_label").text(),
        )

    def test_run_start_server_uses_controller(self) -> None:
        """Le démarrage de serveur délègue au contrôleur dans un thread."""
        self.controller.start_server.return_value = RuntimeReport(
            provider_name="ollama",
            status=RuntimeStatus.HEALTHY,
            message="ok",
            details={},
        )

        self.window._run_start_server("ollama")

        thread = self.window._start_server_thread
        self.assertIsNotNone(thread)
        self.assertTrue(thread.wait(2000))
        self.controller.start_server.assert_called_once_with("ollama")

    def test_ollama_models_list_is_populated(self) -> None:
        """La liste des modèles Ollama est remplie avec le diagnostic."""
        report = RuntimeReport(
            provider_name="ollama",
            status=RuntimeStatus.HEALTHY,
            message="ok",
            details={
                "host": "http://localhost:11434",
                "version": "0.5.0",
                "model": "llama3.2",
                "installed_models": ["llama3.2", "mistral"],
            },
        )
        self.controller.report_for = MagicMock(
            side_effect=lambda name: report if name == "ollama" else None
        )
        self.window._refresh()

        models_list = self.window.findChild(QListWidget, "ollama_models_list")
        self.assertEqual(models_list.count(), 2)
        self.assertIn("mistral", models_list.item(1).text())

    def test_ollama_model_input_exists(self) -> None:
        """Le champ de saisie d'un modèle Ollama est présent."""
        self.assertIsNotNone(
            self.window.findChild(QLineEdit, "ollama_model_input")
        )

    def test_details_group_exists(self) -> None:
        """La section Détails techniques est présente."""
        group = self.window.findChild(QGroupBox, "details_group")
        self.assertIsNotNone(group)
        self.assertIn("Détails", group.title())

    def test_details_edit_exists(self) -> None:
        """Le QTextEdit de détails est présent et accessible."""
        self.assertIsNotNone(
            self.window.findChild(QTextEdit, "details_edit")
        )

    def test_reports_have_tooltips(self) -> None:
        """Les cellules du tableau de diagnostics ont un tooltip."""
        report = RuntimeReport(
            provider_name="whisper",
            status=RuntimeStatus.MISSING,
            message="Modèle absent.",
            details={},
        )
        self.controller.refresh.return_value = (RuntimeStatus.MISSING, [report], [])
        self.controller.report_for.return_value = None
        self.window._refresh()

        table = self.window.findChild(QTableWidget, "reports_table")
        self.assertEqual(table.item(0, 0).toolTip(), "whisper")
        self.assertEqual(table.item(0, 2).toolTip(), "Modèle absent.")


if __name__ == "__main__":
    unittest.main()
