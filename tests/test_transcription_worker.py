"""Tests du worker asynchrone de transcription."""

import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from PySide6.QtCore import QCoreApplication
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from meetingai.core.task import Task, TaskStatus
from meetingai.core.transcription_worker import TranscriptionWorker
from meetingai.models.media_file import MediaFile, MediaType
from meetingai.services.speech_to_text.speech_to_text_service import (
    SpeechToTextService,
)
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class TestTranscriptionWorker(unittest.TestCase):
    """Tests unitaires du worker de transcription."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def _build_media(self) -> MediaFile:
        """Retourne un média factice."""
        return MediaFile(
            path=Path(__file__),
            name="audio.mp3",
            extension=".mp3",
            size=1234,
            media_type=MediaType.AUDIO,
        )

    def _wait_for_signal(self, spy: QSignalSpy, timeout_ms: int = 2000) -> bool:
        """Attend qu'un QSignalSpy reçoive au moins un signal."""
        for _ in range(timeout_ms // 50):
            QCoreApplication.processEvents()
            if spy.count() > 0:
                return True
            time.sleep(0.05)
        return False

    def _wait_for_thread(self, worker: TranscriptionWorker, timeout_ms: int = 2000) -> bool:
        """Attend que le thread interne du worker soit terminé."""
        if worker._thread is None:
            return False
        return worker._thread.wait(timeout_ms)

    def test_worker_emits_finished_with_result(self) -> None:
        """Le worker émet finished avec le résultat en cas de succès."""
        task = Task(name="transcription")
        service = MagicMock(spec=SpeechToTextService)
        expected = TranscriptionResult(
            text="Bonjour",
            language="fr",
            duration=1.0,
            model="fake",
            processing_time=0.1,
            metadata={},
        )
        service.transcribe.return_value = expected
        media = self._build_media()

        worker = TranscriptionWorker(task, service, media)
        spy_finished = QSignalSpy(worker.finished)
        spy_progress = QSignalSpy(worker.progress)

        worker.start()
        self.assertTrue(self._wait_for_signal(spy_finished, timeout_ms=2000))
        self.assertTrue(self._wait_for_thread(worker, timeout_ms=2000))

        self.assertEqual(spy_finished.count(), 1)
        self.assertEqual(spy_finished.at(0)[0], expected)
        self.assertTrue(
            any(spy_progress.at(i)[0] == 100 for i in range(spy_progress.count()))
        )
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIs(task.result, expected)
        service.transcribe.assert_called_once()

    def test_worker_emits_progress_values_from_service(self) -> None:
        """Le worker propage les valeurs de progression du service."""
        task = Task(name="transcription")
        service = MagicMock(spec=SpeechToTextService)
        expected = TranscriptionResult(
            text="Bonjour",
            language="fr",
            duration=1.0,
            model="fake",
            processing_time=0.1,
            metadata={},
        )

        def _transcribe_with_progress(
            media: object,
            task: object,
            progress_callback: object,
        ) -> TranscriptionResult:
            progress_callback(25)
            progress_callback(50)
            progress_callback(75)
            return expected

        service.transcribe.side_effect = _transcribe_with_progress
        media = self._build_media()

        worker = TranscriptionWorker(task, service, media)
        spy_progress = QSignalSpy(worker.progress)
        spy_finished = QSignalSpy(worker.finished)

        worker.start()
        self.assertTrue(self._wait_for_signal(spy_finished, timeout_ms=2000))
        self.assertTrue(self._wait_for_thread(worker, timeout_ms=2000))

        progress_values = [spy_progress.at(i)[0] for i in range(spy_progress.count())]
        self.assertIn(25, progress_values)
        self.assertIn(50, progress_values)
        self.assertIn(75, progress_values)
        self.assertIn(100, progress_values)

    def test_worker_emits_failed_on_error(self) -> None:
        """Le worker émet failed en cas d'erreur du service."""
        task = Task(name="transcription")
        service = MagicMock(spec=SpeechToTextService)
        service.transcribe.side_effect = RuntimeError("modèle absent")
        media = self._build_media()

        worker = TranscriptionWorker(task, service, media)
        spy_failed = QSignalSpy(worker.failed)

        worker.start()
        self.assertTrue(self._wait_for_signal(spy_failed, timeout_ms=2000))
        self.assertTrue(self._wait_for_thread(worker, timeout_ms=2000))

        self.assertEqual(spy_failed.count(), 1)
        self.assertIsInstance(spy_failed.at(0)[0], RuntimeError)
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertEqual(task.error, "modèle absent")

    def test_worker_emits_cancelled_when_cancelled(self) -> None:
        """Le worker émet cancelled si cancel() est appelé avant run()."""
        task = Task(name="transcription")
        service = MagicMock(spec=SpeechToTextService)
        media = self._build_media()

        worker = TranscriptionWorker(task, service, media)
        worker.cancel()
        spy_cancelled = QSignalSpy(worker.cancelled)

        worker.start()
        self.assertTrue(self._wait_for_signal(spy_cancelled, timeout_ms=2000))
        self.assertTrue(self._wait_for_thread(worker, timeout_ms=2000))

        self.assertEqual(spy_cancelled.count(), 1)
        self.assertEqual(task.status, TaskStatus.CANCELLED)
        service.transcribe.assert_not_called()

    def test_worker_emits_model_loading_status(self) -> None:
        """Le worker signale le chargement du modèle avant la transcription."""
        task = Task(name="transcription")
        service = MagicMock(spec=SpeechToTextService)
        service.name.return_value = "FasterWhisper"
        service.is_model_present.return_value = True
        expected = TranscriptionResult(
            text="Bonjour",
            language="fr",
            duration=1.0,
            model="fake",
            processing_time=0.1,
            metadata={},
        )
        service.transcribe.return_value = expected
        media = self._build_media()

        worker = TranscriptionWorker(task, service, media)
        spy_status = QSignalSpy(worker.status)
        spy_finished = QSignalSpy(worker.finished)

        worker.start()
        self.assertTrue(self._wait_for_signal(spy_finished, timeout_ms=2000))
        self.assertTrue(self._wait_for_thread(worker, timeout_ms=2000))

        status_messages = [spy_status.at(i)[0] for i in range(spy_status.count())]
        self.assertTrue(
            any("chargement" in message.lower() for message in status_messages)
        )
        self.assertTrue(
            any("transcription" in message.lower() for message in status_messages)
        )

    def test_worker_emits_model_download_status_when_missing(self) -> None:
        """Le worker signale le téléchargement du modèle s'il n'est pas présent."""
        task = Task(name="transcription")
        service = MagicMock(spec=SpeechToTextService)
        service.name.return_value = "FasterWhisper"
        service.is_model_present.return_value = False
        expected = TranscriptionResult(
            text="Bonjour",
            language="fr",
            duration=1.0,
            model="fake",
            processing_time=0.1,
            metadata={},
        )
        service.transcribe.return_value = expected
        media = self._build_media()

        worker = TranscriptionWorker(task, service, media)
        spy_status = QSignalSpy(worker.status)
        spy_finished = QSignalSpy(worker.finished)

        worker.start()
        self.assertTrue(self._wait_for_signal(spy_finished, timeout_ms=2000))
        self.assertTrue(self._wait_for_thread(worker, timeout_ms=2000))

        status_messages = [spy_status.at(i)[0] for i in range(spy_status.count())]
        self.assertTrue(
            any("téléchargement" in message.lower() for message in status_messages)
        )


if __name__ == "__main__":
    unittest.main()
