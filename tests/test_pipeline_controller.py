"""Tests du contrôleur de pipeline automatique."""

import tempfile
import time
import unittest
from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from meetingai.config.config_manager import ConfigManager
from meetingai.controllers.export_controller import ExportController
from meetingai.controllers.pipeline_controller import PipelineController
from meetingai.controllers.summarization_controller import (
    SummarizationController,
)
from meetingai.controllers.transcription_controller import (
    TranscriptionController,
)
from meetingai.core.task_manager import TaskManager
from meetingai.core.worker_manager import WorkerManager
from meetingai.logging.logger_manager import LoggerManager
from meetingai.models.media_file import MediaFile, MediaType
from meetingai.services.export.export_service import ExportService
from meetingai.services.speech_to_text.fake_speech_to_text_service import (
    FakeSpeechToTextService,
)
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)
from meetingai.services.summarization.summarization_factory import (
    SummarizationFactory,
)
from meetingai.services.summarization.summarization_service import (
    SummarizationService,
)
from meetingai.services.summarization.summary_result import SummaryResult


class TestPipelineController(unittest.TestCase):
    """Tests du pipeline automatique."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        """Prépare les contrôleurs et une configuration temporaire."""
        LoggerManager._reset_instance()
        self._temp_dir = tempfile.TemporaryDirectory()
        config_path = Path(self._temp_dir.name) / "config.json"
        self.config_manager = ConfigManager(config_path)
        self.config_manager.set(
            "export.output_directory",
            self._temp_dir.name,
        )

        self.task_manager = TaskManager()
        self.worker_manager = WorkerManager()
        self.worker_manager.clear()
        self.logger_manager = LoggerManager(
            config_manager=self.config_manager,
            logs_dir=Path(self._temp_dir.name) / "logs",
        )

        self.speech_service = FakeSpeechToTextService()
        self.transcription_controller = TranscriptionController(
            speech_to_text_service=self.speech_service,
            task_manager=self.task_manager,
            worker_manager=self.worker_manager,
            logger_manager=self.logger_manager,
        )
        self.summarization_controller = SummarizationController(
            factory=SummarizationFactory(),
            config_manager=self.config_manager,
        )
        self.export_controller = ExportController(
            export_service=ExportService(),
            config_manager=self.config_manager,
        )
        self.pipeline_controller = PipelineController(
            transcription_controller=self.transcription_controller,
            summarization_controller=self.summarization_controller,
            export_controller=self.export_controller,
        )
        self.media = MediaFile(
            path=__file__,
            name="audio.mp3",
            extension=".mp3",
            size=1234,
            media_type=MediaType.AUDIO,
        )

    def tearDown(self) -> None:
        """Traite les événements Qt en attente et nettoie."""
        for _ in range(60):
            QCoreApplication.processEvents()
            time.sleep(0.005)
        LoggerManager._reset_instance()
        TaskManager._reset_instance()
        WorkerManager._reset_instance()
        self._temp_dir.cleanup()

    def _wait_for_signal(
        self,
        spy: QSignalSpy,
        timeout_ms: int = 2000,
    ) -> bool:
        """Attend qu'un QSignalSpy reçoive au moins un signal."""
        for _ in range(timeout_ms // 50):
            QCoreApplication.processEvents()
            if spy.count() > 0:
                return True
            time.sleep(0.05)
        return False

    def test_pipeline_runs_all_steps(self) -> None:
        """Le pipeline exécute transcription, résumé et export."""
        spy_succeeded = QSignalSpy(self.pipeline_controller.pipeline_succeeded)
        spy_failed = QSignalSpy(self.pipeline_controller.pipeline_failed)

        self.pipeline_controller.start(self.media)

        self.assertTrue(self._wait_for_signal(spy_succeeded, timeout_ms=2000))
        self.assertEqual(spy_failed.count(), 0)
        self.assertEqual(len(spy_succeeded.at(0)[0]), 1)
        exported_path = Path(spy_succeeded.at(0)[0][0])
        self.assertEqual(exported_path.suffix, ".txt")
        self.assertTrue(exported_path.exists())

    def test_pipeline_fails_without_media(self) -> None:
        """Le pipeline échoue immédiatement si aucun média n'est fourni."""
        spy_failed = QSignalSpy(self.pipeline_controller.pipeline_failed)

        self.pipeline_controller.start(None)

        self.assertEqual(spy_failed.count(), 1)
        self.assertIn("Aucun média", spy_failed.at(0)[0])

    def test_pipeline_stops_on_transcription_error(self) -> None:
        """Le pipeline s'arrête si la transcription échoue."""
        def _raise(*args: object, **kwargs: object) -> object:
            raise RuntimeError("erreur transcription")

        self.speech_service.transcribe = _raise

        spy_failed = QSignalSpy(self.pipeline_controller.pipeline_failed)
        spy_succeeded = QSignalSpy(self.pipeline_controller.pipeline_succeeded)

        self.pipeline_controller.start(self.media)

        self.assertTrue(self._wait_for_signal(spy_failed, timeout_ms=2000))
        self.assertEqual(spy_succeeded.count(), 0)
        self.assertIn("Transcription échouée", spy_failed.at(0)[0])
        self.assertIn("erreur transcription", spy_failed.at(0)[0])

    def test_pipeline_stops_on_summarization_error(self) -> None:
        """Le pipeline s'arrête si le résumé IA échoue."""
        self.config_manager.set("summarization.provider", "unknown")

        spy_failed = QSignalSpy(self.pipeline_controller.pipeline_failed)
        spy_succeeded = QSignalSpy(self.pipeline_controller.pipeline_succeeded)

        self.pipeline_controller.start(self.media)

        self.assertTrue(self._wait_for_signal(spy_failed, timeout_ms=2000))
        self.assertEqual(spy_succeeded.count(), 0)
        self.assertIn("Résumé IA échoué", spy_failed.at(0)[0])

    def test_pipeline_steps_order(self) -> None:
        """Les étapes du pipeline sont émises dans le bon ordre."""
        spy_steps = QSignalSpy(self.pipeline_controller.pipeline_step_started)
        spy_succeeded = QSignalSpy(self.pipeline_controller.pipeline_succeeded)

        self.pipeline_controller.start(self.media)

        self._wait_for_signal(spy_succeeded, timeout_ms=2000)
        steps = [spy_steps.at(i)[0] for i in range(spy_steps.count())]
        self.assertIn("transcription", steps)
        self.assertIn("summarization", steps)
        self.assertIn("export", steps)
        self.assertEqual(
            steps,
            ["transcription", "summarization", "export"],
        )

    def test_pipeline_reports_progress(self) -> None:
        """La progression de la transcription remonte via le pipeline."""
        spy_progress = QSignalSpy(self.pipeline_controller.pipeline_progress)
        spy_succeeded = QSignalSpy(self.pipeline_controller.pipeline_succeeded)

        self.pipeline_controller.start(self.media)

        self._wait_for_signal(spy_succeeded, timeout_ms=2000)
        progress_values = [
            spy_progress.at(i)[0] for i in range(spy_progress.count())
        ]
        self.assertIn(100, progress_values)

    def test_pipeline_ignores_manual_summary(self) -> None:
        """Un résumé manuel en dehors du pipeline n'active pas l'export."""
        spy_export = QSignalSpy(self.export_controller.export_succeeded)
        result = TranscriptionResult(
            text="Texte isolé.",
            language="fr",
            duration=1.0,
            model="fake",
            processing_time=0.1,
            metadata={},
        )

        self.summarization_controller.on_transcription_ready(result)
        self.summarization_controller.summarize_current_transcription()
        QCoreApplication.processEvents()

        self.assertEqual(spy_export.count(), 0)


if __name__ == "__main__":
    unittest.main()
