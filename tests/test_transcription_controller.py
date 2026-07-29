"""Tests du contrôleur de transcription."""

import time
import unittest
from unittest.mock import MagicMock

from PySide6.QtCore import QCoreApplication
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QMessageBox

from meetingai.controllers.transcription_controller import (
    TranscriptionController,
)
from meetingai.core.task import Task
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
        self.worker_manager = WorkerManager()
        self.worker_manager.clear()
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
        self.task = Task(name="transcription")
        self.task_manager.create_task.return_value = self.task

    def tearDown(self) -> None:
        """Traite les événements Qt en attente et attend le nettoyage."""
        for _ in range(60):
            QCoreApplication.processEvents()
            time.sleep(0.005)

    def test_dependencies_injected(self) -> None:
        """Le contrôleur reçoit bien ses dépendances."""
        self.assertIs(self.controller._speech_to_text_service, self.speech_service)
        self.assertIs(self.controller._task_manager, self.task_manager)
        self.assertIs(self.controller._worker_manager, self.worker_manager)

    def test_transcribe_without_media_warns(self) -> None:
        """transcribe affiche un avertissement si aucun média n'est fourni."""
        with unittest.mock.patch.object(
            QMessageBox,
            "warning",
            return_value=None,
        ) as mock_warning:
            result = self.controller.transcribe(None)

        self.assertIsNone(result)
        self.task_manager.create_task.assert_not_called()
        mock_warning.assert_called_once()

    def test_transcribe_emits_started_and_ready(self) -> None:
        """transcribe démarre un worker et émet ready à la fin."""
        expected = TranscriptionResult(
            text="Résultat",
            language="fr",
            duration=1.0,
            model="fake",
            processing_time=0.1,
            metadata={},
        )
        self.speech_service.transcribe.return_value = expected

        spy_started = QSignalSpy(self.controller.transcription_started)
        spy_ready = QSignalSpy(self.controller.transcription_ready)
        spy_progress = QSignalSpy(self.controller.transcription_progress)

        returned = self.controller.transcribe(self.media)

        self.assertIs(returned, self.task)
        self.assertEqual(spy_started.count(), 1)
        self.assertEqual(spy_progress.count(), 1)

        self._wait_for_signal(spy_ready, timeout_ms=2000)
        self.assertEqual(spy_ready.count(), 1)
        self.assertEqual(spy_ready.at(0)[0], expected)
        self.assertTrue(spy_progress.count() >= 1)
        self.speech_service.transcribe.assert_called_once_with(self.media, self.task)

    def test_transcribe_emits_failed_on_error(self) -> None:
        """transcribe émet failed en cas d'erreur du service."""
        self.speech_service.transcribe.side_effect = RuntimeError("modèle absent")

        spy_failed = QSignalSpy(self.controller.transcription_failed)
        returned = self.controller.transcribe(self.media)

        self.assertIs(returned, self.task)
        self._wait_for_signal(spy_failed, timeout_ms=2000)
        self.assertEqual(spy_failed.count(), 1)
        self.assertIn("modèle absent", spy_failed.at(0)[0])

    def test_worker_is_cleaned_up_after_success(self) -> None:
        """Le worker est supprimé du registre actif après le traitement."""
        self.speech_service.transcribe.return_value = TranscriptionResult(
            text="OK",
            language="fr",
            duration=0.0,
            model="fake",
            processing_time=0.0,
            metadata={},
        )

        spy_ready = QSignalSpy(self.controller.transcription_ready)
        self.controller.transcribe(self.media)

        self._wait_for_signal(spy_ready, timeout_ms=2000)
        QCoreApplication.processEvents()
        self.assertEqual(self.controller._active_workers, {})

    def _wait_for_signal(self, spy: QSignalSpy, timeout_ms: int = 2000) -> bool:
        """Attend qu'un QSignalSpy reçoive au moins un signal."""
        for _ in range(timeout_ms // 50):
            QCoreApplication.processEvents()
            if spy.count() > 0:
                return True
            time.sleep(0.05)
        return False


if __name__ == "__main__":
    unittest.main()
