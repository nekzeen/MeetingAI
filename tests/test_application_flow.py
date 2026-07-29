"""Tests d'intégration du flux utilisateur complet."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QFileDialog

from meetingai.core.application_context import ApplicationContext
from meetingai.core.service_registry import ServiceRegistry
from meetingai.core.task_manager import TaskManager
from meetingai.core.worker_manager import WorkerManager
from meetingai.gui.action_manager import ActionManager
from meetingai.gui.main_window import MainWindow
from meetingai.logging.logger_manager import LoggerManager
from meetingai.services.media_service import MediaService


class TestApplicationFlow(unittest.TestCase):
    """Vérifie le parcours utilisateur : ouvrir un média, puis transcrire."""

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
        WorkerManager._reset_instance()
        self._temp_dir.cleanup()

    def test_transcribe_receives_current_media_after_open(self) -> None:
        """L'action Transcrire transmet le média courant au contrôleur."""
        with tempfile.NamedTemporaryFile(
            suffix=".mp3", delete=False, dir=self._temp_dir.name
        ) as fake_media:
            fake_media.write(b"fake audio")
            media_path = fake_media.name

        with patch.object(
            QFileDialog,
            "getOpenFileName",
            return_value=(media_path, ""),
        ):
            context = ApplicationContext(
                config_path=self._config_path,
                logs_dir=self._logs_dir,
            )
            window = MainWindow(context=context)

            received_media = [None]
            original_transcribe = context.transcription_controller.transcribe

            def _capture_transcribe(media) -> object:
                received_media[0] = media
                return original_transcribe(media)

            context.transcription_controller.transcribe = _capture_transcribe

            context.action_manager.open_action.trigger()
            self.assertIsNotNone(context.media_controller.current_media)

            context.action_manager.transcribe_action.trigger()
            self.assertIs(
                received_media[0],
                context.media_controller.current_media,
            )
            self.assertIsNotNone(received_media[0])

            window.close()
            window.deleteLater()


if __name__ == "__main__":
    unittest.main()
