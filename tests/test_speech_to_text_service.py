"""Tests de l'abstraction Speech-To-Text."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from meetingai.core.application_context import ApplicationContext
from meetingai.core.service_registry import ServiceRegistry
from meetingai.core.task import Task
from meetingai.core.task_manager import TaskManager
from meetingai.core.worker_manager import WorkerManager
from meetingai.gui.action_manager import ActionManager
from meetingai.logging.logger_manager import LoggerManager
from meetingai.models.media_file import MediaFile, MediaType
from meetingai.services.media_service import MediaService
from meetingai.services.model_manager import ModelManager
from meetingai.services.speech_to_text import (
    FakeSpeechToTextService,
    NullSpeechToTextService,
    SpeechToTextService,
    TranscriptionResult,
)


class TestSpeechToTextService(unittest.TestCase):
    """Tests du contrat Speech-To-Text."""

    def test_abstract_class_cannot_be_instantiated(self) -> None:
        """SpeechToTextService est une classe abstraite."""
        with self.assertRaises(TypeError):
            SpeechToTextService()

    def test_null_service_returns_metadata(self) -> None:
        """NullSpeechToTextService expose des métadonnées cohérentes."""
        service = NullSpeechToTextService()

        self.assertEqual(service.name(), "NullSpeechToText")
        self.assertEqual(service.version(), "0.0.0")
        self.assertEqual(service.supported_languages(), [])
        self.assertFalse(service.is_available())

    def test_null_transcribe_raises_not_implemented(self) -> None:
        """La transcription du placeholder lève NotImplementedError."""
        service = NullSpeechToTextService()
        media = MagicMock(spec=MediaFile)
        task = MagicMock(spec=Task)

        with self.assertRaises(NotImplementedError):
            service.transcribe(media, task)

    def test_null_cancel_raises_not_implemented(self) -> None:
        """L'annulation du placeholder lève NotImplementedError."""
        service = NullSpeechToTextService()

        with self.assertRaises(NotImplementedError):
            service.cancel("task-id")


class TestTranscriptionResult(unittest.TestCase):
    """Tests de la dataclass TranscriptionResult."""

    def test_result_creation(self) -> None:
        """TranscriptionResult stocke les champs attendus."""
        result = TranscriptionResult(
            text="Bonjour",
            language="fr",
            duration=42.0,
            model="null",
            processing_time=1.5,
            metadata={"confidence": 0.99},
        )

        self.assertEqual(result.text, "Bonjour")
        self.assertEqual(result.language, "fr")
        self.assertEqual(result.duration, 42.0)
        self.assertEqual(result.model, "null")
        self.assertEqual(result.processing_time, 1.5)
        self.assertEqual(result.metadata, {"confidence": 0.99})


class TestSpeechToTextIntegration(unittest.TestCase):
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
        TaskManager._reset_instance()
        ModelManager._reset_instance()
        WorkerManager._reset_instance()
        self._temp_dir = tempfile.TemporaryDirectory()
        self._config_path = Path(self._temp_dir.name) / "config.json"
        self._logs_dir = Path(self._temp_dir.name) / "logs"

    def tearDown(self) -> None:
        """Réinitialise les singletons et nettoie le répertoire temporaire."""
        LoggerManager._reset_instance()
        ServiceRegistry._reset_instance()
        ActionManager._reset_instance()
        MediaService._reset_instance()
        TaskManager._reset_instance()
        ModelManager._reset_instance()
        WorkerManager._reset_instance()
        self._temp_dir.cleanup()

    def test_service_registered_in_application_context(self) -> None:
        """ApplicationContext enregistre FakeSpeechToTextService par défaut."""
        context = ApplicationContext(
            config_path=self._config_path,
            logs_dir=self._logs_dir,
        )

        self.assertIsInstance(
            context.speech_to_text_service,
            FakeSpeechToTextService,
        )
        self.assertIs(
            context.service_registry.get("speech_to_text_service"),
            context.speech_to_text_service,
        )


if __name__ == "__main__":
    unittest.main()
