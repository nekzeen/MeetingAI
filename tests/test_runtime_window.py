"""Tests de la fenêtre d'état du Runtime."""

import unittest
from unittest.mock import MagicMock

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QGroupBox,
    QLabel,
    QListWidget,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
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


if __name__ == "__main__":
    unittest.main()
