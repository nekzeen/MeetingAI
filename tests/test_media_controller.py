"""Tests du contrôleur de sélection des médias."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

from meetingai.controllers.media_controller import MediaController
from meetingai.core.application_context import ApplicationContext
from meetingai.core.service_registry import ServiceRegistry
from meetingai.core.task_manager import TaskManager
from meetingai.gui.action_manager import ActionManager
from meetingai.logging.logger_manager import LoggerManager
from meetingai.models.media_file import MediaFile, MediaType
from meetingai.services.media_service import MediaService
from meetingai.services.speech_to_text.speech_to_text_service import (
    SpeechToTextService,
)
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class TestMediaController(unittest.TestCase):
    """Tests unitaires du contrôleur média."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        """Prépare un contrôleur avec des dépendances simulées."""
        self.media_service = MagicMock(spec=MediaService)
        self.logger_manager = MagicMock(spec=LoggerManager)
        self.speech_to_text_service = MagicMock(spec=SpeechToTextService)
        self.task_manager = MagicMock(spec=TaskManager)
        self.logger = MagicMock()
        self.logger_manager.get_logger.return_value = self.logger
        self.controller = MediaController(
            media_service=self.media_service,
            logger_manager=self.logger_manager,
            speech_to_text_service=self.speech_to_text_service,
            task_manager=self.task_manager,
        )

    def test_current_media_is_none_initially(self) -> None:
        """Aucun média n'est sélectionné à l'initialisation."""
        self.assertIsNone(self.controller.current_media)

    @patch("meetingai.controllers.media_controller.QFileDialog.getOpenFileName")
    def test_valid_file_selection_updates_current_media(self, mock_dialog) -> None:
        """La sélection d'un fichier valide met à jour le média courant."""
        selected_path = "/tmp/meeting.mp4"
        expected_media = MediaFile(
            path=Path(selected_path).resolve(),
            name="meeting.mp4",
            extension=".mp4",
            size=1234,
            media_type=MediaType.VIDEO,
        )
        mock_dialog.return_value = (selected_path, "")
        self.media_service.open.return_value = expected_media

        self.controller.open_media()

        self.media_service.open.assert_called_once_with(selected_path)
        self.assertIs(self.controller.current_media, expected_media)
        self.logger.info.assert_called_once()

    @patch("meetingai.controllers.media_controller.QFileDialog.getOpenFileName")
    def test_cancelled_dialog_does_nothing(self, mock_dialog) -> None:
        """L'annulation du dialogue ne déclenche aucune action."""
        mock_dialog.return_value = ("", "")

        self.controller.open_media()

        self.media_service.open.assert_not_called()
        self.assertIsNone(self.controller.current_media)
        self.logger.info.assert_not_called()
        self.logger.error.assert_not_called()

    @patch("meetingai.controllers.media_controller.QMessageBox.critical")
    @patch("meetingai.controllers.media_controller.QFileDialog.getOpenFileName")
    def test_invalid_file_shows_error_and_logs(
        self, mock_dialog, mock_critical
    ) -> None:
        """Une erreur de validation affiche une QMessageBox et journalise."""
        selected_path = "/tmp/invalid.txt"
        mock_dialog.return_value = (selected_path, "")
        self.media_service.open.side_effect = ValueError("Format non supporté")

        self.controller.open_media()

        self.media_service.open.assert_called_once_with(selected_path)
        self.assertIsNone(self.controller.current_media)
        self.logger.error.assert_called_once()
        mock_critical.assert_called_once()

    @patch("meetingai.controllers.media_controller.QMessageBox.warning")
    def test_transcribe_without_media_shows_warning(self, mock_warning) -> None:
        """La transcription sans média affiche un avertissement."""
        self.controller.transcribe_current_media()

        self.task_manager.create_task.assert_not_called()
        mock_warning.assert_called_once()

    def test_transcribe_current_media_emits_result(self) -> None:
        """La transcription du média courant émet le résultat."""
        media = MediaFile(
            path=Path("/tmp/audio.mp3").resolve(),
            name="audio.mp3",
            extension=".mp3",
            size=1234,
            media_type=MediaType.AUDIO,
        )
        self.controller._current_media = media
        result = TranscriptionResult(
            text="Cette transcription est simulée.",
            language="fr",
            duration=0.0,
            model="fake",
            processing_time=0.0,
            metadata={},
        )
        self.speech_to_text_service.transcribe.return_value = result
        received: list[TranscriptionResult] = []
        self.controller.transcription_ready.connect(received.append)

        self.controller.transcribe_current_media()

        self.task_manager.create_task.assert_called_once_with("transcription")
        self.speech_to_text_service.transcribe.assert_called_once_with(
            media,
            self.task_manager.create_task.return_value,
        )
        self.assertEqual(received, [result])


class TestMediaControllerIntegration(unittest.TestCase):
    """Tests d'intégration avec ApplicationContext."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        """Réinitialise les singletons et prépare un répertoire temporaire."""
        LoggerManager._reset_instance()
        ServiceRegistry._reset_instance()
        ActionManager._reset_instance()
        MediaService._reset_instance()
        self._temp_dir = tempfile.TemporaryDirectory()
        self._config_path = Path(self._temp_dir.name) / "config.json"
        self._logs_dir = Path(self._temp_dir.name) / "logs"

    def tearDown(self) -> None:
        """Réinitialise les singletons et nettoie le répertoire temporaire."""
        LoggerManager._reset_instance()
        ServiceRegistry._reset_instance()
        ActionManager._reset_instance()
        MediaService._reset_instance()
        self._temp_dir.cleanup()

    def test_media_controller_registered_in_service_registry(self) -> None:
        """MediaController est créé par ApplicationContext et enregistré."""
        context = ApplicationContext(
            config_path=self._config_path,
            logs_dir=self._logs_dir,
        )

        self.assertIsInstance(context.media_controller, MediaController)
        self.assertIs(
            context.service_registry.get("media_controller"),
            context.media_controller,
        )


if __name__ == "__main__":
    unittest.main()
