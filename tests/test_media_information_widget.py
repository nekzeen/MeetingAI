"""Tests du widget d'affichage des informations d'un média."""

import unittest
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QLabel

from meetingai.gui.widgets.media_information_widget import MediaInformationWidget
from meetingai.gui.workspace import Workspace
from meetingai.models.media_file import MediaFile, MediaType


class _FakeMediaController(QObject):
    """Contrôleur factice émettant media_loaded et transcription_ready."""

    media_loaded = Signal(object)
    transcription_ready = Signal(object)


class TestMediaInformationWidget(unittest.TestCase):
    """Tests du widget MediaInformationWidget."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        """Instancie le widget avant chaque test."""
        self.widget = MediaInformationWidget()

    def test_empty_state_shows_no_media(self) -> None:
        """L'état initial indique qu'aucun média n'est sélectionné."""
        self.assertEqual(self.widget._name_label.text(), "Aucun média sélectionné")
        self.assertEqual(self.widget._path_label.text(), "-")
        self.assertEqual(self.widget._type_label.text(), "-")
        self.assertEqual(self.widget._extension_label.text(), "-")
        self.assertEqual(self.widget._size_label.text(), "-")

    def test_set_media_updates_labels(self) -> None:
        """Les labels sont mis à jour avec les informations du média."""
        media = MediaFile(
            path=Path("/tmp/meeting.mp4").resolve(),
            name="meeting.mp4",
            extension=".mp4",
            size=12345,
            media_type=MediaType.VIDEO,
        )

        self.widget.set_media(media)

        self.assertEqual(self.widget._name_label.text(), "meeting.mp4")
        self.assertEqual(
            self.widget._path_label.text(),
            str(Path("/tmp/meeting.mp4").resolve()),
        )
        self.assertEqual(self.widget._type_label.text(), "video")
        self.assertEqual(self.widget._extension_label.text(), ".mp4")
        self.assertEqual(self.widget._size_label.text(), "12345 octets")

    def test_update_media_replaces_previous_display(self) -> None:
        """L'affichage est remplacé lors du changement de média."""
        first = MediaFile(
            path=Path("/tmp/first.mp3").resolve(),
            name="first.mp3",
            extension=".mp3",
            size=111,
            media_type=MediaType.AUDIO,
        )
        second = MediaFile(
            path=Path("/tmp/second.wav").resolve(),
            name="second.wav",
            extension=".wav",
            size=222,
            media_type=MediaType.AUDIO,
        )

        self.widget.set_media(first)
        self.widget.set_media(second)

        self.assertEqual(self.widget._name_label.text(), "second.wav")
        self.assertEqual(self.widget._size_label.text(), "222 octets")

    def test_set_none_clears_display(self) -> None:
        """Passer ``None`` réinitialise l'affichage."""
        media = MediaFile(
            path=Path("/tmp/meeting.mp4").resolve(),
            name="meeting.mp4",
            extension=".mp4",
            size=1,
            media_type=MediaType.VIDEO,
        )
        self.widget.set_media(media)

        self.widget.set_media(None)

        self.assertEqual(
            self.widget._name_label.text(),
            "Aucun média sélectionné",
        )


class TestWorkspaceIntegration(unittest.TestCase):
    """Tests de l'intégration du widget dans Workspace."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def test_workspace_contains_media_information_widget(self) -> None:
        """Le workspace contient le widget d'information."""
        workspace = Workspace()

        self.assertIsInstance(
            workspace.media_information_widget,
            MediaInformationWidget,
        )

    def test_media_loaded_signal_updates_widget(self) -> None:
        """Le signal ``media_loaded`` met à jour le widget du workspace."""
        controller = _FakeMediaController()
        workspace = Workspace(media_controller=controller)
        media = MediaFile(
            path=Path("/tmp/sample.mp3").resolve(),
            name="sample.mp3",
            extension=".mp3",
            size=42,
            media_type=MediaType.AUDIO,
        )

        controller.media_loaded.emit(media)

        info = workspace.media_information_widget
        self.assertEqual(info._name_label.text(), "sample.mp3")
        self.assertEqual(info._type_label.text(), "audio")


if __name__ == "__main__":
    unittest.main()
