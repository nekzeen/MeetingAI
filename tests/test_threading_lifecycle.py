"""Audit du cycle de vie des threads et des workers de transcription."""

import time
import unittest
import weakref
from unittest.mock import MagicMock

from PySide6.QtCore import QCoreApplication, QThread
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from meetingai.core.task import Task, TaskStatus
from meetingai.core.transcription_worker import TranscriptionWorker
from meetingai.core.worker_manager import WorkerManager
from meetingai.models.media_file import MediaFile, MediaType
from meetingai.services.speech_to_text.fake_speech_to_text_service import (
    FakeSpeechToTextService,
)
from meetingai.services.speech_to_text.speech_to_text_service import (
    SpeechToTextService,
)
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class TestThreadingLifecycle(unittest.TestCase):
    """Tests du cycle de vie des workers et threads."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        """Réinitialise le WorkerManager."""
        self.manager = WorkerManager()
        self.manager.clear()
        self.service = FakeSpeechToTextService()

    def tearDown(self) -> None:
        """Laisse le temps aux threads de se terminer et aux objets d'être supprimés."""
        for _ in range(60):
            QCoreApplication.processEvents()
            time.sleep(0.005)

    def _build_worker(self) -> TranscriptionWorker:
        """Crée un worker factice prêt à démarrer."""
        task = Task(name="transcription")
        media = MediaFile(
            path=__file__,
            name="audio.mp3",
            extension=".mp3",
            size=1234,
            media_type=MediaType.AUDIO,
        )
        return TranscriptionWorker(task, self.service, media)

    def _wait_for_signal(self, spy: QSignalSpy, timeout_ms: int = 2000) -> bool:
        """Attend qu'un QSignalSpy reçoive au moins un signal."""
        deadline = time.time() + (timeout_ms / 1000)
        while time.time() < deadline:
            QCoreApplication.processEvents()
            if spy.count() > 0:
                return True
            time.sleep(0.05)
        return False

    def _wait_for_thread(self, worker: TranscriptionWorker, timeout_ms: int = 2000) -> bool:
        """Attend que le thread interne du worker soit terminé."""
        if worker._thread is None:
            return True
        try:
            return worker._thread.wait(timeout_ms)
        except RuntimeError:
            # L'objet C++ a déjà été détruit : le thread est donc terminé.
            return True

    def _thread_is_finished(self, worker: TranscriptionWorker) -> bool:
        """Indique si le thread interne est terminé ou déjà détruit."""
        if worker._thread is None:
            return True
        try:
            return worker._thread.isFinished()
        except RuntimeError:
            return True

    def _thread_is_running(self, worker: TranscriptionWorker) -> bool:
        """Indique si le thread interne est encore en cours."""
        if worker._thread is None:
            return False
        try:
            return worker._thread.isRunning()
        except RuntimeError:
            return False

    def _drain_events(self) -> None:
        """Pompe les événements Qt restants."""
        for _ in range(60):
            QCoreApplication.processEvents()
            time.sleep(0.005)

    def test_worker_finishes_and_thread_terminates_on_success(self) -> None:
        """Le worker termine et son thread se ferme en cas de succès."""
        worker = self._build_worker()
        spy_finished = QSignalSpy(worker.finished)
        thread_id = worker._thread

        worker.start()
        self.assertTrue(self._wait_for_signal(spy_finished, timeout_ms=2000))
        self.assertTrue(self._wait_for_thread(worker, timeout_ms=2000))

        self.assertTrue(self._thread_is_finished(worker))
        self.assertFalse(self._thread_is_running(worker))
        self.assertEqual(worker.task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(worker.task.result)

    def test_worker_finishes_and_thread_terminates_on_failure(self) -> None:
        """Le worker termine et son thread se ferme en cas d'erreur."""
        service = MagicMock(spec=SpeechToTextService)
        service.transcribe.side_effect = RuntimeError("erreur")
        task = Task(name="transcription")
        media = MediaFile(
            path=__file__,
            name="audio.mp3",
            extension=".mp3",
            size=1234,
            media_type=MediaType.AUDIO,
        )
        worker = TranscriptionWorker(task, service, media)
        spy_failed = QSignalSpy(worker.failed)

        worker.start()
        self.assertTrue(self._wait_for_signal(spy_failed, timeout_ms=2000))
        self.assertTrue(self._wait_for_thread(worker, timeout_ms=2000))

        self.assertTrue(self._thread_is_finished(worker))
        self.assertFalse(self._thread_is_running(worker))
        self.assertEqual(task.status, TaskStatus.FAILED)

    def test_worker_finishes_and_thread_terminates_on_cancel(self) -> None:
        """Le worker termine et son thread se ferme si annulé avant run."""
        worker = self._build_worker()
        worker.cancel()
        spy_cancelled = QSignalSpy(worker.cancelled)

        worker.start()
        self.assertTrue(self._wait_for_signal(spy_cancelled, timeout_ms=2000))
        self.assertTrue(self._wait_for_thread(worker, timeout_ms=2000))

        self.assertTrue(self._thread_is_finished(worker))
        self.assertFalse(self._thread_is_running(worker))
        self.assertEqual(worker.task.status, TaskStatus.CANCELLED)

    def test_worker_is_destroyed_after_execution(self) -> None:
        """Le worker QObject est détruit après l'exécution."""
        def _run() -> list[bool]:
            worker = self._build_worker()
            destroyed: list[bool] = []
            worker.destroyed.connect(lambda: destroyed.append(True))
            spy_finished = QSignalSpy(worker.finished)

            worker.start()
            self._wait_for_signal(spy_finished, timeout_ms=2000)
            self._wait_for_thread(worker, timeout_ms=2000)
            self._drain_events()

            # spy_finished est supprimé en sortant du scope, ce qui libère le
            # worker pour sa destruction programmée par deleteLater.
            return destroyed

        destroyed = _run()
        self._drain_events()
        self.assertEqual(destroyed, [True])

    def test_successive_workers_do_not_leak_threads(self) -> None:
        """Plusieurs workers successifs ne laissent pas de thread résiduel."""
        for _ in range(3):
            worker = self._build_worker()
            spy_finished = QSignalSpy(worker.finished)
            worker.start()
            self.assertTrue(self._wait_for_signal(spy_finished, timeout_ms=2000))
            self.assertTrue(self._wait_for_thread(worker, timeout_ms=2000))
            self._drain_events()
            self.assertTrue(self._thread_is_finished(worker))

    def test_simultaneous_workers_run_in_separate_threads(self) -> None:
        """Plusieurs workers peuvent tourner en parallèle sans interférence."""
        workers: list[TranscriptionWorker] = [self._build_worker() for _ in range(3)]
        spies = [QSignalSpy(worker.finished) for worker in workers]
        for worker in workers:
            worker.start()

        for spy in spies:
            self.assertTrue(self._wait_for_signal(spy, timeout_ms=2000))

        for worker in workers:
            self.assertTrue(self._wait_for_thread(worker, timeout_ms=2000))
            self.assertTrue(self._thread_is_finished(worker))
            self.assertEqual(worker.task.status, TaskStatus.COMPLETED)

        # Les threads doivent être des objets distincts.
        thread_ids = set()
        for worker in workers:
            try:
                thread_ids.add(id(worker._thread))
            except RuntimeError:
                pass
        self.assertEqual(len(thread_ids), len(workers))

    def test_worker_manager_cleans_up_after_execution(self) -> None:
        """Le WorkerManager enregistre puis libère le worker."""
        worker = self._build_worker()
        spy_finished = QSignalSpy(worker.finished)
        self.manager.register(worker)
        worker.start()

        self.assertTrue(self._wait_for_signal(spy_finished, timeout_ms=2000))
        self._wait_for_thread(worker, timeout_ms=2000)
        self._drain_events()

        self.manager.unregister(worker.task.id)
        self.assertEqual(self.manager.list_workers(), [])

    def test_signals_support_multiple_connections(self) -> None:
        """Les signaux du worker peuvent être connectés à plusieurs récepteurs."""
        worker = self._build_worker()
        first: list[TranscriptionResult] = []
        second: list[TranscriptionResult] = []
        worker.finished.connect(first.append)
        worker.finished.connect(second.append)
        spy_finished = QSignalSpy(worker.finished)

        worker.start()
        self.assertTrue(self._wait_for_signal(spy_finished, timeout_ms=2000))
        self._wait_for_thread(worker, timeout_ms=2000)
        self._drain_events()

        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 1)
        self.assertEqual(first[0], second[0])


if __name__ == "__main__":
    unittest.main()
