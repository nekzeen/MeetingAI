"""Tests du contrôleur de transcription."""

import unittest
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from meetingai.controllers.transcription_controller import (
    TranscriptionController,
)
from meetingai.core.task import TaskStatus
from meetingai.core.task_manager import TaskManager
from meetingai.core.worker_manager import WorkerManager
from meetingai.logging.logger_manager import LoggerManager
from meetingai.models.media_file import MediaFile, MediaType
from meetingai.services.speech_to_text.speech_to_text_service import (
    SpeechToTextService,
)
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class TestTranscriptionController(unittest.TestCase):
    """Tests unitaires du contrôleur de transcription."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        """Prépare les dépendances simulées."""
        self.speech_service = MagicMock(spec=SpeechToTextService)
        self.task_manager = MagicMock(spec=TaskManager)
        self.worker_manager = MagicMock(spec=WorkerManager)
        self.logger_manager = MagicMock(spec=LoggerManager)
        self.logger = MagicMock()
        self.logger_manager.get_logger.return_value = self.logger

        self.controller = TranscriptionController(
            speech_to_text_service=self.speech_service,
            task_manager=self.task_manager,
            worker_manager=self.worker_manager,
            logger_manager=self.logger_manager,
        )
        self.media = MediaFile(
            path=__file__,
            name="audio.mp3",
            extension=".mp3",
            size=1234,
            media_type=MediaType.AUDIO,
        )

    def test_dependencies_injected(self) -> None:
        """Le contrôleur reçoit bien ses dépendances."""
        self.assertIs(self.controller._speech_to_text_service, self.speech_service)
        self.assertIs(self.controller._task_manager, self.task_manager)
        self.assertIs(self.controller._worker_manager, self.worker_manager)

    def test_transcribe_emits_started_progress_ready(self) -> None:
        """transcribe émet started, progress et ready."""
        task = MagicMock()
        self.task_manager.create_task.return_value = task
        result = TranscriptionResult(
            text="Résultat",
            language="fr",
            duration=1.0,
            model="fake",
            processing_time=0.1,
            metadata={},
        )
        self.speech_service.transcribe.return_value = result

        started: list[object] = []
        progress: list[int] = []
        ready: list[TranscriptionResult] = []
        self.controller.transcription_started.connect(started.append)
        self.controller.transcription_progress.connect(progress.append)
        self.controller.transcription_ready.connect(ready.append)

        returned = self.controller.transcribe(self.media)

        self.assertIs(returned, task)
        self.assertEqual(len(started), 1)
        self.assertEqual(progress, [0, 100])
        self.assertEqual(ready, [result])
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIs(task.result, result)
        self.speech_service.transcribe.assert_called_once_with(self.media, task)

    def test_transcribe_emits_failed_on_error(self) -> None:
        """transcribe émet failed en cas d'erreur du service."""
        task = MagicMock()
        self.task_manager.create_task.return_value = task
        self.speech_service.transcribe.side_effect = RuntimeError("modèle absent")

        progress: list[int] = []
        failed: list[str] = []
        self.controller.transcription_progress.connect(progress.append)
        self.controller.transcription_failed.connect(failed.append)

        returned = self.controller.transcribe(self.media)

        self.assertIs(returned, task)
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertEqual(task.error, "modèle absent")
        self.assertIn("modèle absent", failed)


if __name__ == "__main__":
    unittest.main()
