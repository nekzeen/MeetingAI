"""Tests du flux de transcription simulée."""

import unittest
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QLabel

from meetingai.core.task import Task
from meetingai.gui.widgets.transcript_widget import TranscriptWidget
from meetingai.models.media_file import MediaFile, MediaType
from meetingai.services.speech_to_text.fake_speech_to_text_service import (
    FakeSpeechToTextService,
)
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class TestFakeSpeechToTextService(unittest.TestCase):
    """Tests du moteur de transcription fictif."""

    def test_transcribe_returns_fixed_text(self) -> None:
        """La transcription simulée retourne le texte attendu."""
        service = FakeSpeechToTextService()
        media = MediaFile(
            path=Path("/tmp/audio.mp3").resolve(),
            name="audio.mp3",
            extension=".mp3",
            size=1,
            media_type=MediaType.AUDIO,
        )
        task = Task(name="transcription")

        result = service.transcribe(media, task)

        self.assertIsInstance(result, TranscriptionResult)
        self.assertEqual(result.text, "Cette transcription est simulée.")
        self.assertEqual(result.language, "fr")
        self.assertTrue(service.is_available())


class TestTranscriptWidgetDisplay(unittest.TestCase):
    """Tests d'affichage du résultat dans TranscriptWidget."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def test_set_transcription_displays_text(self) -> None:
        """Le widget affiche le texte du résultat de transcription."""
        widget = TranscriptWidget()
        result = TranscriptionResult(
            text="Cette transcription est simulée.",
            language="fr",
            duration=0.0,
            model="fake",
            processing_time=0.0,
            metadata={},
        )

        widget.set_transcription(result)

        labels = widget.findChildren(QLabel)
        texts = [label.text() for label in labels]
        self.assertIn("Cette transcription est simulée.", texts)


class _FakeMediaController(QObject):
    """Contrôleur factice émettant media_loaded et transcription_ready."""

    media_loaded = Signal(object)
    transcription_ready = Signal(object)


class TestWorkspaceTranscriptionSignal(unittest.TestCase):
    """Tests de propagation du signal de transcription vers le widget."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def test_signal_updates_transcript_widget(self) -> None:
        """transcription_ready met à jour le TranscriptWidget."""
        from meetingai.gui.workspace import Workspace

        controller = _FakeMediaController()
        workspace = Workspace(media_controller=controller)
        result = TranscriptionResult(
            text="Cette transcription est simulée.",
            language="fr",
            duration=0.0,
            model="fake",
            processing_time=0.0,
            metadata={},
        )

        controller.transcription_ready.emit(result)

        labels = workspace.transcript_widget.findChildren(QLabel)
        texts = [label.text() for label in labels]
        self.assertIn("Cette transcription est simulée.", texts)


if __name__ == "__main__":
    unittest.main()
