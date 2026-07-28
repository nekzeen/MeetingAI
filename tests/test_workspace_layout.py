"""Tests de l'organisation du Workspace."""

import unittest

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QSplitter, QWidget

from meetingai.gui.widgets.history_widget import HistoryWidget
from meetingai.gui.widgets.media_information_widget import MediaInformationWidget
from meetingai.gui.widgets.summary_widget import SummaryWidget
from meetingai.gui.widgets.transcript_widget import TranscriptWidget
from meetingai.gui.workspace import Workspace


class TestWorkspaceLayout(unittest.TestCase):
    """Tests de la structure du Workspace."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        """Instancie le workspace avant chaque test."""
        self.workspace = Workspace()

    def test_workspace_is_widget(self) -> None:
        """Le workspace est un QWidget."""
        self.assertIsInstance(self.workspace, QWidget)

    def test_contains_media_information_widget(self) -> None:
        """Le workspace contient le widget d'information du média."""
        self.assertIsInstance(
            self.workspace.media_information_widget,
            MediaInformationWidget,
        )

    def test_contains_history_widget(self) -> None:
        """Le workspace contient le panneau d'historique."""
        self.assertIsInstance(
            self.workspace.history_widget,
            HistoryWidget,
        )

    def test_contains_transcript_widget(self) -> None:
        """Le workspace contient le panneau de transcription."""
        self.assertIsInstance(
            self.workspace.transcript_widget,
            TranscriptWidget,
        )

    def test_contains_summary_widget(self) -> None:
        """Le workspace contient le panneau de résumé IA."""
        self.assertIsInstance(
            self.workspace.summary_widget,
            SummaryWidget,
        )

    def test_has_horizontal_splitter(self) -> None:
        """Le workspace utilise un QSplitter horizontal."""
        splitter = self.workspace.findChild(QSplitter)
        self.assertIsNotNone(splitter)
        self.assertEqual(splitter.orientation(), Qt.Orientation.Horizontal)

    def test_splitter_has_two_columns(self) -> None:
        """Le splitter contient exactement deux colonnes."""
        splitter = self.workspace.findChild(QSplitter)
        self.assertEqual(splitter.count(), 2)


if __name__ == "__main__":
    unittest.main()
